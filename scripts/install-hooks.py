#!/usr/bin/env python3
"""CloudMask hook installer for Claude Code.

Installs mask-hook.py and demask-hook.py as global Claude Code hooks,
generates a CLOUDMASK_SEED, and safely merges configuration into
~/.claude/settings.json.

Usage:
    python3 scripts/install-hooks.py              # interactive install
    python3 scripts/install-hooks.py --uninstall   # remove hooks
    python3 scripts/install-hooks.py --status       # check installation
    python3 scripts/install-hooks.py --seed abc123  # install with specific seed
"""

import argparse
import json
import os
import secrets
import shlex
import shutil
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
HOOK_SOURCES = REPO_ROOT / "scripts" / "hooks"
CLAUDE_DIR = Path.home() / ".claude"
HOOKS_DIR = CLAUDE_DIR / "hooks"
SETTINGS_FILE = CLAUDE_DIR / "settings.json"
CLOUDMASK_DIR = Path.home() / ".cloudmask"
CLOUDMASK_HOOKS_DIR = CLOUDMASK_DIR / "hooks"
SEED_FILE = CLOUDMASK_DIR / "seed"
VENV_DIR = CLOUDMASK_DIR / ".venv"
VENV_PYTHON = VENV_DIR / "bin" / "python3"

HOOK_FILES = [
    "_hook_common.py",
    "mask-hook.py",
    "demask-hook.py",
    "prompt-mask-hook.py",
    "mask-output.py",
    "sync-cloudmask-hooks.py",
]

HOOK_TAG = "cloudmask-hooks"


def _build_hook_config() -> dict:
    """Build the hooks config to merge into settings.json."""
    py = shlex.quote(str(VENV_PYTHON))
    return {
        "hooks": {
            "PreToolUse": [
                {
                    "matcher": "Read|Write|Edit|Grep|Bash",
                    "_tag": HOOK_TAG,
                    "hooks": [
                        {
                            "type": "command",
                            "command": f"{py} {shlex.quote(str(HOOKS_DIR / 'mask-hook.py'))}",
                            "timeout": 30,
                        }
                    ],
                }
            ],
            "PostToolUse": [
                {
                    "matcher": "Write|Edit",
                    "_tag": HOOK_TAG,
                    "hooks": [
                        {
                            "type": "command",
                            "command": f"{py} {shlex.quote(str(HOOKS_DIR / 'demask-hook.py'))}",
                            "timeout": 30,
                        }
                    ],
                }
            ],
            "UserPromptSubmit": [
                {
                    "matcher": "",
                    "_tag": HOOK_TAG,
                    "hooks": [
                        {
                            "type": "command",
                            "command": f"{py} {shlex.quote(str(HOOKS_DIR / 'prompt-mask-hook.py'))}",
                            "timeout": 30,
                        }
                    ],
                }
            ],
            "SessionStart": [
                {
                    "matcher": "",
                    "_tag": HOOK_TAG,
                    "hooks": [
                        {
                            "type": "command",
                            "command": f"{py} {shlex.quote(str(HOOKS_DIR / 'sync-cloudmask-hooks.py'))}",
                            "timeout": 10,
                        }
                    ],
                }
            ],
        },
    }


def _generate_seed_options() -> list[str]:
    """Generate 5 candidate seeds with 128-bit entropy."""
    return [secrets.token_hex(16) for _ in range(5)]


def _prompt_seed() -> str:
    """Interactive seed selection."""
    options = _generate_seed_options()

    print("\nChoose a CLOUDMASK_SEED (deterministic anonymization key):\n")
    for i, opt in enumerate(options, 1):
        print(f"  [{i}] {opt}")
    print("  [c] Enter custom seed (min 8 characters)")
    print()

    while True:
        choice = input("Select [1-5] or 'c': ").strip().lower()

        if choice in ("1", "2", "3", "4", "5"):
            seed = options[int(choice) - 1]
            print(f"\n  Seed: {seed}")
            return seed
        elif choice == "c":
            while True:
                custom = input("  Enter seed (min 8 chars): ").strip()
                if len(custom) >= 8:
                    return custom
                print("  Too short. Minimum 8 characters.")
        else:
            print("  Invalid choice. Try again.")


