#!/usr/bin/env python3
"""Version bumping script for cloudmask."""

import argparse
import re
import sys
from datetime import date
from pathlib import Path


def get_current_version(root: Path) -> str:
    """Get current version from __version__.py."""
    version_file = root / "src" / "cloudmask" / "__version__.py"
    content = version_file.read_text()
    match = re.search(r'__version__ = "([^"]+)"', content)
    if not match:
        raise ValueError("Could not find version in __version__.py")
    return match.group(1)


def bump_version(version: str, part: str) -> str:
    """Bump version number."""
    major, minor, patch = map(int, version.split("."))

    if part == "major":
        return f"{major + 1}.0.0"
    elif part == "minor":
        return f"{major}.{minor + 1}.0"
    elif part == "patch":
        return f"{major}.{minor}.{patch + 1}"
    else:
        raise ValueError(f"Invalid part: {part}")


def update_version_file(root: Path, new_version: str) -> None:
    """Update __version__.py."""
    version_file = root / "src" / "cloudmask" / "__version__.py"
    content = version_file.read_text()
    content = re.sub(r'__version__ = "[^"]+"', f'__version__ = "{new_version}"', content)
    version_file.write_text(content)


def update_pyproject(root: Path, new_version: str) -> None:
    """Update pyproject.toml."""
    pyproject = root / "pyproject.toml"
    content = pyproject.read_text()
    content = re.sub(r'version = "[^"]+"', f'version = "{new_version}"', content, count=1)
    pyproject.write_text(content)


def update_changelog(root: Path, new_version: str) -> None:
    """Update CHANGELOG.md."""
    changelog = root / "CHANGELOG.md"
    content = changelog.read_text()

    today = date.today().isoformat()

    # Replace [Unreleased] with new version
    content = re.sub(
        r"## \[Unreleased\]", f"## [Unreleased]\n\n## [{new_version}] - {today}", content
    )

    changelog.write_text(content)


def main() -> int:
    """Main entry point."""
    parser = argparse.ArgumentParser(description="Bump version for cloudmask")
    parser.add_argument("part", choices=["major", "minor", "patch"], help="Part of version to bump")
    parser.add_argument(
        "--dry-run", action="store_true", help="Show what would be done without making changes"
    )

    args = parser.parse_args()
    root = Path(__file__).parent.parent

    current = get_current_version(root)
    new = bump_version(current, args.part)

    print(f"Current version: {current}")
    print(f"New version: {new}")

    if args.dry_run:
        print("\nDry run - no changes made")
        return 0

    update_version_file(root, new)
    update_pyproject(root, new)
    update_changelog(root, new)

    print("\nVersion bumped successfully!")
    print("Next steps:")
    print("1. Review changes: git diff")
    print(f"2. Commit: git commit -am 'Bump version to {new}'")
    print(f"3. Tag: git tag v{new}")
    print("4. Push: git push && git push --tags")

    return 0


if __name__ == "__main__":
    sys.exit(main())
