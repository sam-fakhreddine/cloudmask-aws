# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [0.5.0] - 2026-03-12

### Added
- Claude Code hooks: full tool coverage (Read, Write, Edit, Grep, Bash)
- Shadow file anonymization with symlinks for non-sensitive files
- Bash output masking via `mask-output.py` line-by-line pipe
- Real-file demask for new files (CSVs, reports) created with anonymized content
- Prompt blocking hook with masked prompt save/resubmit workflow
- Encrypted mapping file (Fernet/AES-128, PBKDF2 key derivation)
- Rotating file logs (25MB x 3 backups) for all hooks
- Comprehensive hook documentation with Mermaid sequence diagrams

### Changed
- Deterministic anonymization now uses HMAC-SHA256 with configurable seed
- Lazy `__getattr__` imports in `__init__.py` for reduced startup overhead
- Mapping manager uses file locking (`fcntl.flock`) for concurrent access

## [0.1.5] - 2025-10-09

### Changed
- Release automation fix

## [0.1.4] - 2025-10-09

### Changed
- Maintenance release with version sync

## [0.1.1] - 2025-01-XX

### Fixed
- Updated PyPI metadata to correctly show Python 3.10+ requirement (removed 3.7, 3.8, 3.9)

## [0.1.0] - 2025-01-XX

### Added
- Comprehensive test suite with 86%+ coverage
- Security features: encrypted mapping files, rate limiting
- Input validation for all user inputs
- Extensive documentation with Sphinx
- Pre-commit hooks and code quality tools

### Added
- Initial release
- Core anonymization functionality for AWS resources
- Support for VPC, EC2, security groups, ARNs, account IDs
- IP address anonymization
- Company name anonymization
- Custom pattern support via regex
- YAML-based configuration
- CLI interface with `anonymize` and `unanonymize` commands
- Python library API with `CloudMask` and `CloudUnmask` classes
- Convenience functions `anonymize()` and `unanonymize()`
- Deterministic anonymization using SHA-256
- Reversible mapping with JSON export
- Python 3.10+ support with modern features (pattern matching, union types)

### Features
- Preserves AWS resource ID prefixes (vpc-, i-, sg-, etc.)
- Configurable via YAML files
- Dual interface: CLI and Python library
- Clipboard support for quick workflows
- Context manager support for temporary anonymization
- Batch processing utilities

[Unreleased]: https://github.com/samfakhreddine/cloudmask/compare/v0.1.1...HEAD
[0.1.1]: https://github.com/samfakhreddine/cloudmask/compare/v0.1.0...v0.1.1
[0.1.0]: https://github.com/samfakhreddine/cloudmask/releases/tag/v0.1.0
