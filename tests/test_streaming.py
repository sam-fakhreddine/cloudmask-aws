"""Tests for streaming functionality."""

import pytest

from cloudmask import CloudMask, CloudUnmask
from cloudmask.exceptions import FileOperationError
from cloudmask.io.streaming import stream_anonymize_file, stream_unanonymize_file


class TestStreaming:
    """Test streaming file processing."""

    def test_stream_anonymize_small_file(self, tmp_path):
        """Test streaming with small file."""
        input_file = tmp_path / "input.txt"
        output_file = tmp_path / "output.txt"

        content = "Instance i-1234567890abcdef0 in vpc-abc123def456\n" * 10
        input_file.write_text(content)

        mask = CloudMask(seed="test")
        count = stream_anonymize_file(mask, input_file, output_file)

        assert output_file.exists()
        assert count >= 1
        result = output_file.read_text()
        assert "i-1234567890abcdef0" not in result

    def test_stream_anonymize_large_file(self, tmp_path):
        """Test streaming with large file."""
        input_file = tmp_path / "large.txt"
        output_file = tmp_path / "output.txt"

        # Create 1MB file
        lines = [f"Instance i-{i:016x} in vpc-{i:016x}\n" for i in range(10000)]
        input_file.write_text("".join(lines))

        mask = CloudMask(seed="test")
        count = stream_anonymize_file(mask, input_file, output_file, chunk_size=4096)

        assert output_file.exists()
        assert count > 0
        result = output_file.read_text()
        assert "i-0000000000000000" not in result

    def test_stream_unanonymize(self, tmp_path):
        """Test streaming unanonymization."""
        input_file = tmp_path / "input.txt"
        anon_file = tmp_path / "anon.txt"
        output_file = tmp_path / "output.txt"

        original = "Instance i-1234567890abcdef0 in vpc-abc123def456"
        input_file.write_text(original)

        # Anonymize
        mask = CloudMask(seed="test")
        stream_anonymize_file(mask, input_file, anon_file)

        # Unanonymize
        unmask = CloudUnmask(mapping=mask.mapping)
        count = stream_unanonymize_file(unmask, anon_file, output_file)

        assert output_file.exists()
        assert count >= 1
        assert output_file.read_text() == original

    def test_stream_with_progress(self, tmp_path):
        """Test streaming with progress bar (if tqdm available)."""
        input_file = tmp_path / "input.txt"
        output_file = tmp_path / "output.txt"

        content = "vpc-123abc456def i-456abc789def\n" * 100
        input_file.write_text(content)

        mask = CloudMask(seed="test")

        # Should not fail even if tqdm not available
        count = stream_anonymize_file(mask, input_file, output_file, show_progress=True)

        assert output_file.exists()
        assert count >= 1

    def test_stream_nonexistent_file(self, tmp_path):
        """Test streaming with nonexistent file."""
        input_file = tmp_path / "nonexistent.txt"
        output_file = tmp_path / "output.txt"

        mask = CloudMask(seed="test")

        with pytest.raises(FileOperationError):
            stream_anonymize_file(mask, input_file, output_file)

    def test_stream_preserves_newlines(self, tmp_path):
        """Test that streaming preserves line structure."""
        input_file = tmp_path / "input.txt"
        output_file = tmp_path / "output.txt"

        content = "Line 1: vpc-123\nLine 2: i-456\n\nLine 4: sg-789\n"
        input_file.write_text(content)

        mask = CloudMask(seed="test")
        stream_anonymize_file(mask, input_file, output_file)

        result = output_file.read_text()
        assert result.count("\n") == content.count("\n")
