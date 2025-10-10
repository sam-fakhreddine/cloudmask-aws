"""Configuration management."""

import re
from dataclasses import dataclass, field
from pathlib import Path

import yaml

from ..exceptions import ConfigurationError, FileOperationError, ValidationError
from ..logging import log_operation, logger


@dataclass
class CustomPattern:
    """Custom pattern configuration."""

    pattern: str
    name: str = "custom"

    def __post_init__(self) -> None:
        """Validate pattern after initialization."""
        try:
            re.compile(self.pattern)
        except re.error as e:
            raise ValidationError(
                f"Invalid regex pattern '{self.pattern}': {e}",
                "Check your regex syntax and escape special characters",
            ) from e


@dataclass
class Config:
    """Configuration management."""

    company_names: list[str] = field(
        default_factory=lambda: ["Acme Corp", "Example Inc", "MyCompany"]
    )
    custom_patterns: list[CustomPattern] = field(default_factory=list)
    preserve_prefixes: bool = True
    anonymize_ips: bool = True
    anonymize_domains: bool = False
    seed: str = "default-seed"

    def __post_init__(self) -> None:
        """Validate configuration after initialization."""
        if not isinstance(self.company_names, list):
            raise ConfigurationError(
                "company_names must be a list", "Use: company_names: ['Company1', 'Company2']"
            )
        if not isinstance(self.custom_patterns, list):
            raise ConfigurationError(
                "custom_patterns must be a list",
                "Use: custom_patterns: [{pattern: '...', name: '...'}]",
            )

    def validate_for_production(self) -> None:
        """Validate configuration for production use."""
        if not self.seed or not self.seed.strip():
            raise ValidationError(
                "Seed cannot be empty",
                "Provide a strong seed value for deterministic anonymization",
            )
        if len(self.seed) < 8:
            raise ValidationError(
                "Seed must be at least 8 characters for security",
                "Use a longer, more complex seed value",
            )

    @classmethod
    def from_yaml(cls, config_path: Path) -> "Config":
        """Load configuration from YAML file."""
        logger.debug(f"Loading config from {config_path}")

        if not config_path.exists():
            raise FileOperationError(
                f"Config file not found: {config_path}",
                f"Create a config file with: cloudmask init-config -c {config_path}",
            )
        if config_path.stat().st_size > 1_000_000:  # 1MB limit
            raise FileOperationError(
                "Config file too large (max 1MB)", "Reduce the size of your configuration file"
            )

        try:
            with config_path.open() as f:
                data = yaml.safe_load(f) or {}
        except yaml.YAMLError as e:
            raise ConfigurationError(
                f"Invalid YAML syntax: {e}", "Check your YAML file for syntax errors"
            ) from e

        if not isinstance(data, dict):
            raise ConfigurationError(
                "Config file must contain a YAML dictionary",
                "Ensure your config file has key-value pairs",
            )

        if "custom_patterns" in data:
            data["custom_patterns"] = [
                CustomPattern(**p) if isinstance(p, dict) else p for p in data["custom_patterns"]
            ]

        log_operation("config_loaded", path=str(config_path))
        return cls(**{k: v for k, v in data.items() if k in cls.__annotations__})

    def to_yaml(self, config_path: Path) -> None:
        """Save configuration to YAML file."""
        data = {
            "company_names": self.company_names,
            "custom_patterns": [
                {"pattern": p.pattern, "name": p.name} for p in self.custom_patterns
            ],
            "preserve_prefixes": self.preserve_prefixes,
            "anonymize_ips": self.anonymize_ips,
            "anonymize_domains": self.anonymize_domains,
            "seed": self.seed,
        }
        with config_path.open("w") as f:
            yaml.dump(data, f, default_flow_style=False, sort_keys=False)
