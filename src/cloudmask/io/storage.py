"""Central storage management for CloudMask mappings."""

import warnings
from pathlib import Path


def _get_storage_dir() -> Path:
    """Get the central storage directory for CloudMask mappings."""
    storage_dir = Path.home() / ".cloudmask"

    if not storage_dir.exists():
        storage_dir.mkdir(mode=0o700, parents=True)
    else:
        current_perms = storage_dir.stat().st_mode & 0o777
        if current_perms != 0o700:
            warnings.warn(
                f"CloudMask storage directory '{storage_dir}' exists with permissions "
                f"{oct(current_perms)}. "
                "Consider setting to 700 for security: chmod 700 ~/.cloudmask",
                stacklevel=2,
            )

    return storage_dir


def _ensure_secure_permissions(file_path: Path) -> None:
    """Ensure a file has secure permissions (600 - owner read/write only)."""
    if file_path.exists() and file_path.is_file():
        file_path.chmod(0o600)


def _get_default_mapping_path() -> Path:
    """Get the default mapping file path."""
    storage_dir = _get_storage_dir()
    mapping_path = storage_dir / "mapping.json"

    if mapping_path.exists():
        _ensure_secure_permissions(mapping_path)

    return mapping_path


def _get_default_config_path() -> Path | None:
    """Get the default config file path if it exists."""
    storage_dir = _get_storage_dir()
    config_path = storage_dir / "config.yml"
    return config_path if config_path.exists() else None


class _Storage:
    """Central storage paths for CloudMask."""

    @property
    def Dir(self) -> Path:
        """Get the central storage directory (~/.cloudmask)."""
        return _get_storage_dir()

    @property
    def DefaultMappingPath(self) -> Path:
        """Get the default mapping file path (~/.cloudmask/mapping.json)."""
        return _get_default_mapping_path()

    @property
    def DefaultConfigPath(self) -> Path | None:
        """Get the default config file path if it exists (~/.cloudmask/config.yml)."""
        return _get_default_config_path()


# Singleton instance
Storage = _Storage()

# Backward compatibility
get_storage_dir = _get_storage_dir
get_default_mapping_path = _get_default_mapping_path
get_default_config_path = _get_default_config_path
ensure_secure_permissions = _ensure_secure_permissions
