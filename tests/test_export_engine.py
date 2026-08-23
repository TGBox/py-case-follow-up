import pytest
from models.case import Case, CaseCustomer, Classification, WorkflowStatus, TimelineEntry
from models.export_template import ExportTemplate
from models.schema import QuestionSchema, SchemaField
from services.export_service import ExportService


@pytest.fixture
def export_service():
    return ExportService()


@pytest.fixture
def sample_template():
    return ExportTemplate(
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


@pytest.fixture
def sample_schema():
    return QuestionSchema(
        schema_id="schema_1",
        display_name="Test Schema",
        fields=[
            SchemaField(field_id="billing_quarter", label="Quartal", required=True),
            SchemaField(field_id="error_code", label="Fehlercode", required=True),
        ],
    )


def test_export_rendering_success(export_service, sample_template, sample_schema):
    case = Case(
        case_id="T-100",
        created_by="Daniel Rösch",
        customer=CaseCustomer(customer_id="K-100", practice_name="Praxis Ulm"),
        classification=Classification(schema_id="schema_1"),
        form_data={"billing_quarter": "2026-Q2", "error_code": "ERR_01"},
    )

    success, missing, text = export_service.render_template(case, sample_template, sample_schema)
    assert success is True
    assert len(missing) == 0
    assert "Praxis Ulm" in text
    assert "2026-Q2" in text
    assert "ERR_01" in text


def test_export_missing_field_fails(export_service, sample_template, sample_schema):
    case = Case(
        case_id="T-100",
        customer=CaseCustomer(customer_id="K-100", practice_name="Praxis Ulm"),
        classification=Classification(schema_id="schema_1"),
        form_data={"billing_quarter": "2026-Q2"},  # error_code missing
    )

    success, missing, text = export_service.render_template(case, sample_template, sample_schema, force_export=False)
    assert success is False
    assert missing == ["error_code"]
    assert text == ""


def test_export_force_export(export_service, sample_template, sample_schema):
    case = Case(
        case_id="T-100",
        customer=CaseCustomer(customer_id="K-100", practice_name="Praxis Ulm"),
        classification=Classification(schema_id="schema_1"),
        form_data={"billing_quarter": "2026-Q2"},  # error_code missing
    )

    success, missing, text = export_service.render_template(case, sample_template, sample_schema, force_export=True)
    assert success is True
    assert missing == ["error_code"]
    assert "[FEHLT: Fehlercode]" in text


def test_export_inplace_override(export_service, sample_template, sample_schema):
    case = Case(
        case_id="T-100",
        customer=CaseCustomer(customer_id="K-100", practice_name="Praxis Ulm"),
        classification=Classification(schema_id="schema_1"),
        form_data={"billing_quarter": "2026-Q2"},
    )

    success, missing, text = export_service.render_template(
        case, sample_template, sample_schema, override_form_data={"error_code": "ERR_OVERRIDE"}
    )
    assert success is True
    assert "ERR_OVERRIDE" in text
    assert case.form_data["error_code"] == "ERR_OVERRIDE"


def test_export_realworld_dev_mail(export_service):
    from models.export_template import ExportTemplate
    tmpl = ExportTemplate(
        template_id="mail_dev_zuzahlung_abrechnung",
        display_name="Dev Mail",
        required_schema_fields=[
            "action_type", "invoice_number", "invoice_date", "prescription_info",
            "prescription_date", "patient_names", "esol_filename", "action_reason_detail", "has_forwarded_email_or_screenshot"
        ],
        template_string="Betreff: [{{ form_data.action_type }}] {{ customer.practice_name }}\nRechnung: {{ form_data.invoice_number }}"
    )
    case = Case(
        case_id="T-500",
        customer=CaseCustomer(practice_name="Praxis Dr. Test", customer_id="K-100"),
        form_data={
            "action_type": "Zuzahlungsnachforderung",
            "invoice_number": "RE-2026-001",
            "invoice_date": "2026-08-01",
            "prescription_info": "VO-123",
            "prescription_date": "2026-07-01",
            "patient_names": "Max Mustermann",
            "esol_filename": "ESOL_01.dat",
            "action_reason_detail": "Details zum Test",
            "has_forwarded_email_or_screenshot": True,
        }
    )
    success, missing, text = export_service.render_template(case, tmpl)
    assert success is True
    assert len(missing) == 0
    assert "[Zuzahlungsnachforderung]" in text
    assert "RE-2026-001" in text
