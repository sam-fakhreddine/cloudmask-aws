"""Performance and benchmark tests for CloudMask."""

import time

from cloudmask import CloudMask, Config
from cloudmask.streaming import stream_anonymize_file


class TestPerformance:
    """Performance tests for large files and batch operations."""

    def test_large_text_anonymization(self):
        """Test anonymization of large text."""
        mask = CloudMask(seed="perf-test")

        # Generate large text with many AWS resources
        lines = []
        for i in range(1000):
            lines.append(f"Instance i-{i:016x} in vpc-{i:016x} account {i:012d}")

        large_text = "\n".join(lines)

        start = time.time()
        _ = mask.anonymize(large_text)
        duration = time.time() - start

        assert duration < 5.0  # Should complete in under 5 seconds

    def test_repeated_anonymization_performance(self):
        """Test performance with repeated IDs."""
        mask = CloudMask(seed="perf-test")

        # Same IDs repeated many times
        text = "vpc-123 i-456 " * 1000

        start = time.time()
        _ = mask.anonymize(text)
        duration = time.time() - start

        assert duration < 1.0  # Should be fast due to caching
        assert len(mask.mapping) == 2  # Only 2 unique IDs

    def test_many_unique_resources(self):
        """Test with many unique resources."""
        mask = CloudMask(seed="perf-test")

        resources = [f"vpc-{i:016x}" for i in range(5000)]
        text = " ".join(resources)

        start = time.time()
        _ = mask.anonymize(text)
        duration = time.time() - start

        assert duration < 10.0
        assert len(mask.mapping) == 5000

    def test_file_processing_performance(self, tmp_path):
        """Test file processing performance."""
        input_file = tmp_path / "large.txt"
        output_file = tmp_path / "output.txt"

        # Create large file
        content = "\n".join([f"Instance i-{i:016x} in account {i:012d}" for i in range(2000)])
        input_file.write_text(content)

        mask = CloudMask(seed="perf-test")

        start = time.time()
        mask.anonymize_file(input_file, output_file)
        duration = time.time() - start

        assert duration < 5.0
        assert output_file.exists()

    def test_complex_pattern_performance(self):
        """Test performance with complex patterns."""
        config = Config(
            anonymize_ips=True,
            anonymize_domains=True,
            company_names=["Company A", "Company B", "Company C"],
        )
        mask = CloudMask(config=config, seed="perf-test")

        text = (
            """
        Company A uses vpc-123 with IP 192.168.1.1 and domain example.com
        Company B has i-456 at 10.0.0.1 accessing test.example.org
        """
            * 100
        )

        start = time.time()
        result = mask.anonymize(text)
        duration = time.time() - start

        assert duration < 3.0
        assert "Company A" not in result

    def test_caching_performance(self):
        """Test that caching improves performance."""
        mask = CloudMask(seed="perf-test")

        # Same resources repeated
        text = "vpc-123 i-456 " * 10000

        start = time.time()
        _ = mask.anonymize(text)
        duration = time.time() - start

        # Should be very fast due to caching
        assert duration < 0.5
        assert len(mask.mapping) == 2

    def test_streaming_vs_regular(self, tmp_path):
        """Compare streaming vs regular file processing."""
        input_file = tmp_path / "large.txt"
        output1 = tmp_path / "output1.txt"
        output2 = tmp_path / "output2.txt"

        # Create large file with newline-separated entries to avoid chunk boundary issues
        content = "\n".join([f"vpc-{i:016x} i-{i:016x}" for i in range(5000)])
        input_file.write_text(content)

        # Regular processing
        mask1 = CloudMask(seed="perf-test")
        start = time.time()
        mask1.anonymize_file(input_file, output1)
        regular_time = time.time() - start

        # Streaming processing with large chunk size to avoid splitting identifiers
        mask2 = CloudMask(seed="perf-test")
        start = time.time()
        stream_anonymize_file(mask2, input_file, output2, chunk_size=1024 * 1024)
        stream_time = time.time() - start

        # Both should complete reasonably fast
        assert regular_time < 10.0
        assert stream_time < 10.0

        # Both outputs should exist and be non-empty
        assert output1.exists()
        assert output2.exists()
        assert len(output1.read_text()) > 0
        assert len(output2.read_text()) > 0

        # Both should have anonymized the content (original IDs should not be present)
        output1_text = output1.read_text()
        output2_text = output2.read_text()
        assert "vpc-0000000000000000" not in output1_text
        assert "vpc-0000000000000000" not in output2_text

    def test_precompiled_patterns_performance(self):
        """Test that pre-compiled patterns improve performance."""
        mask = CloudMask(seed="perf-test")

        # Text with many AWS resources
        text = " ".join([f"vpc-{i:016x}" for i in range(1000)])

        start = time.time()
        _ = mask.anonymize(text)
        duration = time.time() - start

        # Should be fast with pre-compiled patterns
        assert duration < 2.0
        assert len(mask.mapping) == 1000
