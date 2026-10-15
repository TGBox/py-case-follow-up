"""Case-level dialogs: change practice, permanent case deletion, and case print / HTML report export."""

import webbrowser
from pathlib import Path
from typing import cast
from unittest.mock import MagicMock, patch

import pytest

from config import AppConfig
from enums import Actor, BoardColumn, Channel, LayoutMode
from models.case import Case, CaseCustomer, Classification, TimelineEntry, WorkflowStatus
from models.customer import Contact, Customer
from services.attachment_service import AttachmentService
from services.storage_service import StorageService
from ui.app_dialogs import DialogLaunchersMixin

ASK = "ui.dialogs.confirm_dialog.ask_confirmation"
TOAST = "ui.widgets.toast_notification.ToastNotification"

PNG_1PX = (
    b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01\x08\x06\x00\x00\x00\x1f\x15c4"
    b"\x00\x00\x00\nIDATx\x9cc`\x00\x00\x00\x02\x00\x01H\xaf\xa4q\x00\x00\x00\x00IEND\xaeB`\x82"
)


def _case(case_id: str, practice_name: str = "Alte Praxis", att_dir: str = "") -> Case:
    return Case(
        case_id=case_id,
        created_at="2026-09-01T10:00:00",
        updated_at="2026-09-01T10:00:00",
        created_by="Tester",
        assigned_to="Tester",
        customer=CaseCustomer(customer_id="K-001", practice_name=practice_name, contact_person="Dr. Alt"),
        classification=Classification(schema_id="s1", title="Testfall"),
        workflow_status=WorkflowStatus(),
        attachment_directory=att_dir,
    )


class DummyApp(DialogLaunchersMixin):
    """Minimal host for DialogLaunchersMixin.on_delete_case / on_change_practice."""

    def __init__(self, tmp_path: Path):
        self.config = AppConfig(workspace_dir=tmp_path, username="Tester")
        self.storage_service = StorageService(self.config)
        self.profile = MagicMock()
        self.profile.user.name = "Tester"
        self.cases = []
        self.customers = [Customer(customer_id="K-002", practice_name="Neue Praxis Dr. Neu")]
        self.active_case = None
        self.refresh_views = MagicMock()
        self.on_case_updated = MagicMock()
        self.on_quick_customer_added = MagicMock()
        self._views = {}

    def is_view_built(self, view_name: str) -> bool:
        return view_name in self._views


def _app_with(tmp_path: Path, *cases: Case) -> DummyApp:
    app = DummyApp(tmp_path)
    app.cases = list(cases)
    app.storage_service.save_cases(list(cases), sync=True)
    return app


# ---------------------------------------------------------------------------
# Permanent deletion
# ---------------------------------------------------------------------------


def test_storage_delete_case_permanently_reaches_active_and_archive(storage):
    storage.save_archive([_case("CASE-ARCH-001")], sync=True)
    assert storage.delete_case_permanently("CASE-ARCH-001") is True  # active list read from disk
    assert storage.load_archive() == []

    storage.save_cases([_case("CASE-001"), _case("CASE-002")], sync=True)
    assert storage.delete_case_permanently("CASE-001") is True
    assert [c.case_id for c in storage.load_cases()] == ["CASE-002"]

    for gone in ("CASE-001", "CASE-ARCH-001", "DOES-NOT-EXIST"):
        assert storage.delete_case_permanently(gone) is False


def test_on_delete_case_cancelled_keeps_case(tmp_path: Path):
    case = _case("DEL-001")
    app = _app_with(tmp_path, case)
    with patch(ASK, return_value=False):
        app.on_delete_case(case)
    assert len(app.cases) == 1
    assert len(app.storage_service.load_cases()) == 1


@pytest.mark.parametrize("delete_attachments", [True, False])
def test_on_delete_case_asks_separately_about_attachment_folder(tmp_path: Path, delete_attachments: bool):
    att_dir = tmp_path / "attachments_case_001"
    att_dir.mkdir()
    (att_dir / "doc.pdf").write_bytes(b"pdf")
    case = _case("DEL-ATT", att_dir=str(att_dir))
    app = _app_with(tmp_path, case)

    with patch(ASK, side_effect=[True, delete_attachments]), patch(TOAST):
        app.on_delete_case(case)

    assert app.cases == []
    assert app.storage_service.load_cases() == []
    assert att_dir.exists() is not delete_attachments
    cast(MagicMock, app.refresh_views).assert_called_once_with(force_all=True)


