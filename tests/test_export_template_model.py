"""Tests for ExportTemplate model, validation, and dictionary serialization/deserialization."""

from enums import TargetType
from models.export_template import ExportTemplate


def test_export_template_defaults():
    """Verify default field values of ExportTemplate."""
    tmpl = ExportTemplate()
    assert tmpl.template_id == ""
    assert tmpl.display_name == ""
    assert tmpl.target_type == TargetType.CLIPBOARD_TEXT
    assert tmpl.applicable_cases == []
    assert tmpl.description == ""
    assert tmpl.required_schema_fields == []
    assert tmpl.template_string == ""


def test_export_template_validation_errors():
    """Verify validate() flags missing template_id, display_name, and template_string."""
    tmpl = ExportTemplate()
    errors = tmpl.validate()
    assert len(errors) == 3
    assert "Template ID is required." in errors
    assert "Display name is required." in errors
    assert "Template string cannot be empty." in errors

    # Whitespace-only fields are also treated as missing
    tmpl_ws = ExportTemplate(template_id="  ", display_name="\t", template_string="\n")
    errors_ws = tmpl_ws.validate()
    assert len(errors_ws) == 3


def test_export_template_validation_success():
    """Verify validate() returns empty list for valid template."""
    tmpl = ExportTemplate(
        template_id="tmpl_jira_01",
        display_name="Jira Issue Export",
        template_string="h1. Fall {case_id}\n\n{description}",
    )
    assert tmpl.validate() == []


def test_export_template_to_dict_and_from_dict():
    """Verify to_dict and from_dict roundtrip preserves all attributes."""
    orig = ExportTemplate(
        template_id="tmpl_custom",
        display_name="Custom Markdown",
        target_type=TargetType.FILE_EXPORT,
        applicable_cases=["schema_hotline", "schema_technik"],
        description="Markdown export for external partners",
        required_schema_fields=["kundennr", "kontakt"],
        template_string="# Fall {{ case.case_id }}\n{{ case.customer.practice_name }}",
    )

    data = orig.to_dict()
    assert data["template_id"] == "tmpl_custom"
    assert data["target_type"] == TargetType.FILE_EXPORT
    assert data["applicable_cases"] == ["schema_hotline", "schema_technik"]

    loaded = ExportTemplate.from_dict(data)
    assert loaded.template_id == orig.template_id
    assert loaded.display_name == orig.display_name
    assert loaded.target_type == orig.target_type
    assert loaded.applicable_cases == orig.applicable_cases
    assert loaded.description == orig.description
    assert loaded.required_schema_fields == orig.required_schema_fields
    assert loaded.template_string == orig.template_string


def test_export_template_from_dict_defaults():
    """Verify from_dict gracefully handles empty dictionary."""
    loaded = ExportTemplate.from_dict({})
    assert loaded.template_id == ""
    assert loaded.display_name == ""
    assert loaded.target_type == TargetType.CLIPBOARD_TEXT
    assert loaded.applicable_cases == []
    assert loaded.required_schema_fields == []
    assert loaded.template_string == ""
