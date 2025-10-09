#!/usr/bin/env python3
"""Bump version across all project files."""

import re
import sys
from datetime import date
from pathlib import Path


def bump_version(new_version: str) -> None:
    """Update version in pyproject.toml, __version__.py, and CHANGELOG.md."""
    root = Path(__file__).parent.parent
    today = date.today().isoformat()

    # Update pyproject.toml
    pyproject = root / "pyproject.toml"
    content = pyproject.read_text()
    content = re.sub(r'version = "[^"]+"', f'version = "{new_version}"', content, count=1)
    pyproject.write_text(content)
    print(f"✓ Updated {pyproject}")

    # Update __version__.py
    version_file = root / "src" / "cloudmask" / "__version__.py"
    content = version_file.read_text()
    content = re.sub(r'__version__ = "[^"]+"', f'__version__ = "{new_version}"', content)
    version_file.write_text(content)
    print(f"✓ Updated {version_file}")

    # Update CHANGELOG.md
    changelog = root / "CHANGELOG.md"
    content = changelog.read_text()
    content = re.sub(
        rf"## \[{re.escape(new_version)}\] - \d{{4}}-\d{{2}}-\d{{2}}",
        f"## [{new_version}] - {today}",
        content,
    )
    changelog.write_text(content)
    print(f"✓ Updated {changelog}")


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python scripts/bump_version.py <version>")
        sys.exit(1)

    bump_version(sys.argv[1])
