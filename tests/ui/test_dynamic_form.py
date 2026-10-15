"""DynamicFormWidget: field renderers, required-field highlight, schema v2 conditional fields and repeatable request cards."""

import customtkinter as ctk
import pytest

from enums import BoardColumn, FieldType
from models.case import Case, CaseCustomer, Classification, TimelineEntry, WorkflowStatus
from models.schema import QuestionSchema, SchemaField
from services.attachment_service import AttachmentService
from ui.widgets.dynamic_form_widget import DynamicFormWidget


@pytest.fixture
def form(root, storage, config):
    return DynamicFormWidget(
        root,
        profile=storage.load_profile(),
        storage_service=storage,
        attachment_service=AttachmentService(config),
        on_manage_module_tags=lambda: None,
    )


def _schema(*fields: SchemaField, **kwargs) -> QuestionSchema:
    return QuestionSchema(schema_id="s", display_name="S", fields=list(fields), **kwargs)


def _walk(widget):
    for child in widget.winfo_children():
        yield child
        yield from _walk(child)


def _buttons(form, field_id: str) -> list[str]:
    return [w.cget("text") for w in _walk(form.field_row_frames[field_id]) if isinstance(w, ctk.CTkButton)]


def _border(widget) -> tuple[str, int]:
    return (str(widget.cget("border_color")), int(widget.cget("border_width")))


# --- Field renderers ---

