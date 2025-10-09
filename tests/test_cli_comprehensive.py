"""Comprehensive CLI tests for CloudMask."""

import json
from unittest.mock import patch

import pytest

from cloudmask import CloudMask
from cloudmask.cli import main
from cloudmask.security import save_encrypted_mapping


class TestCLICommands:
    """Test all CLI commands comprehensively."""

    def test_no_command_shows_help(self, capsys):
        """Test that running without command shows help."""
        with patch("sys.argv", ["cloudmask"]):
            result = main()

        assert result == 0
        captured = capsys.readouterr()
        assert "usage:" in captured.out.lower()

    def test_init_config_list_templates(self, capsys):
        """Test listing available templates."""
        with patch("sys.argv", ["cloudmask", "init-config", "--list-templates"]):
            result = main()

        assert result == 0
        captured = capsys.readouterr()
        assert "Available templates:" in captured.out

    def test_init_config_with_template(self, tmp_path):
        """Test creating config with specific template."""
        config_file = tmp_path / "config.yaml"

        with patch(
            "sys.argv", ["cloudmask", "init-config", "-c", str(config_file), "-t", "minimal"]
        ):
            result = main()

        assert result == 0
        assert config_file.exists()

    def test_anonymize_with_streaming(self, tmp_path):
        """Test anonymize with streaming mode."""
        input_file = tmp_path / "input.txt"
        output_file = tmp_path / "output.txt"
        mapping_file = tmp_path / "mapping.json"

        input_file.write_text("vpc-123 i-456")

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
                "--stream",
                "--seed",
                "test",
            ],
        ):
            result = main()

        assert result == 0
        assert output_file.exists()
        assert mapping_file.exists()

    def test_anonymize_with_encryption(self, tmp_path):
        """Test anonymize with encrypted mapping."""
        input_file = tmp_path / "input.txt"
        output_file = tmp_path / "output.txt"
        mapping_file = tmp_path / "mapping.bin"

        input_file.write_text("vpc-123")

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
                "--encrypt",
                "--password",
                "test-password-123",
                "--seed",
                "test",
            ],
        ):
            result = main()

        assert result == 0
        assert mapping_file.exists()

    def test_anonymize_missing_input_output(self, capsys):
        """Test error when input/output missing."""
        with patch("sys.argv", ["cloudmask", "anonymize"]):
            result = main()

        assert result == 1
        captured = capsys.readouterr()
        assert "required" in captured.err.lower()

    def test_unanonymize_with_streaming(self, tmp_path):
        """Test unanonymize with streaming mode."""
        input_file = tmp_path / "input.txt"
        output_file = tmp_path / "output.txt"
        mapping_file = tmp_path / "mapping.json"

        # Create anonymized content
        mask = CloudMask(seed="test")
        original = "vpc-123 i-456"
        anonymized = mask.anonymize(original)
        input_file.write_text(anonymized)
        mask.save_mapping(mapping_file)

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
                str(mapping_file),
                "--stream",
            ],
        ):
            result = main()

        assert result == 0
        assert output_file.read_text() == original

    def test_unanonymize_with_encrypted_mapping(self, tmp_path):
        """Test unanonymize with encrypted mapping."""
        input_file = tmp_path / "input.txt"
        output_file = tmp_path / "output.txt"
        mapping_file = tmp_path / "mapping.bin"

        mask = CloudMask(seed="test")
        original = "vpc-123"
        anonymized = mask.anonymize(original)
        input_file.write_text(anonymized)

        save_encrypted_mapping(mask.mapping, mapping_file, "test-password-123")

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
                str(mapping_file),
                "--encrypted",
                "--password",
                "test-password-123",
            ],
        ):
            result = main()

        assert result == 0
        assert output_file.read_text() == original

    def test_validate_config(self, tmp_path):
        """Test validate command with config."""
        config_file = tmp_path / "config.yaml"
        config_file.write_text("seed: test-seed\ncompany_names:\n  - Test Corp\n")

        with patch("sys.argv", ["cloudmask", "validate", "-c", str(config_file)]):
            result = main()

        assert result == 0

    def test_validate_mapping(self, tmp_path):
        """Test validate command with mapping."""
        mapping_file = tmp_path / "mapping.json"
        mapping_file.write_text('{"vpc-123": "vpc-abc"}')

        with patch("sys.argv", ["cloudmask", "validate", "-m", str(mapping_file)]):
            result = main()

        assert result == 0

    def test_validate_encrypted_mapping(self, tmp_path):
        """Test validate command with encrypted mapping."""
        mapping_file = tmp_path / "mapping.bin"
        mapping = {"vpc-123": "vpc-abc"}
        save_encrypted_mapping(mapping, mapping_file, "test-password-123")

        with patch(
            "sys.argv",
            [
                "cloudmask",
                "validate",
                "-m",
                str(mapping_file),
                "--encrypted",
                "--password",
                "test-password-123",
            ],
        ):
            result = main()

        assert result == 0

    def test_validate_no_args(self, capsys):
        """Test validate without arguments."""
        with patch("sys.argv", ["cloudmask", "validate"]):
            result = main()

        assert result == 1
        captured = capsys.readouterr()
        assert "must be specified" in captured.err.lower()

    def test_batch_processing(self, tmp_path):
        """Test batch command."""
        file1 = tmp_path / "file1.txt"
        file2 = tmp_path / "file2.txt"
        output_dir = tmp_path / "output"
        mapping_file = tmp_path / "mapping.json"

        file1.write_text("vpc-111")
        file2.write_text("vpc-222")

        with patch(
            "sys.argv",
            [
                "cloudmask",
                "batch",
                str(file1),
                str(file2),
                "-o",
                str(output_dir),
                "-m",
                str(mapping_file),
                "--seed",
                "test",
            ],
        ):
            result = main()

        assert result == 0
        assert (output_dir / "file1.txt").exists()
        assert (output_dir / "file2.txt").exists()
        assert mapping_file.exists()

    def test_batch_with_encryption(self, tmp_path):
        """Test batch with encrypted mapping."""
        file1 = tmp_path / "file1.txt"
        output_dir = tmp_path / "output"
        mapping_file = tmp_path / "mapping.bin"

        file1.write_text("vpc-123")

        with patch(
            "sys.argv",
            [
                "cloudmask",
                "batch",
                str(file1),
                "-o",
                str(output_dir),
                "-m",
                str(mapping_file),
                "--encrypt",
                "--password",
                "test-password-123",
                "--seed",
                "test",
            ],
        ):
            result = main()

        assert result == 0
        assert mapping_file.exists()

    def test_stats_command(self, tmp_path):
        """Test stats command."""
        mapping_file = tmp_path / "mapping.json"
        mapping = {
            "vpc-123": "vpc-abc",
            "i-456": "i-def",
            "192.168.1.1": "10.0.0.1",
            "123456789012": "987654321098",
        }
        mapping_file.write_text(json.dumps(mapping))

        with patch("sys.argv", ["cloudmask", "stats", "-m", str(mapping_file)]):
            result = main()

        assert result == 0

    def test_stats_with_detailed(self, tmp_path, capsys):
        """Test stats with detailed output."""
        mapping_file = tmp_path / "mapping.json"
        mapping = {"vpc-123": "vpc-abc"}
        mapping_file.write_text(json.dumps(mapping))

        with patch("sys.argv", ["cloudmask", "stats", "-m", str(mapping_file), "--detailed"]):
            result = main()

        assert result == 0
        captured = capsys.readouterr()
        assert "Sample mappings" in captured.out

    def test_stats_with_encrypted_mapping(self, tmp_path):
        """Test stats with encrypted mapping."""
        mapping_file = tmp_path / "mapping.bin"
        mapping = {"vpc-123": "vpc-abc"}
        save_encrypted_mapping(mapping, mapping_file, "test-password-123")

        with patch(
            "sys.argv",
            [
                "cloudmask",
                "stats",
                "-m",
                str(mapping_file),
                "--encrypted",
                "--password",
                "test-password-123",
            ],
        ):
            result = main()

        assert result == 0

    def test_debug_mode(self, tmp_path):
        """Test debug mode."""
        input_file = tmp_path / "input.txt"
        output_file = tmp_path / "output.txt"
        mapping_file = tmp_path / "mapping.json"

        input_file.write_text("vpc-123")

        with patch(
            "sys.argv",
            [
                "cloudmask",
                "--debug",
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

    def test_quiet_mode(self, tmp_path, capsys):
        """Test quiet mode."""
        input_file = tmp_path / "input.txt"
        output_file = tmp_path / "output.txt"
        mapping_file = tmp_path / "mapping.json"

        input_file.write_text("vpc-123")

        with patch(
            "sys.argv",
            [
                "cloudmask",
                "-q",
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
        captured = capsys.readouterr()
        assert captured.out == ""

    def test_verbose_mode(self, tmp_path):
        """Test verbose mode."""
        input_file = tmp_path / "input.txt"
        output_file = tmp_path / "output.txt"
        mapping_file = tmp_path / "mapping.json"

        input_file.write_text("vpc-123")

        with patch(
            "sys.argv",
            [
                "cloudmask",
                "-v",
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

    def test_keyboard_interrupt(self, tmp_path, capsys):
        """Test handling of keyboard interrupt."""
        input_file = tmp_path / "input.txt"
        output_file = tmp_path / "output.txt"

        input_file.write_text("vpc-123")

        with (
            patch("cloudmask.core.CloudMask.anonymize_file", side_effect=KeyboardInterrupt),
            patch(
                "sys.argv",
                [
                    "cloudmask",
                    "anonymize",
                    "-i",
                    str(input_file),
                    "-o",
                    str(output_file),
                    "-m",
                    str(tmp_path / "mapping.json"),
                    "--seed",
                    "test",
                ],
            ),
        ):
            result = main()

        assert result == 130
        captured = capsys.readouterr()
        assert "cancelled" in captured.err.lower()

    def test_anonymize_with_config_file(self, tmp_path):
        """Test anonymize with config file."""
        input_file = tmp_path / "input.txt"
        output_file = tmp_path / "output.txt"
        mapping_file = tmp_path / "mapping.json"
        config_file = tmp_path / "config.yaml"

        input_file.write_text("Test Corp vpc-123")
        config_file.write_text("seed: test-seed\ncompany_names:\n  - Test Corp\n")

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
        assert "Test Corp" not in output_text

    def test_anonymize_with_no_env(self, tmp_path):
        """Test anonymize with --no-env flag."""
        input_file = tmp_path / "input.txt"
        output_file = tmp_path / "output.txt"
        mapping_file = tmp_path / "mapping.json"

        input_file.write_text("vpc-123")

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
                "--no-env",
                "--seed",
                "test",
            ],
        ):
            result = main()

        assert result == 0

    def test_batch_with_failed_file(self, tmp_path):
        """Test batch processing with one failed file."""
        file1 = tmp_path / "file1.txt"
        file2 = tmp_path / "nonexistent.txt"
        output_dir = tmp_path / "output"

        file1.write_text("vpc-123")

        with patch(
            "sys.argv",
            ["cloudmask", "batch", str(file1), str(file2), "-o", str(output_dir), "--seed", "test"],
        ):
            result = main()

        assert result == 1


@pytest.fixture
def tmp_path(tmp_path_factory):
    """Create a temporary directory."""
    return tmp_path_factory.mktemp("cli_test")
