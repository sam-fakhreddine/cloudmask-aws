"""Tests for CLI handlers to improve coverage."""

import json

from cloudmask.cli.cli_handlers import (
    check_clipboard_available,
    get_password,
    handle_batch,
    handle_init_config,
    handle_stats,
    handle_validate,
)


class TestInitConfigHandler:
    """Test init-config handler."""

    def test_list_templates(self, capsys):
        """Test listing templates."""

        class Args:
            list_templates = True
            config = None
            template = None

        result = handle_init_config(Args())
        assert result == 0

        captured = capsys.readouterr()
        assert "Available templates:" in captured.out
        assert "standard" in captured.out


class TestValidateHandler:
    """Test validate handler."""

    def test_validate_no_args(self, capsys):
        """Test validate with no arguments."""

        class Args:
            config = None
            mapping = None

        result = handle_validate(Args())
        assert result == 1

        captured = capsys.readouterr()
        assert "Either --config or --mapping must be specified" in captured.err

    def test_validate_config_with_issues(self, tmp_path, capsys):
        """Test validate with invalid config."""
        config_file = tmp_path / "config.yaml"
        config_file.write_text("seed: short\n")

        class Args:
            config = config_file
            mapping = None
            format = None

        result = handle_validate(Args())
        assert result == 1

        captured = capsys.readouterr()
        assert "issue(s)" in captured.out

    def test_validate_valid_config(self, tmp_path, capsys):
        """Test validate with valid config."""
        config_file = tmp_path / "config.yaml"
        config_file.write_text("seed: valid-seed-123\n")

        class Args:
            config = config_file
            mapping = None
            format = None

        result = handle_validate(Args())
        assert result == 0

        captured = capsys.readouterr()
        assert "Configuration is valid" in captured.out

    def test_validate_mapping(self, tmp_path, capsys):
        """Test validate mapping."""
        mapping_file = tmp_path / "mapping.json"
        mapping_file.write_text(json.dumps({"vpc-123": "vpc-abc"}))

        class Args:
            config = None
            mapping = mapping_file
            encrypted = False
            password = None

        result = handle_validate(Args())
        assert result == 0

        captured = capsys.readouterr()
        assert "Mapping is valid" in captured.out

    def test_validate_invalid_mapping(self, tmp_path, capsys):
        """Test validate with invalid mapping."""
        mapping_file = tmp_path / "mapping.json"
        mapping_file.write_text(json.dumps(["not", "a", "dict"]))

        class Args:
            config = None
            mapping = mapping_file
            encrypted = False
            password = None

        result = handle_validate(Args())
        assert result == 1

        captured = capsys.readouterr()
        assert "Invalid mapping format" in captured.err


class TestBatchHandler:
    """Test batch handler."""

    def test_batch_with_failed_file(self, tmp_path, capsys):
        """Test batch with a failed file."""
        from types import SimpleNamespace

        out_dir = tmp_path / "output"
        valid_file = tmp_path / "valid.txt"
        valid_file.write_text("vpc-123")
        invalid_file = tmp_path / "nonexistent.txt"

        args = SimpleNamespace(
            files=[valid_file, invalid_file],
            output_dir=out_dir,
            config=None,
            seed="test-seed",
            mapping=None,
            encrypt=False,
            password=None,
            progress=False,
            quiet=False,
        )

        result = handle_batch(args)
        assert result == 1  # Failed due to one file

        captured = capsys.readouterr()
        assert "Failed: 1" in captured.out

    def test_batch_quiet_mode(self, tmp_path, capsys):
        """Test batch in quiet mode."""
        from types import SimpleNamespace

        out_dir = tmp_path / "output"
        file1 = tmp_path / "file1.txt"
        file1.write_text("vpc-123")

        args = SimpleNamespace(
            files=[file1],
            output_dir=out_dir,
            config=None,
            seed="test-seed",
            mapping=None,
            encrypt=False,
            password=None,
            progress=False,
            quiet=True,
        )

        result = handle_batch(args)
        assert result == 0

        captured = capsys.readouterr()
        assert captured.out == ""  # Quiet mode


class TestStatsHandler:
    """Test stats handler."""

    def test_stats_detailed(self, tmp_path, capsys):
        """Test stats with detailed output."""
        mapping_file = tmp_path / "mapping.json"
        mapping = {
            "vpc-123": "vpc-abc",
            "i-456": "i-def",
            "192.168.1.1": "10.0.0.1",
            "123456789012": "999999999999",
            "arn:aws:s3:::bucket": "arn:aws:s3:::anon",
            "example.com": "anon.com",
        }
        mapping_file.write_text(json.dumps(mapping))

        class Args:
            mapping = mapping_file
            encrypted = False
            password = None
            detailed = True

        result = handle_stats(Args())
        assert result == 0

        captured = capsys.readouterr()
        assert "Mapping Statistics" in captured.out
        assert "AWS Resources" in captured.out
        assert "Sample mappings" in captured.out


class TestClipboardCheck:
    """Test clipboard availability check."""

    def test_check_clipboard_available(self, capsys):
        """Test clipboard availability check."""
        result = check_clipboard_available()

        # Result depends on whether pyperclip is installed
        if not result:
            captured = capsys.readouterr()
            assert "pyperclip not available" in captured.err


class TestPasswordHelper:
    """Test password helper."""

    def test_get_password_from_args(self):
        """Test getting password from args."""
        password = get_password("Enter password: ", "my-password")
        assert password == "my-password"
