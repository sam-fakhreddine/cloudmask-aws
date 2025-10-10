"""Tests to fill coverage gaps."""

import json
import sys

import pytest

from cloudmask import Config
from cloudmask.config.config_loader import load_config, load_from_json, load_from_toml
from cloudmask.exceptions import ConfigurationError
from cloudmask.io.storage import ensure_secure_permissions, get_default_config_path


class TestConfigLoaderEdgeCases:
    """Test edge cases in config loader."""

    def test_load_from_json_non_dict(self, tmp_path):
        """Test JSON file with non-dict content."""
        config_file = tmp_path / "config.json"
        config_file.write_text(json.dumps(["not", "a", "dict"]))

        with pytest.raises(ConfigurationError, match="must be a dictionary"):
            load_from_json(config_file)

    def test_load_from_toml_with_cloudmask_section(self, tmp_path):
        """Test TOML file with [cloudmask] section."""
        if sys.version_info < (3, 11):
            pytest.skip("TOML support requires Python 3.11+")

        config_file = tmp_path / "config.toml"
        config_file.write_text(
            """
[cloudmask]
seed = "toml-seed"
preserve_prefixes = true
"""
        )

        data = load_from_toml(config_file)
        assert data["seed"] == "toml-seed"

    def test_load_from_toml_without_section(self, tmp_path):
        """Test TOML file without [cloudmask] section."""
        if sys.version_info < (3, 11):
            pytest.skip("TOML support requires Python 3.11+")

        config_file = tmp_path / "config.toml"
        config_file.write_text('seed = "toml-seed"\n')

        data = load_from_toml(config_file)
        assert data["seed"] == "toml-seed"

    def test_load_config_with_custom_patterns(self, tmp_path):
        """Test loading config with custom patterns."""
        config_file = tmp_path / "config.yaml"
        config_file.write_text(
            """
seed: test-seed
custom_patterns:
  - pattern: 'TEST-\\d+'
    name: test
"""
        )

        config = load_config(config_file, use_env=False)
        assert len(config.custom_patterns) == 1
        assert config.custom_patterns[0].name == "test"

    def test_load_config_empty_yaml(self, tmp_path):
        """Test loading empty YAML file."""
        config_file = tmp_path / "config.yaml"
        config_file.write_text("")

        config = load_config(config_file, use_env=False)
        assert config.seed == "default-seed"  # Default value from Config


class TestStorageEdgeCases:
    """Test edge cases in storage module."""

    def test_ensure_secure_permissions_nonexistent(self, tmp_path):
        """Test ensure_secure_permissions on nonexistent file."""
        nonexistent = tmp_path / "nonexistent.json"
        ensure_secure_permissions(nonexistent)  # Should not raise

    def test_ensure_secure_permissions_directory(self, tmp_path):
        """Test ensure_secure_permissions on directory."""
        ensure_secure_permissions(tmp_path)  # Should not raise

    def test_get_default_config_path_nonexistent(self, tmp_path, monkeypatch):
        """Test get_default_config_path when config doesn't exist."""
        monkeypatch.setenv("HOME", str(tmp_path))
        config_path = get_default_config_path()
        assert config_path is None

    def test_get_default_config_path_exists(self, tmp_path, monkeypatch):
        """Test get_default_config_path when config exists."""
        monkeypatch.setenv("HOME", str(tmp_path))
        cloudmask_dir = tmp_path / ".cloudmask"
        cloudmask_dir.mkdir()
        config_file = cloudmask_dir / "config.yml"
        config_file.write_text("seed: test")

        config_path = get_default_config_path()
        assert config_path is not None
        assert config_path.exists()


class TestCLIMain:
    """Test CLI __main__ module."""

    def test_cli_main_module_import(self):
        """Test that CLI __main__ module can be imported."""
        from cloudmask.cli import __main__

        assert hasattr(__main__, "main")


class TestMapperEdgeCases:
    """Test edge cases in mapper module."""

    def test_mapper_merge_with_seed_mismatch(self, tmp_path):
        """Test merging mappings with different seeds."""
        from cloudmask import CloudMask
        from cloudmask.exceptions import MappingError

        mapping_file = tmp_path / "mapping.json"

        # Create initial mapping
        mask1 = CloudMask(seed="seed1")
        mask1.anonymize("vpc-123")
        mask1.save_mapping(mapping_file)

        # Try to merge with different seed
        mask2 = CloudMask(seed="seed2")
        mask2.anonymize("vpc-456")

        with pytest.raises(MappingError, match="different seeds"):
            mask2.save_mapping(mapping_file)


