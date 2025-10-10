"""Tests for configuration loader."""

import json

import pytest

from cloudmask import Config
from cloudmask.config.config_loader import load_config, load_from_env, validate_config
from cloudmask.exceptions import ConfigurationError


class TestEnvironmentVariables:
    """Test environment variable loading."""

    def test_load_from_env_seed(self, monkeypatch):
        """Test loading seed from environment."""
        monkeypatch.setenv("CLOUDMASK_SEED", "env-seed")
        config = load_from_env()
        assert config["seed"] == "env-seed"

    def test_load_from_env_booleans(self, monkeypatch):
        """Test loading boolean values."""
        monkeypatch.setenv("CLOUDMASK_PRESERVE_PREFIXES", "false")
        monkeypatch.setenv("CLOUDMASK_ANONYMIZE_IPS", "true")
        config = load_from_env()
        assert config["preserve_prefixes"] is False
        assert config["anonymize_ips"] is True

    def test_load_from_env_company_names(self, monkeypatch):
        """Test loading company names."""
        monkeypatch.setenv("CLOUDMASK_COMPANY_NAMES", "Company A, Company B, Company C")
        config = load_from_env()
        assert config["company_names"] == ["Company A", "Company B", "Company C"]


class TestMultipleFormats:
    """Test loading from different file formats."""

    def test_load_from_json(self, tmp_path):
        """Test loading from JSON file."""
        config_file = tmp_path / "config.json"
        config_file.write_text(
            json.dumps(
                {"seed": "json-seed", "preserve_prefixes": False, "company_names": ["Company A"]}
            )
        )

        config = load_config(config_file, format="json", use_env=False)
        assert config.seed == "json-seed"
        assert config.preserve_prefixes is False

    def test_load_from_yaml(self, tmp_path):
        """Test loading from YAML file."""
        config_file = tmp_path / "config.yaml"
        config_file.write_text(
            """
seed: yaml-seed
preserve_prefixes: true
company_names:
  - Company A
  - Company B
"""
        )

        config = load_config(config_file, use_env=False)
        assert config.seed == "yaml-seed"
        assert len(config.company_names) == 2

    def test_auto_detect_format(self, tmp_path):
        """Test format auto-detection."""
        json_file = tmp_path / "config.json"
        json_file.write_text(json.dumps({"seed": "test"}))

        config = load_config(json_file, use_env=False)
        assert config.seed == "test"


class TestConfigValidation:
    """Test configuration validation."""

    def test_validate_valid_config(self):
        """Test validation of valid config."""
        config = Config(seed="valid-seed-123")
        issues = validate_config(config)
        assert len(issues) == 0

    def test_validate_short_seed(self):
        """Test validation catches short seed."""
        config = Config(seed="short")
        issues = validate_config(config)
        assert any("8 characters" in issue for issue in issues)

    def test_validate_empty_seed(self):
        """Test validation catches empty seed."""
        config = Config(seed="")
        issues = validate_config(config)
        assert len(issues) > 0


class TestConfigMerging:
    """Test configuration merging from multiple sources."""

    def test_env_overrides_file(self, tmp_path, monkeypatch):
        """Test environment variables override file config."""
        config_file = tmp_path / "config.yaml"
        config_file.write_text("seed: file-seed\n")

        monkeypatch.setenv("CLOUDMASK_SEED", "env-seed")

        config = load_config(config_file, use_env=True)
        assert config.seed == "env-seed"

    def test_no_env_loading(self, tmp_path, monkeypatch):
        """Test disabling environment variable loading."""
        config_file = tmp_path / "config.yaml"
        config_file.write_text("seed: file-seed\n")

        monkeypatch.setenv("CLOUDMASK_SEED", "env-seed")

        config = load_config(config_file, use_env=False)
        assert config.seed == "file-seed"


class TestErrorHandling:
    """Test error handling in config loading."""

    def test_invalid_json(self, tmp_path):
        """Test handling of invalid JSON."""
        config_file = tmp_path / "config.json"
        config_file.write_text("{invalid json}")

        with pytest.raises(ConfigurationError):
            load_config(config_file, format="json")

    def test_nonexistent_file(self, tmp_path):
        """Test handling of nonexistent file."""
        config_file = tmp_path / "nonexistent.yaml"

        with pytest.raises(ConfigurationError):
            load_config(config_file)
