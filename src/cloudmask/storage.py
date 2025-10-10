"""Central storage management for CloudMask mappings."""

import warnings
from pathlib import Path


def get_storage_dir() -> Path:
    """Get the central storage directory for CloudMask mappings.

    Returns:
        Path to ~/.cloudmask directory with secure permissions (700).
    """
    storage_dir = Path.home() / ".cloudmask"

    if not storage_dir.exists():
        storage_dir.mkdir(mode=0o700, parents=True)
    else:
        # Check permissions but don't force change
        current_perms = storage_dir.stat().st_mode & 0o777
        if current_perms != 0o700:
            warnings.warn(
                f"CloudMask storage directory '{storage_dir}' exists with permissions "
                f"{oct(current_perms)}. "
                "Consider setting to 700 for security: chmod 700 ~/.cloudmask",
                stacklevel=2,
            )

    return storage_dir


def ensure_secure_permissions(file_path: Path) -> None:
    """Ensure a file has secure permissions (600 - owner read/write only).

    Args:
        file_path: Path to the file to secure.
    """
    if file_path.exists() and file_path.is_file():
        file_path.chmod(0o600)


def get_default_mapping_path() -> Path:
    """Get the default mapping file path.

    Returns:
        Path to ~/.cloudmask/mapping.json with secure permissions.
    """
    storage_dir = get_storage_dir()
    mapping_path = storage_dir / "mapping.json"

    # Ensure secure permissions if file exists
    if mapping_path.exists():
        ensure_secure_permissions(mapping_path)

    return mapping_path


def get_default_config_path() -> Path | None:
    """Get the default config file path if it exists.

    Returns:
        Path to ~/.cloudmask/config.yml if it exists, None otherwise.
    """
    storage_dir = get_storage_dir()
    config_path = storage_dir / "config.yml"
    return config_path if config_path.exists() else None