class TestCoreEdgeCases:
    """Test edge cases in core module."""

    def test_cloudmask_with_config_object(self):
        """Test CloudMask with Config object."""
        from cloudmask import CloudMask

        config = Config(seed="test-seed", preserve_prefixes=False)
        mask = CloudMask(config=config)

        result = mask.anonymize("vpc-123")
        assert "vpc-" not in result  # Prefixes not preserved

    def test_cloudunmask_with_nonexistent_mapping(self, tmp_path):
        """Test CloudUnmask with nonexistent mapping file."""
        from cloudmask import CloudUnmask
        from cloudmask.exceptions import FileOperationError

        nonexistent = tmp_path / "nonexistent.json"

        with pytest.raises(FileOperationError, match="not found"):
            CloudUnmask(mapping_file=nonexistent)


class TestStreamingEdgeCases:
    """Test edge cases in streaming module."""

    def test_stream_anonymize_empty_file(self, tmp_path):
        """Test streaming with empty file."""
        from cloudmask import CloudMask
        from cloudmask.io.streaming import stream_anonymize_file

        input_file = tmp_path / "empty.txt"
        output_file = tmp_path / "output.txt"
        input_file.write_text("")

        mask = CloudMask(seed="test")
        count = stream_anonymize_file(mask, input_file, output_file)
        assert output_file.read_text() == ""
        assert count == 0

    def test_stream_unanonymize_empty_file(self, tmp_path):
        """Test streaming unanonymize with empty file."""
        from cloudmask import CloudUnmask
        from cloudmask.io.streaming import stream_unanonymize_file

        input_file = tmp_path / "empty.txt"
        output_file = tmp_path / "output.txt"
        input_file.write_text("")

        unmask = CloudUnmask(mapping={})
        count = stream_unanonymize_file(unmask, input_file, output_file)
        assert output_file.read_text() == ""
        assert count == 0


class TestLoggingEdgeCases:
    """Test edge cases in logging module."""

    def test_setup_logging_with_file(self, tmp_path):
        """Test logging setup with file output."""
        from cloudmask.logging import setup_logging

        log_file = tmp_path / "test.log"
        setup_logging(level="DEBUG", log_file=log_file, debug=True)

        # Verify log file is created
        assert log_file.exists()

    def test_log_error_with_exception(self):
        """Test log_error with exception."""
        from cloudmask.logging import log_error

        try:
            raise ValueError("Test error")
        except ValueError as e:
            log_error(e, "Test context")  # Should not raise


class TestPatternsEdgeCases:
    """Test edge cases in patterns module."""

    def test_compile_pattern_cached(self):
        """Test pattern compilation with caching."""
        from cloudmask.utils.patterns import compile_pattern

        pattern1 = compile_pattern(r"TEST-\d+")
        pattern2 = compile_pattern(r"TEST-\d+")
        assert pattern1 is pattern2  # Same object due to caching

    def test_is_valid_aws_resource_id(self):
        """Test AWS resource ID validation."""
        from cloudmask.utils.patterns import is_valid_aws_resource_id

        assert is_valid_aws_resource_id("vpc-123")
        assert is_valid_aws_resource_id("i-1234567890abcdef0")
        assert not is_valid_aws_resource_id("invalid")


class TestSecurityEdgeCases:
    """Test edge cases in security module."""

    def test_encrypt_decrypt_mapping_roundtrip(self, tmp_path):
        """Test encrypt/decrypt mapping roundtrip."""
        from cloudmask.utils.security import decrypt_mapping, encrypt_mapping

        mapping = {"vpc-123": "vpc-abc", "i-456": "i-def"}
        password = "test-password"

        encrypted_bytes = encrypt_mapping(mapping, password)
        decrypted = decrypt_mapping(encrypted_bytes, password)

        assert decrypted == mapping

    def test_decrypt_mapping_wrong_password(self, tmp_path):
        """Test decrypting with wrong password."""
        from cloudmask.exceptions import EncryptionError
        from cloudmask.utils.security import decrypt_mapping, encrypt_mapping

        mapping = {"vpc-123": "vpc-abc"}
        encrypted_bytes = encrypt_mapping(mapping, "correct-password")

        with pytest.raises(EncryptionError, match="Decryption failed"):
            decrypt_mapping(encrypted_bytes, "wrong-password")
