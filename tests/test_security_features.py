"""Tests for security features."""

import time

import pytest

from cloudmask import (
    Config,
    decrypt_mapping,
    encrypt_mapping,
    load_encrypted_mapping,
    save_encrypted_mapping,
)
from cloudmask.exceptions import (
    ConfigurationError,
    EncryptionError,
    FileOperationError,
    ValidationError,
)
from cloudmask.ratelimit import BatchRateLimiter, RateLimiter


class TestEncryption:
    """Test mapping encryption/decryption."""

    def test_encrypt_decrypt_mapping(self):
        """Test basic encryption and decryption."""
        mapping = {"vpc-123": "vpc-abc", "i-456": "i-def"}
        password = "test-password-123"

        encrypted = encrypt_mapping(mapping, password)
        decrypted = decrypt_mapping(encrypted, password)

        assert decrypted == mapping

    def test_encrypt_with_short_password(self):
        """Test that short passwords are rejected."""
        mapping = {"vpc-123": "vpc-abc"}

        with pytest.raises(ValidationError, match="at least 8 characters"):
            encrypt_mapping(mapping, "short")

    def test_decrypt_with_wrong_password(self):
        """Test that wrong password fails decryption."""
        mapping = {"vpc-123": "vpc-abc"}
        password = "correct-password"

        encrypted = encrypt_mapping(mapping, password)

        with pytest.raises(EncryptionError, match="Decryption failed"):
            decrypt_mapping(encrypted, "wrong-password")

    def test_save_load_encrypted_mapping(self, tmp_path):
        """Test saving and loading encrypted mapping files."""
        mapping = {"vpc-123": "vpc-abc", "i-456": "i-def"}
        password = "test-password-123"
        filepath = tmp_path / "encrypted.bin"

        save_encrypted_mapping(mapping, filepath, password)
        loaded = load_encrypted_mapping(filepath, password)

        assert loaded == mapping

    def test_load_encrypted_nonexistent_file(self, tmp_path):
        """Test loading nonexistent encrypted file."""
        with pytest.raises(FileOperationError):
            load_encrypted_mapping(tmp_path / "nonexistent.bin", "password")


class TestRateLimiting:
    """Test rate limiting functionality."""

    def test_rate_limiter_allows_operations(self):
        """Test that rate limiter allows operations within limit."""
        limiter = RateLimiter(max_operations=5, time_window=1.0)

        # Should allow 5 operations
        for _ in range(5):
            assert limiter.acquire() is True

        # 6th operation should be denied
        assert limiter.acquire() is False

    def test_rate_limiter_wait(self):
        """Test that wait() blocks until operation is allowed."""
        limiter = RateLimiter(max_operations=2, time_window=0.1)

        # Use up the limit
        limiter.acquire()
        limiter.acquire()

        # This should wait and then succeed
        start = time.time()
        limiter.wait()
        duration = time.time() - start

        # Should have waited at least 0.1 seconds
        assert duration >= 0.05

    def test_batch_rate_limiter(self):
        """Test batch rate limiter."""
        limiter = BatchRateLimiter(max_items_per_second=100)

        items = list(range(10))
        results = limiter.process_batch(items, lambda x: x * 2)

        assert results == [x * 2 for x in items]


class TestConfigValidation:
    """Test configuration validation."""

    def test_config_with_empty_seed(self):
        """Test that empty seed is rejected in production validation."""
        config = Config(seed="")
        with pytest.raises(ValidationError, match="Seed cannot be empty"):
            config.validate_for_production()

    def test_config_with_short_seed(self):
        """Test that short seed is rejected in production validation."""
        config = Config(seed="short")
        with pytest.raises(ValidationError, match="at least 8 characters"):
            config.validate_for_production()

    def test_config_with_invalid_company_names(self):
        """Test that invalid company_names type is rejected."""
        with pytest.raises(ConfigurationError, match="must be a list"):
            Config(company_names="not-a-list")  # type: ignore

    def test_config_with_invalid_custom_patterns(self):
        """Test that invalid custom_patterns type is rejected."""
        with pytest.raises(ConfigurationError, match="must be a list"):
            Config(custom_patterns="not-a-list")  # type: ignore

    def test_config_from_yaml_file_too_large(self, tmp_path):
        """Test that large config files are rejected."""
        config_file = tmp_path / "large.yaml"
        # Create a file larger than 1MB
        config_file.write_bytes(b"x" * (1_000_001))

        with pytest.raises(FileOperationError, match="too large"):
            Config.from_yaml(config_file)

    def test_config_from_yaml_invalid_dict(self, tmp_path):
        """Test that non-dict YAML is rejected."""
        config_file = tmp_path / "invalid.yaml"
        config_file.write_text("- item1\n- item2\n")

        with pytest.raises(ConfigurationError, match="must contain a YAML dictionary"):
            Config.from_yaml(config_file)


@pytest.fixture
def tmp_path(tmp_path_factory):
    """Create a temporary directory."""
    return tmp_path_factory.mktemp("security_test")
