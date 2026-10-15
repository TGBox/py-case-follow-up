"""Concrete dialogs: customer/colleague/tag/snippet/schema/template management, help, zip import, export and case helpers."""

import zipfile
from pathlib import Path
from tkinter import filedialog
from typing import Any, cast

import customtkinter as ctk
import pytest

import ui.dialogs.confirm_dialog as confirm_mod
from enums import BoardColumn, FieldType, UrgencyLevel
from models.case import Case, CaseCustomer, Classification, WorkflowStatus
from models.customer import Contact, Customer
from models.export_template import ExportTemplate
from models.profile import Colleague, UserProfile
from models.schema import QuestionSchema, SchemaField
from models.snippet import Snippet
from services.customer_service import CustomerService
from services.export_service import ExportService
from services.i18n_service import get_i18n
from services.schema_service import SchemaService
from services.snippet_service import SnippetService


@pytest.fixture(scope="module")
def _shared_root():
    # One root per module instead of conftest's per-test root: creating a CTk costs ~0.3 s.
    shared = ctk.CTk()
    shared.withdraw()
    yield shared
    try:
        shared.destroy()
    except Exception:
        pass


@pytest.fixture
def app(_shared_root):
    """Shared root; every dialog is destroyed after the test so nothing leaks into the next one."""
    root = _shared_root
    yield root
    for child in list(root.winfo_children()):
        try:
            child.destroy()
        except Exception:
            pass
    try:
        root.update()
    except Exception:
        pass


@pytest.fixture
def confirm_answer(monkeypatch):
    """Replaces ask_confirmation; set state['answer'], read state['calls']."""
    state: dict[str, Any] = {"answer": False, "calls": []}

    def fake_ask(parent, message, **kwargs):
        state["calls"].append(message)
        return state["answer"]

    monkeypatch.setattr(confirm_mod, "ask_confirmation", fake_ask)
    return state


def _case(case_id="CASE-UI-100", **wf) -> Case:
    return Case(
        case_id=case_id,
        customer=CaseCustomer(customer_id="C-1", practice_name="Test Praxis"),
        classification=Classification(schema_id="standard", title="UI Test Case", urgency_level=UrgencyLevel.GREEN),
        workflow_status=WorkflowStatus(board_column=BoardColumn.NEW, **wf),
        form_data={"description": "Programm startet nicht"},
    )


# --- Customer management ---

def _customer_dialog(app, storage):
    from ui.dialogs.customer_management_dialog import CustomerManagementDialog

    service = CustomerService(storage)
    for i in (1, 2):
        service.save_customer(Customer(customer_id=f"K-{i}", practice_name=f"Praxis {i}", city=f"Ort {i}",
                                       contacts=[Contact(name=f"Kontakt {i}")]))
    updates = []
    dialog = CustomerManagementDialog(app, customer_service=service, on_customers_updated=lambda: updates.append(1))
    dialog.update()
    dialog.updates = updates
    return dialog


def test_customer_dialog_edit_create_and_add_contact(app, storage):
    dialog = _customer_dialog(app, storage)
    assert len(dialog.customers) == 2

    dialog.select_customer("K-1")
    assert dialog.name_entry.get() == "Praxis 1"
    dialog.name_entry.delete(0, "end")
    dialog.name_entry.insert(0, "Praxis Alpha-Beta")
    dialog.vip_var.set(True)
    dialog.save_current_customer()
    saved = next(c for c in storage.load_customers() if c.customer_id == "K-1")
    assert saved.practice_name == "Praxis Alpha-Beta" and saved.is_vip

    dialog.on_click_new_customer()
    dialog.cust_id_entry.configure(state="normal")
    dialog.cust_id_entry.delete(0, "end")
    dialog.cust_id_entry.insert(0, "K-200")
    dialog.name_entry.insert(0, "Klinik Gamma")
    dialog.save_current_customer()
    assert any(c.customer_id == "K-200" for c in storage.load_customers())
    assert dialog.updates

    rows = len(dialog.contact_rows)
    dialog.add_contact_row()
    assert len(dialog.contact_rows) == rows + 1