def test_every_field_type_renders_its_widget_kind_and_round_trips(form):
    schema = _schema(
        SchemaField(field_id="programmbereich", label="Programmbereich", field_type=FieldType.TEXT, order=1),
        SchemaField(field_id="tested_browsers", label="Getestete Browser", field_type=FieldType.TEXT, order=2),
        SchemaField(field_id="fehlerdatum", label="Datum des Fehlers", field_type=FieldType.DATE, order=3),
        SchemaField(field_id="prioritaet", label="Priorität", field_type=FieldType.DROPDOWN,
                    options=["Hoch", "Mittel", "Niedrig"], order=4),
        SchemaField(field_id="ist_dringend", label="Ist dringend", field_type=FieldType.BOOLEAN, order=5),
        SchemaField(field_id="anzahl_faelle", label="Anzahl Fälle", field_type=FieldType.NUMBER, order=6),
        SchemaField(field_id="fehlerbeschreibung", label="Fehlerbeschreibung", field_type=FieldType.TEXT, order=7),
        SchemaField(field_id="freitext", label="Freitext Feld", field_type=FieldType.TEXT, order=8),
        SchemaField(field_id="datei_upload", label="Datei Upload", field_type=FieldType.FILE, order=9),
    )
    data = {
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
    form.load_schema(schema, data)

    kinds = {fid: entry[0] for fid, entry in form.field_widgets.items()}
    assert kinds == {
        "programmbereich": "module_picker",
        "tested_browsers": "browser_pills",
        "fehlerdatum": FieldType.DATE,
        "prioritaet": FieldType.DROPDOWN,
        "ist_dringend": FieldType.BOOLEAN,
        "anzahl_faelle": FieldType.NUMBER,
        "fehlerbeschreibung": "textbox",
        "freitext": FieldType.TEXT,
        "datei_upload": "file",
    }
    assert form.get_form_data() == data


def test_module_tags_field_without_profile_starts_empty(form):
    form.profile = None
    form.load_schema(_schema(SchemaField(field_id="programmbereich", label="Programmbereich", order=1)),
                     {"programmbereich": ""})

    kind, holder = form.field_widgets["programmbereich"]
    assert kind == "module_picker"
    assert holder["selected"] == []


def test_browser_multiselect_unbekannt_is_exclusive(form):
    form.load_schema(_schema(SchemaField(field_id="tested_browsers", label="Getestete Browser", order=1)),
                     {"tested_browsers": "Firefox"})
    pills = {w.cget("text"): w for w in _walk(form.field_row_frames["tested_browsers"]) if isinstance(w, ctk.CTkButton)}

    pills["Unbekannt"].invoke()
    assert form.get_form_data()["tested_browsers"] == "Unbekannt"

    pills["Chrome"].invoke()
    assert form.get_form_data()["tested_browsers"] == "Chrome"


@pytest.mark.parametrize("value, shown", [("Niedrig", "Niedrig"), ("Nicht-existent", "Hoch")])
def test_dropdown_shows_value_only_when_it_is_an_option(form, value, shown):
    form.load_schema(_schema(SchemaField(field_id="p", label="Priorität", field_type=FieldType.DROPDOWN,
                                         options=["Hoch", "Mittel", "Niedrig"], order=1)), {"p": value})
    assert form.field_widgets["p"][1].get() == shown


@pytest.mark.parametrize("value", [3, 2.5, None])
def test_number_field_round_trips_int_float_and_empty(form, value):
    form.load_schema(_schema(SchemaField(field_id="anzahl", label="Anzahl", field_type=FieldType.NUMBER, order=1)),
                     {"anzahl": value})
    assert form.get_form_data()["anzahl"] == value


def test_only_the_db_backup_checkbox_gets_an_import_button_and_attachment_section(form):
    case = Case(
        case_id="T-BACKUP-01",
        customer=CaseCustomer(customer_id="K-1", practice_name="Praxis Backup"),
        classification=Classification(title="Backup Test"),
        workflow_status=WorkflowStatus(board_column=BoardColumn.NEW),
    )
    form.load_schema(_schema(SchemaField(field_id="ist_dringend", label="Ist dringend", field_type=FieldType.BOOLEAN, order=1)),
                     {"ist_dringend": False})
    assert _buttons(form, "ist_dringend") == []
    assert not hasattr(form, "mini_attach_scroll")

    form.load_schema(_schema(SchemaField(field_id="database_dump_provided", label="Backup vorhanden",
                                         field_type=FieldType.BOOLEAN, order=1)),
                     {"database_dump_provided": False}, case=case)
    assert len([t for t in _buttons(form, "database_dump_provided") if "backup" in t and "importieren" in t]) == 1
    assert hasattr(form, "mini_attach_scroll")


def test_calendar_button_only_for_explicit_date_field_type(form):
    """Regression: 'Name der originalen ESOL-Datei' bekam einen Kalender-Button,
    weil die alte Heuristik 'date' als Teilstring in 'Datei' fand."""
    form.load_schema(_schema(
        SchemaField(field_id="esol_filename", label="Name der originalen ESOL-Datei", field_type=FieldType.TEXT, order=1),
        SchemaField(field_id="datum_bekannt", label="Datum bekannt?", field_type=FieldType.BOOLEAN, order=2),
        SchemaField(field_id="invoice_date", label="Rechnungsdatum", field_type=FieldType.DATE, order=3),
        SchemaField(field_id="ablauf", label="Gültig bis", field_type=FieldType.DATE, order=4),
    ), {"datum_bekannt": True})

    def has_calendar(fid):
        return any("Kalender" in t for t in _buttons(form, fid))

    assert not has_calendar("esol_filename")
    assert form.field_widgets["datum_bekannt"][0] == FieldType.BOOLEAN
    assert has_calendar("invoice_date")
    assert has_calendar("ablauf")


# --- Required-field borders update in place instead of rebuilding the form ---

def test_missing_field_highlight_is_reversible_without_reload(root):
    """Saving must not rebuild the form just to recolour borders - that threw away typed input."""
    schema = _schema(*[SchemaField(field_id=f"f{i}", label=f"Feld {i}", field_type="text", required=i in (0, 3))
                       for i in range(6)])
    form = DynamicFormWidget(root)
    form.pack()
    form.load_schema(schema, {}, ["f0", "f3"], case=None)
    root.update()

    required, untouched = form.field_widgets["f0"][1], form.field_widgets["f1"][1]
    theme_default = _border(untouched)
    assert _border(required) == ("red", 2)
    untouched.insert(0, "halb getippter Text")
    widgets_before = {fid: str(entry[1]) for fid, entry in form.field_widgets.items()}

    form.apply_missing_field_highlight([])
    root.update()
    assert _border(required) == theme_default

    form.apply_missing_field_highlight(["f0"])
    root.update()
    assert _border(required) == ("red", 2)

    assert {fid: str(entry[1]) for fid, entry in form.field_widgets.items()} == widgets_before
    assert form.field_widgets["f1"][1].get() == "halb getippter Text"
    assert form.missing_fields == ["f0"]


def test_cockpit_save_does_not_reload_the_schema():
    """on_click_save must go through the in-place highlight path, not load_schema."""
    pytest.importorskip("PIL", reason="Pillow fehlt in dieser Umgebung")
    from ui.views.cockpit_view import CockpitView

    calls: list[str] = []

    class FormStub:
        missing_fields: list[str] = []

        def get_form_data(self):
            return {"f0": "wert"}

        def load_schema(self, *a, **k):
            calls.append("load_schema")

        def apply_missing_field_highlight(self, missing):
            calls.append(("apply_missing_field_highlight", missing))

    class ViewStub:
        on_click_save = CockpitView.on_click_save

    view = ViewStub()
    view.current_case = Case(case_id="T-1", classification=Classification(schema_id="s"))
    view.form_widget = FormStub()
    view.schemas = [_schema(*[SchemaField(field_id=f"f{i}", label=f"F{i}", required=i in (0, 3)) for i in range(4)])]
    view.scoring_service = type("S", (), {"update_case_scoring": lambda self, c: None})()
    view.on_case_updated = lambda c: None

    view.on_click_save()

    assert calls == [("apply_missing_field_highlight", ["f3"])]


# --- Schema v2: conditional fields, file extensions, repeatable groups ---

def test_schema_v2_attributes_survive_serialization():
    schema = QuestionSchema(
        schema_id="v2",
        display_name="V2",
        is_repeatable_group=True,
        repeatable_group_title="Test Card",
        repeatable_field_ids=["other_details"],
        fields=[
            SchemaField(field_id="error_category", label="Fehlerkategorie", field_type=FieldType.DROPDOWN,
                        options=["Hardware", "Sonstiges"]),
            SchemaField(field_id="other_details", label="Sonstige Details", field_type=FieldType.TEXT,
                        depends_on_field_id="error_category", depends_on_value="Sonstiges"),
            SchemaField(field_id="log_file", label="Log-Datei", field_type=FieldType.FILE,
                        allowed_extensions=[".log", ".txt"]),
        ],
    )
    d = schema.to_dict()
    assert d["fields"][1]["depends_on_value"] == "Sonstiges"
    assert d["fields"][2]["field_type"] == "file"

    back = QuestionSchema.from_dict(d)
    assert (back.is_repeatable_group, back.repeatable_group_title, back.repeatable_field_ids) == (
        True, "Test Card", ["other_details"])
    assert back.fields[1].depends_on_field_id == "error_category"
    assert back.fields[2].field_type == FieldType.FILE
    assert back.fields[2].allowed_extensions == [".log", ".txt"]


def test_dependent_field_is_shown_only_while_its_condition_holds(root):
    form = DynamicFormWidget(root)
    form.pack()
    form.load_schema(_schema(
        SchemaField(field_id="is_reproducible", label="Reproduzierbar?", field_type=FieldType.BOOLEAN),
        SchemaField(field_id="reproduction_steps", label="Schritte", field_type=FieldType.TEXT,
                    depends_on_field_id="is_reproducible", depends_on_value="true"),
        SchemaField(field_id="screenshot", label="Screenshot", field_type=FieldType.FILE, allowed_extensions=[".png"]),
    ), form_data={"is_reproducible": False, "screenshot": "test.png"})
    child = form.field_row_frames["reproduction_steps"]
    assert child.winfo_manager() == ""

    form.field_widgets["is_reproducible"][1].set(True)
    form.update_conditional_visibility()

    assert child.winfo_manager() == "pack"
    data = form.get_form_data()
    assert data["is_reproducible"] is True
    assert data["screenshot"] == "test.png"


def test_repeatable_request_cards_load_add_and_remove(root):
    form = DynamicFormWidget(root)
    form.load_schema(QuestionSchema(
        schema_id="schema_zuzahlungsnachforderung",
        display_name="Zuzahlungsnachforderung",
        is_repeatable_group=True,
        repeatable_group_title="Datei / Korrektur-Anforderung",
        repeatable_field_ids=["invoice_number", "esol_filename"],
        fields=[
            SchemaField(field_id="has_forwarded_email_or_screenshot", label="Screenshot", field_type="boolean"),
            SchemaField(field_id="invoice_number", label="Rechnungsnummer"),
            SchemaField(field_id="esol_filename", label="ESOL Datei"),
        ],
    ), {
        "has_forwarded_email_or_screenshot": True,
        "file_requests": [
            {"invoice_number": "RE-001", "esol_filename": "ESOL_1.dat"},
            {"invoice_number": "RE-002", "esol_filename": "ESOL_2.dat"},
        ],
    })

    data = form.get_form_data()
    assert data["has_forwarded_email_or_screenshot"] is True
    assert [r["invoice_number"] for r in data["file_requests"]] == ["RE-001", "RE-002"]
    assert data["invoice_number"] == "RE-001"  # flat key kept for older templates

    form.add_repeatable_card()
    assert len(form.get_form_data()["file_requests"]) == 3
    form.remove_repeatable_card(1)
    assert [r["invoice_number"] for r in form.get_form_data()["file_requests"]][:2] == ["RE-001", ""]


def test_saved_file_requests_export_as_numbered_blocks(storage):
    from services.export_service import ExportService
    from services.seed_service import SeedService

    seed = SeedService(storage)
    schema = next(s for s in seed.create_seed_schemas() if s.schema_id == "schema_zuzahlungsnachforderung")
    tpl = next(t for t in seed.create_seed_templates() if t.template_id == "mail_dev_zuzahlung_abrechnung")

    def request(n, action):
        return {
            "action_type": action,
            "esol_filename": f"ESOL_2026080{n}.dat",
            "invoice_number": f"RE-2026-081{n}",
            "invoice_date": f"2026-08-0{n}",
            "prescription_info": f"VO-98765{n}",
            "prescription_date": "2026-07-25",
            "patient_names": "Max Mustermann",
            "action_reason_detail": "Fehlende Zuzahlung 10 EUR",
        }

    case = Case(
        case_id="case-multi-01",
        timeline=[TimelineEntry(timestamp="2026-08-03T10:00:00", author="test_agent", note="Anfrage erhalten")],
        customer=CaseCustomer(customer_id="P100", practice_name="Praxis Dr. Test", contact_person="Frau Müller"),
        classification=Classification(title="Zuzahlungsanfrage Test", schema_id="schema_zuzahlungsnachforderung"),
        form_data={
            "action_type": "Zuzahlungsnachforderung",
            "has_forwarded_email_or_screenshot": True,
            "file_requests": [request(1, "Zuzahlungsnachforderung"), request(2, "Abrechnungskorrektur")],
        },
    )

    storage.save_cases([case], sync=True)
    case = next(c for c in storage.load_cases(use_cache=False) if c.case_id == "case-multi-01")
    success, missing, rendered = ExportService(storage).render_template(case, tpl, schema)

    assert success is True and not missing
    for text in ("--- Datei-Anforderung #1 ---", "--- Datei-Anforderung #2 ---",
                 "ESOL_20260801.dat", "ESOL_20260802.dat", "RE-2026-0811", "RE-2026-0812"):
        assert text in rendered
