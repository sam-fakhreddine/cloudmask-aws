#!/usr/bin/env python3
"""CloudMask post-tool-use hook for Claude Code.

After Claude writes or edits a shadow file (containing anonymized content),
this hook unanonymizes the content and writes it back to the real file path.

Depends on mask-hook.py running as a PreToolUse hook to create the shadow
files and populate the mapping.

Shadow layout: ~/.cloudmask/hooks/shadow/<real-path-without-leading-slash>
Mapping:       ~/.cloudmask/hooks/mapping.json (encrypted at rest)

Install
-------
1. Copy to ~/.claude/hooks/demask-hook.py
2. Run: python3 scripts/install-hooks.py

Note: This hook avoids importing cloudmask for fast startup. Decryption uses
the cryptography library directly (via _hook_common), and unanonymize is a
simple reverse string-replace with chain resolution.
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

from _hook_common import MAPPING_PATH, SHADOW_ROOT, decrypt_json, read_seed

SEED_FILE = Path.home() / ".cloudmask" / "seed"


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

        with contextlib.suppress(OSError):
            MAPPING_PATH.chmod(0o600)

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


def _atomic_write(content: str, target: Path) -> None:
    """Write content to target path atomically."""
    target.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
    fd, tmp = tempfile.mkstemp(dir=target.parent, prefix=".demask_", suffix=".tmp")
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            f.write(content)
        Path(tmp).chmod(0o600)
        Path(tmp).replace(target)
    except BaseException:
        with contextlib.suppress(OSError):
            Path(tmp).unlink()
        raise


def main() -> None:
    """Read hook input from stdin, unanonymize shadow files back to real paths."""
    try:
        hook = json.load(sys.stdin)
    except (json.JSONDecodeError, EOFError):
        return

    file_path = hook.get("tool_input", {}).get("file_path", "")
    if not file_path or not _is_shadow(file_path):
        return

    shadow = Path(file_path)
    if not shadow.is_file():
        return

    try:
        content = shadow.read_text(encoding="utf-8")

        reverse = _load_reverse_mapping()
        if not reverse:
            print(
                f"cloudmask demask-hook: ERROR \u2014 reverse mapping is empty but shadow "
                f"file exists. Refusing to write anonymized content to real file. "
                f"Check {MAPPING_PATH}",
                file=sys.stderr,
            )
            return

        restored = _unanonymize(content, reverse)
        _atomic_write(restored, _shadow_to_real(shadow))
    except Exception as e:
        print(f"cloudmask demask-hook error: {e!r}", file=sys.stderr)


if __name__ == "__main__":
    main()
    sys.exit(0)
