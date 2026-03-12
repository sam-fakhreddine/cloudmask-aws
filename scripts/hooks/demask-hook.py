#!/usr/bin/env python3
"""CloudMask post-tool-use hook for Claude Code.

Handles two cases after Claude writes or edits a file:

1. Shadow writes: Claude wrote to a shadow file (redirected by mask-hook).
   Unanonymizes the content and writes it back to the real file path.

2. Real-path writes: Claude wrote a NEW file (e.g. CSV, report) while working
   with anonymized content. Checks for anonymized tokens in the output and
   replaces them with real values in-place.

Depends on mask-hook.py running as a PreToolUse hook to create the shadow
files and populate the mapping.

Shadow layout: ~/.cloudmask/hooks/shadow/<real-path-without-leading-slash>
Mapping:       ~/.cloudmask/hooks/mapping.json (encrypted at rest)
"""

import contextlib
import fcntl
import json
import os
import re
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from _hook_common import MAPPING_PATH, SHADOW_ROOT, decrypt_json, get_logger, read_seed

SEED_FILE = Path.home() / ".cloudmask" / "seed"

log = get_logger("demask")
log.debug("demask-hook loaded, pid=%d", os.getpid())


def _shadow_to_real(shadow_path: Path) -> Path:
    """Convert a shadow path back to the original real path."""
    resolved_shadow = shadow_path.resolve()
    resolved_root = SHADOW_ROOT.resolve()
    rel = resolved_shadow.relative_to(resolved_root)
    real = (Path("/") / rel).resolve()
    if str(real).startswith(str(resolved_root)):
        raise ValueError(f"Real path resolves inside shadow root: {real}")
    return real


def _is_shadow(file_path: str) -> bool:
    """Check if a path is under the shadow root."""
    try:
        Path(file_path).resolve().relative_to(SHADOW_ROOT.resolve())
        return True
    except ValueError:
        return False


def _load_reverse_mapping() -> dict[str, str]:
    """Load the mapping file and return anonymized->original dict."""
    if not MAPPING_PATH.is_file():
        return {}

    lock_file = None
    try:
        lock_path = MAPPING_PATH.with_suffix(".lock")
        lock_file = lock_path.open("w")
        fcntl.flock(lock_file.fileno(), fcntl.LOCK_SH)
    except OSError:
        pass

    try:
        raw = MAPPING_PATH.read_bytes()
        if not raw:
            return {}

        seed = read_seed()
        if seed:
            try:
                data = decrypt_json(raw, seed)
            except Exception:
                try:
                    data = json.loads(raw.decode("utf-8"))
                except (json.JSONDecodeError, UnicodeDecodeError):
                    return {}
        else:
            try:
                data = json.loads(raw.decode("utf-8"))
            except (json.JSONDecodeError, UnicodeDecodeError):
                return {}

        forward = data.get("mappings", {}) if "_metadata" in data else data

        return {v: k for k, v in forward.items() if isinstance(k, str) and isinstance(v, str)}
    finally:
        if lock_file is not None:
            try:
                fcntl.flock(lock_file.fileno(), fcntl.LOCK_UN)
                lock_file.close()
            except OSError:
                pass


def _resolve_chains(reverse: dict[str, str]) -> dict[str, str]:
    """Resolve transitive chains: if A->B and B->C exists, produce A->C."""
    resolved: dict[str, str] = {}
    for key, value in reverse.items():
        seen = {key}
        current = value
        while current in reverse and current not in seen:
            seen.add(current)
            current = reverse[current]
        resolved[key] = current
    return resolved


def _unanonymize(text: str, reverse: dict[str, str]) -> str:
    """Replace anonymized tokens with originals in a single pass.

    Chains (A->B->C from ARN re-anonymization) are resolved in the mapping
    before text replacement, so one regex pass suffices.
    """
    if not reverse:
        return text
    resolved = _resolve_chains(reverse)
    sorted_keys = sorted(resolved, key=len, reverse=True)
    pattern = re.compile("|".join(re.escape(k) for k in sorted_keys))
    return pattern.sub(lambda m: resolved[m.group(0)], text)


MAX_FILE_SIZE = 10_000_000


def _atomic_write(content: str, target: Path) -> None:
    """Write content to target path atomically."""
    target.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
    fd, tmp = tempfile.mkstemp(dir=target.parent, prefix=".demask_", suffix=".tmp")
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            f.write(content)
        Path(tmp).chmod(0o600)
        Path(tmp).replace(target)
    except Exception:
        with contextlib.suppress(OSError):
            Path(tmp).unlink()
        raise


def _handle_shadow_write(file_path: str) -> None:
    """Unanonymize a shadow file and write back to the real path."""
    shadow = Path(file_path)
    if not shadow.is_file():
        log.debug("Shadow file does not exist, skipping")
        return

    try:
        content = shadow.read_text(encoding="utf-8")

        reverse = _load_reverse_mapping()
        if not reverse:
            log.error("Reverse mapping empty but shadow exists, refusing to write")
            print(
                f"cloudmask demask-hook: ERROR \u2014 reverse mapping is empty but shadow "
                f"file exists. Refusing to write anonymized content to real file. "
                f"Check {MAPPING_PATH}",
                file=sys.stderr,
            )
            return

        restored = _unanonymize(content, reverse)
        real_path = _shadow_to_real(shadow)
        _atomic_write(restored, real_path)
        log.info("Restored %s -> %s (%d reverse mappings)", shadow, real_path, len(reverse))
    except Exception as e:
        log.error("demask-hook shadow error: %s", type(e).__name__)
        print(f"cloudmask demask-hook error: {type(e).__name__}", file=sys.stderr)


def _handle_real_write(file_path: str) -> None:
    """Check a newly written real file for anonymized tokens and unanonymize in-place.

    When Claude works with anonymized content (from shadow files) and creates
    a new output file (CSV, report, etc.), the output contains anonymized
    identifiers. This function detects and reverses them.
    """
    real = Path(file_path)
    if not real.is_file():
        return

    try:
        if real.stat().st_size > MAX_FILE_SIZE:
            log.debug("Real write: file too large (%d), skipping", real.stat().st_size)
            return
    except OSError:
        return

    try:
        content = real.read_text(encoding="utf-8")
    except (UnicodeDecodeError, OSError):
        return

    reverse = _load_reverse_mapping()
    if not reverse:
        log.debug("Real write: no reverse mapping, skipping")
        return

    restored = _unanonymize(content, reverse)
    if restored == content:
        log.debug("Real write: no anonymized tokens found in %s", file_path)
        return

    _atomic_write(restored, real)
    log.info("Real write: unanonymized %s in-place (%d reverse mappings)", file_path, len(reverse))


def main() -> None:
    """Read hook input from stdin, unanonymize shadow files back to real paths."""
    try:
        hook = json.load(sys.stdin)
    except (json.JSONDecodeError, EOFError):
        log.error("Failed to parse hook input from stdin")
        return

    tool = hook.get("tool_name", "")
    file_path = hook.get("tool_input", {}).get("file_path", "")
    log.debug("tool=%s, file_path=%s", tool, file_path)
    if not file_path:
        log.debug("No file_path, skipping")
        return

    if _is_shadow(file_path):
        _handle_shadow_write(file_path)
    else:
        _handle_real_write(file_path)


if __name__ == "__main__":
    main()
    sys.exit(0)
