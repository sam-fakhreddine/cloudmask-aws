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

# Anonymize a file
cloudmask anonymize -i infrastructure.txt -o anonymized.txt -m mapping.json

# Anonymize clipboard content
cloudmask anonymize --clipboard -m mapping.json

# Restore original values
cloudmask unanonymize -i llm-response.txt -o restored.txt -m mapping.json

# Restore clipboard content
cloudmask unanonymize --clipboard -m mapping.json
```

### Python Library Usage

```python
from cloudmask import CloudMask, CloudUnmask

# Anonymize text
mask = CloudMask(seed="my-secret-seed")
anonymized = mask.anonymize("""
    Instance i-1234567890abcdef0 is running in vpc-abcdef123456
    Account: 123456789012
    Company: Acme Corp
""")

# Save mapping for later
mask.save_mapping("mapping.json")

# Unanonymize later
unmask = CloudUnmask(mapping_file="mapping.json")
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

Create a `cloudmask.yaml` file:

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

preserve_prefixes: true
anonymize_ips: true
anonymize_domains: false
seed: my-secret-seed
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

## Security Notes

⚠️ **Keep your mapping files secure!** They contain the reversible mappings.

- Store mapping files separately from anonymized data
- Use strong, unique seeds for different projects
- Don't commit mapping files to version control
- Consider encrypting mapping files for sensitive data

## Contributing

Contributions welcome! Please check out the [GitHub repository](https://github.com/sam-fakhreddine/cloudmask-aws).

## License

MIT License - see LICENSE file for details

## Support

- 📖 [Documentation](https://github.com/sam-fakhreddine/cloudmask-aws#readme)
- 🐛 [Issue Tracker](https://github.com/sam-fakhreddine/cloudmask-aws/issues)
- 💬 [Discussions](https://github.com/sam-fakhreddine/cloudmask-aws/discussions)
