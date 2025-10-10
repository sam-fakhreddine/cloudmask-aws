"""Test default config loading from ~/.cloudmask/config.yml."""

from cloudmask import get_default_config_path, load_config


def test_get_default_config_path_exists(tmp_path, monkeypatch):
    """Test that get_default_config_path returns path when config exists."""
    # Mock home directory
    monkeypatch.setenv("HOME", str(tmp_path))

    # Create config file
    config_dir = tmp_path / ".cloudmask"
    config_dir.mkdir()
    config_file = config_dir / "config.yml"
    config_file.write_text("seed: test-seed")

    # Should return the path
    result = get_default_config_path()
    assert result == config_file
    assert result.exists()


def test_get_default_config_path_not_exists(tmp_path, monkeypatch):
    """Test that get_default_config_path returns None when config doesn't exist."""
    # Mock home directory
    monkeypatch.setenv("HOME", str(tmp_path))

    # Should return None
    result = get_default_config_path()
    assert result is None


def test_load_config_from_default_location(tmp_path, monkeypatch):
    """Test that load_config can load from default location."""
    # Mock home directory
    monkeypatch.setenv("HOME", str(tmp_path))

    # Create config file
    config_dir = tmp_path / ".cloudmask"
    config_dir.mkdir()
    config_file = config_dir / "config.yml"
    config_file.write_text(
        """
seed: default-seed-12345
company_names:
  - Default Corp
preserve_prefixes: true
"""
    )

    # Load config from default location
    config_path = get_default_config_path()
    assert config_path is not None

    config = load_config(config_path, use_env=False)
    assert config.seed == "default-seed-12345"
    assert "Default Corp" in config.company_names
    assert config.preserve_prefixes is True
