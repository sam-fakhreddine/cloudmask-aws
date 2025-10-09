"""CloudMask - Python 3.10+ Optimized Version.

Using modern Python features: structural pattern matching, union types, etc.
"""

__version__ = "0.1.0"

import hashlib
import json
import re
from collections.abc import Callable
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import yaml

from .cache import LRUCache
from .exceptions import ConfigurationError, FileOperationError, MappingError, ValidationError
from .logging import log_operation, logger
from .patterns import AWS_ACCOUNT_PATTERN, AWS_RESOURCE_PATTERN, get_aws_patterns, is_valid_ip

# ============================================================
# Modern Type Hints (Python 3.10+)
# ============================================================

MappingDict = dict[str, str]
ConfigDict = dict[str, Any]


# ============================================================
# Dataclasses for Configuration
# ============================================================


@dataclass
class CustomPattern:
    """Custom pattern configuration."""

    pattern: str
    name: str = "custom"

    def __post_init__(self) -> None:
        """Validate pattern on initialization."""
        try:
            re.compile(self.pattern)
        except re.error as e:
            raise ValidationError(
                f"Invalid regex pattern '{self.pattern}': {e}",
                "Check your regex syntax and escape special characters",
            ) from e


@dataclass
class Config:
    """Configuration management using dataclass."""

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
        """Validate configuration for production use.

        Call this method to enforce stricter security requirements.
        """
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

        # Convert custom_patterns to CustomPattern objects
        if "custom_patterns" in data:
            if not isinstance(data["custom_patterns"], list):
                raise ConfigurationError(
                    "custom_patterns must be a list",
                    "Use: custom_patterns: [{pattern: '...', name: '...'}]",
                )
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


# ============================================================
# Main CloudMask Class
# ============================================================