def test_customer_dialog_guard_ignores_navigation_but_catches_typing(app, storage):
    """Reported bug: searching/sorting/switching records asked 'discard unsaved input?' although nothing was edited."""
    dialog = _customer_dialog(app, storage)
    assert dialog.is_dirty() is False, "frisch geoeffneter Dialog gilt schon als geaendert"

    for cid in ("K-1", "K-2"):
        dialog.select_customer(cid)
        dialog.update()
        assert dialog.is_dirty() is False, "Auswahl eines Datensatzes gilt faelschlich als Eingabe"

    for term in ("Praxis", "gibtesnicht", ""):   # empty result rebuilds the result cards
        dialog.search_entry.delete(0, "end")
        dialog.search_entry.insert(0, term)
        dialog.on_search_changed()
        dialog.update()
        assert dialog.is_dirty() is False, f"Suche {term!r} gilt als Eingabe"

    dialog.sort_criterion_combo.set(dialog.sort_criterion_combo.cget("values")[1])
    dialog.on_sort_changed()
    dialog.update()
    assert dialog.is_dirty() is False, "Sortieren gilt faelschlich als Eingabe"

    dialog.select_customer("K-1")
    dialog.name_entry.insert("end", " geaendert")
    assert dialog.is_dirty() is True, "echte Eingabe wird nicht erkannt"
    dialog.save_current_customer()
    dialog.update()
    assert dialog.is_dirty() is False, "nach dem Speichern wird weiterhin nachgefragt"

    dialog.name_entry.insert("end", "X")
    dialog.on_click_new_customer()
    dialog.update()
    assert dialog.is_dirty() is False, "leeres Formular gilt faelschlich als Eingabe"


# --- Colleague management ---

def test_colleague_dialog_absence_create_and_search(app, storage):
    from ui.dialogs.colleague_management_dialog import ColleagueManagementDialog

    storage.save_colleagues([Colleague(name="Max Mustermann", username="mmustermann", email="max@support.de")])
    dialog = ColleagueManagementDialog(app, storage_service=storage, on_colleagues_updated=lambda: None)
    dialog.update_idletasks()

    dialog.select_colleague(dialog.colleagues[0])
    assert dialog.name_entry.get() == "Max Mustermann"
    dialog.is_absent_var.set(True)
    dialog.absence_reason_entry.delete(0, "end")
    dialog.absence_reason_entry.insert(0, "Im Urlaub bis Freitag")
    dialog.on_click_save()
    saved = storage.load_colleagues()[0]
    assert saved.is_absent and saved.absence_reason == "Im Urlaub bis Freitag"

    dialog.on_click_new_colleague()
    for entry, value in ((dialog.username_entry, "emusterfrau"), (dialog.name_entry, "Erika Musterfrau"),
                         (dialog.email_entry, "erika@support.de")):
        entry.delete(0, "end")
        entry.insert(0, value)
    dialog.on_click_save()
    assert any(c.name == "Erika Musterfrau" for c in storage.load_colleagues())

    dialog.search_entry.insert(0, "Mei")
    dialog.on_search_changed()
    dialog.update()
    assert dialog.is_dirty() is False, "Suchen gilt faelschlich als Eingabe"


# --- Tag management ---

def test_tag_dialog_adds_and_deletes_tags(app, storage):
    from ui.dialogs.tag_management_dialog import TagManagementDialog

    profile = storage.load_profile()
    profile.available_tags = ["PVS", "Abrechnung", "Hardware"]
    storage.save_profile(profile)
    dialog = TagManagementDialog(app, storage_service=storage, profile=profile, on_tags_updated=lambda: None)

    dialog.new_tag_entry.insert(0, "Telematik")
    dialog.on_add_tag()
    dialog.on_delete_tag("Hardware")
    assert dialog.profile.available_tags == ["PVS", "Abrechnung", "Telematik"]
    assert "Telematik" in storage.load_profile().available_tags