@pytest.mark.parametrize("att_dir", ["", "never_created"])
def test_on_delete_case_without_existing_attachment_dir_asks_once(tmp_path: Path, att_dir: str):
    """No (or a stale) attachment folder means no second confirmation."""
    case = _case("DEL-NOATT", att_dir=str(tmp_path / att_dir) if att_dir else "")
    app = _app_with(tmp_path, case)
    with patch(ASK, return_value=True) as ask, patch(TOAST):
        app.on_delete_case(case)
    assert ask.call_count == 1
    assert app.cases == []


def test_on_delete_case_missing_case_shows_notice_and_keeps_state(tmp_path: Path):
    """A case that is already gone must not look like a successful deletion."""
    case = _case("DEL-GONE")
    app = DummyApp(tmp_path)
    app.cases = [case]
    app.storage_service.save_cases([], sync=True)

    with patch(ASK, return_value=True), \
         patch("ui.dialogs.confirm_dialog.show_notice") as notice, \
         patch(TOAST) as toast:
        app.on_delete_case(case)

    notice.assert_called_once()
    toast.assert_not_called()
    cast(MagicMock, app.refresh_views).assert_not_called()
    assert len(app.cases) == 1


def test_on_delete_case_deletes_archived_case(tmp_path: Path):
    case = _case("DEL-ARCHIVED")
    app = _app_with(tmp_path)
    app.storage_service.save_archive([case], sync=True)
    with patch(ASK, return_value=True), patch(TOAST):
        app.on_delete_case(case)
    assert app.storage_service.load_archive() == []
    cast(MagicMock, app.refresh_views).assert_called_once_with(force_all=True)


@pytest.mark.parametrize("open_is_doomed, clear_fails", [(True, False), (False, False), (True, True)])
def test_on_delete_case_resets_cockpit_only_for_the_open_case(tmp_path: Path, open_is_doomed, clear_fails):
    """Regression: the guard checked is_view_built("cockpit") while the registry key is "COCKPIT",
    so the detail pane kept showing a deleted case. A failing reset must not abort the deletion."""
    doomed = _case("DEL-DOOMED")
    other = _case("DEL-OTHER")
    app = _app_with(tmp_path, doomed, other)
    cockpit = MagicMock()
    cockpit.current_case = doomed if open_is_doomed else other
    if clear_fails:
        cockpit.clear_current_case.side_effect = RuntimeError("widget already destroyed")
    app.cockpit_view = cockpit
    app._views[LayoutMode.COCKPIT.value] = cockpit

    with patch(ASK, return_value=True), patch(TOAST):
        app.on_delete_case(doomed)

    assert cockpit.clear_current_case.call_count == (1 if open_is_doomed else 0)
    assert [c.case_id for c in app.storage_service.load_cases()] == ["DEL-OTHER"]
    cast(MagicMock, app.refresh_views).assert_called_once_with(force_all=True)


@pytest.fixture
def cockpit(root, config, storage):
    from services.scoring_service import ScoringService
    from services.wiki_sync_service import WikiSyncService
    from ui.views.cockpit_view import CockpitView

    return CockpitView(
        root,
        author_name="Tester",
        scoring_service=ScoringService(),
        attachment_service=AttachmentService(config),
        wiki_service=WikiSyncService(config),
        on_case_updated=lambda c: None,
        on_case_selected=lambda c: None,
        on_search_changed=lambda s: None,
        on_open_export_dialog=lambda c: None,
        on_archive_case=lambda c: None,
        app_config=config,
        profile=storage.load_profile(),
        storage_service=storage,
    )


