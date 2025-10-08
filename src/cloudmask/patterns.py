"""Optimized regex patterns for AWS resource matching."""

import re
from functools import lru_cache

# Pre-compiled patterns for better performance
# AWS resource IDs are typically 8 or 17 hexadecimal characters
# We use 3-17 to support test IDs
# For 3-char IDs: allow any alphanumeric combination
# For 4+ chars: require hex to avoid matching malformed IDs like "vpc-123i" in "vpc-123i-456"
AWS_RESOURCE_PATTERN = re.compile(
    r"\b(vpc|subnet|sg|igw|rtb|eni|eip|vol|snap|ami|i|r|lt|asg|elb|tg|elbv2|"
    r"natgw|vpce|acl|pcx|vgw|cgw|vpn|dopt|nacl)-(?:[0-9a-z]{3}(?![0-9a-z])|[0-9a-f]{4,17})\b",
    re.IGNORECASE,
)

AWS_ACCOUNT_PATTERN = re.compile(r"\b\d{12}\b")

AWS_ARN_PATTERN = re.compile(
    r"\barn:aws:[a-z0-9-]+:[a-z0-9-]*:\d{12}:[a-zA-Z0-9/_-]+", re.IGNORECASE
)

AWS_SERVICE_URL_PATTERN = re.compile(
    r"\b(s3|dynamodb|lambda|rds|ec2|ecs|eks|sqs|sns)://[a-zA-Z0-9._-]+", re.IGNORECASE
)

IP_ADDRESS_PATTERN = re.compile(r"\b(?:\d{1,3}\.){3}\d{1,3}\b")

DOMAIN_PATTERN = re.compile(
    r"\b(?:[a-z0-9](?:[a-z0-9-]{0,61}[a-z0-9])?\.)+[a-z0-9][a-z0-9-]{0,61}[a-z0-9]\b", re.IGNORECASE
)


@lru_cache(maxsize=256)
def compile_pattern(pattern: str) -> re.Pattern[str]:
    """Compile and cache regex patterns.

    Args:
        pattern: Regex pattern string

    Returns:
        Compiled pattern
    """
    return re.compile(pattern)


def get_aws_patterns() -> list[re.Pattern[str]]:
    """Get list of pre-compiled AWS patterns.

    Returns:
        List of compiled patterns
    """
    return [
        AWS_RESOURCE_PATTERN,
        AWS_SERVICE_URL_PATTERN,
        AWS_ARN_PATTERN,
    ]


def is_valid_aws_resource_id(resource_id: str) -> bool:
    """Fast validation of AWS resource ID format.

    Args:
        resource_id: Resource ID to validate

    Returns:
        True if valid format
    """
    return bool(AWS_RESOURCE_PATTERN.match(resource_id))


def is_valid_account_id(account_id: str) -> bool:
    """Fast validation of AWS account ID.

    Args:
        account_id: Account ID to validate

    Returns:
        True if valid format
    """
    return bool(AWS_ACCOUNT_PATTERN.match(account_id))


def is_valid_ip(ip: str) -> bool:
    """Fast validation of IP address format.

    Args:
        ip: IP address to validate

    Returns:
        True if valid format
    """
    if not IP_ADDRESS_PATTERN.match(ip):
        return False

    # Validate octets
    try:
        parts = ip.split(".")
        if len(parts) != 4:
            return False
        octets = [int(x) for x in parts]
        return all(0 <= octet <= 255 for octet in octets)
    except (ValueError, AttributeError):
        return False