@pytest.mark.parametrize("answer", [False, True])
def test_tag_and_module_deletion_follow_the_confirmation(app, storage, confirm_answer, answer):
    """A declined confirmation must leave the data untouched."""
    from ui.dialogs.tag_management_dialog import TagManagementDialog

    profile = UserProfile()
    profile.available_tags = ["Schnittstelle", "Abrechnung"]
    profile.available_module_tags = ["Rezeptdruck", "Abrechnung"]
    dialog = TagManagementDialog(app, profile=profile, storage_service=storage, on_tags_updated=lambda: None)

    confirm_answer["answer"] = answer
    dialog.confirm_delete_tag("Schnittstelle")
    dialog.confirm_delete_module("Rezeptdruck")

    assert len(confirm_answer["calls"]) == 2, "no confirmation was requested before deleting"
    assert ("Schnittstelle" in profile.available_tags) is not answer
    assert ("Rezeptdruck" in profile.available_module_tags) is not answer
    assert "Abrechnung" in profile.available_tags


# --- Snippet management / picker ---

def test_snippet_deletion_respects_the_confirmation(app, tmp_path: Path, confirm_answer):
    from ui.dialogs.snippet_management_dialog import SnippetManagementDialog

    service = SnippetService(workspace_dir=tmp_path)
    service.add_or_update_snippet(Snippet(snippet_id="S-1", title="Begrüßung", content="Hallo"))
    dialog = SnippetManagementDialog(app, snippet_service=service, on_snippets_updated=lambda: None)

    for answer in (False, True):
        confirm_answer["answer"] = answer
        dialog.selected_snippet = next(s for s in service.get_all_snippets() if s.snippet_id == "S-1")
        dialog.confirm_click_delete()
        assert any(s.snippet_id == "S-1" for s in service.get_all_snippets()) is not answer


@pytest.fixture
def picker_service(tmp_path: Path) -> SnippetService:
    svc = SnippetService(workspace_dir=tmp_path)
    svc.snippets = [   # fixed snippets instead of the locale-dependent seed
        Snippet(snippet_id="S-1", title="Screenshot anfordern", category="Rückfrage",
                content="Bitte senden Sie uns einen Screenshot.", tags=["screenshot", "fehler"]),
        Snippet(snippet_id="S-2", title="PVS neustarten", category="Anleitung",
                content="1. PVS beenden.\n2. PVS neu starten.", tags=["pvs", "neustart"], shortcut="<Control-Alt-1>"),
        Snippet(snippet_id="S-3", title="Fallabschluss", category="Standardantwort",
                content="Vielen Dank, der Fall ist gelöst.", tags=["abschluss"]),
    ]
    svc.save_snippets()
    return svc


def _picker_rows(dialog):
    children = dialog.list_scroll.winfo_children()
    return ([w for w in children if isinstance(w, ctk.CTkFrame)], [w for w in children if isinstance(w, ctk.CTkLabel)])


@pytest.mark.parametrize("search, category, expected_cards", [
    ("", None, 3), ("PVS", None, 1), ("", "Anleitung", 1), ("zzz-nonexistent-query", None, 0),
])
def test_snippet_picker_filters_by_search_and_category(app, picker_service, search, category, expected_cards):
    from ui.dialogs.snippet_picker_dialog import SnippetPickerDialog

    dialog = SnippetPickerDialog(app, snippet_service=picker_service, on_snippet_selected=lambda text: None)
    dialog.search_entry.insert(0, search)
    if category:
        dialog.cat_combo.set(category)
    dialog.refresh_snippet_list()

    cards, labels = _picker_rows(dialog)
    assert len(cards) == expected_cards
    if expected_cards == 0:
        assert len(labels) == 1, "no 'nothing found' placeholder"