class CloudMask:
    """Main anonymizer using Python 3.10+ features."""

    def __init__(self, config: Config | None = None, seed: str | None = None):
        """Initialize with union type hints (Python 3.10+)."""
        self.config = config or Config()
        self.mapping: MappingDict = {}
        self.seed = seed or self.config.seed
        self._cache = LRUCache(maxsize=1000)

    def _generate_deterministic_id(self, original: str, prefix: str = "") -> str:
        """Generate deterministic anonymized ID."""
        hash_obj = hashlib.sha256(f"{self.seed}:{original}".encode())
        hash_hex = hash_obj.hexdigest()[:16]

        # Structural pattern matching (Python 3.10+)
        match prefix:
            case "" | None:
                return hash_hex
            case _:
                return f"{prefix}-{hash_hex}"

    def _anonymize_by_type(self, original: str, resource_type: str) -> str:
        """Anonymize based on resource type using pattern matching."""
        # Check mapping first
        if cached := self.mapping.get(original):
            return cached

        # Check LRU cache
        if cached := self._cache.get(original):
            return cached

        # Pattern matching for different resource types
        match resource_type:
            case "account":
                anonymized = self._hash_to_account_id(original)

            case "ip":
                anonymized = self._hash_to_ip(original)

            case "domain":
                anonymized = self._hash_to_domain(original)

            case "company":
                hash_hex = hashlib.sha256(f"{self.seed}:company:{original}".encode()).hexdigest()[
                    :8
                ]
                anonymized = f"Company-{hash_hex}"

            case _:  # Default case
                hash_hex = hashlib.sha256(
                    f"{self.seed}:{resource_type}:{original}".encode()
                ).hexdigest()[:12]
                anonymized = f"{resource_type}-{hash_hex}"

        self.mapping[original] = anonymized
        self._cache.put(original, anonymized)
        return anonymized

    def _hash_to_account_id(self, original: str) -> str:
        """Generate 12-digit account ID."""
        hash_obj = hashlib.sha256(f"{self.seed}:account:{original}".encode())
        hash_int = int(hash_obj.hexdigest()[:12], 16)
        return f"{hash_int % 1_000_000_000_000:012d}"  # Underscore separators

    def _hash_to_ip(self, original: str) -> str:
        """Generate IP address."""
        hash_obj = hashlib.sha256(f"{self.seed}:ip:{original}".encode())
        hash_bytes = hash_obj.digest()[:4]
        return ".".join(str(b) for b in hash_bytes)

    def _hash_to_domain(self, original: str) -> str:
        """Generate domain name."""
        hash_obj = hashlib.sha256(f"{self.seed}:domain:{original}".encode())
        hash_hex = hash_obj.hexdigest()[:12]

        # Preserve TLD if possible
        if parts := original.split("."):
            tld = parts[-1] if len(parts) >= 2 else "com"
            return f"domain-{hash_hex}.{tld}"

        return f"domain-{hash_hex}.com"

    def _extract_prefix(self, resource_id: str) -> tuple[str, bool]:
        """Extract AWS resource prefix.

        Returns (prefix, has_prefix) tuple.
        """
        if "-" not in resource_id:
            return "", False

        prefix, *_rest = resource_id.split("-", 1)

        # Check if it's a known AWS prefix
        known_prefixes = {
            "vpc",
            "subnet",
            "sg",
            "igw",
            "rtb",
            "eni",
            "eip",
            "vol",
            "snap",
            "ami",
            "i",
            "r",
            "lt",
            "asg",
            "elb",
            "tg",
            "elbv2",
            "natgw",
            "vpce",
            "acl",
            "pcx",
        }

        return (prefix, True) if prefix in known_prefixes else ("", False)

    def _anonymize_aws_resource(self, match: re.Match[str]) -> str:
        """Anonymize AWS resource IDs with pattern matching."""
        original = match.group(0)

        # Early return if already mapped
        if cached := self.mapping.get(original):
            return cached

        # Check if this is an ARN - if so, anonymize account IDs within it
        if original.startswith("arn:aws:"):
            # Anonymize account IDs within the ARN
            result = AWS_ACCOUNT_PATTERN.sub(
                lambda m: self._anonymize_by_type(m.group(0), "account"), original
            )
            # Also anonymize any resource IDs in the ARN
            for pattern in [AWS_RESOURCE_PATTERN]:
                result = pattern.sub(lambda m: self._anonymize_aws_resource(m), result)
            self.mapping[original] = result
            return result

        prefix, has_prefix = self._extract_prefix(original)

        # Use walrus operator and pattern matching
        match (has_prefix, self.config.preserve_prefixes):
            case (True, True):
                anonymized = self._generate_deterministic_id(original, prefix)
            case _:
                anonymized = self._generate_deterministic_id(original)

        self.mapping[original] = anonymized
        return anonymized

    def anonymize(self, text: str) -> str:
        """Anonymize AWS infrastructure information.

        Uses modern Python 3.10+ features throughout.
        """
        result = text

        # AWS Resource IDs (using pre-compiled patterns) - do this BEFORE account IDs
        # to avoid breaking ARNs
        for pattern in get_aws_patterns():
            result = pattern.sub(self._anonymize_aws_resource, result)

        # AWS Account IDs (using pre-compiled pattern) - do this AFTER ARNs
        # so account IDs within ARNs are preserved in the ARN structure
        result = AWS_ACCOUNT_PATTERN.sub(
            lambda m: self._anonymize_by_type(m.group(0), "account"), result
        )

        # Company names with case-insensitive matching
        if self.config.company_names:
            for company in sorted(self.config.company_names, key=len, reverse=True):
                if not company.strip():
                    continue

                company_name = company

                def replace_company(_m: re.Match[str], c: str = company_name) -> str:
                    return self._anonymize_by_type(c, "company")

                result = re.sub(
                    re.escape(company_name),
                    replace_company,
                    result,
                    flags=re.IGNORECASE,
                )

        # IP addresses (if enabled)
        if self.config.anonymize_ips:

            def anonymize_ip(m: re.Match[str]) -> str:
                ip = m.group(0)
                # Only anonymize valid IPs
                if is_valid_ip(ip):
                    return self._anonymize_by_type(ip, "ip")
                return ip

            result = re.sub(
                r"\b(?:\d{1,3}\.){3}\d{1,3}\b",
                anonymize_ip,
                result,
            )

        # Domains (if enabled)
        if self.config.anonymize_domains:
            result = re.sub(
                r"\b(?:[a-z0-9](?:[a-z0-9-]{0,61}[a-z0-9])?\.)+[a-z0-9][a-z0-9-]{0,61}[a-z0-9]\b",
                lambda m: self._anonymize_by_type(m.group(0), "domain"),
                result,
                flags=re.IGNORECASE,
            )

        # Custom patterns
        for custom_pattern in self.config.custom_patterns:
            pattern_name = custom_pattern.name

            def replace_custom(match: re.Match[str], name: str = pattern_name) -> str:
                return self._anonymize_by_type(match.group(0), name)

            result = re.sub(
                custom_pattern.pattern,
                replace_custom,
                result,
            )

        return result

    def anonymize_file(self, input_path: Path, output_path: Path) -> int:
        """Anonymize a file and return count of unique identifiers."""
        logger.debug(f"Anonymizing file: {input_path} -> {output_path}")

        if not input_path.exists():
            raise FileOperationError(
                f"Input file not found: {input_path}",
                "Check the file path and ensure the file exists",
            )

        file_size = input_path.stat().st_size
        if file_size > 100_000_000:  # 100MB limit
            raise FileOperationError(
                f"File too large ({file_size / 1_000_000:.1f}MB, max 100MB)",
                "Use streaming for larger files or split the file",
            )

        try:
            text = input_path.read_text(encoding="utf-8")
        except UnicodeDecodeError as e:
            raise FileOperationError(
                f"Cannot read file (encoding error): {e}", "Ensure the file is UTF-8 encoded"
            ) from e

        anonymized = self.anonymize(text)

        try:
            output_path.write_text(anonymized, encoding="utf-8")
        except OSError as e:
            raise FileOperationError(
                f"Cannot write to output file: {e}", "Check file permissions and disk space"
            ) from e

        log_operation(
            "file_anonymized",
            input=str(input_path),
            output=str(output_path),
            count=len(self.mapping),
        )
        return len(self.mapping)

    def save_mapping(self, filepath: Path | str) -> None:
        """Save mapping to JSON file."""
        filepath = Path(filepath) if isinstance(filepath, str) else filepath
        logger.debug(f"Saving mapping to {filepath}")

        if len(self.mapping) > 1_000_000:
            raise MappingError(
                f"Mapping too large ({len(self.mapping)} entries, max 1M)",
                "Process data in smaller batches",
            )

        try:
            filepath.write_text(json.dumps(self.mapping, indent=2), encoding="utf-8")
        except OSError as e:
            raise FileOperationError(
                f"Cannot write mapping file: {e}", "Check file permissions and disk space"
            ) from e

        log_operation("mapping_saved", path=str(filepath), entries=len(self.mapping))

    def load_mapping(self, filepath: Path | str) -> None:
        """Load mapping from JSON file."""
        filepath = Path(filepath) if isinstance(filepath, str) else filepath
        logger.debug(f"Loading mapping from {filepath}")

        if not filepath.exists():
            raise FileOperationError(
                f"Mapping file not found: {filepath}",
                "Ensure you have saved the mapping file during anonymization",
            )

        file_size = filepath.stat().st_size
        if file_size > 50_000_000:  # 50MB limit
            raise MappingError(
                f"Mapping file too large ({file_size / 1_000_000:.1f}MB, max 50MB)",
                "Use a smaller mapping file or process in batches",
            )

        try:
            content = filepath.read_text(encoding="utf-8")
            mapping = json.loads(content)
        except json.JSONDecodeError as e:
            raise MappingError(
                f"Invalid JSON in mapping file: {e}", "Ensure the mapping file is valid JSON"
            ) from e
        except UnicodeDecodeError as e:
            raise FileOperationError(
                f"Cannot read mapping file (encoding error): {e}",
                "Ensure the file is UTF-8 encoded",
            ) from e

        if not isinstance(mapping, dict):
            raise MappingError(
                "Mapping file must contain a JSON object",
                "The mapping file should be a dictionary of key-value pairs",
            )
        if len(mapping) > 1_000_000:
            raise MappingError(
                f"Mapping too large ({len(mapping)} entries, max 1M)", "Use a smaller mapping file"
            )

        self.mapping = mapping
        log_operation("mapping_loaded", path=str(filepath), entries=len(mapping))

    def get_mapping(self) -> MappingDict:
        """Get copy of current mapping."""
        return self.mapping.copy()


