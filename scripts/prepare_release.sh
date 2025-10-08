#!/bin/bash
# Prepare a new release for cloudmask

set -e

if [ $# -ne 1 ]; then
    echo "Usage: $0 <major|minor|patch>"
    exit 1
fi

PART=$1

# Ensure we're on main branch
BRANCH=$(git rev-parse --abbrev-ref HEAD)
if [ "$BRANCH" != "main" ]; then
    echo "Error: Must be on main branch (currently on $BRANCH)"
    exit 1
fi

# Ensure working directory is clean
if [ -n "$(git status --porcelain)" ]; then
    echo "Error: Working directory is not clean"
    git status --short
    exit 1
fi

# Pull latest changes
git pull origin main

# Run tests
echo "Running tests..."
uv run pytest

# Bump version
echo "Bumping version..."
python scripts/bump_version.py "$PART"

# Get new version
NEW_VERSION=$(grep -oP '__version__ = "\K[^"]+' src/cloudmask/__version__.py)

# Show changes
echo ""
echo "Changes to be committed:"
git diff

# Confirm
read -p "Commit and tag version $NEW_VERSION? (y/n) " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo "Aborted"
    git checkout -- .
    exit 1
fi

# Commit and tag
git add src/cloudmask/__version__.py pyproject.toml CHANGELOG.md
git commit -m "Bump version to $NEW_VERSION"
git tag "v$NEW_VERSION"

echo ""
echo "Release prepared successfully!"
echo "To publish, run: git push && git push --tags"
