"""Performance features example for CloudMask."""

from pathlib import Path

from cloudmask import CloudMask
from cloudmask.streaming import stream_anonymize_file, stream_unanonymize_file


def basic_caching_example() -> None:
    """Demonstrate caching performance improvement."""
    print("=== Caching Example ===")

    mask = CloudMask(seed="demo-seed")

    # Same resources repeated many times - caching makes this fast
    text = "vpc-123abc456def i-456abc789def " * 1000

    import time

    start = time.time()
    _ = mask.anonymize(text)
    duration = time.time() - start

    print(f"Anonymized {len(text)} characters in {duration:.3f}s")
    print(f"Found {len(mask.mapping)} unique identifiers")
    print(f"Cache efficiency: {len(text.split()) / len(mask.mapping):.1f}x reuse")
    print()


def streaming_example() -> None:
    """Demonstrate streaming for large files."""
    print("=== Streaming Example ===")

    # Create a large test file
    test_file = Path("large_test.txt")
    output_file = Path("large_anonymized.txt")

    # Generate large content
    lines = [f"Instance i-{i:016x} in vpc-{i:016x}\n" for i in range(5000)]
    test_file.write_text("".join(lines))

    print(f"Created test file: {test_file.stat().st_size / 1024:.1f} KB")

    # Stream process with progress
    mask = CloudMask(seed="demo-seed")

    import time

    start = time.time()
    count = stream_anonymize_file(
        mask,
        test_file,
        output_file,
        chunk_size=8192,
        show_progress=False,  # Set to True if tqdm is installed
    )
    duration = time.time() - start

    print(f"Streamed {count} identifiers in {duration:.3f}s")
    print("Memory-efficient processing complete")

    # Cleanup
    test_file.unlink()
    output_file.unlink()
    print()


def pattern_optimization_example() -> None:
    """Demonstrate pre-compiled pattern performance."""
    print("=== Pattern Optimization Example ===")

    from cloudmask.patterns import is_valid_account_id, is_valid_aws_resource_id, is_valid_ip

    # Fast validation with pre-compiled patterns
    test_ids = [
        "vpc-1234567890abcdef",
        "i-abc12345678",
        "123456789012",
        "192.168.1.1",
        "invalid-id",
    ]

    for test_id in test_ids:
        if is_valid_aws_resource_id(test_id):
            print(f"✓ Valid AWS resource: {test_id}")
        elif is_valid_account_id(test_id):
            print(f"✓ Valid account ID: {test_id}")
        elif is_valid_ip(test_id):
            print(f"✓ Valid IP address: {test_id}")
        else:
            print(f"✗ Invalid: {test_id}")
    print()


def combined_example() -> None:
    """Demonstrate combined performance features."""
    print("=== Combined Performance Features ===")

    # Create test file
    test_file = Path("combined_test.txt")
    anon_file = Path("combined_anon.txt")
    restored_file = Path("combined_restored.txt")

    # Generate content with repeated IDs (benefits from caching)
    content = "\n".join(
        ["vpc-abc123def456 i-def789abc123 account 123456789012" for _ in range(1000)]
    )
    test_file.write_text(content)

    # Anonymize with streaming (memory efficient)
    mask = CloudMask(seed="demo-seed")
    count = stream_anonymize_file(mask, test_file, anon_file)
    print(f"Anonymized {count} unique IDs (from {len(content.split())} total tokens)")

    # Unanonymize with streaming
    unmask = CloudMask(seed="demo-seed")
    unmask.mapping = mask.mapping
    from cloudmask import CloudUnmask

    unmask_obj = CloudUnmask(mapping=mask.mapping)
    stream_unanonymize_file(unmask_obj, anon_file, restored_file)

    # Verify
    original = test_file.read_text()
    restored = restored_file.read_text()
    print(f"Restoration successful: {original == restored}")

    # Cleanup
    test_file.unlink()
    anon_file.unlink()
    restored_file.unlink()
    print()


if __name__ == "__main__":
    print("CloudMask Performance Features Demo\n")

    basic_caching_example()
    streaming_example()
    pattern_optimization_example()
    combined_example()

    print("Demo complete!")
