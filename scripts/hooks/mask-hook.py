#!/usr/bin/env python3
"""CloudMask pre-tool-use hook for Claude Code.

Intercepts Read/Write/Edit/Grep/Bash operations to anonymize AWS identifiers
before Claude processes file content or command output.

For Read/Write/Edit: writes anonymized copies to a shadow directory and
redirects Claude's tool operations to those shadow copies.

For Grep: creates shadow copies of target files/directories and redirects
the search to the shadow directory so results contain anonymized content.

For Bash: wraps the command to pipe output through mask-output.py so
Claude sees anonymized command output.

Shadow layout: ~/.cloudmask/hooks/shadow/<real-path-without-leading-slash>
Mapping:       ~/.cloudmask/hooks/mapping.json (encrypted at rest)
Seed:          OS keychain > ~/.cloudmask/seed > $CLOUDMASK_SEED env var
"""

import fcntl
import json
import os
import re
import shlex
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from _hook_common import (
    CLOUDMASK_MARKER,
    MAPPING_PATH,
    SHADOW_ROOT,
    block_tool,
    get_logger,
    load_mapping_data,
    read_seed,
    save_mapping_encrypted,
)

from cloudmask.utils.patterns import AWS_RESOURCE_PREFIXES

log = get_logger("mask")
log.debug("mask-hook loaded, pid=%d", os.getpid())

SEED = read_seed()
if not SEED:
    log.error("No seed configured, blocking tool call")
    block_tool("CloudMask seed not configured. Run: python3 scripts/install-hooks.py")
    sys.exit(0)

log.debug("Seed resolved, len=%d", len(SEED))

MAX_FILE_SIZE = 10_000_000
MAX_SHADOW_FILES = 1000

INCLUDE_EXT = frozenset(
    {
        ".tf", ".tfvars", ".hcl", ".yaml", ".yml", ".json", ".toml", ".py",
        ".js", ".ts", ".jsx", ".tsx", ".sh", ".bash", ".zsh", ".cfg", ".ini",
        ".conf", ".env", ".properties", ".txt", ".md", ".rst", ".log", ".csv",
        ".xml", ".go", ".rs", ".java", ".rb",
    }
)

_EXCLUDED_DIRS = frozenset(
    {
        ".git", "node_modules", ".venv", "venv", "__pycache__",
        ".tox", ".mypy_cache", ".ruff_cache", ".pytest_cache",
        "dist", "build", ".eggs", ".cloudmask", ".worktrees", ".temp",
    }
)

# Commands that RTK rewrites — skip Bash wrapping for these to avoid
# updatedInput conflicts (RTK and mask-hook both return updatedInput).
_RTK_COMMANDS = frozenset(
    {
        "git", "npm", "npx", "yarn", "pnpm", "cargo",
        "docker", "podman", "rustup", "brew",
    }
)

_prefix_alt = "|".join(sorted(AWS_RESOURCE_PREFIXES, key=len, reverse=True))
_QUICK_SCAN = re.compile(rf"(?:(?:{_prefix_alt})-[0-9a-f]{{4,17}}|\b\d{{12}}\b|arn:aws:)")

_MASK_OUTPUT_SCRIPT = Path(__file__).resolve().parent / "mask-output.py"


def _is_shadow_path(file_path: str) -> bool:
    """Check if a path is already under the shadow root."""
    try:
        Path(file_path).resolve().relative_to(SHADOW_ROOT.resolve())
        return True
    except ValueError:
        return False


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


def _anonymize_to_shadow(file_path: str, content: str) -> "Path | None":
    """Anonymize content and write to shadow copy. Returns shadow path or None."""
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

        log.info("Anonymized %s -> %s (%d mappings)", file_path, shadow, len(mask.mapping))
        return shadow
    except Exception as e:
        log.error("Anonymization failed for %s: %r", file_path, e)
        return None
    finally:
        if lock_file is not None:
            try:
                fcntl.flock(lock_file.fileno(), fcntl.LOCK_UN)
                lock_file.close()
            except OSError:
                pass


def _link_to_shadow(file_path: str) -> "Path | None":
    """Create a symlink in shadow pointing to the real file."""
    try:
        shadow = _real_to_shadow(file_path)
        shadow.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
        if shadow.exists() or shadow.is_symlink():
            shadow.unlink()
        shadow.symlink_to(Path(file_path).resolve())
        return shadow
    except Exception as e:
        log.warning("Failed to create shadow symlink for %s: %r", file_path, e)
        return None


def _handle_read(file_path: str) -> bool:
    """Intercept Read: anonymize file content, redirect to shadow copy."""
    log.debug("Read: %s", file_path)

    if _is_shadow_path(file_path):
        log.debug("Read: already shadow path, passing through")
        return False

    real = Path(file_path)
    if not real.is_file():
        log.debug("Read: not a file, skipping")
        return False
    ext = real.suffix.lower()
    if ext and ext not in INCLUDE_EXT:
        log.debug("Read: extension %s not in INCLUDE_EXT, skipping", ext)
        return False
    try:
        if real.stat().st_size > MAX_FILE_SIZE:
            log.debug("Read: file too large, skipping")
            return False
    except OSError:
        return False

    try:
        content = real.read_text(encoding="utf-8")
    except (UnicodeDecodeError, OSError):
        log.debug("Read: cannot read as UTF-8, skipping")
        return False

    if CLOUDMASK_MARKER in content:
        log.debug("Read: CLOUDMASK_MARKER found, skipping")
        return False

    if not _QUICK_SCAN.search(content):
        log.debug("Read: no sensitive patterns found, skipping")
        return False

    shadow = _anonymize_to_shadow(file_path, content)
    if shadow:
        _respond({"file_path": str(shadow)})
        log.info("Read: redirected to shadow %s", shadow)
        return True
    return False


