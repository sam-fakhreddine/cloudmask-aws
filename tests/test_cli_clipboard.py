"""CLI clipboard tests for CloudMask."""

from unittest.mock import patch

import pytest

from cloudmask import CloudMask
from cloudmask.cli.cli import main
from cloudmask.utils.security import save_encrypted_mapping


class TestCLIClipboard:
    """Test CLI clipboard functionality."""

    @patch("cloudmask.cli.cli_handlers.CLIPBOARD_AVAILABLE", True)
    @patch("cloudmask.cli.cli_handlers.pyperclip")
    def test_anonymize_clipboard(self, mock_pyperclip, tmp_path):
        """Test anonymizing clipboard content."""
        mapping_file = tmp_path / "mapping.json"
        mock_pyperclip.paste.return_value = "vpc-123 i-456"

        with patch(
            "sys.argv",
            ["cloudmask", "anonymize", "--clipboard", "-m", str(mapping_file), "--seed", "test"],
        ):
            result = main()

        assert result == 0
        mock_pyperclip.copy.assert_called_once()
        anonymized = mock_pyperclip.copy.call_args[0][0]
        assert "vpc-123" not in anonymized

    @patch("cloudmask.cli.cli_handlers.CLIPBOARD_AVAILABLE", True)
    @patch("cloudmask.cli.cli_handlers.pyperclip")
    def test_anonymize_clipboard_with_encryption(self, mock_pyperclip, tmp_path):
        """Test anonymizing clipboard with encrypted mapping."""
        mapping_file = tmp_path / "mapping.bin"
        mock_pyperclip.paste.return_value = "vpc-123"

        with patch(
            "sys.argv",
            [
                "cloudmask",
                "anonymize",
                "--clipboard",
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

    @patch("cloudmask.cli.cli_handlers.CLIPBOARD_AVAILABLE", True)
    @patch("cloudmask.cli.cli_handlers.pyperclip")
    def test_anonymize_clipboard_empty(self, mock_pyperclip, tmp_path, capsys):
        """Test error when clipboard is empty."""
        mock_pyperclip.paste.return_value = "   "

        with patch(
            "sys.argv",
            [
                "cloudmask",
                "anonymize",
                "--clipboard",
                "-m",
                str(tmp_path / "mapping.json"),
                "--seed",
                "test",
            ],
        ):
            result = main()

        assert result == 1
        captured = capsys.readouterr()
        assert "empty" in captured.err.lower()

    @patch("cloudmask.cli.cli_handlers.CLIPBOARD_AVAILABLE", True)
    @patch("cloudmask.cli.cli_handlers.pyperclip")
    def test_anonymize_clipboard_read_error(self, mock_pyperclip, tmp_path, capsys):
        """Test error when clipboard read fails."""
        mock_pyperclip.paste.side_effect = Exception("Clipboard error")

        with patch(
            "sys.argv",
            [
                "cloudmask",
                "anonymize",
                "--clipboard",
                "-m",
                str(tmp_path / "mapping.json"),
                "--seed",
                "test",
            ],
        ):
            result = main()

        assert result == 1
        captured = capsys.readouterr()
        assert "clipboard" in captured.err.lower()

    @patch("cloudmask.cli.cli_handlers.CLIPBOARD_AVAILABLE", True)
    @patch("cloudmask.cli.cli_handlers.pyperclip")
    def test_anonymize_clipboard_write_error(self, mock_pyperclip, tmp_path, capsys):
        """Test error when clipboard write fails."""
        mock_pyperclip.paste.return_value = "vpc-123"
        mock_pyperclip.copy.side_effect = Exception("Clipboard error")

        with patch(
            "sys.argv",
            [
                "cloudmask",
                "anonymize",
                "--clipboard",
                "-m",
                str(tmp_path / "mapping.json"),
                "--seed",
                "test",
            ],
        ):
            result = main()

        assert result == 1
        captured = capsys.readouterr()
        assert "clipboard" in captured.err.lower()

    @patch("cloudmask.cli.cli_handlers.CLIPBOARD_AVAILABLE", False)
    def test_anonymize_clipboard_not_available(self, capsys):
        """Test error when clipboard not available."""
        with patch(
            "sys.argv",
            ["cloudmask", "anonymize", "--clipboard", "-m", "mapping.json", "--seed", "test"],
        ):
            result = main()

        assert result == 1
        captured = capsys.readouterr()
        assert "pyperclip" in captured.err.lower()

    def test_anonymize_clipboard_with_input_conflict(self, tmp_path, capsys):
        """Test error when clipboard used with input file."""
        with patch(
            "sys.argv",
            [
                "cloudmask",
                "anonymize",
                "--clipboard",
                "-i",
                str(tmp_path / "input.txt"),
                "-m",
                "mapping.json",
                "--seed",
                "test",
            ],
        ):
            result = main()

        assert result == 1
        captured = capsys.readouterr()
        assert "cannot be used" in captured.err.lower()

    @patch("cloudmask.cli.cli_handlers.CLIPBOARD_AVAILABLE", True)
    @patch("cloudmask.cli.cli_handlers.pyperclip")
    def test_unanonymize_clipboard(self, mock_pyperclip, tmp_path):
        """Test unanonymizing clipboard content."""
        mapping_file = tmp_path / "mapping.json"

        # Create mapping
        mask = CloudMask(seed="test")
        original = "vpc-123"
        anonymized = mask.anonymize(original)
        mask.save_mapping(mapping_file)

        mock_pyperclip.paste.return_value = anonymized

        with patch(
            "sys.argv", ["cloudmask", "unanonymize", "--clipboard", "-m", str(mapping_file)]
        ):
            result = main()

        assert result == 0
        mock_pyperclip.copy.assert_called_once()
        unanonymized = mock_pyperclip.copy.call_args[0][0]
        assert unanonymized == original

    @patch("cloudmask.cli.cli_handlers.CLIPBOARD_AVAILABLE", True)
    @patch("cloudmask.cli.cli_handlers.pyperclip")
    def test_unanonymize_clipboard_with_encryption(self, mock_pyperclip, tmp_path):
        """Test unanonymizing clipboard with encrypted mapping."""
        mapping_file = tmp_path / "mapping.bin"

        mask = CloudMask(seed="test")
        original = "vpc-123"
        anonymized = mask.anonymize(original)
        save_encrypted_mapping(mask.mapping, mapping_file, "test-password-123")

        mock_pyperclip.paste.return_value = anonymized

        with patch(
            "sys.argv",
            [
                "cloudmask",
                "unanonymize",
                "--clipboard",
                "-m",
                str(mapping_file),
                "--encrypted",
                "--password",
                "test-password-123",
            ],
        ):
            result = main()

        assert result == 0
        unanonymized = mock_pyperclip.copy.call_args[0][0]
        assert unanonymized == original

    @patch("cloudmask.cli.cli_handlers.CLIPBOARD_AVAILABLE", True)
    @patch("cloudmask.cli.cli_handlers.pyperclip")
    def test_unanonymize_clipboard_empty(self, mock_pyperclip, tmp_path, capsys):
        """Test error when clipboard is empty for unanonymize."""
        mapping_file = tmp_path / "mapping.json"
        mapping_file.write_text('{"vpc-123": "vpc-abc"}')

        mock_pyperclip.paste.return_value = ""

        with patch(
            "sys.argv", ["cloudmask", "unanonymize", "--clipboard", "-m", str(mapping_file)]
        ):
            result = main()

        assert result == 1
        captured = capsys.readouterr()
        assert "empty" in captured.err.lower()

    @patch("cloudmask.cli.cli_handlers.CLIPBOARD_AVAILABLE", False)
    def test_unanonymize_clipboard_not_available(self, capsys):
        """Test error when clipboard not available for unanonymize."""
        with patch("sys.argv", ["cloudmask", "unanonymize", "--clipboard", "-m", "mapping.json"]):
            result = main()

        assert result == 1
        captured = capsys.readouterr()
        assert "pyperclip" in captured.err.lower()

    def test_unanonymize_clipboard_with_input_conflict(self, tmp_path, capsys):
        """Test error when clipboard used with input file for unanonymize."""
        with patch(
            "sys.argv",
            [
                "cloudmask",
                "unanonymize",
                "--clipboard",
                "-i",
                str(tmp_path / "input.txt"),
                "-m",
                "mapping.json",
            ],
        ):
            result = main()

        assert result == 1
        captured = capsys.readouterr()
        assert "cannot be used" in captured.err.lower()


@pytest.fixture
def tmp_path(tmp_path_factory):
    """Create a temporary directory."""
    return tmp_path_factory.mktemp("cli_clipboard_test")
