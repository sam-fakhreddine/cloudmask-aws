"""Example demonstrating security features."""

from pathlib import Path

from cloudmask import (
    BatchRateLimiter,
    CloudMask,
    CloudUnmask,
    Config,
    load_encrypted_mapping,
    save_encrypted_mapping,
)


def basic_encryption_example() -> None:
    """Demonstrate basic encryption of mapping files."""
    print("=== Basic Encryption Example ===\n")

    # Create anonymizer with strong seed
    config = Config(seed="strong-seed-12345")
    mask = CloudMask(config=config)

    # Anonymize some data
    text = """
    Instance i-1234567890abcdef in vpc-abcdef123456
    Account: 123456789012
    Company: Acme Corp
    """

    anonymized = mask.anonymize(text)
    print(f"Original:\n{text}")
    print(f"\nAnonymized:\n{anonymized}")

    # Save encrypted mapping
    password = "secure-password-123"
    mapping_file = Path("encrypted_mapping.bin")

    save_encrypted_mapping(mask.mapping, mapping_file, password)
    print(f"\n✓ Encrypted mapping saved to: {mapping_file}")

    # Load and unanonymize
    loaded_mapping = load_encrypted_mapping(mapping_file, password)
    unmask = CloudUnmask(mapping=loaded_mapping)
    restored = unmask.unanonymize(anonymized)

    print(f"\nRestored:\n{restored}")
    print("\n✓ Successfully encrypted, saved, loaded, and decrypted mapping!")

    # Cleanup
    mapping_file.unlink()


def rate_limiting_example() -> None:
    """Demonstrate rate limiting for batch operations."""
    print("\n=== Rate Limiting Example ===\n")

    mask = CloudMask(seed="batch-seed")

    # Create batch of items to process
    items = [f"vpc-{i:016x}" for i in range(20)]

    print(f"Processing {len(items)} items with rate limiting...")

    # Process with rate limiting (1000 items/second)
    limiter = BatchRateLimiter(max_items_per_second=1000)
    results = limiter.process_batch(items, mask.anonymize)

    print(f"✓ Processed {len(results)} items")
    print(f"Sample results: {results[:3]}")


def validation_example() -> None:
    """Demonstrate input validation."""
    print("\n=== Input Validation Example ===\n")

    # Valid config
    try:
        _ = Config(seed="valid-seed-123")
        print("✓ Valid config created")
    except ValueError as e:
        print(f"✗ Config validation failed: {e}")

    # Invalid config - seed too short
    try:
        _ = Config(seed="short")
        print("✗ Should have failed validation")
    except ValueError as e:
        print(f"✓ Correctly rejected short seed: {e}")

    # Invalid config - empty seed
    try:
        _ = Config(seed="")
        print("✗ Should have failed validation")
    except ValueError as e:
        print(f"✓ Correctly rejected empty seed: {e}")


def main() -> None:
    """Run all examples."""
    basic_encryption_example()
    rate_limiting_example()
    validation_example()

    print("\n" + "=" * 50)
    print("All security examples completed successfully!")
    print("=" * 50)


if __name__ == "__main__":
    main()
