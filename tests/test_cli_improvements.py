"""Tests for CLI improvements."""

import json
import subprocess
import sys

import pytest


@pytest.fixture
def sample_files(tmp_path):
    """Create sample files for batch processing."""
    files = []
    for i in range(3):
        file = tmp_path / f"input_{i}.txt"
        file.write_text(f"vpc-{i}234567890abcd i-{i}234567890abcdef0\n")
        files.append(file)
    return files


@pytest.fixture
def sample_mapping(tmp_path):
    """Create sample mapping file."""
    mapping_file = tmp_path / "mapping.json"
    mapping = {
        "vpc-123": "vpc-anon123",
        "i-456": "i-anon456",
        "123456789012": "987654321098",
    }
    mapping_file.write_text(json.dumps(mapping))
    return mapping_file


def test_verbose_flag(tmp_path):
    """Test verbose flag."""
    input_file = tmp_path / "input.txt"
    output_file = tmp_path / "output.txt"
    mapping_file = tmp_path / "mapping.json"

    input_file.write_text("vpc-123 i-456")

    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "cloudmask.cli",
            "--verbose",
            "anonymize",
            "-i",
            str(input_file),
            "-o",
            str(output_file),
            "-m",
            str(mapping_file),
        ],
        capture_output=True,
        text=True,
    )

    assert result.returncode == 0


def test_quiet_flag(tmp_path):
    """Test quiet flag."""
    input_file = tmp_path / "input.txt"
    output_file = tmp_path / "output.txt"
    mapping_file = tmp_path / "mapping.json"

    input_file.write_text("vpc-123 i-456")

    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "cloudmask.cli",
            "--quiet",
            "anonymize",
            "-i",
            str(input_file),
            "-o",
            str(output_file),
            "-m",
            str(mapping_file),
        ],
        capture_output=True,
        text=True,
    )

    assert result.returncode == 0
    # Quiet mode should suppress most output but still show results
    # Just verify it ran successfully


def test_validate_config(tmp_path):
    """Test config validation."""
    config_file = tmp_path / "config.yaml"
    config_file.write_text(
        """
company_names:
  - Test Corp
seed: test-seed-123
"""
    )

    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "cloudmask.cli",
            "validate",
            "-c",
            str(config_file),
        ],
        capture_output=True,
        text=True,
    )

    assert result.returncode == 0
    assert "valid" in result.stdout.lower()


def test_validate_mapping(tmp_path, sample_mapping):
    """Test mapping validation."""
    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "cloudmask.cli",
            "validate",
            "-m",
            str(sample_mapping),
        ],
        capture_output=True,
        text=True,
    )

    assert result.returncode == 0
    assert "valid" in result.stdout.lower()
    assert "Total mappings: 3" in result.stdout


def test_validate_invalid_mapping(tmp_path):
    """Test validation of invalid mapping."""
    invalid_mapping = tmp_path / "invalid.json"
    invalid_mapping.write_text("not a json object")

    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "cloudmask.cli",
            "validate",
            "-m",
            str(invalid_mapping),
        ],
        capture_output=True,
        text=True,
    )

    assert result.returncode == 1


def test_batch_processing(tmp_path, sample_files):
    """Test batch processing command."""
    output_dir = tmp_path / "output"
    mapping_file = tmp_path / "mapping.json"

    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "cloudmask.cli",
            "batch",
            *[str(f) for f in sample_files],
            "-o",
            str(output_dir),
            "-m",
            str(mapping_file),
        ],
        capture_output=True,
        text=True,
    )

    assert result.returncode == 0
    assert output_dir.exists()
    assert mapping_file.exists()

    # Check output files
    for input_file in sample_files:
        output_file = output_dir / input_file.name
        assert output_file.exists()
        assert output_file.read_text() != input_file.read_text()

    # Check summary
    assert "Batch processing complete" in result.stdout
    assert "Total files: 3" in result.stdout
    assert "Processed: 3" in result.stdout


def test_batch_processing_with_progress(tmp_path, sample_files):
    """Test batch processing with progress bar."""
    output_dir = tmp_path / "output"
    mapping_file = tmp_path / "mapping.json"

    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "cloudmask.cli",
            "batch",
            *[str(f) for f in sample_files],
            "-o",
            str(output_dir),
            "-m",
            str(mapping_file),
            "--progress",
        ],
        capture_output=True,
        text=True,
    )

    assert result.returncode == 0


def test_batch_processing_quiet(tmp_path, sample_files):
    """Test batch processing in quiet mode."""
    output_dir = tmp_path / "output"
    mapping_file = tmp_path / "mapping.json"

    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "cloudmask.cli",
            "--quiet",
            "batch",
            *[str(f) for f in sample_files],
            "-o",
            str(output_dir),
            "-m",
            str(mapping_file),
        ],
        capture_output=True,
        text=True,
    )

    assert result.returncode == 0
    # Quiet mode should have minimal output
    assert len(result.stdout) < 50


def test_stats_command(tmp_path, sample_mapping):
    """Test stats command."""
    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "cloudmask.cli",
            "stats",
            "-m",
            str(sample_mapping),
        ],
        capture_output=True,
        text=True,
    )

    assert result.returncode == 0
    assert "Mapping Statistics" in result.stdout
    assert "Total mappings: 3" in result.stdout
    assert "By category:" in result.stdout


def test_stats_command_detailed(tmp_path, sample_mapping):
    """Test stats command with detailed output."""
    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "cloudmask.cli",
            "stats",
            "-m",
            str(sample_mapping),
            "--detailed",
        ],
        capture_output=True,
        text=True,
    )

    assert result.returncode == 0
    assert "Sample mappings" in result.stdout
    assert "vpc-123" in result.stdout


def test_batch_with_failed_file(tmp_path):
    """Test batch processing with a failed file."""
    output_dir = tmp_path / "output"
    mapping_file = tmp_path / "mapping.json"

    # Create valid and invalid files
    valid_file = tmp_path / "valid.txt"
    valid_file.write_text("vpc-123")

    invalid_file = tmp_path / "nonexistent.txt"

    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "cloudmask.cli",
            "batch",
            str(valid_file),
            str(invalid_file),
            "-o",
            str(output_dir),
            "-m",
            str(mapping_file),
        ],
        capture_output=True,
        text=True,
    )

    # Should fail due to invalid file
    assert result.returncode == 1
    assert "Failed: 1" in result.stdout


def test_validate_no_args():
    """Test validate command without arguments."""
    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "cloudmask.cli",
            "validate",
        ],
        capture_output=True,
        text=True,
    )

    assert result.returncode == 1
    assert "Either --config or --mapping must be specified" in result.stderr


def test_help_messages():
    """Test help messages for new commands."""
    # Test batch help
    result = subprocess.run(
        [sys.executable, "-m", "cloudmask.cli", "batch", "--help"],
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0
    assert "batch" in result.stdout.lower()

    # Test stats help
    result = subprocess.run(
        [sys.executable, "-m", "cloudmask.cli", "stats", "--help"],
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0
    assert "stats" in result.stdout.lower()

    # Test validate help
    result = subprocess.run(
        [sys.executable, "-m", "cloudmask.cli", "validate", "--help"],
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0
    assert "validate" in result.stdout.lower()
