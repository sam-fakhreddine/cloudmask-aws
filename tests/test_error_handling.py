"""Error handling tests for CloudMask."""

import json

import pytest

from cloudmask import CloudMask, CloudUnmask, Config, CustomPattern, anonymize_dict
from cloudmask.exceptions import (
    ConfigurationError,
    FileOperationError,
    MappingError,
    ValidationError,
)


class TestErrorHandling:
    """Test error handling and exception cases."""

    def test_invalid_config_file(self, tmp_path):
        """Test loading invalid YAML config."""
        config_file = tmp_path / "invalid.yaml"
        config_file.write_text("invalid: yaml: content: [")

        with pytest.raises((ValueError, FileOperationError, ConfigurationError)):
            Config.from_yaml(config_file)

    def test_nonexistent_config_file(self, tmp_path):
        """Test loading nonexistent config file."""
        with pytest.raises(FileOperationError):
            Config.from_yaml(tmp_path / "nonexistent.yaml")

    def test_invalid_mapping_file(self, tmp_path):
        """Test loading invalid JSON mapping."""
        mapping_file = tmp_path / "invalid.json"
        mapping_file.write_text("{invalid json")

        with pytest.raises(MappingError):
            CloudUnmask(mapping_file=mapping_file)

    def test_nonexistent_mapping_file(self, tmp_path):
        """Test loading nonexistent mapping file."""
        with pytest.raises(FileOperationError):
            CloudUnmask(mapping_file=tmp_path / "nonexistent.json")

    def test_both_mapping_and_file_provided(self, tmp_path):
        """Test error when both mapping and mapping_file provided."""
        mapping_file = tmp_path / "mapping.json"
        mapping_file.write_text("{}")

        with pytest.raises(ValidationError, match="not both"):
            CloudUnmask(mapping={"test": "value"}, mapping_file=mapping_file)

    def test_anonymize_nonexistent_file(self, tmp_path):
        """Test anonymizing nonexistent file."""
        mask = CloudMask(seed="test")

        with pytest.raises(FileOperationError):
            mask.anonymize_file(tmp_path / "nonexistent.txt", tmp_path / "output.txt")

    def test_anonymize_to_readonly_location(self, tmp_path):
        """Test writing to read-only location."""
        input_file = tmp_path / "input.txt"
        input_file.write_text("vpc-123")

        output_dir = tmp_path / "readonly"
        output_dir.mkdir()
        output_dir.chmod(0o444)  # Read-only

        mask = CloudMask(seed="test")

        try:
            with pytest.raises(FileOperationError):
                mask.anonymize_file(input_file, output_dir / "output.txt")
        finally:
            output_dir.chmod(0o755)  # Restore permissions for cleanup

    def test_save_mapping_to_readonly_location(self, tmp_path):
        """Test saving mapping to read-only location."""
        readonly_dir = tmp_path / "readonly"
        readonly_dir.mkdir()
        readonly_dir.chmod(0o444)

        mask = CloudMask(seed="test")
        mask.anonymize("vpc-123")

        try:
            with pytest.raises(FileOperationError):
                mask.save_mapping(readonly_dir / "mapping.json")
        finally:
            readonly_dir.chmod(0o755)

    def test_load_corrupted_mapping(self, tmp_path):
        """Test loading corrupted mapping file."""
        mapping_file = tmp_path / "corrupted.json"
        mapping_file.write_text('{"key": "value"')  # Missing closing brace

        with pytest.raises(MappingError):
            mask = CloudMask(seed="test")
            mask.load_mapping(mapping_file)

    def test_empty_mapping_file(self, tmp_path):
        """Test loading empty mapping file."""
        mapping_file = tmp_path / "empty.json"
        mapping_file.write_text("")

        with pytest.raises(MappingError):
            CloudUnmask(mapping_file=mapping_file)

    def test_config_with_invalid_pattern(self):
        """Test config with invalid regex pattern."""
        with pytest.raises(ValidationError, match="Invalid regex"):
            CustomPattern(pattern="[invalid(", name="bad")

    def test_unanonymize_nonexistent_file(self, tmp_path):
        """Test unanonymizing nonexistent file."""
        unmask = CloudUnmask(mapping={})

        with pytest.raises(FileOperationError):
            unmask.unanonymize_file(tmp_path / "nonexistent.txt", tmp_path / "output.txt")

    def test_binary_file_handling(self, tmp_path):
        """Test handling of binary files."""
        binary_file = tmp_path / "binary.bin"
        binary_file.write_bytes(b"\x00\x01\x02\x03\xff\xfe")

        mask = CloudMask(seed="test")

        with pytest.raises(FileOperationError):
            mask.anonymize_file(binary_file, tmp_path / "output.txt")

    def test_extremely_large_mapping(self, tmp_path):
        """Test handling of very large mapping files."""
        mask = CloudMask(seed="test")

        # Create large mapping
        for i in range(10000):
            mask.anonymize(f"vpc-{i:016x}")

        mapping_file = tmp_path / "large_mapping.json"
        mask.save_mapping(mapping_file)

        # Should be able to load it back
        mask2 = CloudMask(seed="different")
        mask2.load_mapping(mapping_file)

        assert len(mask2.mapping) == 10000

    def test_config_with_none_values(self):
        """Test config with None values."""
        config = Config(seed=None)  # type: ignore
        mask = CloudMask(config=config)

        # Should use default seed
        result = mask.anonymize("vpc-123")
        assert "vpc-123" not in result

    def test_anonymize_with_encoding_errors(self, tmp_path):
        """Test file with encoding issues."""
        file_with_encoding = tmp_path / "encoded.txt"

        # Write file with latin-1 encoding
        file_with_encoding.write_bytes("vpc-123 café".encode("latin-1"))

        mask = CloudMask(seed="test")

        # Should handle encoding gracefully or raise appropriate error
        with pytest.raises(FileOperationError):
            mask.anonymize_file(file_with_encoding, tmp_path / "output.txt")

    def test_circular_reference_in_dict(self):
        """Test handling of circular references in dict anonymization."""
        mask = CloudMask(seed="test")

        # Create circular reference
        data: dict[str, object] = {"vpc": "vpc-123"}
        data["self"] = data

        # Should handle gracefully (may raise RecursionError)
        with pytest.raises(RecursionError):
            anonymize_dict(data, mask)

    def test_save_mapping_overwrites_existing(self, tmp_path):
        """Test that saving mapping overwrites existing file."""
        mapping_file = tmp_path / "mapping.json"

        mask1 = CloudMask(seed="test1")
        mask1.anonymize("vpc-111")
        mask1.save_mapping(mapping_file)

        mask2 = CloudMask(seed="test2")
        mask2.anonymize("vpc-222")
        mask2.save_mapping(mapping_file)

        # Should contain only mask2's mapping
        loaded = json.loads(mapping_file.read_text())
        assert "vpc-222" in loaded
        assert "vpc-111" not in loaded

    def test_load_mapping_with_wrong_format(self, tmp_path):
        """Test loading mapping with wrong format."""
        mapping_file = tmp_path / "wrong_format.json"
        mapping_file.write_text('["array", "not", "dict"]')

        mask = CloudMask(seed="test")

        with pytest.raises(MappingError):
            mask.load_mapping(mapping_file)

    def test_config_yaml_with_extra_fields(self, tmp_path):
        """Test config YAML with extra unknown fields."""
        config_file = tmp_path / "config.yaml"
        config_file.write_text(
            """
company_names:
  - Test Corp
unknown_field: value
another_unknown: 123
seed: test-seed
"""
        )

        # Should load successfully, ignoring unknown fields
        config = Config.from_yaml(config_file)
        assert config.seed == "test-seed"
        assert "Test Corp" in config.company_names

    def test_empty_config_file(self, tmp_path):
        """Test loading empty config file."""
        config_file = tmp_path / "empty.yaml"
        config_file.write_text("")

        # Should create config with defaults
        config = Config.from_yaml(config_file)
        assert config.preserve_prefixes is True

    def test_config_with_null_values(self, tmp_path):
        """Test config with null/None values in YAML."""
        config_file = tmp_path / "null_config.yaml"
        config_file.write_text(
            """
company_names: null
seed: test-seed
"""
        )

        with pytest.raises(ConfigurationError):
            Config.from_yaml(config_file)


@pytest.fixture
def tmp_path(tmp_path_factory):
    """Create a temporary directory."""
    return tmp_path_factory.mktemp("error_test")
