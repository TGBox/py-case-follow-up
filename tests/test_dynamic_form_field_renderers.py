"""Tests for src/ui/widgets/dynamic_form_field_renderers.py (FieldRendererMixin).

This mixin is baked into DynamicFormWidget and dispatches to one
_render_*_field() method per detected field type/keyword
(render_single_field() in dynamic_form_widget.py). DynamicFormWidget itself
is already used by other tests (test_schema_v2_and_conditional_logic.py,
test_ui_integration.py, test_views_and_widgets_comprehensive.py,
test_zuzahlungsnachforderung_multi_requests.py) but none of them exercise
every dispatch branch (module tags, browser multiselect, date-by-keyword,
dropdown, boolean incl. the DB-backup special case, file, number, textbox-
by-keyword, plain text). This file builds one schema covering every branch
and verifies both widget construction and that get_form_data() extracts the
right value back out of each widget type.
"""

from pathlib import Path
import customtkinter as ctk
import pytest

from config import AppConfig
from enums import BoardColumn, FieldType
from models.case import Case, CaseCustomer, Classification, WorkflowStatus
from models.schema import QuestionSchema, SchemaField
from services.storage_service import StorageService
from services.attachment_service import AttachmentService
from ui.widgets.dynamic_form_widget import DynamicFormWidget


@pytest.fixture
def widget(tmp_path: Path):
    config = AppConfig(workspace_dir=tmp_path)
    storage = StorageService(config)
    profile = storage.load_profile()
    attachment_service = AttachmentService(config)

    app = ctk.CTk()
    app.withdraw()

    w = DynamicFormWidget(
        app,
        profile=profile,
        storage_service=storage,
        attachment_service=attachment_service,
        on_manage_module_tags=lambda: None,
    )
    yield w
    try:
        app.destroy()
    except Exception:
        pass


def _full_schema() -> QuestionSchema:
    return QuestionSchema(
        schema_id="schema_all_field_types",
        display_name="Alle Feldtypen",
        fields=[
            SchemaField(field_id="programmbereich", label="Programmbereich", field_type=FieldType.TEXT, order=1),
            SchemaField(field_id="tested_browsers", label="Getestete Browser", field_type=FieldType.TEXT, order=2),
            SchemaField(field_id="fehlerdatum", label="Datum des Fehlers", field_type=FieldType.TEXT, order=3),
            SchemaField(field_id="prioritaet", label="Priorität", field_type=FieldType.DROPDOWN,
                        options=["Hoch", "Mittel", "Niedrig"], order=4),
            SchemaField(field_id="ist_dringend", label="Ist dringend", field_type=FieldType.BOOLEAN, order=5),
            SchemaField(field_id="anzahl_faelle", label="Anzahl Fälle", field_type=FieldType.NUMBER, order=6),
            SchemaField(field_id="fehlerbeschreibung", label="Fehlerbeschreibung", field_type=FieldType.TEXT, order=7),
            SchemaField(field_id="freitext", label="Freitext Feld", field_type=FieldType.TEXT, order=8),
            SchemaField(field_id="datei_upload", label="Datei Upload", field_type=FieldType.FILE, order=9),
        ],
    )


def _form_data() -> dict:
    return {
        "programmbereich": "Abrechnung, Telematik",
        "tested_browsers": "Firefox, Chrome",
        "fehlerdatum": "01.09.2026",
        "prioritaet": "Mittel",
        "ist_dringend": True,
        "anzahl_faelle": 5,
        "fehlerbeschreibung": "Mehrzeiliger Text\nZeile 2",
        "freitext": "Einfacher Text",
        "datei_upload": "C:\\Faelle\\anlage.pdf",
    }


def test_all_field_types_dispatch_to_expected_widget_kind(widget):
    widget.load_schema(_full_schema(), _form_data())

    assert widget.field_widgets["programmbereich"][0] == "module_picker"
    assert widget.field_widgets["tested_browsers"][0] == "browser_pills"
    assert widget.field_widgets["fehlerdatum"][0] == FieldType.TEXT  # date branch keeps the field's own type marker
    assert widget.field_widgets["prioritaet"][0] == FieldType.DROPDOWN
    assert widget.field_widgets["ist_dringend"][0] == FieldType.BOOLEAN
    assert widget.field_widgets["anzahl_faelle"][0] == FieldType.NUMBER
    assert widget.field_widgets["fehlerbeschreibung"][0] == "textbox"
    assert widget.field_widgets["freitext"][0] == FieldType.TEXT
    assert widget.field_widgets["datei_upload"][0] == "file"


def test_get_form_data_round_trips_every_field_type(widget):
    schema = _full_schema()
    data = _form_data()
    widget.load_schema(schema, data)

    result = widget.get_form_data()

    assert result["programmbereich"] == "Abrechnung, Telematik"
    assert result["tested_browsers"] == "Firefox, Chrome"
    assert result["fehlerdatum"] == "01.09.2026"
    assert result["prioritaet"] == "Mittel"
    assert result["ist_dringend"] is True
    assert result["anzahl_faelle"] == 5
    assert result["fehlerbeschreibung"] == "Mehrzeiliger Text\nZeile 2"
    assert result["freitext"] == "Einfacher Text"
    assert result["datei_upload"] == "C:\\Faelle\\anlage.pdf"


def test_module_tags_field_falls_back_to_default_tags_without_profile(widget):
    widget.profile = None
    schema = QuestionSchema(schema_id="s1", display_name="S1", fields=[
        SchemaField(field_id="programmbereich", label="Programmbereich", field_type=FieldType.TEXT, order=1),
    ])
    widget.load_schema(schema, {"programmbereich": ""})

    ftype, holder = widget.field_widgets["programmbereich"]
    assert ftype == "module_picker"
    assert holder["selected"] == []