def _load_settings() -> dict:
    """Load existing settings.json or return empty dict."""
    if SETTINGS_FILE.is_file():
        try:
            return json.loads(SETTINGS_FILE.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError) as e:
            print(f"  WARNING: Could not parse {SETTINGS_FILE}: {e}")
            print("  A backup will be created before writing.")
            return {}
    return {}


def _remove_tagged_hooks(settings: dict) -> dict:
    """Remove any hook entries tagged with HOOK_TAG."""
    hooks = settings.get("hooks", {})
    for event_name in list(hooks.keys()):
        matchers = hooks[event_name]
        if isinstance(matchers, list):
            hooks[event_name] = [m for m in matchers if m.get("_tag") != HOOK_TAG]
            if not hooks[event_name]:
                del hooks[event_name]
    if not hooks:
        settings.pop("hooks", None)

    env = settings.get("env", {})
    env.pop("CLOUDMASK_SEED", None)
    if not env:
        settings.pop("env", None)

    return settings


def _merge_settings(settings: dict, hook_config: dict) -> dict:
    """Deep-merge hook_config into settings, preserving everything else."""
    settings = _remove_tagged_hooks(settings)

    if "hooks" not in settings:
        settings["hooks"] = {}
    for event_name, new_matchers in hook_config["hooks"].items():
        if event_name not in settings["hooks"]:
            settings["hooks"][event_name] = []
        settings["hooks"][event_name].extend(new_matchers)

    return settings


def _write_settings(settings: dict) -> None:
    """Write settings.json atomically with backup."""
    CLAUDE_DIR.mkdir(parents=True, exist_ok=True)

    if SETTINGS_FILE.is_file():
        backup = SETTINGS_FILE.with_suffix(".json.bak")
        shutil.copy2(SETTINGS_FILE, backup)
        print(f"  Backup: {backup}")

    import tempfile

    fd, tmp = tempfile.mkstemp(dir=CLAUDE_DIR, prefix=".settings_", suffix=".tmp")
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            json.dump(settings, f, indent=2)
            f.write("\n")
        Path(tmp).chmod(0o600)
        Path(tmp).replace(SETTINGS_FILE)
    except BaseException:
        Path(tmp).unlink()
        raise


def _check_cloudmask_importable() -> bool:
    """Check if cloudmask is importable from the hooks venv."""
    if not VENV_PYTHON.is_file():
        return False
    import subprocess

    result = subprocess.run(
        [str(VENV_PYTHON), "-c", "import cloudmask"],
        capture_output=True,
    )
    return result.returncode == 0


def _setup_venv() -> bool:
    """Create ~/.cloudmask/.venv/ and install cloudmask-aws into it.

    Tries uv first, falls back to python3 -m venv + pip.
    Returns True on success, False on failure.
    """
    import subprocess

    CLOUDMASK_DIR.mkdir(parents=True, exist_ok=True, mode=0o700)

    venv_created = False

    uv_bin = shutil.which("uv")
    if uv_bin:
        print(f"  Creating venv with uv: {VENV_DIR}")
        result = subprocess.run(
            [uv_bin, "venv", str(VENV_DIR), "--python", "3.10"],
            capture_output=True,
            text=True,
        )
        if result.returncode == 0 and VENV_PYTHON.is_file():
            venv_created = True
        else:
            result = subprocess.run(
                [uv_bin, "venv", str(VENV_DIR)],
                capture_output=True,
                text=True,
            )
            venv_created = result.returncode == 0 and VENV_PYTHON.is_file()

    if not venv_created:
        py3 = shutil.which("python3")
        if py3:
            print(f"  Creating venv with python3 -m venv: {VENV_DIR}")
            result = subprocess.run(
                [py3, "-m", "venv", str(VENV_DIR)],
                capture_output=True,
                text=True,
            )
            venv_created = result.returncode == 0 and VENV_PYTHON.is_file()

    if not venv_created:
        print("  ERROR: Could not create venv. Install uv or ensure python3 -m venv works.")
        return False

    installed = False

    if uv_bin:
        print("  Installing cloudmask-aws with uv pip...")
        result = subprocess.run(
            [uv_bin, "pip", "install", "--python", str(VENV_PYTHON), f"{REPO_ROOT}"],
            capture_output=True,
            text=True,
        )
        installed = result.returncode == 0
        if not installed:
            print(f"  uv pip install failed: {result.stderr.strip()}")

    if not installed:
        pip_bin = VENV_DIR / "bin" / "pip"
        if pip_bin.is_file():
            print("  Installing cloudmask-aws with pip...")
            result = subprocess.run(
                [str(pip_bin), "install", str(REPO_ROOT)],
                capture_output=True,
                text=True,
            )
            installed = result.returncode == 0
            if not installed:
                print(f"  pip install failed: {result.stderr.strip()}")

    if not installed:
        print("  ERROR: Could not install cloudmask-aws into the venv.")
        return False

    result = subprocess.run(
        [str(VENV_PYTHON), "-c", "import cloudmask; print(cloudmask.__version__)"],
        capture_output=True,
        text=True,
    )
    if result.returncode == 0:
        version = result.stdout.strip()
        print(f"  cloudmask-aws {version} installed in {VENV_DIR}")
        return True
    else:
        print("  ERROR: cloudmask-aws installed but import verification failed.")
        return False


