#!/usr/bin/env python3
"""CloudMask pre-tool-use hook for Claude Code.

Intercepts Read/Write/Edit operations to anonymize AWS identifiers before
Claude processes file content. Writes anonymized copies to a shadow directory
and redirects Claude's tool operations to those shadow copies.

Shadow layout: ~/.cloudmask/hooks/shadow/<real-path-without-leading-slash>
Mapping:       ~/.cloudmask/hooks/mapping.json (encrypted at rest)
Seed:          OS keychain > ~/.cloudmask/seed > $CLOUDMASK_SEED env var

Install
-------
1. pip install cloudmask-aws  (or: uv pip install -e ".[dev]" from repo root)
2. Copy to ~/.claude/hooks/mask-hook.py
3. Run: python3 scripts/install-hooks.py

Limitations
-----------
- Grep results and Bash output reach Claude unmasked.
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

sys.path.insert(0, str(Path(__file__).resolve().parent))

from _hook_common import (
    MAPPING_PATH,
    SHADOW_ROOT,
    block_tool,
    load_mapping_data,
    read_seed,
    save_mapping_encrypted,
)

from cloudmask.utils.patterns import AWS_RESOURCE_PREFIXES

SEED = read_seed()
if not SEED:
    block_tool("CloudMask seed not configured. Run: python3 scripts/install-hooks.py")
    sys.exit(0)

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

_prefix_alt = "|".join(sorted(AWS_RESOURCE_PREFIXES, key=len, reverse=True))
_QUICK_SCAN = re.compile(rf"(?:(?:{_prefix_alt})-[0-9a-f]{{4,17}}|\b\d{{12}}\b|arn:aws:)")


def _real_to_shadow(real_path: str) -> Path:
    """Convert a real absolute path to its shadow counterpart."""
    resolved = Path(real_path).resolve()
    shadow = SHADOW_ROOT / str(resolved).lstrip("/")
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


def _handle_read(file_path: str) -> bool:
    """Intercept Read: anonymize file content, redirect to shadow copy.

    Returns True if a response was emitted, False otherwise.
    """
    real = Path(file_path)

    if not real.is_file():
        return False
    ext = real.suffix.lower()
    if ext and ext not in INCLUDE_EXT:
        return False
    try:
        if real.stat().st_size > MAX_FILE_SIZE:
            return False
    except OSError:
        return False

    try:
        content = real.read_text(encoding="utf-8")
    except (UnicodeDecodeError, OSError):
        return False

    if not _QUICK_SCAN.search(content):
        return False

    lock_file = None
    try:
        from cloudmask.core import CloudMask

        lock_path = MAPPING_PATH.with_suffix(".lock")
        lock_path.parent.mkdir(parents=True, exist_ok=True)
        try:
            lock_file = lock_path.open("w")
            fcntl.flock(lock_file.fileno(), fcntl.LOCK_EX)
        except OSError:
            pass

        mask = CloudMask(seed=SEED)

        existing = load_mapping_data(SEED)
        mappings = existing.get("mappings", {}) if "_metadata" in existing else existing
        if isinstance(mappings, dict):
            mask._anonymizer.mapping.update(mappings)
        mapping_size_before = len(mask.mapping)

        anonymized = mask.anonymize(content)

        shadow = _real_to_shadow(file_path)
        shadow.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
        fd, tmp = tempfile.mkstemp(dir=shadow.parent, prefix=".mask_", suffix=".tmp")
        try:
            with os.fdopen(fd, "w", encoding="utf-8") as f:
                f.write(anonymized)
            Path(tmp).chmod(0o600)
            Path(tmp).replace(shadow)
        except BaseException:
            Path(tmp).unlink(missing_ok=True)
            raise

        if len(mask.mapping) > mapping_size_before:
            save_mapping_encrypted(mask.mapping, SEED)

        _respond({"file_path": str(shadow)})
        return True
    except Exception as e:
        print(f"cloudmask mask-hook error: {e!r}", file=sys.stderr)
        return False
    finally:
        if lock_file is not None:
            try:
                fcntl.flock(lock_file.fileno(), fcntl.LOCK_UN)
                lock_file.close()
            except OSError:
                pass


def _handle_write_or_edit(file_path: str) -> None:
    """Redirect Write/Edit to the shadow copy if the file was previously masked."""
    if not _shadow_exists(file_path):
        return
    shadow = _real_to_shadow(file_path)
    real = Path(file_path)
    if real.is_file():
        try:
            if real.stat().st_mtime > shadow.stat().st_mtime:
                if _handle_read(file_path):
                    return
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
