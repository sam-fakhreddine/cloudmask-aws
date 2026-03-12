"""Anonymization engine for CloudMask."""

import hashlib
import hmac
import re

from .config.config import Config
from .utils.patterns import (
    AWS_ACCOUNT_PATTERN,
    AWS_RESOURCE_PATTERN,
    AWS_RESOURCE_PREFIXES,
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
        self._seed_bytes = seed.encode()
        self.mapping: dict[str, str] = {}

        self._compiled_custom: list[tuple[re.Pattern[str], str]] = []
        for cp in config.custom_patterns:
            try:
                compiled = re.compile(cp.pattern, re.IGNORECASE)
                self._compiled_custom.append((compiled, cp.name))
            except re.error:
                pass  # Already validated in CustomPattern.__post_init__

        self._aws_patterns = get_aws_patterns()

        _companies = [c for c in config.company_names if c.strip()]
        self._compiled_company: re.Pattern[str] | None = (
            re.compile(
                "|".join(re.escape(c) for c in sorted(_companies, key=len, reverse=True)),
                re.IGNORECASE,
            )
            if _companies
            else None
        )

    def _hash(self, value: str, prefix: str = "") -> str:
        """Generate deterministic HMAC-based hash."""
        msg = f"{prefix}:{value}".encode()
        hash_hex = hmac.new(self._seed_bytes, msg, hashlib.sha256).hexdigest()[:16]
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
                msg = f"company:{original}".encode()
                hash_hex = hmac.new(self._seed_bytes, msg, hashlib.sha256).hexdigest()[:8]
                anonymized = f"Company-{hash_hex}"
            case _:
                anonymized = self._hash(original, resource_type)

        self.mapping[original] = anonymized
        return anonymized

    def _hash_to_account(self, original: str) -> str:
        """Generate 12-digit account ID (never starts with 0)."""
        msg = f"account:{original}".encode()
        hash_hex = hmac.new(self._seed_bytes, msg, hashlib.sha256).hexdigest()[:12]
        hash_int = int(hash_hex, 16)
        return str((hash_int % 900_000_000_000) + 100_000_000_000)

    def _hash_to_ip(self, original: str) -> str:
        """Generate IP in RFC 5737 documentation ranges."""
        msg = f"ip:{original}".encode()
        hash_bytes = hmac.new(self._seed_bytes, msg, hashlib.sha256).digest()[:2]
        idx = int.from_bytes(hash_bytes, "big")
        ranges = [(192, 0, 2), (198, 51, 100), (203, 0, 113)]
        net = ranges[idx % 3]
        host = (idx % 254) + 1
        return f"{net[0]}.{net[1]}.{net[2]}.{host}"

    def _hash_to_domain(self, original: str) -> str:
        """Generate domain name."""
        msg = f"domain:{original}".encode()
        hash_hex = hmac.new(self._seed_bytes, msg, hashlib.sha256).hexdigest()[:12]
        tld = original.split(".")[-1] if "." in original else "com"
        return f"domain-{hash_hex}.{tld}"

    def _extract_prefix(self, resource_id: str) -> str:
        """Extract AWS resource prefix."""
        if "-" not in resource_id:
            return ""
        prefix = resource_id.split("-", 1)[0]
        return prefix if prefix in AWS_RESOURCE_PREFIXES else ""

    def _anonymize_aws_resource(self, match: re.Match[str]) -> str:
        """Anonymize AWS resource IDs."""
        original = match.group(0)
        if cached := self.mapping.get(original):
            return cached

        if original.startswith("arn:aws:"):
            result = AWS_ACCOUNT_PATTERN.sub(
                lambda m: self._anonymize_by_type(m.group(0), "account"), original
            )
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

        for pattern in self._aws_patterns:
            result = pattern.sub(self._anonymize_aws_resource, result)

        if self.config.anonymize_standalone_accounts:
            mapped_values = set(self.mapping.values())
            result = AWS_ACCOUNT_PATTERN.sub(
                lambda m: (
                    m.group(0)
                    if m.group(0) in mapped_values
                    else self._anonymize_by_type(m.group(0), "account")
                ),
                result,
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
