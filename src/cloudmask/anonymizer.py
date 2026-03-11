"""Anonymization engine for CloudMask."""

import hashlib
import re

from .config.config import Config
from .utils.patterns import (
    AWS_ACCOUNT_PATTERN,
    DOMAIN_PATTERN,
    IP_ADDRESS_PATTERN,
    get_aws_patterns,
    is_valid_ip,
)


class Anonymizer:
    """Core anonymization engine."""

    def __init__(self, config: Config, seed: str):
        """Initialize anonymizer with configuration and seed."""
        self.config = config
        self.seed = seed
        self.mapping: dict[str, str] = {}

        self._compiled_custom: list[tuple[re.Pattern[str], str]] = [
            (re.compile(cp.pattern, re.IGNORECASE), cp.name)
            for cp in config.custom_patterns
        ]

        _companies = [c for c in config.company_names if c.strip()]
        self._compiled_company: re.Pattern[str] | None = (
            re.compile(
                "|".join(
                    re.escape(c) for c in sorted(_companies, key=len, reverse=True)
                ),
                re.IGNORECASE,
            )
            if _companies
            else None
        )

    def _hash(self, value: str, prefix: str = "") -> str:
        """Generate deterministic hash."""
        hash_hex = hashlib.sha256(f"{self.seed}:{prefix}:{value}".encode()).hexdigest()[:16]
        return f"{prefix}-{hash_hex}" if prefix else hash_hex

    def _anonymize_by_type(self, original: str, resource_type: str) -> str:
        """Anonymize based on resource type."""
        if cached := self.mapping.get(original):
            return cached

        match resource_type:
            case "account":
                anonymized = self._hash_to_account(original)
            case "ip":
                anonymized = self._hash_to_ip(original)
            case "domain":
                anonymized = self._hash_to_domain(original)
            case "company":
                anonymized = f"Company-{self._hash(original, 'company')[:8]}"
            case _:
                anonymized = self._hash(original, resource_type)[:12]

        self.mapping[original] = anonymized
        return anonymized

    def _hash_to_account(self, original: str) -> str:
        """Generate 12-digit account ID."""
        hash_hex = hashlib.sha256(f"{self.seed}:account:{original}".encode()).hexdigest()[:12]
        hash_int = int(hash_hex, 16)
        return f"{hash_int % 1_000_000_000_000:012d}"

    def _hash_to_ip(self, original: str) -> str:
        """Generate IP address."""
        hash_bytes = hashlib.sha256(f"{self.seed}:ip:{original}".encode()).digest()[:4]
        return ".".join(str(b) for b in hash_bytes)

    def _hash_to_domain(self, original: str) -> str:
        """Generate domain name."""
        hash_hex = self._hash(original, "domain")[:12]
        tld = original.split(".")[-1] if "." in original else "com"
        return f"domain-{hash_hex}.{tld}"

    def _extract_prefix(self, resource_id: str) -> str:
        """Extract AWS resource prefix."""
        if "-" not in resource_id:
            return ""
        prefix = resource_id.split("-", 1)[0]
        known = {
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
            "vgw",
            "cgw",
            "vpn",
            "dopt",
            "nacl",
        }
        return prefix if prefix in known else ""

    def _anonymize_aws_resource(self, match: re.Match[str]) -> str:
        """Anonymize AWS resource IDs."""
        original = match.group(0)
        if cached := self.mapping.get(original):
            return cached

        if original.startswith("arn:aws:"):
            result = AWS_ACCOUNT_PATTERN.sub(
                lambda m: self._anonymize_by_type(m.group(0), "account"), original
            )
            from .utils.patterns import AWS_RESOURCE_PATTERN

            result = AWS_RESOURCE_PATTERN.sub(lambda m: self._anonymize_aws_resource(m), result)
            self.mapping[original] = result
            return result

        prefix = self._extract_prefix(original)
        anonymized = (
            self._hash(original, prefix)
            if prefix and self.config.preserve_prefixes
            else self._hash(original)
        )
        self.mapping[original] = anonymized
        return anonymized

    def anonymize(self, text: str) -> str:
        """Anonymize text."""
        result = text

        for pattern in get_aws_patterns():
            result = pattern.sub(self._anonymize_aws_resource, result)

        result = AWS_ACCOUNT_PATTERN.sub(
            lambda m: self._anonymize_by_type(m.group(0), "account"), result
        )

        for compiled, name in self._compiled_custom:
            result = compiled.sub(
                lambda m, n=name: self._anonymize_by_type(m.group(0), n),  # type: ignore[misc]
                result,
            )

        if self._compiled_company:
            result = self._compiled_company.sub(
                lambda m: self._anonymize_by_type(m.group(0), "company"),
                result,
            )

        if self.config.anonymize_ips:
            result = IP_ADDRESS_PATTERN.sub(
                lambda m: (
                    self._anonymize_by_type(m.group(0), "ip")
                    if is_valid_ip(m.group(0))
                    else m.group(0)
                ),
                result,
            )

        if self.config.anonymize_domains:
            result = DOMAIN_PATTERN.sub(
                lambda m: self._anonymize_by_type(m.group(0), "domain"),
                result,
            )

        return result
