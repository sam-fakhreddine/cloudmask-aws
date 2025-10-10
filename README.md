<div align="center">

<img src="logo.png" alt="CloudMask Logo" width="200"/>

# CloudMask-AWS 🎭

**Anonymize AWS infrastructure identifiers for secure LLM processing**

[![PyPI version](https://badge.fury.io/py/cloudmask-aws.svg)](https://badge.fury.io/py/cloudmask-aws)
[![Python Versions](https://img.shields.io/pypi/pyversions/cloudmask-aws.svg)](https://pypi.org/project/cloudmask-aws/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

</div>

CloudMask helps you safely share AWS infrastructure data with Large Language Models by anonymizing sensitive identifiers while maintaining structure and reversibility.

## Features

- 🔒 **Secure Anonymization**: Hash-based deterministic anonymization
- 🔄 **Reversible**: Complete mapping for unanonymization
- 🏗️ **Structure-Preserving**: Maintains AWS resource ID prefixes (vpc-, i-, etc.)
- ⚙️ **Configurable**: YAML-based configuration for company names and custom patterns
- 🐍 **Dual Interface**: Use as CLI tool or Python library
- 📋 **Clipboard Support**: Direct clipboard anonymization for quick workflows
- 📦 **Modern Python**: Built with Python 3.10+ features (pattern matching, union types)
- 🚀 **Minimal Dependencies**: Only requires PyYAML and pyperclip

## Requirements

- Python 3.10 or higher
- PyYAML 6.0+

CloudMask leverages modern Python features including structural pattern matching, union type operators, and built-in generic types.

## Installation

```bash
pip install cloudmask-aws
```

## Quick Start

### CLI Usage

```bash
# Generate config file
cloudmask init-config

# Anonymize (mapping stored in ~/.cloudmask/mapping.json by default)
cloudmask anonymize -i infrastructure.txt -o anonymized.txt

# Anonymize clipboard content
cloudmask anonymize --clipboard

# Restore original values
cloudmask unanonymize -i llm-response.txt -o restored.txt

# Restore clipboard content
cloudmask unanonymize --clipboard

# Use custom mapping location if needed
cloudmask anonymize --clipboard -m /path/to/custom-mapping.json
```

### Python Library Usage

```python
from cloudmask import CloudMask, CloudUnmask, get_default_mapping_path

# Anonymize text
mask = CloudMask(seed="my-secret-seed")
anonymized = mask.anonymize("""
    Instance i-1234567890abcdef0 is running in vpc-abcdef123456
    Account: 123456789012
    Company: Acme Corp
""")

# Save mapping to secure central location (~/.cloudmask/mapping.json)
mask.save_mapping(get_default_mapping_path())

# Unanonymize later
unmask = CloudUnmask(mapping_file=get_default_mapping_path())
original = unmask.unanonymize(anonymized)
```

### Quick Function Usage

```python
from cloudmask import anonymize, unanonymize

# One-liner anonymization
text, mapping = anonymize(
    "Instance i-123 in account 123456789012",
    seed="my-seed",
    company_names=["Acme Corp"]
)

# Restore original
original = unanonymize(text, mapping)
```

## Configuration

Create a `~/.cloudmask/config.yml` file (or use `cloudmask init-config`):

```yaml
company_names:
  - Acme Corp
  - Example Inc
  - MyCompany LLC

custom_patterns:
  - pattern: '\bTICKET-\d{4,6}\b'
    name: ticket
  - pattern: '\bPROJ-[A-Z0-9]+'
    name: project
  # Example: Match company domains
  - pattern: '[a-zA-Z0-9][-a-zA-Z0-9.]*\.acme\.local\b'
    name: domain
  # Example: Match company emails
  - pattern: '[a-zA-Z0-9._%+-]+@acme-corp\.local\b'
    name: email

preserve_prefixes: true
anonymize_ips: true
anonymize_domains: false
seed: my-secret-seed
```

### Custom Pattern Edge Cases

When creating custom patterns, be aware of:

- **Case sensitivity**: Patterns are case-insensitive by default
- **Multi-level subdomains**: Use `[-a-zA-Z0-9.]*` to match `app.corp.acme.local`
- **HTML entities**: `&quot;` in data is handled automatically
- **Email variations**: Pattern supports `user+tag@domain` and `user.name@domain`
- **URLs and paths**: Patterns work in `https://server.acme.local/path`
- **Trailing punctuation**: Word boundaries (`\b`) handle `server.acme.local.`

Test your patterns:
```bash
cloudmask anonymize -i test.txt -o output.txt
grep -i "sensitive-term" output.txt  # Should return nothing
```

## What Gets Anonymized?

- ✅ AWS Resource IDs (vpc-, i-, sg-, ami-, etc.)
- ✅ AWS Account IDs (12-digit numbers)
- ✅ AWS ARNs
- ✅ IP Addresses
- ✅ Company names (from config)
- ✅ Custom patterns (via regex)
- ✅ Domain names (optional)

## Use Cases

- 🤖 **LLM Assistance**: Get help with infrastructure without exposing sensitive IDs
- 📊 **Data Sharing**: Share infrastructure diagrams and configs safely
- 🔍 **Security Analysis**: Analyze configs with external tools
- 📝 **Documentation**: Create shareable examples from real infrastructure

## Advanced Usage

### Using in Scripts

```python
from cloudmask import CloudMask, Config
from pathlib import Path

# Load custom config
config = Config.from_yaml(Path("custom-config.yaml"))

# Create anonymizer
mask = CloudMask(config=config, seed="production-seed")

# Process multiple files
for file in Path("configs").glob("*.yaml"):
    output = Path("anonymized") / file.name
    mask.anonymize_file(file, output)

# Save single mapping for all files
mask.save_mapping("master-mapping.json")
```

### Context Manager

```python
from cloudmask import TemporaryMask

with TemporaryMask(seed="temp-seed") as mask:
    anonymized = mask.anonymize("vpc-123 i-456")
    # Process anonymized data
    # Mapping is discarded after context exits
```

### Batch Processing

```python
from cloudmask import create_batch_anonymizer

# Create reusable anonymizer
anon = create_batch_anonymizer(seed="batch-seed")

# Use it multiple times
result1 = anon("vpc-123")
result2 = anon("i-456")
```

## Central Storage

CloudMask stores mapping files in a secure central location by default:

```
~/.cloudmask/mapping.json
```

### Benefits

- 🔐 **Automatic Security**: Files created with `600` permissions (owner read/write only)
- 📍 **Centralized**: All mappings in one location
- 🔄 **Auto-Merge**: New mappings are merged with existing ones (same seed required)
- ⚡ **Convenient**: No need to specify `-m` flag for common workflows

### Seed Verification

CloudMask tracks which seed created each mapping file. Mappings can only be merged if they use the same seed:

```python
# First use
mask1 = CloudMask(seed="prod-seed")
mask1.anonymize("vpc-11111")
mask1.save_mapping(get_default_mapping_path())  # Creates mapping

# Later use with SAME seed - mappings merge automatically
mask2 = CloudMask(seed="prod-seed")
mask2.anonymize("vpc-22222")
mask2.save_mapping(get_default_mapping_path())  # Merges with existing

# Different seed - prevents accidental corruption
mask3 = CloudMask(seed="different-seed")
mask3.save_mapping(get_default_mapping_path())  # ERROR: Seed mismatch
```

### Custom Locations

You can still use custom mapping locations:

```bash
cloudmask anonymize -i file.txt -m /custom/path/mapping.json
```

```python
mask.save_mapping("/custom/path/mapping.json")
```

## Security Notes

⚠️ **Keep your mapping files secure!** They contain the reversible mappings.

- The `~/.cloudmask/` directory is automatically secured with `700` permissions
- Mapping files are created with `600` permissions (owner only)
- Store mapping files separately from anonymized data
- Use strong, unique seeds for different projects
- Don't commit mapping files to version control
- Consider encrypting mapping files for sensitive data
- Always use the same seed for a project to enable mapping merges

## Contributing

Contributions welcome! Please check out the [GitHub repository](https://github.com/sam-fakhreddine/cloudmask-aws).

## License

MIT License - see LICENSE file for details

## Troubleshooting

### Pattern Not Matching?

1. Test the regex: `python -c "import re; print(re.search(r'your-pattern', 'test-string'))"`
2. Check case sensitivity: Patterns are case-insensitive
3. Verify word boundaries: `\b` may not work with special characters
4. Test with real data: Use small samples first

### Data Still Leaking?

1. Check pattern order: Custom patterns run before company names
2. Verify pattern name: Use generic names like `domain`, not `acme-domain`
3. Test thoroughly: `grep -i "sensitive" output.txt`

## Support

- 📖 [Documentation](https://github.com/sam-fakhreddine/cloudmask-aws#readme)
- 🐛 [Issue Tracker](https://github.com/sam-fakhreddine/cloudmask-aws/issues)
- 💬 [Discussions](https://github.com/sam-fakhreddine/cloudmask-aws/discussions)
