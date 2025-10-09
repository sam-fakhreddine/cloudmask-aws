# Scripts

Development and maintenance scripts for CloudMask.

## Setup Scripts

- **`setup_dev.sh`** - Set up development environment with dependencies
- **`init.sh`** - Initialize CloudMask project after creation

## Build & Release Scripts

- **`build.sh`** - Build and publish package to PyPI
- **`bump_version.py`** - Bump version numbers in project files
- **`prepare_release.sh`** - Prepare a new release

## Testing Scripts

- **`run_tests.sh`** - Quick test runner with coverage

## GitHub Scripts

- **`setup-github.sh`** - Configure GitHub repository protection and settings
- **`add-secrets.sh`** - Add secrets to GitHub repository

## Usage

Most scripts should be run from the project root:

```bash
# Set up development environment
./scripts/setup_dev.sh

# Run tests
./scripts/run_tests.sh

# Build and publish
./scripts/build.sh
```