def test_cockpit_clear_current_case_empties_pane_and_can_be_reselected(cockpit):
    from services.i18n_service import tr

    case = _case("COCKPIT-001", practice_name="Praxis Vorher")
    cockpit.on_select_case_from_list(case)
    assert case.case_id in cockpit.case_title_label.cget("text")
    assert "Praxis Vorher" in cockpit.kunde_label.cget("text")
    assert cockpit.save_btn.cget("state") == "normal"

    cockpit.clear_current_case()
    cockpit.clear_current_case()  # deleting two cases in a row must be safe

    assert cockpit.current_case is None
    assert cockpit.case_title_label.cget("text") == tr("cockpit.select_case_prompt", "Bitte einen Fall auswählen")
    assert cockpit.kunde_label.cget("text") == ""
    assert cockpit.ansprechpartner_label.cget("text") == ""
    assert cockpit.save_btn.cget("state") == "disabled"
    # A stale per-tab cache entry would keep the deleted case rendered in the sidebar.
    assert cockpit._loaded_tab_case_ids == {}

    again = _case("COCKPIT-004", practice_name="Praxis Nachher")
    cockpit.on_select_case_from_list(again)
    assert cockpit.current_case is again
    assert "COCKPIT-004" in cockpit.case_title_label.cget("text")
    assert "Praxis Nachher" in cockpit.kunde_label.cget("text")
    assert cockpit.save_btn.cget("state") == "normal"


# ---------------------------------------------------------------------------
# Change practice
# ---------------------------------------------------------------------------


def test_on_change_practice_updates_customer_and_logs_timeline(tmp_path: Path):
    app = DummyApp(tmp_path)
    case = _case("PRACTICE-001", practice_name="Alte Praxis Dr. Alt")
    app.cases = [case]
    new_cust = CaseCustomer(customer_id="K-002", practice_name="Neue Praxis Dr. Neu", contact_person="Dr. Neu")
    captured = {}

    def fake_dialog(parent, case, customers, on_practice_changed, on_customer_added):
        captured["cb"] = on_practice_changed

    with patch("ui.dialogs.change_practice_dialog.ChangePracticeDialog", side_effect=fake_dialog), patch(TOAST):
        app.on_change_practice(case)
        captured["cb"](new_cust, "Praxisübernahme zum Quartalsende.")

    assert (case.customer.customer_id, case.customer.practice_name) == ("K-002", "Neue Praxis Dr. Neu")
    assert len(case.timeline) == 1
    entry = case.timeline[0]
    assert entry.author == "Tester"
    assert entry.channel == Channel.INTERNAL_NOTE.value
    for text in ("Alte Praxis Dr. Alt", "Neue Praxis Dr. Neu", "Praxisübernahme zum Quartalsende."):
        assert text in entry.note
    assert "PRAXIS: Alte Praxis Dr. Alt → Neue Praxis Dr. Neu" in entry.status_change
    cast(MagicMock, app.on_case_updated).assert_called_once_with(case)


def _customer(customer_id: str = "K-900", **kwargs) -> Customer:
    defaults = dict(
        customer_id=customer_id,
        practice_name="Praxis Ziel",
        phone_main="0900-111",
        email_address="praxis@ziel.de",
        city="Musterstadt",
        contacts=[Contact(name="Dr. Ziel", role="Inhaber", phone="0900-222", email="dr@ziel.de")],
    )
    defaults.update(kwargs)
    return Customer(**defaults)


def _practice_dialog(root, customer: Customer):
    from ui.dialogs.change_practice_dialog import ChangePracticeDialog

    calls: list[tuple] = []
    dialog = ChangePracticeDialog(
        root,
        case=_case("CPD-001", practice_name="Praxis Start"),
        customers=[customer],
        on_practice_changed=lambda cust, note: calls.append((cust, note)),
        on_customer_added=lambda c: calls.append(("added", c)),
    )
    return dialog, calls


def test_change_practice_dialog_lists_and_searches_customers(root):
    cust = _customer()
    dialog, _ = _practice_dialog(root, cust)
    display = dialog._customer_display_name(cust)
    assert display == "Praxis Ziel (K-900)"
    assert display in dialog._customer_by_display
    # Searching by contact or town must find the practice.
    haystack = dialog._customer_search_text(cust)
    for needle in ("Dr. Ziel", "dr@ziel.de", "Musterstadt", "0900-111"):
        assert needle in haystack


def test_change_practice_dialog_confirm_requires_selection_and_confirmation(root):
    cust = _customer()
    dialog, calls = _practice_dialog(root, cust)

    dialog.customer_combo.set_selected("")
    dialog.on_confirm()
    assert dialog.error_label.cget("text") != ""

    dialog.customer_combo.set_selected(dialog._customer_display_name(cust))
    with patch(ASK, return_value=False):
        dialog.on_confirm()
    assert calls == []


