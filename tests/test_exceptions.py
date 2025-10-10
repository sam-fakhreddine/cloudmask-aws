"""Tests for custom exceptions and error handling."""

import pytest

from cloudmask import (
    CloudMask,
    CloudMaskError,
    Config,
    ConfigurationError,
    CustomPattern,
    FileOperationError,
    MappingError,
    ValidationError,
)
from cloudmask.exceptions import EncryptionError
from cloudmask.utils.security import decrypt_mapping, encrypt_mapping


def test_exception_with_suggestion():
    """Test that exceptions include suggestions."""
    error = CloudMaskError("Something went wrong", "Try this instead")
    assert "Something went wrong" in str(error)
    assert "Try this instead" in str(error)


def test_exception_without_suggestion():
    """Test that exceptions work without suggestions."""
    error = CloudMaskError("Something went wrong")
    assert "Something went wrong" in str(error)
    assert "Suggestion" not in str(error)


def test_invalid_regex_raises_validation_error():
    """Test that invalid regex raises ValidationError."""
    with pytest.raises(ValidationError) as exc_info:
        CustomPattern(pattern="[invalid(", name="test")

    assert "Invalid regex pattern" in str(exc_info.value)
    assert exc_info.value.suggestion is not None


def test_short_password_raises_validation_error():
    """Test that short password raises ValidationError."""
    with pytest.raises(ValidationError) as exc_info:
        encrypt_mapping({"key": "value"}, "short")

    assert "8 characters" in str(exc_info.value)


def test_wrong_password_raises_encryption_error():
    """Test that wrong password raises EncryptionError."""
    encrypted = encrypt_mapping({"key": "value"}, "correct_password")

    with pytest.raises(EncryptionError) as exc_info:
        decrypt_mapping(encrypted, "wrong_password")

    assert "Decryption failed" in str(exc_info.value)


def test_missing_file_raises_file_operation_error(tmp_path):
    """Test that missing file raises FileOperationError."""
    mask = CloudMask()
    nonexistent = tmp_path / "nonexistent.txt"
    output = tmp_path / "output.txt"

    with pytest.raises(FileOperationError) as exc_info:
        mask.anonymize_file(nonexistent, output)

    assert "not found" in str(exc_info.value)
    assert exc_info.value.suggestion is not None


def test_invalid_mapping_file_raises_mapping_error(tmp_path):
    """Test that invalid mapping file raises MappingError."""
    mapping_file = tmp_path / "invalid.json"
    mapping_file.write_text("not valid json")

    mask = CloudMask()
    with pytest.raises(MappingError) as exc_info:
        mask.load_mapping(mapping_file)

    assert "Invalid JSON" in str(exc_info.value)


def test_invalid_config_type_raises_configuration_error():
    """Test that invalid config types raise ConfigurationError."""
    with pytest.raises(ConfigurationError) as exc_info:
        Config(company_names="not a list")  # type: ignore[arg-type]

    assert "must be a list" in str(exc_info.value)


def test_missing_config_file_raises_file_operation_error(tmp_path):
    """Test that missing config file raises FileOperationError."""
    nonexistent = tmp_path / "nonexistent.yaml"

    with pytest.raises(FileOperationError) as exc_info:
        Config.from_yaml(nonexistent)

    assert "not found" in str(exc_info.value)
