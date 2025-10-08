# Release Process

This document describes how to release a new version of cloudmask.

## Version Management

CloudMask follows [Semantic Versioning](https://semver.org/):
- **MAJOR** version for incompatible API changes
- **MINOR** version for new functionality in a backwards compatible manner
- **PATCH** version for backwards compatible bug fixes

## Automated Release Process

### Quick Release

Use the automated script:

```bash
# For a patch release (0.1.0 -> 0.1.1)
./scripts/prepare_release.sh patch

# For a minor release (0.1.0 -> 0.2.0)
./scripts/prepare_release.sh minor

# For a major release (0.1.0 -> 1.0.0)
./scripts/prepare_release.sh major
```

This script will:
1. Verify you're on the main branch
2. Ensure working directory is clean
3. Run tests
4. Bump version in all files
5. Update CHANGELOG.md
6. Commit changes
7. Create git tag

Then push to trigger automated publishing:

```bash
git push && git push --tags
```

### Manual Release Process

If you prefer manual control:

1. **Update version files**:
   ```bash
   python scripts/bump_version.py patch  # or minor/major
   ```

2. **Update CHANGELOG.md**:
   - Move items from `[Unreleased]` to new version section
   - Add release date
   - Create new empty `[Unreleased]` section

3. **Commit and tag**:
   ```bash
   git add src/cloudmask/__version__.py pyproject.toml CHANGELOG.md
   git commit -m "Bump version to X.Y.Z"
   git tag vX.Y.Z
   ```

4. **Push to trigger release**:
   ```bash
   git push && git push --tags
   ```

## What Happens Automatically

When you push a version tag (e.g., `v0.1.0`), GitHub Actions will:

1. Run all tests
2. Build the package
3. Create a GitHub Release with changelog notes
4. Publish to PyPI

## Pre-Release Checklist

Before releasing, ensure:

- [ ] All tests pass: `uv run pytest`
- [ ] Code quality checks pass: `pre-commit run --all-files`
- [ ] Documentation is up to date
- [ ] CHANGELOG.md has all changes documented
- [ ] Version numbers are consistent across files
- [ ] README.md examples work with new version

## Post-Release Checklist

After releasing:

- [ ] Verify package on PyPI: https://pypi.org/project/cloudmask/
- [ ] Test installation: `pip install cloudmask==X.Y.Z`
- [ ] Verify GitHub Release: https://github.com/samfakhreddine/cloudmask/releases
- [ ] Update documentation if needed
- [ ] Announce release (if significant)

## Version File Locations

Version must be updated in:
- `src/cloudmask/__version__.py` - Source of truth
- `pyproject.toml` - Package metadata
- `CHANGELOG.md` - Release notes

The `bump_version.py` script updates all three automatically.

## Troubleshooting

### Version mismatch error in CI

If CI fails with version mismatch, ensure all three files have the same version:
```bash
grep -r "0.1.0" src/cloudmask/__version__.py pyproject.toml CHANGELOG.md
```

### Failed PyPI upload

Check that `PYPI_API_TOKEN` secret is set in GitHub repository settings.

### Tag already exists

If you need to re-release:
```bash
git tag -d vX.Y.Z
git push origin :refs/tags/vX.Y.Z
```

Then create the tag again.
