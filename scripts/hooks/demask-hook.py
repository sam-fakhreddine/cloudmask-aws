#!/usr/bin/env python3
"""CloudMask post-tool-use hook for Claude Code.

After Claude writes or edits a shadow file (containing anonymized content),
this hook unanonymizes the content and writes it back to the real file path.

Depends on mask-hook.py running as a PreToolUse hook to create the shadow
files and populate the mapping.

Shadow layout: ~/.cloudmask/hooks/shadow/<real-path-without-leading-slash>
Mapping:       ~/.cloudmask/hooks/mapping.json

Install
-------
1. Copy to ~/.claude/hooks/demask-hook.py
2. Add to ~/.claude/settings.json:

    {
      "hooks": {
        "PostToolUse": [
          {
            "matcher": "Write|Edit",
            "hooks": [
              {
                "type": "command",
                "command": "python3 ~/.claude/hooks/demask-hook.py",
                "timeout": 30
              }
            ]
          }
        ]
      }
    }

Note: This hook intentionally does NOT import cloudmask. The unanonymize
logic is a simple reverse string-replace, keeping the post-hook fast and
dependency-light.
"""

import fcntl
import json
import os
import re
import sys
import tempfile
from pathlib import Path

SHADOW_ROOT = Path.home() / ".cloudmask" / "hooks" / "shadow"
MAPPING_PATH = Path.home() / ".cloudmask" / "hooks" / "mapping.json"
MAX_UNANONYMIZE_PASSES = 5


def _shadow_to_real(shadow_path: Path) -> Path:
    """Convert a shadow path back to the original real path."""
    resolved_shadow = shadow_path.resolve()
    resolved_root = SHADOW_ROOT.resolve()
    rel = resolved_shadow.relative_to(resolved_root)
    real = (Path("/") / rel).resolve()
    # Block path traversal: real path must not contain shadow root
    if str(real).startswith(str(resolved_root)):
        raise ValueError(f"Real path resolves inside shadow root: {real}")
    return real


def _is_shadow(file_path: str) -> bool:
    """Check if a path is under the shadow root."""
    try:
        Path(file_path).relative_to(SHADOW_ROOT)
        return True
    except ValueError:
        return False


def _load_reverse_mapping() -> dict[str, str]:
    """Load the mapping file and return anonymized->original dict."""
    if not MAPPING_PATH.is_file():
        return {}

    # Acquire shared lock for read consistency with mask-hook writes
    lock_file = None
    try:
        lock_path = MAPPING_PATH.with_suffix(".lock")
        lock_file = lock_path.open("w")
        fcntl.flock(lock_file.fileno(), fcntl.LOCK_SH)
    except OSError:
        pass

    try:
        raw = json.loads(MAPPING_PATH.read_text(encoding="utf-8"))

        # Ensure mapping has secure permissions
        try:
            os.chmod(MAPPING_PATH, 0o600)
        except OSError:
            pass

        # Robust format detection: only use "mappings" key if it exists
        if "_metadata" in raw:
            forward = raw.get("mappings", {})
        else:
            forward = raw

        # Filter non-string entries to prevent TypeErrors during replacement
        return {
            v: k for k, v in forward.items()
            if isinstance(k, str) and isinstance(v, str)
        }
    finally:
        if lock_file is not None:
            try:
                fcntl.flock(lock_file.fileno(), fcntl.LOCK_UN)
                lock_file.close()
            except OSError:
                pass


def _unanonymize(text: str, reverse: dict[str, str]) -> str:
    """Replace anonymized tokens with originals using regex for O(M) per pass.

    Multiple passes handle chained mappings (A->B->C) from ARN re-anonymization.
    """
    if not reverse:
        return text
    # Build regex alternation (longest first to avoid partial matches)
    sorted_keys = sorted(reverse, key=len, reverse=True)
    pattern = re.compile("|".join(re.escape(k) for k in sorted_keys))
    converged = False
    for _ in range(MAX_UNANONYMIZE_PASSES):
        prev = text
        text = pattern.sub(lambda m: reverse[m.group(0)], text)
        if text == prev:
            converged = True
            break
    if not converged:
        print(
            f"cloudmask demask-hook: unanonymize did not converge in {MAX_UNANONYMIZE_PASSES} passes",
            file=sys.stderr,
        )
    return text


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
        reverse = _load_reverse_mapping()
        if not reverse:
            return

        content = shadow.read_text(encoding="utf-8")
        restored = _unanonymize(content, reverse)

        real = _shadow_to_real(shadow)
        real.parent.mkdir(parents=True, exist_ok=True)
        # Atomic write to prevent truncation on interrupt
        fd, tmp = tempfile.mkstemp(dir=real.parent, prefix=".demask_", suffix=".tmp")
        try:
            with os.fdopen(fd, "w", encoding="utf-8") as f:
                f.write(restored)
            os.chmod(tmp, 0o600)
            os.replace(tmp, real)
        except BaseException:
            try:
                os.unlink(tmp)
            except OSError:
                pass
            raise
    except Exception as e:
        print(f"cloudmask demask-hook error: {e!r}", file=sys.stderr)


if __name__ == "__main__":
    main()
    sys.exit(0)