def _handle_write_or_edit(file_path: str) -> None:
    """Redirect Write/Edit to the shadow copy if the file was previously masked."""
    log.debug("Write/Edit: %s", file_path)

    if _is_shadow_path(file_path):
        log.debug("Write/Edit: already shadow path, passing through")
        return

    if not _shadow_exists(file_path):
        log.debug("Write/Edit: no shadow exists, passing through")
        return

    shadow = _real_to_shadow(file_path)
    real = Path(file_path)
    if real.is_file():
        try:
            if real.stat().st_mtime > shadow.stat().st_mtime:
                log.debug("Write/Edit: real file newer, re-anonymizing")
                if _handle_read(file_path):
                    return
                if not shadow.is_file():
                    return
        except OSError:
            pass

    _respond({"file_path": str(shadow)})
    log.info("Write/Edit: redirected to shadow %s", shadow)


def _ensure_shadow_file(file_path: str) -> "Path | None":
    """Ensure a shadow copy exists for a file (for Grep coverage).

    Unlike _handle_read, this also handles non-sensitive files by creating
    symlinks so Grep searches find all files in the shadow directory.
    """
    if _is_shadow_path(file_path):
        return Path(file_path)

    real = Path(file_path)
    if not real.is_file():
        return None

    shadow = _real_to_shadow(file_path)
    if shadow.exists() or shadow.is_symlink():
        try:
            if shadow.is_symlink() or shadow.stat().st_mtime >= real.stat().st_mtime:
                return shadow
        except OSError:
            pass

    ext = real.suffix.lower()
    if ext and ext not in INCLUDE_EXT:
        return _link_to_shadow(file_path)

    try:
        if real.stat().st_size > MAX_FILE_SIZE:
            return _link_to_shadow(file_path)
    except OSError:
        return None

    try:
        content = real.read_text(encoding="utf-8")
    except (UnicodeDecodeError, OSError):
        return _link_to_shadow(file_path)

    if CLOUDMASK_MARKER in content:
        return _link_to_shadow(file_path)

    if not _QUICK_SCAN.search(content):
        return _link_to_shadow(file_path)

    return _anonymize_to_shadow(file_path, content) or _link_to_shadow(file_path)


def _handle_grep(tool_input: dict) -> bool:
    """Intercept Grep: redirect search to shadow copies."""
    path = tool_input.get("path", "")
    if not path:
        path = str(Path.cwd())
    log.debug("Grep: path=%s", path)

    target = Path(path).resolve()
    if not target.exists():
        log.debug("Grep: target does not exist, passing through")
        return False

    if _is_shadow_path(str(target)):
        log.debug("Grep: already shadow path, passing through")
        return False

    if target.is_file():
        shadow = _ensure_shadow_file(str(target))
        if shadow:
            updated = dict(tool_input)
            updated["path"] = str(shadow)
            _respond(updated)
            log.info("Grep: redirected file to shadow %s", shadow)
            return True
        return False

    if target.is_dir():
        count = 0
        for root, dirs, files in os.walk(target):
            dirs[:] = [d for d in dirs if d not in _EXCLUDED_DIRS]
            for fname in files:
                real_file = str(Path(root) / fname)
                _ensure_shadow_file(real_file)
                count += 1
                if count >= MAX_SHADOW_FILES:
                    log.warning("Grep: shadow file limit reached (%d)", MAX_SHADOW_FILES)
                    break
            if count >= MAX_SHADOW_FILES:
                break

        shadow_dir = _real_to_shadow(str(target))
        if shadow_dir.is_dir():
            updated = dict(tool_input)
            updated["path"] = str(shadow_dir)
            _respond(updated)
            log.info("Grep: redirected dir to shadow %s (%d files)", shadow_dir, count)
            return True
        else:
            log.warning("Grep: shadow dir not created for %s", target)

    return False


def _handle_bash(tool_input: dict) -> bool:
    """Intercept Bash: wrap command to pipe output through mask-output.py."""
    command = tool_input.get("command", "")
    if not command:
        log.debug("Bash: empty command, passing through")
        return False

    first_word = command.split()[0] if command.strip() else ""
    if first_word in _RTK_COMMANDS:
        log.debug("Bash: %s is RTK-rewritable, skipping masking", first_word)
        return False

    if not _MASK_OUTPUT_SCRIPT.is_file():
        log.error("Bash: mask-output.py not found at %s", _MASK_OUTPUT_SCRIPT)
        return False

    masker = shlex.quote(str(_MASK_OUTPUT_SCRIPT))
    wrapped = f"( {command} ) 2>&1 | python3 {masker}"

    updated = dict(tool_input)
    updated["command"] = wrapped
    _respond(updated)
    log.info("Bash: wrapped command (original_len=%d)", len(command))
    return True


def main() -> None:
    """Read hook input from stdin, dispatch by tool name."""
    try:
        hook = json.load(sys.stdin)
    except (json.JSONDecodeError, EOFError):
        log.error("Failed to parse hook input from stdin")
        return

    tool = hook.get("tool_name", "")
    tool_input = hook.get("tool_input", {})
    log.debug("Dispatching tool=%s", tool)

    if tool == "Read":
        file_path = tool_input.get("file_path", "")
        if file_path:
            _handle_read(file_path)
    elif tool in ("Write", "Edit"):
        file_path = tool_input.get("file_path", "")
        if file_path:
            _handle_write_or_edit(file_path)
    elif tool == "Grep":
        _handle_grep(tool_input)
    elif tool == "Bash":
        _handle_bash(tool_input)
    else:
        log.debug("Unhandled tool: %s", tool)


if __name__ == "__main__":
    main()
    sys.exit(0)
