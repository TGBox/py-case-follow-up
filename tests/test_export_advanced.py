import pytest
from pathlib import Path
from models.case import Case, TimelineEntry
from models.customer import Customer
from models.export_template import ExportTemplate, TargetType
from services.export_service import ExportService
from services.storage_service import StorageService, AppConfig


def test_export_template_rendering_with_custom_placeholders(tmp_path: Path):
    config = AppConfig(workspace_dir=tmp_path)
    storage = StorageService(config)
    export_service = ExportService(storage)

    tmpl = ExportTemplate(
        template_id="tmpl_custom_01",
        display_name="Dev Ticket Export",
        target_type=TargetType.CLIPBOARD_TEXT,
        template_string="TICKET: {{ case.case_id }}\nKUNDE: {{ case.customer.practice_name }}",
        required_schema_fields=[],
    )

    c = Case(case_id="T-2026-888")
    c.customer = Customer(customer_id="K-555", practice_name="Radiologie Nord", is_vip=True)
    c.classification.title = "DICOM-Export bricht ab"
    c.timeline.append(TimelineEntry(timestamp="2026-08-23T10:00:00", author="Daniel Rösch", note="Patientenbild konnte nicht geladen werden"))

    success, missing, rendered = export_service.render_template(c, tmpl)

    assert success is True
    assert len(missing) == 0
    assert "TICKET: T-2026-888" in rendered
    assert "KUNDE: Radiologie Nord" in rendered


def test_export_service_validates_required_fields(tmp_path: Path):
    config = AppConfig(workspace_dir=tmp_path)
    storage = StorageService(config)
    export_service = ExportService(storage)

    tmpl = ExportTemplate(
        template_id="tmpl_req_01",
        display_name="Zuzahlungs-Export",
        target_type=TargetType.FILE_EXPORT,
        template_string="Zuzahlungsbeitrag: {{ form_data.zuzahlungsbetrag }}",
        required_schema_fields=["zuzahlungsbetrag"],
    )

    c_incomplete = Case(case_id="T-001")
    c_incomplete.form_data = {}  # missing zuzahlungsbetrag

    success, missing, _ = export_service.render_template(c_incomplete, tmpl, force_export=False)
    assert success is False
    assert missing == ["zuzahlungsbetrag"]

    c_complete = Case(case_id="T-002")
    c_complete.form_data = {"zuzahlungsbetrag": "10.00 €"}

    success2, missing2, rendered = export_service.render_template(c_complete, tmpl, force_export=False)
    assert success2 is True
    assert len(missing2) == 0
    assert "10.00 €" in rendered
