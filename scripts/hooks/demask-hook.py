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

import json
import sys
from pathlib import Path

SHADOW_ROOT = Path.home() / ".cloudmask" / "hooks" / "shadow"
MAPPING_PATH = Path.home() / ".cloudmask" / "hooks" / "mapping.json"


def _shadow_to_real(shadow_path: Path) -> Path:
    """Convert a shadow path back to the original real path."""
    rel = shadow_path.relative_to(SHADOW_ROOT)
    return Path("/") / rel


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

    raw = json.loads(MAPPING_PATH.read_text(encoding="utf-8"))
    forward = raw.get("mappings", raw) if "_metadata" in raw else raw

    return {v: k for k, v in forward.items()}


def _unanonymize(text: str, reverse: dict[str, str]) -> str:
    """Replace anonymized tokens with originals, multi-pass.

    Multiple passes are needed because the anonymizer can produce chained
    mappings (A->B->C) when ARN components get re-anonymized. Each pass
    resolves one level of the chain.
    """
    sorted_items = sorted(reverse.items(), key=lambda x: len(x[0]), reverse=True)
    for _ in range(5):
        prev = text
        for anon, orig in sorted_items:
            text = text.replace(anon, orig)
        if text == prev:
            break
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
        real.write_text(restored, encoding="utf-8")
    except Exception:
        pass


if __name__ == "__main__":
    main()
    sys.exit(0)