def test_snippet_picker_inserts_only_a_selected_snippet(app, picker_service):
    from ui.dialogs.snippet_picker_dialog import SnippetPickerDialog

    received = []
    dialog = SnippetPickerDialog(app, snippet_service=picker_service, on_snippet_selected=received.append)
    assert dialog.insert_btn.cget("state") == "disabled"
    dialog.on_click_insert()
    assert received == []

    target = next(s for s in picker_service.get_all_snippets() if s.snippet_id == "S-2")
    dialog.select_snippet(target)
    assert dialog.preview_textbox.get("1.0", "end").strip() == target.content
    assert dialog.insert_btn.cget("state") == "normal"
    dialog.on_click_insert()
    assert received == [target.content]


# --- Schema builder / template manager ---

def test_schema_builder_creates_schema_and_adds_field(app, storage, config):
    from ui.dialogs.schema_builder_dialog import NewSchemaDialog, SchemaBuilderDialog

    dialog = SchemaBuilderDialog(app, schemas=storage.load_schemas(), schema_service=SchemaService(config),
                                 on_schemas_updated=lambda s: None)
    new_diag = NewSchemaDialog(app, on_schema_created=dialog.on_schema_created)
    new_diag.name_entry.insert(0, "Abrechnung Test")
    new_diag.id_entry.insert(0, "schema_test_custom")
    new_diag.desc_entry.insert(0, "Test Formular")
    new_diag.on_save()
    assert dialog.selected_schema.schema_id == "schema_test_custom"

    dialog.new_id_entry.insert(0, "test_field_1")
    dialog.new_label_entry.insert(0, "Test Frage")
    dialog.new_type_combo.set(FieldType.TEXT.value)
    dialog.on_add_field()
    assert dialog.selected_schema.fields[0].field_id == "test_field_1"


def test_last_schema_cannot_be_deleted(app, storage, monkeypatch):
    from ui.dialogs.schema_builder_dialog import SchemaBuilderDialog

    notices: list[str] = []
    monkeypatch.setattr(confirm_mod, "show_notice", lambda parent, message, **kw: notices.append(message))
    monkeypatch.setattr(confirm_mod, "ask_confirmation", lambda *a, **k: True)
    only = QuestionSchema(schema_id="S-ONLY", display_name="Einziges Formular")
    dialog = SchemaBuilderDialog(app, schemas=[only], schema_service=SchemaService(storage), on_schemas_updated=lambda s: None)

    dialog.confirm_delete_schema()
    assert len(dialog.schemas) == 1, "the last remaining schema must not be deletable"
    assert notices, "the user got no explanation why nothing happened"


def test_schema_validation_reports_missing_required_fields():
    schema = QuestionSchema(schema_id="s", display_name="S", fields=[
        SchemaField(field_id="f1", label="Pflicht", field_type=FieldType.TEXT, required=True),
        SchemaField(field_id="f2", label="Optional", field_type=FieldType.BOOLEAN, required=False),
    ])
    assert SchemaService.validate_form_data(schema, {}) == (False, ["f1"])
    assert SchemaService.validate_form_data(schema, {"f1": "x", "f2": False}) == (True, [])


def test_edit_template_dialog_lists_schemas(app, storage):
    from ui.dialogs.template_manager_dialog import EditTemplateDialog

    schemas = [QuestionSchema(schema_id="schema_test", display_name="Test Schema",
                              fields=[SchemaField(field_id="short_f", label="Kurz", field_type=FieldType.TEXT)])]
    dialog = EditTemplateDialog(app, template=None, schemas=schemas, export_service=ExportService(storage),
                                on_save=lambda t: None)
    dialog.update_idletasks()
    assert len(dialog.schema_vars) == 1
    assert dialog.id_entry.get() == ""


# --- Help ---

