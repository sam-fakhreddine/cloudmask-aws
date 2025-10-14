"""Configuration templates for common use cases."""

from pathlib import Path

# Template configurations
_TEMPLATES = {
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


def _get_template(name: str) -> str:
    """Get configuration template by name."""
    if name not in _TEMPLATES:
        available = ", ".join(_TEMPLATES.keys())
        raise KeyError(f"Unknown template '{name}'. Available: {available}")
    return _TEMPLATES[name]


def _list_templates() -> list[str]:
    """List available template names."""
    return list(_TEMPLATES.keys())


def _save_template(name: str, path: Path) -> None:
    """Save template to file."""
    template = _get_template(name)
    path.write_text(template)


class _ConfigTemplates:
    """Configuration template management."""

    def Get(self, name: str) -> str:
        """Get configuration template by name.

        Args:
            name: Template name (minimal, standard, comprehensive, security-focused)
        """
        return _get_template(name)

    @property
    def List(self) -> list[str]:
        """List available template names."""
        return _list_templates()

    def Save(self, name: str, path: Path) -> None:
        """Save template to file.

        Args:
            name: Template name
            path: Output file path
        """
        _save_template(name, path)


# Singleton instance
ConfigTemplates = _ConfigTemplates()

# Backward compatibility
get_template = _get_template
list_templates = _list_templates
save_template = _save_template
