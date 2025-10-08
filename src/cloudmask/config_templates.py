"""Configuration templates for common use cases."""

from pathlib import Path

# Template configurations
TEMPLATES = {
    "minimal": """# Minimal CloudMask Configuration
seed: my-secret-seed
preserve_prefixes: true
anonymize_ips: false
anonymize_domains: false
company_names: []
custom_patterns: []
""",
    "standard": """# Standard CloudMask Configuration
seed: my-secret-seed
preserve_prefixes: true
anonymize_ips: true
anonymize_domains: false

company_names:
  - Acme Corp
  - Example Inc

custom_patterns: []
""",
    "comprehensive": """# Comprehensive CloudMask Configuration
seed: my-secret-seed
preserve_prefixes: true
anonymize_ips: true
anonymize_domains: true

company_names:
  - Acme Corp
  - Example Inc
  - MyCompany LLC

custom_patterns:
  - pattern: '\\bTICKET-\\d{4,6}\\b'
    name: ticket
  - pattern: '\\bPROJ-[A-Z0-9]+'
    name: project
""",
    "security-focused": """# Security-Focused Configuration
seed: use-strong-random-seed-here
preserve_prefixes: false  # Maximum anonymization
anonymize_ips: true
anonymize_domains: true

company_names:
  - YourCompany

custom_patterns:
  - pattern: '\\b[A-Z]{2,}-\\d{3,}\\b'
    name: internal_id
""",
}


def get_template(name: str) -> str:
    """Get configuration template by name.

    Args:
        name: Template name (minimal, standard, comprehensive, security-focused)

    Returns:
        Template content as string

    Raises:
        KeyError: If template name not found
    """
    if name not in TEMPLATES:
        available = ", ".join(TEMPLATES.keys())
        raise KeyError(f"Unknown template '{name}'. Available: {available}")

    return TEMPLATES[name]


def list_templates() -> list[str]:
    """List available template names."""
    return list(TEMPLATES.keys())


def save_template(name: str, path: Path) -> None:
    """Save template to file.

    Args:
        name: Template name
        path: Output file path
    """
    template = get_template(name)
    path.write_text(template)
