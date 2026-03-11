# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

CloudMask is a Python library and CLI tool that anonymizes AWS infrastructure identifiers (resource IDs, account IDs, ARNs, IPs, domains, company names) for secure LLM processing. Anonymization is deterministic (SHA256 + seed), reversible via mapping files, and structure-preserving (AWS prefixes like `vpc-`, `i-`, `sg-` are retained).

## Development Commands

```bash
# Setup
uv venv && uv pip install -e ".[dev]"

# Quality checks
make format          # black (line-length 100)
make lint            # ruff check
make lint-fix        # ruff check --fix
make type-check      # mypy (strict mode)
make quality-check   # all of the above + pydocstyle

# Tests
make test            # pytest (includes coverage)
make test-cov        # pytest with HTML coverage report
pytest tests/test_cloudmask.py              # single file
pytest tests/test_cloudmask.py::test_name   # single test

# Docs
make docs            # Sphinx HTML docs → docs/_build/html/
```

## Architecture

Source lives in `src/cloudmask/` using a src-layout. The package is organized into four subpackages:

**Core layer** (`core.py`, `anonymizer.py`, `mapper.py`):
- `CloudMask` — main entry point; composes `Anonymizer` + `MappingManager`
- `CloudUnmask` — reverses anonymization using a mapping dict or file
- `TemporaryMask` — context manager for scoped anonymization
- `Anonymizer` — the hashing engine (SHA256 with seed); maintains an in-memory mapping dict
- `MappingManager` — JSON mapping file I/O with atomic writes, seed verification, and merge support

**config/** — `Config` and `CustomPattern` dataclasses, multi-format loader (YAML/JSON/TOML + env vars), predefined templates via `ConfigTemplates`

**io/** — `Storage` singleton for `~/.cloudmask/` central storage (secure permissions 700/600), `FileProcessor` for bounded file I/O (100MB limit), `streaming.py` for chunked large-file processing with optional tqdm progress

**utils/** — `patterns.py` has pre-compiled regex for all AWS resource types; `security.py` provides Fernet/AES-256 encryption with PBKDF2 key derivation; `cache.py` has LRU cache (1000 entries); `ratelimit.py` has token-bucket rate limiters

**cli/** — argparse-based CLI dispatching to handler functions in `cli_handlers.py`. Entry point: `cloudmask.cli.cli:main`

## Key Conventions

- **Python 3.10+** required. Uses `match/case`, `X | Y` union types, `list[T]`/`dict[K,V]` generics.
- **Type annotations** on all public functions (mypy strict mode).
- **Google-style docstrings** enforced by pydocstyle.
- **Line length**: 100 characters (black + ruff).
- **Import order**: ruff isort with `cloudmask` as known first-party.
- **Exceptions**: custom hierarchy rooted at `CloudMaskError` in `exceptions.py`. Six subclasses: `ConfigurationError`, `ValidationError`, `FileOperationError`, `MappingError`, `EncryptionError`, `ClipboardError`.
- **`__init__.py`** re-exports the full public API (~91 names). New public symbols must be added there.
- **Ruff ignores**: `F401` in `__init__.py`, `ARG`/`S101` in tests.