@pytest.mark.parametrize(
    "kwargs, expected",
    [
        ({}, ("Dr. Ziel", "0900-222", "dr@ziel.de", False)),  # first contact wins
        ({"contacts": []}, ("", "0900-111", "praxis@ziel.de", False)),  # practice-level fallback
        ({"is_vip": True}, ("Dr. Ziel", "0900-222", "dr@ziel.de", True)),
    ],
)
def test_change_practice_dialog_confirm_hands_over_customer_snapshot(root, kwargs, expected):
    cust = _customer(**kwargs)
    dialog, calls = _practice_dialog(root, cust)
    dialog.customer_combo.set_selected(dialog._customer_display_name(cust))
    dialog.note_textbox.insert("1.0", "  Übernahme zum 01.10.  ")

    with patch(ASK, return_value=True), patch.object(dialog, "close_dialog"):
        dialog.on_confirm()

    assert len(calls) == 1
    new_cust, note = calls[0]
    assert (new_cust.customer_id, new_cust.practice_name) == ("K-900", "Praxis Ziel")
    assert (new_cust.contact_person, new_cust.phone, new_cust.email, new_cust.is_vip) == expected
    assert note == "Übernahme zum 01.10."


def test_change_practice_dialog_selects_quick_added_customer(root):
    dialog, calls = _practice_dialog(root, _customer())
    fresh = _customer("K-999", practice_name="Frisch Angelegt")

    dialog._on_quick_customer_created(fresh)

    assert fresh in dialog.customers
    assert ("added", fresh) in calls
    assert dialog.customer_combo.get() == dialog._customer_display_name(fresh)


# ---------------------------------------------------------------------------
# Print / HTML report
# ---------------------------------------------------------------------------


def test_case_print_dialog_builds_opens_and_prints_report(root, config, monkeypatch):
    att_service = AttachmentService(config)
    case = Case(
        case_id="T-2026-PRINT-OPT",
        customer=CaseCustomer(customer_id="K-55", practice_name="Praxis Dr. Med. Test", is_vip=True),
        classification=Classification(title="Druckoptionen Testfall", calculated_score=92.0),
        workflow_status=WorkflowStatus(board_column=BoardColumn.ACTION_REQUIRED, current_actor=Actor.SUPPORT),
        created_by="DaniBani",
        form_data={"Modul": "Abrechnung", "Betrag": "120,50 €"},
        timeline=[TimelineEntry(timestamp="2026-08-25T11:00:00", author="DaniBani", note="Korrekturdatei erhalten.")],
    )
    (att_service.get_case_attachment_dir(case) / "screenshot.png").write_bytes(PNG_1PX)
    from ui.dialogs.case_print_dialog import CasePrintDialog

    dialog = CasePrintDialog(root, case, attachment_service=att_service)
    html_print = dialog.build_html_content(auto_print=True)
    assert "window.print()" in html_print
    for text in ("T-2026-PRINT-OPT", "Praxis Dr. Med. Test", "VIP-Kunde", "data:image/png;base64"):
        assert text in html_print
    html_static = dialog.build_html_content(auto_print=False)
    assert "window.addEventListener('DOMContentLoaded'" not in html_static

    opened: list[str] = []
    monkeypatch.setattr(webbrowser, "open", lambda uri: opened.append(uri))
    dialog.generate_and_open_html()
    CasePrintDialog(root, case, attachment_service=att_service).generate_and_print_pdf()
    assert "Fallbericht_T-2026-PRINT-OPT.html" in opened[0]
    assert "Fallbericht_T-2026-PRINT-OPT_Print.html" in opened[1]


