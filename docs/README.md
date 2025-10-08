# CloudMask Documentation

This directory contains the Sphinx documentation for CloudMask.

## Building Documentation

### Install Dependencies

```bash
uv pip install -e ".[dev]"
```

Or install just documentation dependencies:

```bash
uv pip install -r docs/requirements.txt
```

### Build HTML Documentation

```bash
cd docs
make html
```

The built documentation will be in `docs/_build/html/`.

### View Documentation

```bash
open _build/html/index.html  # macOS
xdg-open _build/html/index.html  # Linux
start _build/html/index.html  # Windows
```

### Clean Build

```bash
make clean
```

## Documentation Structure

- `index.rst` - Main documentation index
- `getting_started.rst` - Installation and quick start guide
- `usage.rst` - Detailed usage examples and tutorials
- `api.rst` - API reference documentation
- `architecture.rst` - Architecture and design documentation
- `security.rst` - Security considerations and best practices
- `troubleshooting.rst` - Common issues and solutions
- `migration.rst` - Version migration guide

## Contributing to Documentation

1. Edit `.rst` files in this directory
2. Build documentation locally to preview changes
3. Ensure no Sphinx warnings or errors
4. Submit pull request with documentation changes

## Documentation Style Guide

- Use reStructuredText (RST) format
- Follow Google docstring style in code
- Include code examples for all features
- Keep examples minimal and focused
- Use proper Sphinx directives (autoclass, autofunction, etc.)
- Cross-reference other documentation sections
