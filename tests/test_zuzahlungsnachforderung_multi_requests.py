import pytest
from pathlib import Path
from models.schema import QuestionSchema, SchemaField
from models.case import Case, Classification, CaseCustomer
from services.seed_service import SeedService
from services.export_service import ExportService
from ui.widgets.dynamic_form_widget import DynamicFormWidget
import customtkinter as ctk


def test_schema_repeatable_group_serialization():
    """Verify that is_repeatable_group and repeatable fields serialize correctly."""
    schema = QuestionSchema(
        schema_id="schema_test_repeatable",
        display_name="Test Repeatable Schema",
        is_repeatable_group=True,
        repeatable_group_title="Test Card",
        repeatable_field_ids=["field1", "field2"],
        fields=[
            SchemaField(field_id="top_field", label="Top Field"),
            SchemaField(field_id="field1", label="Field 1"),
            SchemaField(field_id="field2", label="Field 2"),
        ]
    )

    data = schema.to_dict()
    assert data["is_repeatable_group"] is True
    assert data["repeatable_group_title"] == "Test Card"
    assert data["repeatable_field_ids"] == ["field1", "field2"]

    deserialized = QuestionSchema.from_dict(data)
    assert deserialized.is_repeatable_group is True
    assert deserialized.repeatable_group_title == "Test Card"
    assert deserialized.repeatable_field_ids == ["field1", "field2"]


def test_dynamic_form_repeatable_cards_add_remove(tmp_path: Path):
    """Test adding and removing card containers in DynamicFormWidget."""
    root = ctk.CTk()
    form_widget = DynamicFormWidget(root)

    schema = QuestionSchema(
        schema_id="schema_zuzahlungsnachforderung",
        display_name="Zuzahlungsnachforderung",
        is_repeatable_group=True,
        repeatable_group_title="Datei / Korrektur-Anforderung",
        repeatable_field_ids=["invoice_number", "esol_filename"],
        fields=[
            SchemaField(field_id="has_forwarded_email_or_screenshot", label="Screenshot", field_type="boolean"),
            SchemaField(field_id="invoice_number", label="Rechnungsnummer"),
            SchemaField(field_id="esol_filename", label="ESOL Datei"),
        ]
    )

    initial_form_data = {
        "has_forwarded_email_or_screenshot": True,
        "file_requests": [
            {"invoice_number": "RE-001", "esol_filename": "ESOL_1.dat"},
            {"invoice_number": "RE-002", "esol_filename": "ESOL_2.dat"},
        ]
    }

    form_widget.load_schema(schema, initial_form_data)

    assert len(form_widget.card_field_widgets) == 2

    # Verify extracted form data
    current_data = form_widget.get_form_data()
    assert current_data["has_forwarded_email_or_screenshot"] is True
    assert len(current_data["file_requests"]) == 2
    assert current_data["file_requests"][0]["invoice_number"] == "RE-001"
    assert current_data["file_requests"][1]["invoice_number"] == "RE-002"
    # Backward compatibility flat keys
    assert current_data["invoice_number"] == "RE-001"

    # Add a third card
    form_widget.add_repeatable_card()
    assert len(form_widget.card_field_widgets) == 3

    # Remove the second card (index 1)
    form_widget.remove_repeatable_card(1)
    assert len(form_widget.card_field_widgets) == 2

    root.destroy()


def test_export_rendering_multi_file_requests(tmp_path: Path):
    """Verify ExportService renders Jinja templates with multiple file requests formatted as numbered blocks."""
    from config import AppConfig
    from services.storage_service import StorageService

    config = AppConfig(workspace_dir=tmp_path)
    storage = StorageService(config)
    export_service = ExportService(storage)
    seed_service = SeedService(storage)
    schemas = seed_service.create_seed_schemas()
    templates = seed_service.create_seed_templates()

    zuzahlung_schema = next(s for s in schemas if s.schema_id == "schema_zuzahlungsnachforderung")
    zuzahlung_tpl = next(t for t in templates if t.template_id == "mail_dev_zuzahlung_abrechnung")

    from models.case import Case, Classification, CaseCustomer

    customer = CaseCustomer(customer_id="P100", practice_name="Praxis Dr. Test", contact_person="Frau Müller")
    classification = Classification(title="Zuzahlungsanfrage Test", schema_id="schema_zuzahlungsnachforderung")

    case = Case(
        case_id="case-multi-01",
        customer=customer,
        classification=classification,
        form_data={
            "action_type": "Zuzahlungsnachforderung",
            "has_forwarded_email_or_screenshot": True,
            "file_requests": [
                {
                    "action_type": "Zuzahlungsnachforderung",
                    "esol_filename": "ESOL_20260801.dat",
                    "invoice_number": "RE-2026-0815",
                    "invoice_date": "2026-08-01",
                    "prescription_info": "VO-987654",
                    "prescription_date": "2026-07-25",
                    "patient_names": "Max Mustermann",
                    "action_reason_detail": "Fehlende Zuzahlung 10 EUR",
                },
                {
                    "action_type": "Abrechnungskorrektur",
                    "esol_filename": "ESOL_20260802.dat",
                    "invoice_number": "RE-2026-0816",
                    "invoice_date": "2026-08-02",
                    "prescription_info": "VO-987655",
                    "prescription_date": "2026-07-26",
                    "patient_names": "Erika Musterfrau",
                    "action_reason_detail": "Falsche Versichertennummer",
                },
            ]
        }
    )

    success, missing, rendered = export_service.render_template(case, zuzahlung_tpl, zuzahlung_schema)
    assert success is True
    assert not missing
    assert "--- Datei-Anforderung #1 ---" in rendered
    assert "--- Datei-Anforderung #2 ---" in rendered
    assert "ESOL_20260801.dat" in rendered
    assert "ESOL_20260802.dat" in rendered
    assert "RE-2026-0815" in rendered
    assert "RE-2026-0816" in rendered
