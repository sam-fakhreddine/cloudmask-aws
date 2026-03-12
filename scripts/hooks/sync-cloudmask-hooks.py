#!/usr/bin/env python3
"""SessionStart hook: sync cloudmask hooks into project settings.

Works around anthropics/claude-code#17017 where project-level hooks
replace global hooks instead of merging. If the current project defines
hooks for an event that cloudmask also uses, this script injects the
cloudmask hook entries into the project's .claude/settings.json
so they actually run. Uses settings.json (not settings.local.json)
because both local and global settings are replaced by project-level
settings per #19487.

Runs at SessionStart — fast, no-op if nothing to sync.
Also runnable standalone: python3 sync-cloudmask-hooks.py
"""

import json
import os
import sys
import tempfile
from pathlib import Path

HOOK_TAG = "cloudmask-hooks"
GLOBAL_SETTINGS = Path.home() / ".claude" / "settings.json"


def _find_project_root():
    """Walk up from cwd to find .claude/ directory."""
    current = Path.cwd()
    for parent in [current, *current.parents]:
        if (parent / ".claude").is_dir():
            return parent
        if parent == parent.parent:
            break
    return None


def _load_json(path):
    if path.is_file():
        try:
            return json.loads(path.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            pass
    return {}


def _atomic_write_json(data, path):
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp = tempfile.mkstemp(dir=path.parent, prefix=".sync_", suffix=".tmp")
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)
            f.write("\n")
        Path(tmp).replace(path)
    except Exception:
        Path(tmp).unlink(missing_ok=True)
        raise


def main():
    project_root = _find_project_root()
    if not project_root:
        return

    project_settings = project_root / ".claude" / "settings.json"

    proj = _load_json(project_settings)
    proj_hooks = proj.get("hooks", {})
    if not proj_hooks:
        return

    glob = _load_json(GLOBAL_SETTINGS)
    glob_hooks = glob.get("hooks", {})

    cm_entries = {}
    for event, matchers in glob_hooks.items():
        if not isinstance(matchers, list):
            continue
        for matcher in matchers:
            if matcher.get("_tag") == HOOK_TAG:
                cm_entries.setdefault(event, []).append(matcher)

    if not cm_entries:
        return

    needs_sync = False

    for event, cm_matchers in cm_entries.items():
        if event not in proj_hooks:
            continue

        existing_tags = {m.get("_tag") for m in proj_hooks[event] if isinstance(m, dict)}
        if HOOK_TAG in existing_tags:
            continue

        proj_hooks[event].extend(cm_matchers)
        needs_sync = True

    if needs_sync:
        _atomic_write_json(proj, project_settings)
        count = sum(len(v) for v in cm_entries.values())
        print(
            f"cloudmask: synced {count} hook(s) into {project_settings} "
            f"(workaround for anthropics/claude-code#17017)",
            file=sys.stderr,
        )


if __name__ == "__main__":
    main()
    sys.exit(0)