def test_help_dialog_search_select_and_language(app):
    from ui.dialogs.help_dialog import HELP_ARTICLES, HelpDialog

    ids = {a["id"] for a in HELP_ARTICLES}
    assert {"basics", "scoring", "schemas", "email_calendar_outlook", "case_print_reporting",
            "stepper_time_picker", "handover_followup", "wiki"} <= ids

    dialog = HelpDialog(app)
    dialog.search_entry.insert(0, "Outlook")
    dialog.on_search_changed()
    assert "email_calendar_outlook" in [a["id"] for a in dialog.filtered_articles]
    dialog.select_article("email_calendar_outlook")
    assert "Outlook" in dialog.article_title_lbl.cget("text")
    dialog.search_entry.delete(0, "end")
    dialog.on_search_changed()
    assert len(dialog.filtered_articles) == len(dialog.articles)

    german = [a["title"] for a in dialog.articles]
    get_i18n().current_language = "en"
    app.update_idletasks()
    english = [a["title"] for a in dialog.articles]
    assert len(english) == len(german) and english != german, "help articles stayed German"


# --- Zip import ---

@pytest.fixture
def backup_zip(tmp_path: Path) -> Path:
    zip_path = tmp_path / "sample_backup.zip"
    with zipfile.ZipFile(zip_path, "w") as zf:
        zf.writestr("data/cases.json", '{"cases": []}')
        zf.writestr("data/customers.json", '{"customers": []}')
        zf.writestr("attachments/att1.png", b"fake image bytes")
    return zip_path


def _zip_dialog(app, zip_path, tmp_path, confirmed):
    from ui.dialogs.zip_import_dialog import ZipImportPathDialog

    return ZipImportPathDialog(app, zip_file_path=zip_path, default_data_dir=tmp_path / "data",
                               default_attachments_dir=tmp_path / "attachments",
                               on_import_confirmed=lambda d, a: confirmed.append((d, a)))


def test_zip_import_root_mode_validates_and_confirms(app, backup_zip, tmp_path: Path):
    confirmed: list = []
    dialog = _zip_dialog(app, backup_zip, tmp_path, confirmed)
    assert dialog.mode == "root"
    assert (dialog.zip_info["total_files"], dialog.zip_info["data_files"], dialog.zip_info["attachment_files"]) == (3, 2, 1)

    dialog.root_entry.delete(0, "end")
    dialog.on_confirm()
    assert confirmed == []

    dialog.root_entry.insert(0, str(tmp_path / "ws"))
    dialog.on_confirm()
    assert confirmed == [(tmp_path / "ws" / "data", tmp_path / "ws" / "data" / "attachments")]


def test_zip_import_custom_mode_requires_both_paths(app, backup_zip, tmp_path: Path):
    confirmed: list = []
    dialog = _zip_dialog(app, backup_zip, tmp_path, confirmed)
    dialog.set_mode_custom()
    assert dialog.mode == "custom"

    dialog.data_entry.delete(0, "end")
    dialog.on_confirm()
    dialog.data_entry.insert(0, str(tmp_path / "d"))
    dialog.att_entry.delete(0, "end")
    dialog.on_confirm()
    assert confirmed == []

    dialog.att_entry.insert(0, str(tmp_path / "a"))
    dialog.on_confirm()
    assert confirmed == [(tmp_path / "d", tmp_path / "a")]


def test_zip_import_browse_buttons_fill_paths(app, backup_zip, tmp_path: Path, monkeypatch):
    dialog = _zip_dialog(app, backup_zip, tmp_path, [])

    def browse(answer):
        monkeypatch.setattr(filedialog, "askdirectory", lambda **k: answer)

    browse(str(tmp_path / "r"))
    dialog.browse_root_dir()
    assert dialog.root_entry.get() == str(tmp_path / "r")

    dialog.set_mode_custom()
    browse(str(tmp_path / "d"))
    dialog.browse_data_dir()
    browse(str(tmp_path / "a"))
    dialog.browse_att_dir()
    browse("")   # cancelled browse keeps the value
    dialog.browse_data_dir()
    assert (dialog.data_entry.get(), dialog.att_entry.get()) == (str(tmp_path / "d"), str(tmp_path / "a"))

    dialog.set_mode_root()
    assert dialog.mode == "root"


