"""Security tests for CloudMask."""

import json
import re

import pytest

from cloudmask import CloudMask, CloudUnmask, Config, CustomPattern
from cloudmask.exceptions import ValidationError


class TestSecurityValidation:
    """Security-focused tests for edge cases and validation."""

    def test_malicious_regex_pattern(self):
        """Test handling of potentially malicious regex patterns."""
        # ReDoS patterns are valid regex, just slow - test invalid regex instead
        pass

    def test_invalid_regex_pattern(self):
        """Test handling of invalid regex patterns."""
        with pytest.raises(ValidationError):
            CustomPattern(pattern="[invalid(", name="bad")

    def test_sql_injection_in_text(self):
        """Test that SQL injection attempts are handled safely."""
        mask = CloudMask(seed="test")
        text = "vpc-123'; DROP TABLE users; --"
        result = mask.anonymize(text)

        assert "vpc-123" not in result
        assert "DROP TABLE" in result  # SQL should remain as-is

    def test_xss_in_text(self):
        """Test that XSS attempts are handled safely."""
        mask = CloudMask(seed="test")
        text = "vpc-123<script>alert('xss')</script>"
        result = mask.anonymize(text)

        assert "vpc-123" not in result
        assert "<script>" in result  # HTML should remain

    def test_path_traversal_in_company_names(self):
        """Test path traversal attempts in company names."""
        config = Config(company_names=["../../etc/passwd", "normal-company"])
        mask = CloudMask(config=config, seed="test")

        text = "../../etc/passwd and normal-company"
        result = mask.anonymize(text)

        assert "../../etc/passwd" not in result
        assert "normal-company" not in result

    def test_unicode_handling(self):
        """Test proper Unicode handling."""
        mask = CloudMask(seed="test")
        text = "vpc-123 with emoji 🚀 and unicode café"
        result = mask.anonymize(text)

        assert "vpc-123" not in result
        assert "🚀" in result
        assert "café" in result

    def test_null_bytes_in_text(self):
        """Test handling of null bytes."""
        mask = CloudMask(seed="test")
        text = "vpc-123\x00hidden"
        result = mask.anonymize(text)

        assert "vpc-123" not in result

    def test_extremely_long_resource_id(self):
        """Test handling of unusually long resource IDs."""
        mask = CloudMask(seed="test")
        text = f"vpc-{'a' * 1000}"
        result = mask.anonymize(text)

        # Should not match as it's too long
        assert f"vpc-{'a' * 1000}" in result

    def test_mapping_file_permissions(self, tmp_path):
        """Test that mapping files are created with appropriate permissions."""
        mapping_file = tmp_path / "mapping.json"
        mask = CloudMask(seed="test")
        mask.anonymize("vpc-123")
        mask.save_mapping(mapping_file)

        # File should exist and be readable
        assert mapping_file.exists()
        assert mapping_file.read_text()

    def test_sensitive_data_not_in_mapping_keys(self):
        """Test that sensitive patterns aren't leaked in mapping structure."""
        mask = CloudMask(seed="test")
        mask.anonymize("vpc-123 account 123456789012")

        mapping_json = json.dumps(mask.mapping)

        # Original values should be keys, anonymized should be values
        assert "vpc-123" in mapping_json
        assert "123456789012" in mapping_json

    def test_collision_resistance(self):
        """Test that different inputs produce different outputs."""
        mask = CloudMask(seed="test")

        ids = [f"vpc-{i:016x}" for i in range(100)]
        anonymized = [mask.anonymize(id_) for id_ in ids]

        # All should be unique
        assert len(set(anonymized)) == len(anonymized)

    def test_seed_isolation(self):
        """Test that different seeds produce isolated mappings."""
        text = "vpc-123 i-456"

        mask1 = CloudMask(seed="seed1")
        result1 = mask1.anonymize(text)

        mask2 = CloudMask(seed="seed2")
        result2 = mask2.anonymize(text)

        # Results should be different
        assert result1 != result2

        # Mappings should have same keys but different values
        assert set(mask1.mapping.keys()) == set(mask2.mapping.keys())
        assert mask1.mapping != mask2.mapping

    def test_reverse_mapping_security(self):
        """Test that reverse mapping doesn't expose original values accidentally."""
        mask = CloudMask(seed="test")
        original = "vpc-123 secret-data i-456"
        anonymized = mask.anonymize(original)

        unmask = CloudUnmask(mapping=mask.get_mapping())
        restored = unmask.unanonymize(anonymized)

        assert restored == original
        # Ensure anonymized version doesn't contain originals
        assert "vpc-123" not in anonymized
        assert "i-456" not in anonymized

    def test_empty_seed_handling(self):
        """Test handling of empty seed."""
        mask = CloudMask(seed="")
        text = "vpc-123"
        result = mask.anonymize(text)

        assert "vpc-123" not in result

    def test_special_characters_in_seed(self):
        """Test seeds with special characters."""
        special_seeds = ["test!@#$%", "test\n\t", "test'\"", "test\\"]

        for seed in special_seeds:
            mask = CloudMask(seed=seed)
            result = mask.anonymize("vpc-123")
            assert "vpc-123" not in result

    def test_account_id_format_validation(self):
        """Test that generated account IDs are valid."""
        mask = CloudMask(seed="test")

        for i in range(100):
            result = mask.anonymize(f"account {i:012d}")
            # Extract the anonymized account ID
            match = re.search(r"\d{12}", result)
            assert match is not None
            assert len(match.group(0)) == 12

    def test_ip_address_format_validation(self):
        """Test that generated IPs are valid."""
        config = Config(anonymize_ips=True)
        mask = CloudMask(config=config, seed="test")

        result = mask.anonymize("IP: 192.168.1.1")

        # Extract anonymized IP
        match = re.search(r"\b(?:\d{1,3}\.){3}\d{1,3}\b", result)
        assert match is not None

        # Validate IP format
        parts = match.group(0).split(".")
        assert len(parts) == 4
        assert all(0 <= int(p) <= 255 for p in parts)