def _is_installed() -> dict:
    """Check current installation status. Returns a dict of what's present."""
    status = {
        "mask_hook": (HOOKS_DIR / "mask-hook.py").is_file(),
        "demask_hook": (HOOKS_DIR / "demask-hook.py").is_file(),
        "settings_configured": False,
        "seed": None,
        "seed_source": None,
    }

    if SETTINGS_FILE.is_file():
        try:
            settings = json.loads(SETTINGS_FILE.read_text(encoding="utf-8"))
            for _event_name, matchers in settings.get("hooks", {}).items():
                if isinstance(matchers, list):
                    for m in matchers:
                        if m.get("_tag") == HOOK_TAG:
                            status["settings_configured"] = True
                            break
            env_seed = settings.get("env", {}).get("CLOUDMASK_SEED")
            if env_seed:
                status["seed"] = env_seed
                status["seed_source"] = "env"
        except (json.JSONDecodeError, OSError):
            pass

    try:
        if SEED_FILE.is_file():
            file_seed = SEED_FILE.read_text(encoding="utf-8").strip()
            if file_seed:
                status["seed"] = file_seed
                status["seed_source"] = "file"
    except OSError:
        pass

    try:
        import keyring

        keychain_seed = keyring.get_password("cloudmask", "seed")
        if keychain_seed:
            status["seed"] = keychain_seed
            status["seed_source"] = "keychain"
    except Exception:
        pass

    return status