def test_browser_multiselect_click_toggles_and_unbekannt_is_exclusive(widget):
    schema = QuestionSchema(schema_id="s2", display_name="S2", fields=[
        SchemaField(field_id="tested_browsers", label="Getestete Browser", field_type=FieldType.TEXT, order=1),
    ])
    widget.load_schema(schema, {"tested_browsers": "Firefox"})

    # row_frame's children in order: [label_row, b_frame (built by
    # _render_browser_multiselect_field)]; b_frame's first child is b_pills_box.
    row_frame = widget.field_row_frames["tested_browsers"]
    b_frame = row_frame.winfo_children()[1]
    pills_box = b_frame.winfo_children()[0]
    buttons_by_text = {b.cget("text"): b for b in pills_box.winfo_children() if isinstance(b, ctk.CTkButton)}

    # Selecting "Unbekannt" must clear the previously selected concrete browser.
    buttons_by_text["Unbekannt"].invoke()
    assert widget.get_form_data()["tested_browsers"] == "Unbekannt"

    # Selecting a concrete browser again must clear "Unbekannt".
    buttons_by_text["Chrome"].invoke()
    assert widget.get_form_data()["tested_browsers"] == "Chrome"


def test_dropdown_field_uses_provided_value_when_valid(widget):
    schema = QuestionSchema(schema_id="s3", display_name="S3", fields=[
        SchemaField(field_id="prioritaet", label="Priorität", field_type=FieldType.DROPDOWN,
                    options=["Hoch", "Mittel", "Niedrig"], order=1),
    ])
    widget.load_schema(schema, {"prioritaet": "Niedrig"})
    _, combo = widget.field_widgets["prioritaet"]
    assert combo.get() == "Niedrig"


def test_dropdown_field_ignores_value_not_in_options(widget):
    schema = QuestionSchema(schema_id="s4", display_name="S4", fields=[
        SchemaField(field_id="prioritaet", label="Priorität", field_type=FieldType.DROPDOWN,
                    options=["Hoch", "Mittel", "Niedrig"], order=1),
    ])
    widget.load_schema(schema, {"prioritaet": "Nicht-existent"})
    _, combo = widget.field_widgets["prioritaet"]
    assert combo.get() == "Hoch"  # CTkOptionMenu defaults to the first option


def test_boolean_backup_field_with_case_shows_import_button_and_attachment_section(widget, tmp_path: Path):
    case = Case(
        case_id="T-BACKUP-01",
        customer=CaseCustomer(customer_id="K-1", practice_name="Praxis Backup"),
        classification=Classification(title="Backup Test"),
        workflow_status=WorkflowStatus(board_column=BoardColumn.NEW),
    )
    schema = QuestionSchema(schema_id="s5", display_name="S5", fields=[
        SchemaField(field_id="database_dump_provided", label="Backup vorhanden", field_type=FieldType.BOOLEAN, order=1),
    ])
    widget.load_schema(schema, {"database_dump_provided": False}, case=case)

    assert hasattr(widget, "mini_attach_scroll")
    assert hasattr(widget, "mini_attach_hdr_label")

    # row_frame's children in order: [label_row, chk_frame (built by
    # _render_boolean_field)].
    row_frame = widget.field_row_frames["database_dump_provided"]
    chk_frame = row_frame.winfo_children()[1]
    import_buttons = [
        b for b in chk_frame.winfo_children()
        if isinstance(b, ctk.CTkButton) and "importieren" in b.cget("text")
    ]
    assert len(import_buttons) == 1


def test_boolean_non_backup_field_has_no_import_button(widget):
    schema = QuestionSchema(schema_id="s6", display_name="S6", fields=[
        SchemaField(field_id="ist_dringend", label="Ist dringend", field_type=FieldType.BOOLEAN, order=1),
    ])
    widget.load_schema(schema, {"ist_dringend": False})

    row_frame = widget.field_row_frames["ist_dringend"]
    chk_frame = row_frame.winfo_children()[1]
    import_buttons = [b for b in chk_frame.winfo_children() if isinstance(b, ctk.CTkButton)]
    assert len(import_buttons) == 0
    assert not hasattr(widget, "mini_attach_scroll")


def test_number_field_extracts_int_and_float_correctly(widget):
    schema = QuestionSchema(schema_id="s7", display_name="S7", fields=[
        SchemaField(field_id="anzahl", label="Anzahl", field_type=FieldType.NUMBER, order=1),
    ])
    widget.load_schema(schema, {"anzahl": 3})
    assert widget.get_form_data()["anzahl"] == 3

    widget.load_schema(schema, {"anzahl": 2.5})
    assert widget.get_form_data()["anzahl"] == 2.5


def test_number_field_returns_none_when_empty(widget):
    schema = QuestionSchema(schema_id="s8", display_name="S8", fields=[
        SchemaField(field_id="anzahl", label="Anzahl", field_type=FieldType.NUMBER, order=1),
    ])
    widget.load_schema(schema, {"anzahl": None})
    assert widget.get_form_data()["anzahl"] is None


def test_date_keyword_detection_is_overridden_by_explicit_dropdown_or_boolean_type(widget):
    """A field whose id/label mentions 'datum' but whose field_type is
    DROPDOWN or BOOLEAN must NOT be hijacked by the date branch."""
    schema = QuestionSchema(schema_id="s9", display_name="S9", fields=[
        SchemaField(field_id="datum_bekannt", label="Datum bekannt?", field_type=FieldType.BOOLEAN, order=1),
    ])
    widget.load_schema(schema, {"datum_bekannt": True})
    assert widget.field_widgets["datum_bekannt"][0] == FieldType.BOOLEAN
