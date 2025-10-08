# CloudMask Documentation Quick Start

## Building the Documentation

```bash
# Install dependencies
uv pip install -e ".[dev]"

# Build HTML docs
make docs

# View in browser
open docs/_build/html/index.html
```

## Documentation Pages

| Page | Description | Key Topics |
|------|-------------|------------|
| **Getting Started** | Installation and quick start | Installation, requirements, first steps |
| **Usage Guide** | Detailed examples and tutorials | Basic usage, advanced features, use cases |
| **API Reference** | Complete API documentation | Classes, functions, modules |
| **Architecture** | Technical design and internals | Components, data flow, algorithms |
| **Security** | Security best practices | Threat model, encryption, compliance |
| **Troubleshooting** | Common issues and solutions | Error messages, debugging, diagnostics |
| **Migration** | Version upgrade guide | Breaking changes, migration steps |

## Quick Commands

```bash
# Build docs
cd docs && make html

# Clean build
cd docs && make clean

# Rebuild from scratch
cd docs && make clean && make html

# View locally
python -m http.server 8000 --directory docs/_build/html
# Then open http://localhost:8000
```

## Documentation Standards

- **Format**: reStructuredText (.rst)
- **Docstrings**: Google style
- **Theme**: Read the Docs
- **Build Tool**: Sphinx 8.x

## Adding New Documentation

1. Create new `.rst` file in `docs/`
2. Add to `toctree` in `docs/index.rst`
3. Build and verify: `make docs`
4. Check for warnings in build output

## Common Sphinx Directives

```rst
.. code-block:: python

   # Python code example

.. autoclass:: cloudmask.CloudMask
   :members:

.. autofunction:: cloudmask.anonymize

.. note::
   Important information

.. warning::
   Critical warning
```

## Links

- [Sphinx Documentation](https://www.sphinx-doc.org/)
- [reStructuredText Primer](https://www.sphinx-doc.org/en/master/usage/restructuredtext/basics.html)
- [Read the Docs Theme](https://sphinx-rtd-theme.readthedocs.io/)