def install(seed: str | None = None) -> int:
    """Run the full installation."""
    print("=" * 60)
    print("  CloudMask Hook Installer for Claude Code")
    print("=" * 60)

    print("\n[1/6] Checking prerequisites...")

    if not _check_cloudmask_importable():
        print("  ERROR: cloudmask-aws is not installed.")
        print("  Run:  pip install cloudmask-aws")
        print(f"  Or:   pip install -e '{REPO_ROOT}'")
        return 1
    print("  cloudmask-aws: OK")

    if not (HOOK_SOURCES / "mask-hook.py").is_file():
        print(f"  ERROR: Hook source files not found at {HOOK_SOURCES}")
        return 1
    print(f"  Hook sources: OK ({HOOK_SOURCES})")

    status = _is_installed()
    if status["settings_configured"]:
        seed_display = (
            f"{status['seed'][:4]}...{status['seed'][-4:]}"
            if status["seed"] and len(status["seed"]) > 8
            else status["seed"] or "not set"
        )
        print(f"\n  CloudMask hooks are already installed (seed: {seed_display})")
        choice = input("  Reinstall? [y/N]: ").strip().lower()
        if choice != "y":
            print("  Aborted.")
            return 0

    print("\n[2/6] Configuring seed...")
    if seed:
        if len(seed) < 8:
            print(f"  ERROR: Seed must be at least 8 characters (got {len(seed)}).")
            return 1
        print(f"  Using provided seed: {seed}")
    else:
        seed = _prompt_seed()

    print("\n[3/6] Setting up dedicated venv...")
    if VENV_PYTHON.is_file() and _check_cloudmask_importable():
        print(f"  Existing venv OK: {VENV_DIR}")
    else:
        if not _setup_venv():
            return 1

    print("\n[4/6] Installing hook files...")
    HOOKS_DIR.mkdir(parents=True, exist_ok=True)
    for fname in HOOK_FILES:
        src = HOOK_SOURCES / fname
        dst = HOOKS_DIR / fname
        shutil.copy2(src, dst)
        dst.chmod(0o700)
        print(f"  {dst}")

    print("\n[5/6] Storing seed and creating shadow directory...")
    keychain_ok = False
    try:
        import keyring

        keyring.set_password("cloudmask", "seed", seed)
        keychain_ok = True
        print("  Seed stored in OS keychain (cloudmask/seed)")
    except Exception as e:
        print(f"  Keychain unavailable ({e}), using file fallback")
    CLOUDMASK_DIR.mkdir(parents=True, exist_ok=True, mode=0o700)
    if SEED_FILE.exists():
        SEED_FILE.chmod(0o600)
    SEED_FILE.write_text(seed, encoding="utf-8")
    SEED_FILE.chmod(0o400)
    print(f"  Seed file: {SEED_FILE}" + (" (fallback)" if keychain_ok else " (primary)"))
    CLOUDMASK_HOOKS_DIR.mkdir(parents=True, exist_ok=True)
    print(f"  {CLOUDMASK_HOOKS_DIR}")

    print("\n[6/6] Configuring Claude Code settings...")
    settings = _load_settings()
    hook_config = _build_hook_config()
    settings = _merge_settings(settings, hook_config)
    _write_settings(settings)
    print(f"  {SETTINGS_FILE}")

    print("\n" + "=" * 60)
    print("  Installation complete!")
    print("=" * 60)
    print(f"""
  Seed:       {seed[:4]}...{seed[-4:]}
  Hooks:      {HOOKS_DIR / "mask-hook.py"}
              {HOOKS_DIR / "demask-hook.py"}
              {HOOKS_DIR / "prompt-mask-hook.py"}
  Settings:   {SETTINGS_FILE}
  Shadow dir: {CLOUDMASK_HOOKS_DIR / "shadow"}
  Mapping:    {CLOUDMASK_HOOKS_DIR / "mapping.json"}

  What happens now:
    - Claude Code reads a file  -> mask-hook anonymizes AWS identifiers
    - Claude works with masked content (IDs, ARNs, IPs hidden)
    - Claude writes/edits a file -> demask-hook restores real values
    - You type a prompt with AWS IDs -> prompt-mask-hook anonymizes it

  Limitations:
    - Grep and Bash output are masked via shadow redirection and pipe wrapping
    - User prompts are masked via UserPromptSubmit hook
    - Only text files with recognized extensions are processed
    - Files > 10 MB are passed through unmasked

  To change the seed later:
    python3 {Path(__file__).resolve()} --seed NEW_SEED

  To uninstall:
    python3 {Path(__file__).resolve()} --uninstall
""")
    return 0


