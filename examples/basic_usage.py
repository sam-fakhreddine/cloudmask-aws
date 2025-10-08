"""Basic CloudMask usage examples."""

from cloudmask import CloudMask, CloudUnmask, Config, anonymize, unanonymize

# Example 1: Simple anonymization
print("=" * 50)
print("Example 1: Simple Anonymization")
print("=" * 50)

mask = CloudMask(seed="my-secret-seed")
text = """
Infrastructure Overview:
- VPC: vpc-1234567890abcdef
- Instance: i-0987654321fedcba
- Security Group: sg-abcdef123456
- Account: 123456789012
- IP: 10.0.1.50
"""

anonymized = mask.anonymize(text)
print("Original:")
print(text)
print("\nAnonymized:")
print(anonymized)

# Example 2: Anonymization with company names
print("\n" + "=" * 50)
print("Example 2: With Company Names")
print("=" * 50)

config = Config(company_names=["Acme Corp", "Example Inc"], seed="company-seed")
mask2 = CloudMask(config=config)

text2 = """
Acme Corp is running infrastructure in AWS:
- Main VPC: vpc-abc123
- Database instance: i-def456
- Partnering with Example Inc
"""

anonymized2 = mask2.anonymize(text2)
print("Original:")
print(text2)
print("\nAnonymized:")
print(anonymized2)

# Example 3: Unanonymization
print("\n" + "=" * 50)
print("Example 3: Unanonymization")
print("=" * 50)

unmask = CloudUnmask(mapping=mask2.get_mapping())
restored = unmask.unanonymize(anonymized2)
print("Restored:")
print(restored)
print("\nMatch original:", restored == text2)

# Example 4: Quick functions
print("\n" + "=" * 50)
print("Example 4: Quick Functions")
print("=" * 50)

original = "Instance i-123 in account 999888777666"
result, mapping = anonymize(original, seed="quick-seed")

print(f"Original: {original}")
print(f"Anonymized: {result}")
print(f"Mapping entries: {len(mapping)}")

restored = unanonymize(result, mapping)
print(f"Restored: {restored}")
