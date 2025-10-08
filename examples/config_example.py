"""Configuration flexibility examples."""

import os
from pathlib import Path

from cloudmask import list_templates, load_config, save_template, validate_config


def environment_variables_example() -> None:
    """Example using environment variables."""
    print("=== Environment Variables Example ===")

    # Set environment variables
    os.environ["CLOUDMASK_SEED"] = "my-env-seed"
    os.environ["CLOUDMASK_ANONYMIZE_IPS"] = "true"
    os.environ["CLOUDMASK_COMPANY_NAMES"] = "Acme Corp, Example Inc"

    # Load config from environment
    config = load_config(use_env=True)

    print(f"Seed from env: {config.seed}")
    print(f"Anonymize IPs: {config.anonymize_ips}")
    print(f"Companies: {config.company_names}")
    print()


def multiple_formats_example() -> None:
    """Example loading from different formats."""
    print("=== Multiple Formats Example ===")

    # Create JSON config
    json_config = Path("config.json")
    json_config.write_text('{"seed": "json-seed", "anonymize_ips": true}')

    config = load_config(json_config, format="json", use_env=False)
    print(f"Loaded from JSON: seed={config.seed}")

    json_config.unlink()
    print()


def template_example() -> None:
    """Example using configuration templates."""
    print("=== Template Example ===")

    # List available templates
    print("Available templates:")
    for template in list_templates():
        print(f"  - {template}")

    # Save a template
    config_file = Path("my_config.yaml")
    save_template("standard", config_file)
    print(f"\nSaved 'standard' template to {config_file}")

    # Load and use it
    config = load_config(config_file, use_env=False)
    print(f"Loaded config: seed={config.seed}")

    config_file.unlink()
    print()


def validation_example() -> None:
    """Example validating configuration."""
    print("=== Validation Example ===")

    from cloudmask import Config

    # Valid config
    valid_config = Config(seed="strong-seed-123")
    issues = validate_config(valid_config)
    print(f"Valid config issues: {len(issues)}")

    # Invalid config
    invalid_config = Config(seed="short")
    issues = validate_config(invalid_config)
    print(f"Invalid config issues: {len(issues)}")
    for issue in issues:
        print(f"  - {issue}")
    print()


def priority_example() -> None:
    """Example showing configuration priority."""
    print("=== Configuration Priority Example ===")

    # Create file config
    file_config = Path("file_config.yaml")
    file_config.write_text("seed: file-seed\nanonymize_ips: false\n")

    # Set environment variable
    os.environ["CLOUDMASK_SEED"] = "env-seed"

    # Load with env (env overrides file)
    config_with_env = load_config(file_config, use_env=True)
    print(f"With env vars: seed={config_with_env.seed}")

    # Load without env (file only)
    config_without_env = load_config(file_config, use_env=False)
    print(f"Without env vars: seed={config_without_env.seed}")

    file_config.unlink()
    print()


if __name__ == "__main__":
    print("CloudMask Configuration Flexibility Demo\n")

    environment_variables_example()
    multiple_formats_example()
    template_example()
    validation_example()
    priority_example()

    print("Demo complete!")
