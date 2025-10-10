"""Configuration loading with environment variable and multiple format support."""

import json
import os
import sys
from pathlib import Path
from typing import Any

import yaml

from ..exceptions import ConfigurationError
from .config import Config, CustomPattern

if sys.version_info >= (3, 11):
    import tomllib  # type: ignore[import-not-found]
else:
    try:
        import tomli as tomllib  # type: ignore[import-not-found,unused-ignore]
    except ImportError:
        tomllib = None  # type: ignore[assignment,unused-ignore]


def load_from_env() -> dict[str, Any]:
    """Load configuration from environment variables.

    Environment variables:
        CLOUDMASK_SEED: Seed value
        CLOUDMASK_PRESERVE_PREFIXES: true/false
        CLOUDMASK_ANONYMIZE_IPS: true/false
        CLOUDMASK_ANONYMIZE_DOMAINS: true/false
        CLOUDMASK_COMPANY_NAMES: Comma-separated list
    """
    config = {}

    if seed := os.getenv("CLOUDMASK_SEED"):
        config["seed"] = seed

    if preserve := os.getenv("CLOUDMASK_PRESERVE_PREFIXES"):
        config["preserve_prefixes"] = preserve.lower() in ("true", "1", "yes")  # type: ignore[assignment]

    if anon_ips := os.getenv("CLOUDMASK_ANONYMIZE_IPS"):
        config["anonymize_ips"] = anon_ips.lower() in ("true", "1", "yes")  # type: ignore[assignment]

    if anon_domains := os.getenv("CLOUDMASK_ANONYMIZE_DOMAINS"):
        config["anonymize_domains"] = anon_domains.lower() in ("true", "1", "yes")  # type: ignore[assignment]

    if companies := os.getenv("CLOUDMASK_COMPANY_NAMES"):
        config["company_names"] = [c.strip() for c in companies.split(",") if c.strip()]  # type: ignore[assignment]

    return config


def load_from_json(path: Path) -> dict[str, Any]:
    """Load configuration from JSON file."""
    try:
        data = json.loads(path.read_text())
    except json.JSONDecodeError as e:
        raise ConfigurationError(f"Invalid JSON: {e}", "Check JSON syntax") from e

    if not isinstance(data, dict):
        raise ConfigurationError("Config must be a dictionary", "Use key-value pairs")

    return data


def load_from_toml(path: Path) -> dict[str, Any]:
    """Load configuration from TOML file."""
    if tomllib is None:
        raise ConfigurationError(
            "TOML support requires Python 3.11+ or tomli package",
            "Install with: pip install tomli",
        )

    try:
        with path.open("rb") as f:
            data = tomllib.load(f)
    except Exception as e:
        raise ConfigurationError(f"Invalid TOML: {e}", "Check TOML syntax") from e

    # Handle [cloudmask] section if present
    if "cloudmask" in data:
        return data["cloudmask"]  # type: ignore[no-any-return]

    return data  # type: ignore[no-any-return,unused-ignore]


def load_config(
    path: Path | None = None, format: str | None = None, use_env: bool = True
) -> Config:
    """Load configuration from file and/or environment.

    Args:
        path: Config file path
        format: File format (yaml/json/toml), auto-detected if None
        use_env: Whether to load from environment variables

    Returns:
        Config object
    """
    config_data: dict[str, Any] = {}

    # Load from file
    if path:
        if not path.exists():
            raise ConfigurationError(f"Config file not found: {path}", "Check the file path")

        # Auto-detect format
        if not format:
            suffix = path.suffix.lower()
            format = {".yaml": "yaml", ".yml": "yaml", ".json": "json", ".toml": "toml"}.get(
                suffix, "yaml"
            )

        # Load based on format
        if format == "json":
            config_data = load_from_json(path)
        elif format == "toml":
            config_data = load_from_toml(path)
        else:
            config_data = yaml.safe_load(path.read_text()) or {}

        # Convert custom_patterns
        if "custom_patterns" in config_data:
            config_data["custom_patterns"] = [
                CustomPattern(**p) if isinstance(p, dict) else p
                for p in config_data["custom_patterns"]
            ]

    # Override with environment variables
    if use_env:
        env_config = load_from_env()
        config_data.update(env_config)

    # Create Config object
    return Config(**{k: v for k, v in config_data.items() if k in Config.__annotations__})


def validate_config(config: Config) -> list[str]:
    """Validate configuration and return list of issues.

    Returns:
        List of validation error messages (empty if valid)
    """
    issues = []

    if not config.seed or len(config.seed) < 8:
        issues.append("Seed must be at least 8 characters")

    if not isinstance(config.company_names, list):
        issues.append("company_names must be a list")

    if not isinstance(config.custom_patterns, list):
        issues.append("custom_patterns must be a list")

    for pattern in config.custom_patterns:
        if not isinstance(pattern, CustomPattern):
            issues.append(f"Invalid custom pattern: {pattern}")

    return issues
