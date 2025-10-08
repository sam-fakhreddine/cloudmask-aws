"""Integration tests for CloudMask CLI."""

from unittest.mock import patch

import pytest

from cloudmask import CloudMask
from cloudmask.cli import main


class TestCLIIntegration:
    """Integration tests for CLI commands."""

    def test_init_config_command(self, tmp_path):
        """Test init-config command creates config file."""
        config_file = tmp_path / "cloudmask.yaml"

        with patch("sys.argv", ["cloudmask", "init-config", "-c", str(config_file)]):
            result = main()

        assert result == 0
        assert config_file.exists()
        content = config_file.read_text()
        assert "company_names:" in content
        assert "preserve_prefixes:" in content

    def test_anonymize_file_command(self, tmp_path):
        """Test anonymize command with files."""
        input_file = tmp_path / "input.txt"
        output_file = tmp_path / "output.txt"
        mapping_file = tmp_path / "mapping.json"

        input_file.write_text("Instance i-123 in vpc-456")

        with patch(
            "sys.argv",
            [
                "cloudmask",
                "anonymize",
                "-i",
                str(input_file),
                "-o",
                str(output_file),
                "-m",
                str(mapping_file),
                "--seed",
                "test",
            ],
        ):
            result = main()

        assert result == 0
        assert output_file.exists()
        assert mapping_file.exists()
        assert "i-123" not in output_file.read_text()

    def test_unanonymize_file_command(self, tmp_path):
        """Test unanonymize command with files."""
        anon_file = tmp_path / "anon.txt"
        output_file = tmp_path / "output.txt"
        mapping_file = tmp_path / "mapping.json"

        # Create anonymized content
        mask = CloudMask(seed="test")
        original = "Instance i-123 in vpc-456"
        anonymized = mask.anonymize(original)
        anon_file.write_text(anonymized)
        mask.save_mapping(mapping_file)

        with patch(
            "sys.argv",
            [
                "cloudmask",
                "unanonymize",
                "-i",
                str(anon_file),
                "-o",
                str(output_file),
                "-m",
                str(mapping_file),
            ],
        ):
            result = main()

        assert result == 0
        assert output_file.read_text() == original

    def test_anonymize_with_config_file(self, tmp_path):
        """Test anonymize with custom config file."""
        input_file = tmp_path / "input.txt"
        output_file = tmp_path / "output.txt"
        mapping_file = tmp_path / "mapping.json"
        config_file = tmp_path / "config.yaml"

        input_file.write_text("Acme Corp instance i-123")
        config_file.write_text("company_names:\n  - Acme Corp\nseed: test-seed\n")

        with patch(
            "sys.argv",
            [
                "cloudmask",
                "anonymize",
                "-i",
                str(input_file),
                "-o",
                str(output_file),
                "-m",
                str(mapping_file),
                "-c",
                str(config_file),
            ],
        ):
            result = main()

        assert result == 0
        output_text = output_file.read_text()
        assert "Acme Corp" not in output_text
        assert "i-123" not in output_text

    def test_missing_input_file(self, tmp_path):
        """Test error handling for missing input file."""
        with patch(
            "sys.argv",
            [
                "cloudmask",
                "anonymize",
                "-i",
                str(tmp_path / "nonexistent.txt"),
                "-o",
                str(tmp_path / "output.txt"),
                "-m",
                str(tmp_path / "mapping.json"),
            ],
        ):
            result = main()

        assert result != 0

    def test_missing_mapping_file_for_unanonymize(self, tmp_path):
        """Test error handling for missing mapping file."""
        input_file = tmp_path / "input.txt"
        output_file = tmp_path / "output.txt"
        input_file.write_text("test")

        with patch(
            "sys.argv",
            [
                "cloudmask",
                "unanonymize",
                "-i",
                str(input_file),
                "-o",
                str(output_file),
                "-m",
                str(tmp_path / "nonexistent.json"),
            ],
        ):
            result = main()

        assert result != 0


@pytest.fixture
def tmp_path(tmp_path_factory):
    """Create a temporary directory."""
    return tmp_path_factory.mktemp("integration_test")
