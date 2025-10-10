"""Test suite for CloudMask."""

import os
import re
from pathlib import Path
from unittest.mock import patch

import pytest

from cloudmask import CloudMask, CloudUnmask, Config, CustomPattern, anonymize, unanonymize
from cloudmask.cli.cli import main


class TestConfig:
    """Test configuration management."""

    def test_default_config(self):
        config = Config()
        assert config.preserve_prefixes is True
        assert config.anonymize_ips is True
        assert len(config.company_names) > 0

    def test_load_save_config(self, tmp_path):
        config = Config(seed="test-seed", company_names=["Test Corp"])

        config_file = tmp_path / "config.yaml"
        config.to_yaml(config_file)

        loaded_config = Config.from_yaml(config_file)
        assert loaded_config.seed == "test-seed"
        assert loaded_config.company_names == ["Test Corp"]


class TestCloudMask:
    """Test CloudMask anonymization."""

    def test_anonymize_vpc_id(self):
        mask = CloudMask(seed="test-seed")
        text = "VPC: vpc-1234567890abcdef"
        result = mask.anonymize(text)

        assert "vpc-1234567890abcdef" not in result
        assert "vpc-" in result  # Prefix preserved
        assert len(mask.mapping) == 1

    def test_anonymize_instance_id(self):
        mask = CloudMask(seed="test-seed")
        text = "Instance i-0123456789abcdef running"
        result = mask.anonymize(text)

        assert "i-0123456789abcdef" not in result
        assert "i-" in result

    def test_anonymize_account_id(self):
        mask = CloudMask(seed="test-seed")
        text = "Account: 123456789012"
        result = mask.anonymize(text)

        assert "123456789012" not in result
        assert result.count("Account: ") == 1
        # Should be a 12-digit number
        match = re.search(r"Account: (\d{12})", result)
        assert match is not None

    def test_anonymize_arn(self):
        mask = CloudMask(seed="test-seed")
        text = "arn:aws:ec2:us-east-1:123456789012:instance/i-1234567890abcdef"
        result = mask.anonymize(text)

        assert "arn:aws:ec2:us-east-1:123456789012:instance/i-1234567890abcdef" not in result
        assert "arn:aws:" in result

    def test_anonymize_ip_address(self):
        mask = CloudMask(seed="test-seed")
        text = "IP: 192.168.1.100"
        result = mask.anonymize(text)

        assert "192.168.1.100" not in result

    def test_anonymize_company_name(self):
        config = Config(company_names=["Acme Corp", "Example Inc"])
        mask = CloudMask(config=config, seed="test-seed")

        text = "Acme Corp uses Example Inc services"
        result = mask.anonymize(text)

        assert "Acme Corp" not in result
        assert "Example Inc" not in result
        assert "Company-" in result

    def test_deterministic_anonymization(self):
        """Same seed should produce same results."""
        text = "vpc-123 in account 123456789012"

        mask1 = CloudMask(seed="same-seed")
        result1 = mask1.anonymize(text)

        mask2 = CloudMask(seed="same-seed")
        result2 = mask2.anonymize(text)

        assert result1 == result2

    def test_different_seeds_different_results(self):
        """Different seeds should produce different results."""
        text = "vpc-123 in account 123456789012"

        mask1 = CloudMask(seed="seed1")
        result1 = mask1.anonymize(text)

        mask2 = CloudMask(seed="seed2")
        result2 = mask2.anonymize(text)

        assert result1 != result2

    def test_preserve_structure(self):
        """Anonymization should preserve text structure."""
        mask = CloudMask(seed="test-seed")
        text = "Instance i-123 in vpc-abc\nAccount: 123456789012"
        result = mask.anonymize(text)

        # Should preserve newlines and basic structure
        assert result.count("\n") == text.count("\n")
        assert "Instance" in result
        assert "in" in result
        assert "Account:" in result

    def test_anonymize_file(self, tmp_path):
        """Test file anonymization."""
        input_file = tmp_path / "input.txt"
        output_file = tmp_path / "output.txt"

        input_file.write_text("Instance i-123 in vpc-abc")

        mask = CloudMask(seed="test-seed")
        count = mask.anonymize_file(input_file, output_file)

        assert output_file.exists()
        assert count == 2
        assert "i-123" not in output_file.read_text()

    def test_save_load_mapping(self, tmp_path):
        """Test mapping persistence."""
        mapping_file = tmp_path / "mapping.json"

        mask = CloudMask(seed="test-seed")
        mask.anonymize("vpc-123 i-456")
        mask.save_mapping(mapping_file)

        # Load into new instance with same seed
        new_mask = CloudMask(seed="test-seed")
        new_mask.load_mapping(mapping_file)

        assert new_mask.mapping == mask.mapping


class TestCloudUnmask:
    """Test CloudUnmask functionality."""

    def test_unanonymize(self):
        """Test basic unanonymization."""
        mask = CloudMask(seed="test-seed")
        original = "Instance i-123 in vpc-456"
        anonymized = mask.anonymize(original)

        unmask = CloudUnmask(mapping=mask.get_mapping())
        restored = unmask.unanonymize(anonymized)

        assert restored == original

    def test_unanonymize_from_file(self, tmp_path):
        """Test loading mapping from file."""
        mapping_file = tmp_path / "mapping.json"

        mask = CloudMask(seed="test-seed")
        original = "vpc-123 in account 123456789012"
        anonymized = mask.anonymize(original)
        mask.save_mapping(mapping_file)

        unmask = CloudUnmask(mapping_file=mapping_file)
        restored = unmask.unanonymize(anonymized)

        assert restored == original

    def test_unanonymize_file(self, tmp_path):
        """Test file unanonymization."""
        anon_file = tmp_path / "anonymized.txt"
        output_file = tmp_path / "restored.txt"

        original = "Instance i-123 in vpc-456"

        mask = CloudMask(seed="test-seed")
        anonymized = mask.anonymize(original)
        anon_file.write_text(anonymized)

        unmask = CloudUnmask(mapping=mask.get_mapping())
        count = unmask.unanonymize_file(anon_file, output_file)

        assert output_file.read_text() == original
        assert count == 2


