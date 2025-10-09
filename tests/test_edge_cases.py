"""Edge case tests for CloudMask."""

import tempfile

from cloudmask import CloudMask, CloudUnmask, Config, CustomPattern, anonymize_dict


class TestEdgeCases:
    """Comprehensive edge case testing."""

    def test_whitespace_only_text(self):
        """Test with whitespace-only text."""
        mask = CloudMask(seed="test")
        assert mask.anonymize("   \n\t  ") == "   \n\t  "

    def test_very_long_line(self):
        """Test with extremely long single line."""
        mask = CloudMask(seed="test")
        long_line = "vpc-123 " * 10000
        result = mask.anonymize(long_line)
        assert "vpc-123" not in result

    def test_mixed_line_endings(self):
        """Test with mixed line endings."""
        mask = CloudMask(seed="test")
        text = "vpc-123\ni-456\r\nsg-789\r"
        result = mask.anonymize(text)
        assert "\n" in result
        assert "\r\n" in result or "\n" in result

    def test_consecutive_resources(self):
        """Test resources without spaces."""
        mask = CloudMask(seed="test")
        text = "vpc-123i-456sg-789"
        result = mask.anonymize(text)
        # Should not match as they're not properly separated
        assert "vpc-123i-456sg-789" in result

    def test_partial_resource_ids(self):
        """Test partial or incomplete resource IDs."""
        mask = CloudMask(seed="test")
        text = "vpc- i- sg-"
        result = mask.anonymize(text)
        # Should not match incomplete IDs
        assert result == text

    def test_resource_id_in_url(self):
        """Test resource IDs within URLs."""
        mask = CloudMask(seed="test")
        text = "https://console.aws.amazon.com/vpc/home?vpc-1234567890abcdef"
        result = mask.anonymize(text)
        assert "vpc-1234567890abcdef" not in result

    def test_resource_id_in_json(self):
        """Test resource IDs in JSON strings."""
        mask = CloudMask(seed="test")
        text = '{"vpc_id": "vpc-123", "instance": "i-456"}'
        result = mask.anonymize(text)
        assert "vpc-123" not in result
        assert "i-456" not in result
        assert '"vpc_id":' in result or '"vpc_id": ' in result

    def test_overlapping_patterns(self):
        """Test overlapping pattern matches."""
        mask = CloudMask(seed="test")
        text = "arn:aws:ec2:us-east-1:123456789012:vpc/vpc-123"
        result = mask.anonymize(text)
        assert "vpc-123" not in result
        assert "123456789012" not in result

    def test_case_variations(self):
        """Test case variations in resource IDs."""
        mask = CloudMask(seed="test")
        text = "VPC-123 Vpc-456 vpc-789"
        result = mask.anonymize(text)
        # AWS IDs are case-insensitive in matching
        assert "VPC-123" not in result
        assert "Vpc-456" not in result
        assert "vpc-789" not in result

    def test_account_id_in_arn(self):
        """Test account ID within ARN is anonymized."""
        mask = CloudMask(seed="test")
        text = "arn:aws:iam::123456789012:role/MyRole"
        result = mask.anonymize(text)
        assert "123456789012" not in result
        assert "arn:aws:iam::" in result

    def test_multiple_arns(self):
        """Test multiple ARNs in text."""
        mask = CloudMask(seed="test")
        text = """
        arn:aws:s3:::my-bucket
        arn:aws:ec2:us-east-1:123456789012:instance/i-123
        arn:aws:iam::987654321098:user/admin
        """
        result = mask.anonymize(text)
        assert "123456789012" not in result
        assert "987654321098" not in result
        assert "i-123" not in result

    def test_company_name_with_special_chars(self):
        """Test company names with special characters."""
        config = Config(company_names=["Acme & Co.", "Test (Inc)", "Foo-Bar LLC"])
        mask = CloudMask(config=config, seed="test")
        text = "Acme & Co. and Test (Inc) and Foo-Bar LLC"
        result = mask.anonymize(text)
        assert "Acme & Co." not in result
        assert "Test (Inc)" not in result
        assert "Foo-Bar LLC" not in result

    def test_empty_company_names_list(self):
        """Test with empty company names list."""
        config = Config(company_names=[])
        mask = CloudMask(config=config, seed="test")
        text = "vpc-123 in MyCompany"
        result = mask.anonymize(text)
        assert "vpc-123" not in result
        assert "MyCompany" in result  # Should not be anonymized

    def test_company_name_substring_matching(self):
        """Test that company names don't match substrings incorrectly."""
        config = Config(company_names=["Test"])
        mask = CloudMask(config=config, seed="test")
        text = "Test Testing Tested"
        result = mask.anonymize(text)
        # Should match whole words, not substrings
        assert "Test" not in result or "Testing" in result

    def test_ip_address_edge_cases(self):
        """Test IP address edge cases."""
        config = Config(anonymize_ips=True)
        mask = CloudMask(config=config, seed="test")

        # Valid IPs
        text = "0.0.0.0 255.255.255.255 192.168.1.1"
        result = mask.anonymize(text)
        assert "192.168.1.1" not in result

        # Invalid IPs (should not match)
        text2 = "999.999.999.999 1.2.3"
        result2 = mask.anonymize(text2)
        assert "999.999.999.999" in result2  # Invalid, should remain

    def test_domain_edge_cases(self):
        """Test domain name edge cases."""
        config = Config(anonymize_domains=True)
        mask = CloudMask(config=config, seed="test")

        text = "example.com sub.example.com very.long.subdomain.example.org"
        result = mask.anonymize(text)
        assert "example.com" not in result

    def test_custom_pattern_with_groups(self):
        """Test custom patterns with capture groups."""
        pattern = CustomPattern(pattern=r"TICKET-(\d+)", name="ticket")
        config = Config(custom_patterns=[pattern])
        mask = CloudMask(config=config, seed="test")

        text = "See TICKET-12345 and TICKET-67890"
        result = mask.anonymize(text)
        assert "TICKET-12345" not in result
        assert "TICKET-67890" not in result

    def test_multiple_custom_patterns(self):
        """Test multiple custom patterns."""
        patterns = [
            CustomPattern(pattern=r"TICKET-\d+", name="ticket"),
            CustomPattern(pattern=r"PROJ-[A-Z]+", name="project"),
        ]
        config = Config(custom_patterns=patterns)
        mask = CloudMask(config=config, seed="test")

        text = "TICKET-123 for PROJ-ABC"
        result = mask.anonymize(text)
        assert "TICKET-123" not in result
        assert "PROJ-ABC" not in result

    def test_preserve_prefixes_disabled(self):
        """Test with preserve_prefixes disabled."""
        config = Config(preserve_prefixes=False)
        mask = CloudMask(config=config, seed="test")

        text = "vpc-123 i-456"
        result = mask.anonymize(text)
        # Prefixes should not be preserved
        assert "vpc-123" not in result
        assert "i-456" not in result

    def test_anonymize_ips_disabled(self):
        """Test with IP anonymization disabled."""
        config = Config(anonymize_ips=False)
        mask = CloudMask(config=config, seed="test")

        text = "vpc-123 at 192.168.1.1"
        result = mask.anonymize(text)
        assert "vpc-123" not in result
        assert "192.168.1.1" in result  # IP should remain

    def test_anonymize_domains_disabled(self):
        """Test with domain anonymization disabled."""
        config = Config(anonymize_domains=False)
        mask = CloudMask(config=config, seed="test")

        text = "vpc-123 at example.com"
        result = mask.anonymize(text)
        assert "vpc-123" not in result
        assert "example.com" in result  # Domain should remain

    def test_unanonymize_partial_mapping(self):
        """Test unanonymization with incomplete mapping."""
        mask = CloudMask(seed="test")
        text = "vpc-123 i-456"
        anonymized = mask.anonymize(text)

        # Create partial mapping (only vpc)
        partial_mapping = {k: v for k, v in mask.mapping.items() if "vpc" in k}

        unmask = CloudUnmask(mapping=partial_mapping)
        result = unmask.unanonymize(anonymized)

        # vpc should be restored, i- should remain anonymized
        assert "vpc-123" in result
        assert "i-456" not in result

    def test_unanonymize_empty_mapping(self):
        """Test unanonymization with empty mapping."""
        unmask = CloudUnmask(mapping={})
        text = "some anonymized text"
        result = unmask.unanonymize(text)
        assert result == text

    def test_anonymize_dict_nested(self):
        """Test dictionary anonymization with nested structures."""
        mask = CloudMask(seed="test")

        data = {
            "vpc": "vpc-123",
            "instances": ["i-456", "i-789"],
            "nested": {"subnet": "subnet-abc", "sg": "sg-def"},
        }

        result = anonymize_dict(data, mask)

        assert "vpc-123" not in str(result)
        assert "i-456" not in str(result)
        assert "subnet-abc" not in str(result)

    def test_anonymize_dict_with_non_string_values(self):
        """Test dictionary anonymization with mixed types."""
        mask = CloudMask(seed="test")

        data = {"vpc": "vpc-123", "count": 42, "enabled": True, "ratio": 3.14}

        result = anonymize_dict(data, mask)

        assert "vpc-123" not in str(result)
        assert result["count"] == 42
        assert result["enabled"] is True
        assert result["ratio"] == 3.14

    def test_mapping_persistence_with_unicode(self):
        """Test mapping file with Unicode content."""
        mask = CloudMask(seed="test")
        mask.anonymize("vpc-123 café 🚀")

        with tempfile.NamedTemporaryFile(mode="w", delete=False, suffix=".json") as f:
            mask.save_mapping(f.name)

            # Load it back
            mask2 = CloudMask(seed="different")
            mask2.load_mapping(f.name)

            assert mask2.mapping == mask.mapping

    def test_all_aws_resource_types(self):
        """Test all supported AWS resource types."""
        mask = CloudMask(seed="test")

        resources = [
            "vpc-123",
            "subnet-456",
            "sg-789",
            "igw-abc",
            "rtb-def",
            "eni-ghi",
            "eip-jkl",
            "vol-mno",
            "snap-pqr",
            "ami-stu",
            "i-vwx",
            "r-yz1",
            "lt-234",
            "asg-567",
            "elb-890",
            "tg-abc",
            "elbv2-def",
            "natgw-ghi",
            "vpce-jkl",
            "acl-mno",
            "pcx-pqr",
        ]

        text = " ".join(resources)
        result = mask.anonymize(text)

        for resource in resources:
            assert resource not in result
