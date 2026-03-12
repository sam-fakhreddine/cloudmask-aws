#!/usr/bin/env python3
"""Stdin-to-stdout masker for CloudMask Bash hook.

Reads stdin line by line, anonymizes any AWS identifiers found, and outputs
the masked content to stdout.  Used by mask-hook.py to pipe Bash command
output through anonymization.

Falls back to passthrough if cloudmask is not importable or seed is missing.
"""

import sys
from pathlib import Path


def _passthrough() -> None:
    """Pass stdin to stdout unmodified."""
    for line in sys.stdin:
        sys.stdout.write(line)
        sys.stdout.flush()


def main() -> None:
    """Anonymize stdin line by line, output to stdout."""
    sys.path.insert(0, str(Path(__file__).resolve().parent))

    try:
        import fcntl
        import re

        from _hook_common import (
            MAPPING_PATH,
            get_logger,
            load_mapping_data,
            read_seed,
            save_mapping_encrypted,
        )

        from cloudmask.core import CloudMask
        from cloudmask.utils.patterns import AWS_RESOURCE_PREFIXES
    except ImportError as e:
        print(f"cloudmask mask-output: import failed ({e}), passing through", file=sys.stderr)
        _passthrough()
        return

    log = get_logger("mask-output")
    seed = read_seed()
    if not seed:
        log.warning("No seed, passing through")
        _passthrough()
        return

    _prefix_alt = "|".join(sorted(AWS_RESOURCE_PREFIXES, key=len, reverse=True))
    quick_scan = re.compile(rf"(?:(?:{_prefix_alt})-[0-9a-f]{{4,17}}|\d{{12}}|arn:aws:)")

    mask = CloudMask(seed=seed)

    # Load existing mapping
    lock_file = None
    try:
        lock_path = MAPPING_PATH.with_suffix(".lock")
        lock_path.parent.mkdir(parents=True, exist_ok=True)
        lock_file = lock_path.open("w")
        fcntl.flock(lock_file.fileno(), fcntl.LOCK_EX)
        existing = load_mapping_data(seed)
        mappings = existing.get("mappings", {}) if "_metadata" in existing else existing
        if isinstance(mappings, dict):
            mask._anonymizer.mapping.update(mappings)
    except Exception as e:
        log.warning("Failed to load mapping: %r", e)
    finally:
        if lock_file:
            try:
                fcntl.flock(lock_file.fileno(), fcntl.LOCK_UN)
                lock_file.close()
            except OSError:
                pass

    mapping_size_before = len(mask.mapping)
    masked_lines = 0

    for line in sys.stdin:
        if quick_scan.search(line):
            line = mask.anonymize(line)
            masked_lines += 1
        sys.stdout.write(line)
        sys.stdout.flush()

    # Save mapping if new entries were added
    if len(mask.mapping) > mapping_size_before:
        lock_file = None
        try:
            lock_path = MAPPING_PATH.with_suffix(".lock")
            lock_file = lock_path.open("w")
            fcntl.flock(lock_file.fileno(), fcntl.LOCK_EX)
            save_mapping_encrypted(mask.mapping, seed)
        except Exception:
            pass
        finally:
            if lock_file:
                try:
                    fcntl.flock(lock_file.fileno(), fcntl.LOCK_UN)
                    lock_file.close()
                except OSError:
                    pass

    log.info("Processed: %d lines masked, %d total mappings", masked_lines, len(mask.mapping))


if __name__ == "__main__":
    main()
