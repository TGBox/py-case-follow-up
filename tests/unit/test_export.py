"""ExportService template rendering: placeholders, required-field validation, force export and overrides."""

import pytest

from models.case import Case, CaseCustomer, Classification, TimelineEntry
from models.export_template import ExportTemplate, TargetType
from models.schema import QuestionSchema, SchemaField
from services.export_service import ExportService

TEMPLATE = ExportTemplate(
    template_id="gitlab_ticket",
    display_name="GitLab Ticket",
    applicable_cases=["schema_1"],
    required_schema_fields=["billing_quarter", "error_code"],
    template_string=(
        "### Support: {{ customer.practice_name }} ({{ customer.customer_id }})\n"
        "* Quartal: {{ form_data.billing_quarter }}\n"
        "* Fehler: {{ form_data.error_code }}\n"
        "Author: {{ created_by }}"
    ),
)
SCHEMA = QuestionSchema(schema_id="schema_1", display_name="Test Schema", fields=[
    SchemaField(field_id="billing_quarter", label="Quartal", required=True),
    SchemaField(field_id="error_code", label="Fehlercode", required=True),
])


def _case(form_data):
    return Case(case_id="T-100", created_by="Daniel Rösch",
                customer=CaseCustomer(customer_id="K-100", practice_name="Praxis Ulm"),
                classification=Classification(schema_id="schema_1"), form_data=dict(form_data))


@pytest.fixture
def export_service(storage):
    return ExportService(storage)


def test_render_complete_case(export_service):
    ok, missing, text = export_service.render_template(
        _case({"billing_quarter": "2026-Q2", "error_code": "ERR_01"}), TEMPLATE, SCHEMA)
    assert ok is True and missing == []
    for part in ("Praxis Ulm", "K-100", "2026-Q2", "ERR_01", "Daniel Rösch"):
        assert part in text


def test_missing_required_field_blocks_unless_forced():
    service = ExportService()
    case = _case({"billing_quarter": "2026-Q2"})
    assert service.render_template(case, TEMPLATE, SCHEMA, force_export=False) == (False, ["error_code"], "")

    ok, missing, text = service.render_template(case, TEMPLATE, SCHEMA, force_export=True)
    assert ok is True and missing == ["error_code"]
    assert "[FEHLT: Fehlercode]" in text


def test_override_form_data_fills_gap_and_is_written_back(export_service):
    case = _case({"billing_quarter": "2026-Q2"})
    ok, _, text = export_service.render_template(case, TEMPLATE, SCHEMA, override_form_data={"error_code": "ERR_OVERRIDE"})
    assert ok is True and "ERR_OVERRIDE" in text
    assert case.form_data["error_code"] == "ERR_OVERRIDE"


def test_case_namespace_placeholders(export_service):
    tmpl = ExportTemplate(template_id="tmpl_custom_01", display_name="Dev Ticket Export",
                          target_type=TargetType.CLIPBOARD_TEXT, required_schema_fields=[],
                          template_string="TICKET: {{ case.case_id }}\nKUNDE: {{ case.customer.practice_name }}")
    c = Case(case_id="T-2026-888", customer=CaseCustomer(customer_id="K-555", practice_name="Radiologie Nord", is_vip=True),
             timeline=[TimelineEntry(timestamp="2026-08-23T10:00:00", author="Daniel Rösch", note="Bild nicht geladen")])
    ok, missing, text = export_service.render_template(c, tmpl)
    assert ok is True and missing == []
    assert "TICKET: T-2026-888" in text and "KUNDE: Radiologie Nord" in text


def test_required_fields_without_schema(export_service):
    """Required fields are validated from form_data alone when no schema is passed."""
    tmpl = ExportTemplate(template_id="tmpl_req_01", display_name="Zuzahlungs-Export", target_type=TargetType.FILE_EXPORT,
                          template_string="Betrag: {{ form_data.zuzahlungsbetrag }} [{{ form_data.has_mail }}]",
                          required_schema_fields=["zuzahlungsbetrag", "has_mail"])
    ok, missing, _ = export_service.render_template(Case(case_id="T-001", form_data={}), tmpl, force_export=False)
    assert ok is False and missing == ["zuzahlungsbetrag", "has_mail"]

    ok, missing, text = export_service.render_template(
        Case(case_id="T-002", form_data={"zuzahlungsbetrag": "10.00 €", "has_mail": True}), tmpl)
    assert ok is True and missing == []
    assert "Betrag: 10.00 €" in text