# ============================================================
# CloudUnmask
# ============================================================


class CloudUnmask:
    """Unanonymizer using Python 3.10+ features."""

    def __init__(self, mapping: MappingDict | None = None, mapping_file: Path | None = None):
        """Initialize with union types."""
        match (mapping, mapping_file):
            case (dict() as m, None):
                logger.debug("Initializing with provided mapping")
                self.reverse_mapping = {v: k for k, v in m.items()}

            case (None, Path() as f):
                logger.debug(f"Loading mapping from {f}")
                if not f.exists():
                    raise FileOperationError(
                        f"Mapping file not found: {f}",
                        "Ensure you have saved the mapping file during anonymization",
                    )
                try:
                    loaded_mapping = json.loads(f.read_text())
                    self.reverse_mapping = {v: k for k, v in loaded_mapping.items()}
                except json.JSONDecodeError as e:
                    raise MappingError(
                        f"Invalid JSON in mapping file: {e}",
                        "Ensure the mapping file is valid JSON",
                    ) from e

            case (None, None):
                logger.debug("Initializing with empty mapping")
                self.reverse_mapping = {}

            case _:
                raise ValidationError(
                    "Provide either mapping or mapping_file, not both",
                    "Use only one parameter: mapping=dict or mapping_file=Path",
                )

    def unanonymize(self, text: str) -> str:
        """Restore original values."""
        result = text

        # Sort by length to avoid partial replacements
        for anonymized, original in sorted(
            self.reverse_mapping.items(), key=lambda x: len(x[0]), reverse=True
        ):
            result = result.replace(anonymized, original)

        return result

    def unanonymize_file(self, input_path: Path, output_path: Path) -> int:
        """Unanonymize a file."""
        logger.debug(f"Unanonymizing file: {input_path} -> {output_path}")

        if not input_path.exists():
            raise FileOperationError(
                f"Input file not found: {input_path}",
                "Check the file path and ensure the file exists",
            )

        file_size = input_path.stat().st_size
        if file_size > 100_000_000:  # 100MB limit
            raise FileOperationError(
                f"File too large ({file_size / 1_000_000:.1f}MB, max 100MB)",
                "Process the file in smaller chunks",
            )

        try:
            text = input_path.read_text(encoding="utf-8")
        except UnicodeDecodeError as e:
            raise FileOperationError(
                f"Cannot read file (encoding error): {e}", "Ensure the file is UTF-8 encoded"
            ) from e

        unanonymized = self.unanonymize(text)

        try:
            output_path.write_text(unanonymized, encoding="utf-8")
        except OSError as e:
            raise FileOperationError(
                f"Cannot write to output file: {e}", "Check file permissions and disk space"
            ) from e

        log_operation(
            "file_unanonymized",
            input=str(input_path),
            output=str(output_path),
            count=len(self.reverse_mapping),
        )
        return len(self.reverse_mapping)