class TestConvenienceFunctions:
    """Test quick anonymize/unanonymize functions."""

    def test_quick_anonymize(self):
        """Test convenience anonymize function."""
        text = "Instance i-123"
        result, mapping = anonymize(text, seed="test-seed")

        assert "i-123" not in result
        assert "i-123" in mapping
        assert isinstance(mapping, dict)

    def test_quick_unanonymize(self):
        """Test convenience unanonymize function."""
        original = "Instance i-123"
        anonymized, mapping = anonymize(original, seed="test-seed")
        restored = unanonymize(anonymized, mapping)

        assert restored == original

    def test_quick_with_options(self):
        """Test quick function with config options."""
        text = "Acme Corp instance i-123"
        result, _mapping = anonymize(
            text, seed="test-seed", company_names=["Acme Corp"], anonymize_ips=False
        )

        assert "Acme Corp" not in result
        assert "i-123" not in result


class TestCustomPatterns:
    """Test custom pattern anonymization."""

    def test_custom_pattern(self):
        """Test custom regex pattern anonymization."""
        pattern = CustomPattern(pattern=r"\bTICKET-\d+\b", name="ticket")
        config = Config(custom_patterns=[pattern])

        mask = CloudMask(config=config, seed="test-seed")
        text = "See TICKET-12345 for details"
        result = mask.anonymize(text)

        assert "TICKET-12345" not in result
        assert "ticket-" in result.lower()


class TestEdgeCases:
    """Test edge cases and error handling."""

    def test_empty_text(self):
        """Test anonymizing empty text."""
        mask = CloudMask(seed="test-seed")
        result = mask.anonymize("")
        assert result == ""

    def test_no_matches(self):
        """Test text with no AWS identifiers."""
        mask = CloudMask(seed="test-seed")
        text = "Hello world, this is plain text."
        result = mask.anonymize(text)
        assert result == text

    def test_multiple_same_ids(self):
        """Test same ID appearing multiple times."""
        mask = CloudMask(seed="test-seed")
        text = "vpc-123 and vpc-123 again"
        result = mask.anonymize(text)

        # Should map to same anonymized value
        parts = result.split(" and ")
        assert parts[0] == parts[1].replace(" again", "")

    def test_case_insensitive_company_names(self):
        """Test case-insensitive company name matching."""
        config = Config(company_names=["Acme Corp"])
        mask = CloudMask(config=config, seed="test-seed")

        text = "ACME CORP and acme corp and Acme Corp"
        result = mask.anonymize(text)

        assert "ACME CORP" not in result
        assert "acme corp" not in result
        assert "Acme Corp" not in result


class TestCLIClipboard:
    """Test CLI clipboard functionality."""

    @patch("cloudmask.cli.cli_handlers.pyperclip")
    @patch("cloudmask.cli.cli_handlers.CLIPBOARD_AVAILABLE", True)
    @patch("sys.argv", ["cloudmask", "anonymize", "--clipboard", "-m", "mapping.json"])
    def test_anonymize_clipboard(self, mock_pyperclip, tmp_path):
        """Test clipboard anonymization."""
        mock_pyperclip.paste.return_value = "Instance i-123 in vpc-456"

        # Change to temp directory for mapping file
        old_cwd = Path.cwd()
        os.chdir(tmp_path)

        try:
            result = main()
            assert result == 0
            mock_pyperclip.copy.assert_called_once()
            # Verify anonymized content was copied
            copied_text = mock_pyperclip.copy.call_args[0][0]
            assert "i-123" not in copied_text
            assert "vpc-456" not in copied_text
        finally:
            os.chdir(old_cwd)

    @patch("cloudmask.cli.cli_handlers.pyperclip")
    @patch("cloudmask.cli.cli_handlers.CLIPBOARD_AVAILABLE", True)
    @patch("sys.argv", ["cloudmask", "unanonymize", "--clipboard", "-m", "mapping.json"])
    def test_unanonymize_clipboard(self, mock_pyperclip, tmp_path):
        """Test clipboard unanonymization."""
        # First create a mapping
        mapping_file = tmp_path / "mapping.json"
        mask = CloudMask(seed="test-seed")
        original = "Instance i-123 in vpc-456"
        anonymized = mask.anonymize(original)
        mask.save_mapping(mapping_file)

        mock_pyperclip.paste.return_value = anonymized

        old_cwd = Path.cwd()
        os.chdir(tmp_path)

        try:
            result = main()
            assert result == 0
            mock_pyperclip.copy.assert_called_once()
            # Verify original content was restored
            copied_text = mock_pyperclip.copy.call_args[0][0]
            assert copied_text == original
        finally:
            os.chdir(old_cwd)


@pytest.fixture
def tmp_path(tmp_path_factory):
    """Create a temporary directory."""
    return tmp_path_factory.mktemp("cloudmask_test")
