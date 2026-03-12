#!/usr/bin/env python3
"""CloudMask UserPromptSubmit hook for Claude Code.

Detects sensitive infrastructure identifiers in user prompts and blocks them
from reaching Claude. Saves the anonymized version to a uniquely named file
so the user can resubmit cleanly.

Since Claude Code does not support rewriting prompts via hooks, this is a
fail-closed design: real identifiers never reach the model.

Blocked prompts are saved to ~/.cloudmask/.blockedprompts/<timestamp>-<short-hash>.txt
Files older than 15 days are cleaned up on each invocation.

Mapping:  ~/.cloudmask/hooks/mapping.json (encrypted, shared with mask-hook)
Seed:     OS keychain > ~/.cloudmask/seed > $CLOUDMASK_SEED env var
"""

import fcntl
import hashlib
import json
import re
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from _hook_common import (
    CLOUDMASK_MARKER,
    MAPPING_PATH,
    load_mapping_data,
    read_seed,
    save_mapping_encrypted,
)

from cloudmask.utils.patterns import AWS_RESOURCE_PREFIXES

SEED = read_seed()
if not SEED:
    sys.exit(0)

BLOCKED_DIR = Path.home() / ".cloudmask" / ".blockedprompts"
MAX_AGE_DAYS = 15

_prefix_alt = "|".join(sorted(AWS_RESOURCE_PREFIXES, key=len, reverse=True))
_QUICK_SCAN = re.compile(rf"(?:(?:{_prefix_alt})-[0-9a-f]{{4,17}}|\b\d{{12}}\b|arn:aws:)")


def _cleanup_old_prompts() -> None:
    """Remove blocked prompt files older than MAX_AGE_DAYS."""
    if not BLOCKED_DIR.is_dir():
        return
    cutoff = time.time() - (MAX_AGE_DAYS * 86400)
    for f in BLOCKED_DIR.iterdir():
        if f.suffix == ".txt" and f.stat().st_mtime < cutoff:
            f.unlink(missing_ok=True)


def _generate_prompt_path(prompt: str) -> Path:
    """Generate a unique filename: YYYYMMDD-HHMMSS-<6char-hash>.txt"""
    ts = datetime.now(timezone.utc).strftime("%Y%m%d-%H%M%S")
    short_hash = hashlib.sha256(prompt.encode()).hexdigest()[:6]
    return BLOCKED_DIR / f"{ts}-{short_hash}.txt"


def _describe_matches(prompt: str) -> str:
    """Build a human-readable summary of what was caught."""
    found = []
    if re.search(r"arn:aws:", prompt):
        found.append("ARNs")
    if re.search(r"\b\d{12}\b", prompt):
        found.append("account IDs")
    prefix_hits = set()
    for m in re.finditer(rf"(?:{_prefix_alt})-[0-9a-f]{{4,17}}", prompt):
        prefix = m.group(0).rsplit("-", 1)[0]
        prefix_hits.add(prefix.split("-")[0])
    if prefix_hits:
        readable = sorted(prefix_hits)
        found.append(f"resource IDs ({', '.join(readable)})")
    if re.search(r"\b(?:10|172|192)\.\d{1,3}\.\d{1,3}\.\d{1,3}\b", prompt):
        found.append("private IPs")
    return ", ".join(found) if found else "sensitive identifiers"


def main() -> None:
    """Block prompts with sensitive IDs, save masked version for easy resubmit."""
    try:
        hook = json.load(sys.stdin)
    except (json.JSONDecodeError, EOFError):
        return

    prompt = hook.get("prompt", "")
    if not prompt or not _QUICK_SCAN.search(prompt):
        return

    # Skip if prompt contains the CloudMask marker (already sanitized)
    if CLOUDMASK_MARKER in prompt:
        return

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

        anonymized = mask.anonymize(prompt)

        if len(mask.mapping) > mapping_size_before:
            save_mapping_encrypted(mask.mapping, SEED)

        if anonymized == prompt:
            return

        matched = _describe_matches(prompt)

        # Cleanup old files, then save masked prompt
        _cleanup_old_prompts()
        BLOCKED_DIR.mkdir(parents=True, exist_ok=True, mode=0o700)
        prompt_file = _generate_prompt_path(prompt)
        file_content = (
            f"{CLOUDMASK_MARKER}\n"
            "This is a CloudMask-sanitized prompt. The identifiers below have "
            "been anonymized to protect real infrastructure. Treat this as the "
            "user's actual request and respond normally.\n\n" + anonymized
        )
        prompt_file.write_text(file_content, encoding="utf-8")
        prompt_file.chmod(0o600)

        # decision/reason at top level, not inside hookSpecificOutput
        json.dump(
            {
                "decision": "block",
                "reason": (
                    f"CloudMask blocked this prompt — detected: {matched}\n"
                    "Masked version saved. Resubmit with:\n\n"
                    f"  @{prompt_file}\n\n"
                    "Or copy the masked prompt:\n\n"
                    f"  {anonymized}"
                ),
            },
            sys.stdout,
        )
    except Exception as e:
        print(f"cloudmask prompt-mask-hook error: {e!r}", file=sys.stderr)
    finally:
        if lock_file is not None:
            try:
                fcntl.flock(lock_file.fileno(), fcntl.LOCK_UN)
                lock_file.close()
            except OSError:
                pass


if __name__ == "__main__":
    main()
    sys.exit(0)
