#!/usr/bin/env python3
"""CloudMask pre-tool-use hook for Claude Code.

Intercepts Read/Write/Edit operations to anonymize AWS identifiers before
Claude processes file content. Writes anonymized copies to a shadow directory
and redirects Claude's tool operations to those shadow copies.

Shadow layout: ~/.cloudmask/hooks/shadow/<real-path-without-leading-slash>
Mapping:       ~/.cloudmask/hooks/mapping.json
Seed:          $CLOUDMASK_SEED env var, or "claude-hook-default-seed"

Install
-------
1. pip install cloudmask-aws  (or: uv pip install -e ".[dev]" from repo root)
2. Copy to ~/.claude/hooks/mask-hook.py
3. Add to ~/.claude/settings.json:

    {
      "hooks": {
        "PreToolUse": [
          {
            "matcher": "Read|Write|Edit",
            "hooks": [
              {
                "type": "command",
                "command": "python3 ~/.claude/hooks/mask-hook.py",
                "timeout": 30
              }
            ]
          }
        ]
      }
    }

Limitations
-----------
- Only covers file Read/Write/Edit. Grep results, Bash output, and user-typed
  prompts reach Claude unmasked.
- Files >10 MB or with non-text extensions are passed through unmasked.
- Requires cloudmask-aws to be importable by the python3 in your PATH.
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
SEED = os.environ.get("CLOUDMASK_SEED", "")
if not SEED:
    print("CLOUDMASK_SEED not set. Run: python3 scripts/install-hooks.py", file=sys.stderr)
    sys.exit(0)  # Exit cleanly — hook produces no output, Claude reads file normally
MAX_FILE_SIZE = 10_000_000

INCLUDE_EXT = frozenset(
    {
        ".tf",
        ".tfvars",
        ".hcl",
        ".yaml",
        ".yml",
        ".json",
        ".toml",
        ".py",
        ".js",
        ".ts",
        ".jsx",
        ".tsx",
        ".sh",
        ".bash",
        ".zsh",
        ".cfg",
        ".ini",
        ".conf",
        ".env",
        ".properties",
        ".txt",
        ".md",
        ".rst",
        ".log",
        ".csv",
        ".xml",
        ".go",
        ".rs",
        ".java",
        ".rb",
    }
)

_QUICK_SCAN = re.compile(
    r"(?:"
    r"(?:vpc|subnet|sg|igw|rtb|eni|eip|vol|snap|ami|i|r|lt|asg|elb|tg|"
    r"elbv2|natgw|vpce|acl|pcx|vgw|cgw|vpn|dopt|nacl)-[0-9a-f]{4,17}"
    r"|\b\d{12}\b"
    r"|arn:aws:"
    r")"
)


def _real_to_shadow(real_path: str) -> Path:
    """Convert a real absolute path to its shadow counterpart."""
    resolved = Path(real_path).resolve()
    shadow = SHADOW_ROOT / str(resolved).lstrip("/")
    # Validate shadow stays under SHADOW_ROOT
    shadow.resolve().relative_to(SHADOW_ROOT.resolve())
    return shadow


def _shadow_exists(real_path: str) -> bool:
    """Check whether a shadow copy already exists for this real path."""
    return _real_to_shadow(real_path).exists()


def _respond(updated_input: dict) -> None:
    """Write a PreToolUse hook response that redirects the tool to a new input."""
    json.dump(
        {
            "hookSpecificOutput": {
                "hookEventName": "PreToolUse",
                "permissionDecision": "allow",
                "updatedInput": updated_input,
            }
        },
        sys.stdout,
    )


def _handle_read(file_path: str) -> None:
    """Intercept Read: anonymize file content, redirect to shadow copy."""
    real = Path(file_path)

    if not real.is_file():
        return
    ext = real.suffix.lower()
    if ext and ext not in INCLUDE_EXT:
        return
    try:
        if real.stat().st_size > MAX_FILE_SIZE:
            return
    except OSError:
        return

    try:
        content = real.read_text(encoding="utf-8")
    except (UnicodeDecodeError, OSError):
        return

    if not _QUICK_SCAN.search(content):
        return

    try:
        from cloudmask.core import CloudMask

        mask = CloudMask(seed=SEED)

        if MAPPING_PATH.exists():
            mask.load_mapping(MAPPING_PATH)
        mapping_size_before = len(mask.mapping)

        anonymized = mask.anonymize(content)

        shadow = _real_to_shadow(file_path)
        shadow.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
        # Atomic write with secure permissions
        fd, tmp = tempfile.mkstemp(dir=shadow.parent, prefix=".mask_", suffix=".tmp")
        try:
            with os.fdopen(fd, "w", encoding="utf-8") as f:
                f.write(anonymized)
            os.chmod(tmp, 0o600)
            os.replace(tmp, shadow)
        except BaseException:
            os.unlink(tmp)
            raise

        if len(mask.mapping) > mapping_size_before:
            MAPPING_PATH.parent.mkdir(parents=True, exist_ok=True)
            mask.save_mapping(MAPPING_PATH)

        _respond({"file_path": str(shadow)})
    except Exception as e:
        print(f"cloudmask mask-hook error: {e!r}", file=sys.stderr)
        return


def _handle_write_or_edit(file_path: str) -> None:
    """Redirect Write/Edit to the shadow copy if the file was previously masked."""
    if not _shadow_exists(file_path):
        return
    shadow = _real_to_shadow(file_path)
    real = Path(file_path)
    # If real file is newer than shadow, shadow is stale — re-anonymize first
    if real.is_file():
        try:
            if real.stat().st_mtime > shadow.stat().st_mtime:
                _handle_read(file_path)
                if not shadow.is_file():
                    return
        except OSError:
            pass
    _respond({"file_path": str(shadow)})


def main() -> None:
    """Read hook input from stdin, dispatch by tool name."""
    try:
        hook = json.load(sys.stdin)
    except (json.JSONDecodeError, EOFError):
        return

    tool = hook.get("tool_name", "")
    file_path = hook.get("tool_input", {}).get("file_path", "")
    if not file_path:
        return

    if tool == "Read":
        _handle_read(file_path)
    elif tool in ("Write", "Edit"):
        _handle_write_or_edit(file_path)


if __name__ == "__main__":
    main()
    sys.exit(0)
