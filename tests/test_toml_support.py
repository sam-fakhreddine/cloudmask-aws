"""Tests for TOML configuration support."""

import sys

import pytest

from cloudmask.config.config_loader import load_config, load_from_toml
from cloudmask.exceptions import ConfigurationError


class TestTOMLSupport:
    """Test TOML configuration loading."""

    def test_load_from_toml_basic(self, tmp_path):
        """Test loading basic TOML config."""
        if sys.version_info < (3, 11):
            pytest.skip("TOML support requires Python 3.11+")

        config_file = tmp_path / "config.toml"
        config_file.write_text(
            """
seed = "toml-test-seed"
preserve_prefixes = true
anonymize_ips = false
company_names = ["Company A", "Company B"]
"""
        )

        config = load_config(config_file, format="toml", use_env=False)
        assert config.seed == "toml-test-seed"
        assert config.preserve_prefixes is True
        assert config.anonymize_ips is False
        assert len(config.company_names) == 2

    def test_load_from_toml_with_section(self, tmp_path):
        """Test loading TOML with [cloudmask] section."""
        if sys.version_info < (3, 11):
            pytest.skip("TOML support requires Python 3.11+")

        config_file = tmp_path / "config.toml"
        config_file.write_text(
            """
[cloudmask]
seed = "section-seed"
preserve_prefixes = false

[other_section]
ignored = "value"
"""
        )

        data = load_from_toml(config_file)
        assert data["seed"] == "section-seed"
        assert "ignored" not in data

    def test_load_from_toml_invalid(self, tmp_path):
        """Test loading invalid TOML."""
        if sys.version_info < (3, 11):
            pytest.skip("TOML support requires Python 3.11+")

        config_file = tmp_path / "config.toml"
        config_file.write_text("invalid toml [[[")

        with pytest.raises(ConfigurationError, match="Invalid TOML"):
            load_from_toml(config_file)

    def test_load_toml_auto_detect(self, tmp_path):
        """Test auto-detecting TOML format."""
        if sys.version_info < (3, 11):
            pytest.skip("TOML support requires Python 3.11+")

        config_file = tmp_path / "config.toml"
        config_file.write_text('seed = "auto-detect-seed"\n')

        config = load_config(config_file, use_env=False)
        assert config.seed == "auto-detect-seed"

    def test_load_toml_with_custom_patterns(self, tmp_path):
        """Test loading TOML with custom patterns."""
        if sys.version_info < (3, 11):
            pytest.skip("TOML support requires Python 3.11+")

        config_file = tmp_path / "config.toml"
        config_file.write_text(
            """
seed = "pattern-seed"

[[custom_patterns]]
pattern = "TICKET-\\\\d+"
name = "ticket"

[[custom_patterns]]
pattern = "PROJ-[A-Z]+"
name = "project"
"""
        )

        config = load_config(config_file, use_env=False)
        assert config.seed == "pattern-seed"
        assert len(config.custom_patterns) == 2
        assert config.custom_patterns[0].name == "ticket"
        assert config.custom_patterns[1].name == "project"


class TestTOMLPython310Compatibility:
    """Test TOML support on Python 3.10."""

    def test_toml_unavailable_python310(self, tmp_path, monkeypatch):
        """Test TOML error when tomllib not available."""
        # Simulate Python 3.10 without tomli
        import cloudmask.config.config_loader as loader

        original_tomllib = getattr(loader, "tomllib", None)
        monkeypatch.setattr(loader, "tomllib", None)

        config_file = tmp_path / "config.toml"
        config_file.write_text('seed = "test"\n')

        with pytest.raises(ConfigurationError, match="TOML support requires"):
            load_from_toml(config_file)

        # Restore
        if original_tomllib is not None:
            monkeypatch.setattr(loader, "tomllib", original_tomllib)