# --- Case-related dialogs ---

@pytest.mark.parametrize("with_schema", [True, False])
def test_export_dialog_renders_preview_with_first_template(app, storage, with_schema):
    from ui.dialogs.export_dialog import ExportDialog

    templates = [ExportTemplate(template_id="tpl_dev", display_name="Entwickler-Ticket",
                                template_string="Fall {{ case.case_id }}: {{ case.classification.title }}")]
    schemas = [QuestionSchema(schema_id="standard", display_name="Standard Formular")] if with_schema else []
    dialog = ExportDialog(app, case=_case("T-EXP-01"), templates=templates, schemas=schemas,
                          export_service=ExportService(storage), on_case_updated=lambda c: None)
    dialog.update_idletasks()
    assert dialog.active_template.template_id == "tpl_dev"
    assert "T-EXP-01: UI Test Case" in dialog.preview_textbox.get("1.0", "end")


def test_followup_flyout_selects_and_stays_open_until_all_done(app):
    from ui.dialogs.followup_flyout_dialog import FollowupFlyoutDialog

    case1 = _case("T-FW-01", followup_at="2026-08-01T10:00:00", followup_note="Wichtig!")
    case2 = _case("T-FW-02")   # no follow-up date set
    selected, refreshes = [], []
    dialog = FollowupFlyoutDialog(app, due_cases=[case1, case2], on_case_selected=selected.append,
                                  on_refresh=lambda: refreshes.append(1))
    dialog.update_idletasks()

    dialog.on_case_selected(case1)
    assert selected == [case1]

    dialog.complete_followup(case1)
    dialog.update_idletasks()
    assert len(refreshes) == 1 and len(dialog.due_cases) == 1 and dialog.winfo_exists()

    dialog.complete_followup(case2)
    assert len(refreshes) == 2 and dialog.due_cases == []


def test_handover_dialog_passes_note_to_callback(app):
    from ui.dialogs.handover_dialog import HandoverDialog

    colleagues = [Colleague(username="col1", name="Anna Schmidt", is_absent=True, absence_reason="Urlaub"),
                  Colleague(username="col2", name="Bernd Weber")]
    recorded = []
    dialog = HandoverDialog(app, case=_case(), colleagues=colleagues,
                            on_handover_confirmed=lambda *args: recorded.append(args))
    dialog.actor_combo.set("Support")
    dialog.note_entry.insert(0, "Bitte Fall bis 14 Uhr prüfen.")
    dialog.on_confirm()
    assert "Bitte Fall bis 14 Uhr prüfen." in recorded[0][3]


def test_convert_schema_dialog_keeps_matching_form_data(app):
    from ui.dialogs.convert_schema_dialog import ConvertSchemaDialog

    q1 = SchemaField(field_id="q1", label="Problembeschreibung", field_type=FieldType.TEXT)
    schema_1 = QuestionSchema(schema_id="schema_1", display_name="Schema 1", fields=[q1])
    schema_2 = QuestionSchema(schema_id="schema_2", display_name="Schema 2", fields=[
        q1, SchemaField(field_id="q2", label="Dringlichkeit", field_type=FieldType.NUMBER)])
    case = Case(case_id="T-CONV-01", classification=Classification(schema_id="schema_1", title="Altfall"),
                form_data={"q1": "Alte Daten"})
    converted = []
    dialog = ConvertSchemaDialog(app, case=case, schemas=[schema_1, schema_2], author_name="DaniBani",
                                 on_schema_converted=lambda c, s: converted.append(c))
    dialog.schema_combo.set("Schema 2 [schema_2]")
    dialog.on_convert()
    assert converted[0].classification.schema_id == "schema_2"
    assert converted[0].form_data.get("q1") == "Alte Daten"


