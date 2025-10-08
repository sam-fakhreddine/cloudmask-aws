"""File processing examples."""

import tempfile
from pathlib import Path

from cloudmask import CloudMask, CloudUnmask, Config

# Example: Process files
print("=" * 50)
print("File Processing Example")
print("=" * 50)

# Create temporary files for demo
with tempfile.TemporaryDirectory() as tmpdir_str:
    tmpdir = Path(tmpdir_str)

    input_file: Path = tmpdir / "infrastructure.txt"
    input_file.write_text(
        """
AWS Infrastructure Configuration:

VPC Configuration:
- VPC ID: vpc-1234567890abcdef
- CIDR: 10.0.0.0/16
- Subnets:
  - subnet-111: 10.0.1.0/24
  - subnet-222: 10.0.2.0/24

EC2 Instances:
- Web Server: i-aaa111bbb222ccc
- Database: i-ddd333eee444fff
- Account: 123456789012

Security Groups:
- sg-web123: Port 80, 443
- sg-db456: Port 3306
    """
    )

    output_file: Path = tmpdir / "anonymized.txt"
    mapping_file: Path = tmpdir / "mapping.json"

    config = Config()
    mask = CloudMask(config=config, seed="file-processing-seed")

    count = mask.anonymize_file(input_file, output_file)
    mask.save_mapping(mapping_file)

    print(f"✓ Anonymized {count} unique identifiers")
    print("\nAnonymized content:")
    print(output_file.read_text())

    restored_file: Path = tmpdir / "restored.txt"
    unmask = CloudUnmask(mapping_file=mapping_file)
    unmask.unanonymize_file(output_file, restored_file)

    print("\n" + "=" * 50)
    print("Verification")
    print("=" * 50)
    original = input_file.read_text()
    restored = restored_file.read_text()
    print(f"Files match: {original == restored}")
