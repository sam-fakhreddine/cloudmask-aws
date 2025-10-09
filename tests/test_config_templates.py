"""Tests for configuration templates."""

import pytest
import yaml

from cloudmask.config_templates import get_template, list_templates, save_template


class TestTemplates:
    """Test configuration templates."""

    def test_list_templates(self):
        """Test listing available templates."""
        templates = list_templates()
        assert len(templates) > 0
        assert "minimal" in templates
        assert "standard" in templates

    def test_get_template(self):
        """Test getting template content."""
        template = get_template("minimal")
        assert "seed:" in template
        assert isinstance(template, str)

    def test_get_invalid_template(self):
        """Test getting non-existent template."""
        with pytest.raises(KeyError):
            get_template("nonexistent")

    def test_save_template(self, tmp_path):
        """Test saving template to file."""
        output_file = tmp_path / "config.yaml"
        save_template("standard", output_file)

        assert output_file.exists()
        content = output_file.read_text()
        assert "seed:" in content

    def test_all_templates_valid(self):
        """Test that all templates are valid YAML."""
        for template_name in list_templates():
            template = get_template(template_name)
            data = yaml.safe_load(template)
            assert isinstance(data, dict)
            assert "seed" in data