def test_compact_report_layout_with_and_without_customer():
    from services.case_report_builder import generate_case_report_html

    case = Case(
        case_id="T-COMPACT-01",
        customer=CaseCustomer(customer_id="K-100", practice_name="Gemeinschaftspraxis Nord"),
        classification=Classification(title="Kompakt-Test", calculated_score=75.0),
        workflow_status=WorkflowStatus(board_column=BoardColumn.ACTION_REQUIRED, current_actor=Actor.SUPPORT),
        created_by="Agent1",
        form_data={"Kurzfeld": "Wert1", "Langfeld": "x" * 120},
        timeline=[TimelineEntry(timestamp="2026-08-25T14:00:00", author="Agent1", channel="TELEPHONE", note="Erster Anruf")],
    )

    html = generate_case_report_html(case, include_customer=True, include_fields=True)
    for marker in ("@page { size: A4 portrait; margin: 8mm 10mm; }", "class='top-grid'", "Gemeinschaftspraxis Nord",
                   "class='field-card'", "class='field-card full-width'", "class='timeline-list'", "class='entry'"):
        assert marker in html

    html_no_cust = generate_case_report_html(case, include_customer=False, include_fields=True)
    assert "class='top-grid'" not in html_no_cust
    assert "Gemeinschaftspraxis Nord" not in html_no_cust
    assert "T-COMPACT-01" in html_no_cust
    assert "class='fields-grid'" in html_no_cust


def test_export_dialog_builds_the_same_compact_report(root):
    from services.export_service import ExportService
    from ui.dialogs.export_dialog import ExportDialog

    case = Case(
        case_id="T-EXPORT-COMPACT",
        customer=CaseCustomer(customer_id="K-200", practice_name="Test Praxis"),
        classification=Classification(title="Export Compact"),
        workflow_status=WorkflowStatus(board_column=BoardColumn.ACTION_REQUIRED, current_actor=Actor.SUPPORT),
    )
    dialog = ExportDialog(root, case, templates=[], schemas=[], export_service=ExportService(), on_case_updated=lambda c: None)
    html = dialog.build_html_content(auto_print=False)
    for marker in ("@page { size: A4 portrait; margin: 8mm 10mm; }", "class='top-grid'", "Test Praxis", "T-EXPORT-COMPACT"):
        assert marker in html


def _localization_case() -> Case:
    return Case(
        case_id="T-I18N-01",
        classification=Classification(schema_id="schema_quick", title="Lokalisierungstest", urgency_level="RED", calculated_score=820.0),
        workflow_status=WorkflowStatus(board_column=BoardColumn.ACTION_REQUIRED, current_actor=Actor.SUPPORT),
        created_by="Agent1",
        form_data={"module_name": "Abrechnung", "unformatted_description": "Text"},
        timeline=[
            TimelineEntry(timestamp="2026-08-04T16:05:00", author="Agent1", channel="PHONE_INBOUND", note="Anruf"),
            TimelineEntry(timestamp="2026-09-14T13:46:00", author="Agent1", channel="INTERNAL_NOTE", note="Vermerk"),
        ],
    )


def test_report_localizes_identifiers_and_follows_language():
    """Regression: the report showed raw identifiers (PHONE_INBOUND, module_name, RED) and was German-only."""
    from services.case_report_builder import generate_case_report_html
    from services.i18n_service import get_i18n

    html = generate_case_report_html(_localization_case(), include_customer=False, include_fields=True)
    for raw in ("PHONE_INBOUND", "INTERNAL_NOTE", "module_name", "unformatted_description", "(RED)"):
        assert raw not in html, raw
    for text in ("Telefonat", "Interner Vermerk", "Betroffenes Modul / Programmbereich (optional)",
                 "Unformatierte Informationen / Beschreibung", "820 Pkt. (Hoch)"):
        assert text in html

    get_i18n().current_language = "en"
    html_en = generate_case_report_html(_localization_case(), include_customer=False, include_fields=True)
    for text in ("Phone Call", "Internal Note", "820 pts (High)"):
        assert text in html_en
    assert "Telefonat" not in html_en


def test_report_falls_back_to_the_stored_schema_label():
    """Schema-builder schemas have no locale entries, so the stored label must be used (else the raw key)."""
    from models.schema import QuestionSchema, SchemaField
    from services.case_report_builder import generate_case_report_html

    case = _localization_case()
    case.form_data = {"eigenes_feld": "Wert"}
    schemas = [QuestionSchema(schema_id="schema_quick", fields=[SchemaField(field_id="eigenes_feld", label="Selbstgebautes Feld")])]

    html = generate_case_report_html(case, include_customer=False, include_fields=True, schemas=schemas)
    assert "Selbstgebautes Feld" in html
    assert "eigenes_feld" not in html
    assert "eigenes_feld" in generate_case_report_html(case, include_customer=False, include_fields=True)