def test_profile_settings_dialog_saves(app, storage):
    from ui.dialogs.profile_settings_dialog import ProfileSettingsDialog

    profile = storage.load_profile()
    profile.user.name = "Test User"
    updated = []
    dialog = ProfileSettingsDialog(app, profile=profile, storage_service=storage, on_profile_updated=lambda: updated.append(1))
    dialog.update_idletasks()
    dialog.save_settings()
    assert updated
    assert storage.load_profile().user.name == "Test User"


def test_calendar_cobra_and_p2p_dialogs_open_with_their_data(app, seeded_storage, config):
    from services.calendar_email_service import CalendarEmailService
    from services.p2p_sync_service import P2PSyncService
    from ui.dialogs.calendar_export_dialog import CalendarExportDialog
    from ui.dialogs.cobra_import_dialog import CobraImportDialog
    from ui.dialogs.email_calendar_dialog import EmailCalendarDialog
    from ui.dialogs.p2p_diff_dialog import P2PDiffDialog

    cal = CalendarEmailService(config)
    for dlg in (EmailCalendarDialog(app, case=_case(), calendar_email_service=cal, user_name="Agent User"),
                CalendarExportDialog(app, case=_case(), calendar_email_service=cal)):
        dlg.update_idletasks()
        assert dlg.case.case_id == "CASE-UI-100"

    cobra = CobraImportDialog(app, existing_customers=[Customer(customer_id="C-1", practice_name="Test")],
                              on_import_completed=lambda custs: None)
    assert len(cobra.existing_customers) == 1

    colleagues = [Colleague(username="col1", name="Max")] + seeded_storage.load_colleagues()   # col1 has no cases path
    p2p = P2PDiffDialog(app, colleagues=colleagues, p2p_service=P2PSyncService(seeded_storage), on_sync_completed=lambda: None)
    p2p.update_idletasks()
    assert p2p.active_colleague.username == "col1"


# --- Cockpit helpers formerly tested next to the dialogs ---

def test_cockpit_copy_practice_email_only_when_present():
    from ui.views.cockpit_view import CockpitView

    cockpit = CockpitView.__new__(CockpitView)
    copied: list[str] = []
    setattr(cockpit, "clipboard_clear", copied.clear)
    setattr(cockpit, "clipboard_append", copied.append)
    setattr(cockpit, "winfo_toplevel", lambda: None)

    for email, expected in (("praxis@test.de", ["praxis@test.de"]), ("", [])):
        copied.clear()
        cockpit.current_case = Case(case_id="F", customer=CaseCustomer(customer_id="K", practice_name="Dr.", email=email))
        cockpit.on_more_actions_selected("📧 Praxis-E-Mail kopieren")
        assert copied == expected


def test_more_actions_combo_does_not_offer_its_header_label():
    import inspect

    from ui.views.cockpit_layout_builders import CockpitLayoutBuilderMixin

    source = inspect.getsource(CockpitLayoutBuilderMixin._build_toolbar_row)
    values_line = [line for line in source.splitlines() if "values=[" in line][0]
    assert '"⚙ Weitere Aktionen..."' not in values_line


def test_bind_mouse_wheel_to_canvas_reaches_children():
    from utils.ui_utils import bind_mouse_wheel_to_canvas

    class DummyWidget:
        def __init__(self):
            self.bound, self.children = [], []
            self._parent_canvas = None
            self.yview_scroll = None

        def bind(self, event, func, add=None):
            self.bound.append(event)

        def winfo_children(self):
            return self.children

    frame, child = DummyWidget(), DummyWidget()
    frame._parent_canvas = DummyWidget()
    frame._parent_canvas.yview_scroll = lambda n, u: None
    frame.children.append(child)
    bind_mouse_wheel_to_canvas(cast(Any, frame), scroll_frame=cast(Any, frame))
    assert "<MouseWheel>" in child.bound