# ============================================================
# Convenience Functions
# ============================================================


def anonymize(
    text: str, seed: str = "default-seed", **config_options: Any
) -> tuple[str, MappingDict]:
    """Quick anonymization using modern return type hints.

    Example:
        >>> result, mapping = anonymize(
        ...     "vpc-123",
        ...     seed="my-seed",
        ...     company_names=["Acme Corp"]
        ... )
    """
    config = Config(seed=seed, **config_options)
    mask = CloudMask(config=config)
    anonymized = mask.anonymize(text)
    return anonymized, mask.get_mapping()


def unanonymize(text: str, mapping: MappingDict) -> str:
    """Quick unanonymization."""
    unmask = CloudUnmask(mapping=mapping)
    return unmask.unanonymize(text)


# ============================================================
# Context Manager
# ============================================================


class TemporaryMask:
    """Context manager for temporary anonymization."""

    def __init__(self, seed: str | None = None, config: Config | None = None):
        """Initialize temporary mask."""
        self.seed = seed
        self.config = config
        self.mask: CloudMask | None = None

    def __enter__(self) -> CloudMask:
        """Enter context."""
        self.mask = CloudMask(config=self.config, seed=self.seed)
        return self.mask

    def __exit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        """Exit context."""


# ============================================================
# Functional Utilities
# ============================================================


def create_batch_anonymizer(seed: str, config: Config | None = None) -> Callable[[str], str]:
    """Create a reusable anonymization function.

    Example:
        >>> anon = create_batch_anonymizer(seed="my-seed")
        >>> result1 = anon("vpc-123")
        >>> result2 = anon("i-456")
    """
    mask = CloudMask(config=config, seed=seed)
    return mask.anonymize


def anonymize_dict(data: dict[str, Any], mask: CloudMask) -> dict[str, Any]:
    """Recursively anonymize dictionary values.

    Uses structural pattern matching for type handling.
    """
    result: dict[str, Any] = {}

    for key, value in data.items():
        match value:
            case str():
                result[key] = mask.anonymize(value)

            case dict():
                result[key] = anonymize_dict(value, mask)

            case list():
                result[key] = [
                    (
                        mask.anonymize(item)
                        if isinstance(item, str)
                        else anonymize_dict(item, mask) if isinstance(item, dict) else item
                    )
                    for item in value
                ]

            case _:
                result[key] = value

    return result