def uninstall() -> int:
    """Remove hooks and settings entries."""
    print("=" * 60)
    print("  CloudMask Hook Uninstaller")
    print("=" * 60)

    status = _is_installed()
    if not any((status["mask_hook"], status["demask_hook"], status["settings_configured"])):
        print("\n  CloudMask hooks are not installed. Nothing to do.")
        return 0

    choice = input("\n  Remove CloudMask hooks from Claude Code? [y/N]: ").strip().lower()
    if choice != "y":
        print("  Aborted.")
        return 0

    for fname in HOOK_FILES:
        hook_file = HOOKS_DIR / fname
        if hook_file.is_file():
            hook_file.unlink()
            print(f"  Removed: {hook_file}")

    if SETTINGS_FILE.is_file():
        settings = _load_settings()
        settings = _remove_tagged_hooks(settings)
        _write_settings(settings)
        print(f"  Cleaned: {SETTINGS_FILE}")

    try:
        import keyring

        if keyring.get_password("cloudmask", "seed"):
            keyring.delete_password("cloudmask", "seed")
            print("  Removed: OS keychain (cloudmask/seed)")
    except Exception:
        pass

    if SEED_FILE.is_file():
        SEED_FILE.unlink()
        print(f"  Removed: {SEED_FILE}")

    if VENV_DIR.exists():
        choice = input(f"\n  Also delete hooks venv? ({VENV_DIR}) [y/N]: ").strip().lower()
        if choice == "y":
            shutil.rmtree(VENV_DIR)
            print(f"  Removed: {VENV_DIR}")
        else:
            print(f"  Kept: {VENV_DIR}")

    if CLOUDMASK_HOOKS_DIR.exists():
        choice = (
            input(f"\n  Also delete shadow files and mapping? ({CLOUDMASK_HOOKS_DIR}) [y/N]: ")
            .strip()
            .lower()
        )
        if choice == "y":
            shutil.rmtree(CLOUDMASK_HOOKS_DIR)
            print(f"  Removed: {CLOUDMASK_HOOKS_DIR}")
        else:
            print(f"  Kept: {CLOUDMASK_HOOKS_DIR}")

    print("\n  Uninstall complete.\n")
    return 0


def show_status() -> int:
    """Show current installation status."""
    print("=" * 60)
    print("  CloudMask Hook Status")
    print("=" * 60)

    status = _is_installed()
    cloudmask_ok = _check_cloudmask_importable()
    venv_ok = VENV_PYTHON.is_file()

    def yesno(val: bool) -> str:
        return "installed" if val else "NOT installed"

    print(f"""
  hooks venv:       {"exists" if venv_ok else "NOT found"} ({VENV_DIR})
  cloudmask-aws:    {"importable" if cloudmask_ok else "NOT importable (run installer)"}
  mask-hook.py:     {yesno(status["mask_hook"])}    ({HOOKS_DIR / "mask-hook.py"})
  demask-hook.py:   {yesno(status["demask_hook"])}    ({HOOKS_DIR / "demask-hook.py"})
  settings.json:    {"configured" if status["settings_configured"] else "NOT configured"}
  seed source:      {status["seed_source"] or "none"}
  seed file:        {"exists" if SEED_FILE.is_file() else "NOT found"} ({SEED_FILE})
  seed:             {(status["seed"][:4] + "..." + status["seed"][-4:]) if status["seed"] and len(status["seed"]) > 8 else status["seed"] or "not set"}
  shadow dir:       {"exists" if (CLOUDMASK_HOOKS_DIR / "shadow").is_dir() else "not created yet"}
  mapping file:     {"exists" if (CLOUDMASK_HOOKS_DIR / "mapping.json").is_file() else "not created yet"}
""")

    if all(
        (
            venv_ok,
            cloudmask_ok,
            status["mask_hook"],
            status["demask_hook"],
            status["settings_configured"],
            status["seed"],
        )
    ):
        print("  Status: FULLY INSTALLED\n")
    elif any((status["mask_hook"], status["demask_hook"], status["settings_configured"])):
        print("  Status: PARTIALLY INSTALLED (run installer to fix)\n")
    else:
        print("  Status: NOT INSTALLED\n")

    return 0


def main() -> int:
    """Parse args and dispatch."""
    parser = argparse.ArgumentParser(
        description="Install CloudMask anonymization hooks for Claude Code",
    )
    parser.add_argument(
        "--uninstall",
        action="store_true",
        help="Remove CloudMask hooks from Claude Code",
    )
    parser.add_argument(
        "--status",
        action="store_true",
        help="Show current installation status",
    )
    parser.add_argument(
        "--seed",
        type=str,
        default=None,
        help="Set a specific CLOUDMASK_SEED (min 8 characters, skip interactive prompt)",
    )

    args = parser.parse_args()

    if args.uninstall:
        return uninstall()
    elif args.status:
        return show_status()
    else:
        return install(seed=args.seed)


if __name__ == "__main__":
    sys.exit(main())
