"""Tests for optimized pattern matching."""

from cloudmask.utils.patterns import (
    AWS_ACCOUNT_PATTERN,
    AWS_ARN_PATTERN,
    AWS_RESOURCE_PATTERN,
    AWS_SERVICE_URL_PATTERN,
    DOMAIN_PATTERN,
    IP_ADDRESS_PATTERN,
    compile_pattern,
    get_aws_patterns,
    is_valid_account_id,
    is_valid_aws_resource_id,
    is_valid_ip,
)


class TestPatternMatching:
    """Test pre-compiled pattern matching."""

    def test_aws_resource_pattern(self):
        """Test AWS resource ID pattern."""
        assert AWS_RESOURCE_PATTERN.match("vpc-1234567890abcdef")
        assert AWS_RESOURCE_PATTERN.match("i-abc12345")
        assert AWS_RESOURCE_PATTERN.match("sg-12345678")
        assert not AWS_RESOURCE_PATTERN.match("invalid-123")

    def test_account_pattern(self):
        """Test AWS account ID pattern."""
        assert AWS_ACCOUNT_PATTERN.match("123456789012")
        assert not AWS_ACCOUNT_PATTERN.match("12345678901")  # Too short
        assert not AWS_ACCOUNT_PATTERN.match("1234567890123")  # Too long

    def test_arn_pattern(self):
        """Test AWS ARN pattern."""
        assert AWS_ARN_PATTERN.match("arn:aws:ec2:us-east-1:123456789012:instance/i-123")
        assert not AWS_ARN_PATTERN.match("invalid:arn")

    def test_service_url_pattern(self):
        """Test AWS service URL pattern."""
        assert AWS_SERVICE_URL_PATTERN.match("s3://my-bucket")
        assert AWS_SERVICE_URL_PATTERN.match("dynamodb://my-table")
        assert not AWS_SERVICE_URL_PATTERN.match("http://example.com")

    def test_ip_pattern(self):
        """Test IP address pattern."""
        assert IP_ADDRESS_PATTERN.match("192.168.1.1")
        assert IP_ADDRESS_PATTERN.match("10.0.0.1")
        # Pattern matches format, validation function checks values

    def test_domain_pattern(self):
        """Test domain pattern."""
        assert DOMAIN_PATTERN.match("example.com")
        assert DOMAIN_PATTERN.match("sub.example.com")
        assert DOMAIN_PATTERN.match("my-site.co.uk")


class TestPatternCompilation:
    """Test pattern compilation and caching."""

    def test_compile_pattern(self):
        """Test pattern compilation."""
        pattern = compile_pattern(r"\d+")
        assert pattern.match("123")
        assert not pattern.match("abc")

    def test_compile_pattern_caching(self):
        """Test that patterns are cached."""
        pattern1 = compile_pattern(r"\d+")
        pattern2 = compile_pattern(r"\d+")
        assert pattern1 is pattern2  # Same object due to caching

    def test_get_aws_patterns(self):
        """Test getting AWS patterns."""
        patterns = get_aws_patterns()
        assert len(patterns) == 3
        assert all(hasattr(p, "match") for p in patterns)


class TestValidation:
    """Test validation functions."""

    def test_is_valid_aws_resource_id(self):
        """Test AWS resource ID validation."""
        assert is_valid_aws_resource_id("vpc-1234567890abcdef")
        assert is_valid_aws_resource_id("i-abc12345")
        assert not is_valid_aws_resource_id("invalid-123")
        assert not is_valid_aws_resource_id("vpc")

    def test_is_valid_account_id(self):
        """Test account ID validation."""
        assert is_valid_account_id("123456789012")
        assert not is_valid_account_id("12345678901")
        assert not is_valid_account_id("abc123456789")

    def test_is_valid_ip(self):
        """Test IP validation."""
        assert is_valid_ip("192.168.1.1")
        assert is_valid_ip("10.0.0.1")
        assert is_valid_ip("0.0.0.0")
        assert is_valid_ip("255.255.255.255")
        assert not is_valid_ip("256.1.1.1")
        assert not is_valid_ip("192.168.1")
        assert not is_valid_ip("abc.def.ghi.jkl")


class TestPerformance:
    """Test pattern matching performance."""

    def test_precompiled_patterns_faster(self):
        """Test that pre-compiled patterns are reusable."""

        text = "vpc-123abc456def i-456abc789def sg-789abc123def " * 1000

        # Pre-compiled pattern can be reused
        results1 = AWS_RESOURCE_PATTERN.findall(text)
        results2 = AWS_RESOURCE_PATTERN.findall(text)

        # Should find same results
        assert results1 == results2
        assert len(results1) > 0
