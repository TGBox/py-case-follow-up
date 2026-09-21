from pathlib import Path
from typing import cast
from unittest.mock import MagicMock, patch

import pytest

from config import AppConfig
from enums import Channel, LayoutMode
from models.case import Case, CaseCustomer, Classification, WorkflowStatus
from models.customer import Customer
from services.storage_service import StorageService
from ui.app_dialogs import DialogLaunchersMixin


@pytest.fixture
def tmp_config(tmp_path: Path) -> AppConfig:
    return AppConfig(workspace_dir=tmp_path, username="test_user")


def _make_dummy_case(case_id: str, practice_name: str = "Alte Praxis", att_dir: str = "") -> Case:
    return Case(
        case_id=case_id,
        created_at="2026-09-01T10:00:00",
        updated_at="2026-09-01T10:00:00",
        created_by="Tester",
        assigned_to="Tester",
        customer=CaseCustomer(
            customer_id="K-001",
            practice_name=practice_name,
            contact_person="Dr. Alt",
        ),
        classification=Classification(schema_id="s1", title="Testfall"),
        workflow_status=WorkflowStatus(),
        attachment_directory=att_dir,
    )


def test_storage_delete_case_permanently_active_case(tmp_config: AppConfig):
    storage = StorageService(tmp_config)
    case1 = _make_dummy_case("CASE-001")
    case2 = _make_dummy_case("CASE-002")
    storage.save_cases([case1, case2], sync=True)

    assert len(storage.load_cases()) == 2

    # Delete CASE-001
    assert storage.delete_case_permanently("CASE-001") is True

    remaining = storage.load_cases()
    assert len(remaining) == 1
    assert remaining[0].case_id == "CASE-002"

    # Deleting it again should return False
    assert storage.delete_case_permanently("CASE-001") is False


def test_storage_delete_case_permanently_archive(tmp_config: AppConfig):
    storage = StorageService(tmp_config)
    case_archived = _make_dummy_case("CASE-ARCH-001")
    storage.save_archive([case_archived], sync=True)

    assert len(storage.load_archive()) == 1

    # Delete archived case
    assert storage.delete_case_permanently("CASE-ARCH-001") is True

    assert len(storage.load_archive()) == 0
    assert storage.delete_case_permanently("CASE-ARCH-001") is False


def test_storage_delete_case_permanently_nonexistent(tmp_config: AppConfig):
    storage = StorageService(tmp_config)
    storage.save_cases([], sync=True)
    storage.save_archive([], sync=True)

    assert storage.delete_case_permanently("DOES-NOT-EXIST") is False


class DummyApp(DialogLaunchersMixin):
    """Minimal dummy implementing DialogLaunchersMixin for testing on_delete_case and on_change_practice."""

    def __init__(self, tmp_path: Path):
        self.config = AppConfig(workspace_dir=tmp_path, username="Tester")
        self.storage_service = StorageService(self.config)
        self.profile = MagicMock()
        self.profile.user.name = "Tester"
        self.cases = []
        self.customers = [
            Customer(customer_id="K-002", practice_name="Neue Praxis Dr. Neu"),
        ]
        self.active_case = None
        self.refresh_views = MagicMock()
        self.on_case_updated = MagicMock()
        self.on_quick_customer_added = MagicMock()
        self._views = {}

    def is_view_built(self, view_name: str) -> bool:
        # Mirrors App.is_view_built, which looks the layout up in _views. A test
        # that needs a built cockpit puts a stand-in there; everything else keeps
        # the previous behaviour, because _views starts out empty.
        return view_name in self._views


def test_on_delete_case_cancelled_stage1(tmp_path: Path):
    app = DummyApp(tmp_path)
    case = _make_dummy_case("DEL-001")
    app.cases = [case]
    app.storage_service.save_cases([case], sync=True)

    with patch("ui.dialogs.confirm_dialog.ask_confirmation", return_value=False):
        app.on_delete_case(case)

    # Not deleted
    assert len(app.cases) == 1
    assert len(app.storage_service.load_cases()) == 1


def test_on_delete_case_confirmed_with_attachments(tmp_path: Path):
    app = DummyApp(tmp_path)
    att_dir = tmp_path / "attachments_case_001"
    att_dir.mkdir(parents=True, exist_ok=True)
    (att_dir / "doc.pdf").write_bytes(b"pdf content")

    case = _make_dummy_case("DEL-002", att_dir=str(att_dir))
    app.cases = [case]
    app.storage_service.save_cases([case], sync=True)

    # Confirm both stage 1 (case deletion) and stage 2 (attachment folder deletion)
    with patch("ui.dialogs.confirm_dialog.ask_confirmation", side_effect=[True, True]), \
         patch("ui.widgets.toast_notification.ToastNotification"):
        app.on_delete_case(case)

    # Case removed from memory and disk
    assert len(app.cases) == 0
    assert len(app.storage_service.load_cases()) == 0
    # Attachment directory removed from disk
    assert not att_dir.exists()
    cast(MagicMock, app.refresh_views).assert_called_once_with(force_all=True)


def test_on_delete_case_confirmed_keep_attachments(tmp_path: Path):
    app = DummyApp(tmp_path)
    att_dir = tmp_path / "attachments_case_002"
    att_dir.mkdir(parents=True, exist_ok=True)
    (att_dir / "doc.pdf").write_bytes(b"pdf content")

    case = _make_dummy_case("DEL-003", att_dir=str(att_dir))
    app.cases = [case]
    app.storage_service.save_cases([case], sync=True)

    # Confirm stage 1 (case deletion), decline stage 2 (keep attachments)
    with patch("ui.dialogs.confirm_dialog.ask_confirmation", side_effect=[True, False]), \
         patch("ui.widgets.toast_notification.ToastNotification"):
        app.on_delete_case(case)

    # Case removed, attachment dir remains intact
    assert len(app.cases) == 0
    assert len(app.storage_service.load_cases()) == 0
    assert att_dir.exists()
    assert (att_dir / "doc.pdf").exists()


def test_on_change_practice_workflow(tmp_path: Path):
    app = DummyApp(tmp_path)
    case = _make_dummy_case("PRACTICE-001", practice_name="Alte Praxis Dr. Alt")
    app.cases = [case]

    new_cust = CaseCustomer(
        customer_id="K-002",
        practice_name="Neue Praxis Dr. Neu",
        contact_person="Dr. Neu",
    )

    captured_callback = None

    def mock_dialog(parent, case, customers, on_practice_changed, on_customer_added):
        nonlocal captured_callback
        captured_callback = on_practice_changed

    with patch("ui.dialogs.change_practice_dialog.ChangePracticeDialog", side_effect=mock_dialog), \
         patch("ui.widgets.toast_notification.ToastNotification"):
        app.on_change_practice(case)
        assert captured_callback is not None

        # Simulate user confirming practice change with a timeline note
        captured_callback(new_cust, "Praxisübernahme zum Quartalsende.")

    # Verify customer updated
    assert case.customer.practice_name == "Neue Praxis Dr. Neu"
    assert case.customer.customer_id == "K-002"

    # Verify timeline entry added
    assert len(case.timeline) == 1
    t_entry = case.timeline[0]
    assert t_entry.author == "Tester"
    assert t_entry.channel == Channel.INTERNAL_NOTE.value
    assert "Alte Praxis Dr. Alt" in t_entry.note
    assert "Neue Praxis Dr. Neu" in t_entry.note
    assert "Praxisübernahme zum Quartalsende." in t_entry.note
    assert "PRAXIS: Alte Praxis Dr. Alt → Neue Praxis Dr. Neu" in t_entry.status_change

    cast(MagicMock, app.on_case_updated).assert_called_once_with(case)


# ---------------------------------------------------------------------------
# on_delete_case: the paths the original tests left open
# ---------------------------------------------------------------------------


def test_on_delete_case_missing_case_shows_notice_and_keeps_state(tmp_path: Path):
    """A case that is already gone must not look like a successful deletion."""
    app = DummyApp(tmp_path)
    case = _make_dummy_case("DEL-GONE")
    app.cases = [case]           # still in memory ...
    app.storage_service.save_cases([], sync=True)   # ... but no longer on disk

    with patch("ui.dialogs.confirm_dialog.ask_confirmation", return_value=True), \
         patch("ui.dialogs.confirm_dialog.show_notice") as notice, \
         patch("ui.widgets.toast_notification.ToastNotification") as toast:
        app.on_delete_case(case)

    notice.assert_called_once()
    toast.assert_not_called()
    cast(MagicMock, app.refresh_views).assert_not_called()
    # The in-memory list is left alone, so the case does not silently vanish
    # from the UI while it is still somewhere on disk.
    assert len(app.cases) == 1


def test_on_delete_case_without_attachment_dir_skips_second_question(tmp_path: Path):
    """No attachment folder means no second confirmation to answer."""
    app = DummyApp(tmp_path)
    case = _make_dummy_case("DEL-NOATT", att_dir="")
    app.cases = [case]
    app.storage_service.save_cases([case], sync=True)

    with patch("ui.dialogs.confirm_dialog.ask_confirmation", return_value=True) as ask, \
         patch("ui.widgets.toast_notification.ToastNotification"):
        app.on_delete_case(case)

    assert ask.call_count == 1
    assert len(app.cases) == 0


def test_on_delete_case_with_missing_attachment_dir_skips_second_question(tmp_path: Path):
    """A recorded folder that no longer exists must not be asked about either."""
    app = DummyApp(tmp_path)
    case = _make_dummy_case("DEL-STALEATT", att_dir=str(tmp_path / "never_created"))
    app.cases = [case]
    app.storage_service.save_cases([case], sync=True)

    with patch("ui.dialogs.confirm_dialog.ask_confirmation", return_value=True) as ask, \
         patch("ui.widgets.toast_notification.ToastNotification"):
        app.on_delete_case(case)

    assert ask.call_count == 1
    assert len(app.cases) == 0


def test_on_delete_case_deletes_archived_case(tmp_path: Path):
    """Deleting reaches the archive, not just the active list."""
    app = DummyApp(tmp_path)
    case = _make_dummy_case("DEL-ARCHIVED")
    app.cases = []
    app.storage_service.save_cases([], sync=True)
    app.storage_service.save_archive([case], sync=True)

    with patch("ui.dialogs.confirm_dialog.ask_confirmation", return_value=True), \
         patch("ui.widgets.toast_notification.ToastNotification"):
        app.on_delete_case(case)

    assert len(app.storage_service.load_archive()) == 0
    cast(MagicMock, app.refresh_views).assert_called_once_with(force_all=True)


# ---------------------------------------------------------------------------
# on_delete_case -> cockpit detail pane
#
# The pane used to keep showing a deleted case until the user clicked another
# one, because the guard asked is_view_built("cockpit") while the registry is
# keyed by LayoutMode.COCKPIT.value ("COCKPIT") - so the branch never ran.
# ---------------------------------------------------------------------------


def _app_with_cockpit(tmp_path: Path, open_case: Case | None):
    app = DummyApp(tmp_path)
    cockpit = MagicMock()
    cockpit.current_case = open_case
    app.cockpit_view = cockpit
    app._views[LayoutMode.COCKPIT.value] = cockpit
    return app, cockpit


def test_on_delete_case_clears_cockpit_showing_that_case(tmp_path: Path):
    case = _make_dummy_case("DEL-OPEN")
    app, cockpit = _app_with_cockpit(tmp_path, open_case=case)
    app.cases = [case]
    app.storage_service.save_cases([case], sync=True)

    with patch("ui.dialogs.confirm_dialog.ask_confirmation", return_value=True), \
         patch("ui.widgets.toast_notification.ToastNotification"):
        app.on_delete_case(case)

    cockpit.clear_current_case.assert_called_once_with()


def test_on_delete_case_leaves_cockpit_showing_a_different_case(tmp_path: Path):
    open_case = _make_dummy_case("DEL-OTHER-OPEN")
    doomed = _make_dummy_case("DEL-OTHER-DOOMED")
    app, cockpit = _app_with_cockpit(tmp_path, open_case=open_case)
    app.cases = [open_case, doomed]
    app.storage_service.save_cases([open_case, doomed], sync=True)

    with patch("ui.dialogs.confirm_dialog.ask_confirmation", return_value=True), \
         patch("ui.widgets.toast_notification.ToastNotification"):
        app.on_delete_case(doomed)

    cockpit.clear_current_case.assert_not_called()


def test_on_delete_case_survives_a_failing_cockpit_reset(tmp_path: Path):
    """A broken detail pane must not abort the deletion that already happened."""
    case = _make_dummy_case("DEL-BOOM")
    app, cockpit = _app_with_cockpit(tmp_path, open_case=case)
    cockpit.clear_current_case.side_effect = RuntimeError("widget already destroyed")
    app.cases = [case]
    app.storage_service.save_cases([case], sync=True)

    with patch("ui.dialogs.confirm_dialog.ask_confirmation", return_value=True), \
         patch("ui.widgets.toast_notification.ToastNotification"):
        app.on_delete_case(case)

    assert len(app.storage_service.load_cases()) == 0
    cast(MagicMock, app.refresh_views).assert_called_once_with(force_all=True)


# ---------------------------------------------------------------------------
# CockpitView.clear_current_case - the reset the branch above triggers
# ---------------------------------------------------------------------------


@pytest.fixture
def cockpit(tmp_path: Path):
    import customtkinter as ctk
    from services.attachment_service import AttachmentService
    from services.scoring_service import ScoringService
    from services.wiki_sync_service import WikiSyncService
    from ui.views.cockpit_view import CockpitView

    config = AppConfig(workspace_dir=tmp_path)
    storage = StorageService(config)

    app = ctk.CTk()
    app.withdraw()
    view = CockpitView(
        app,
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
    yield view
    try:
        app.destroy()
    except Exception:
        pass


def test_clear_current_case_empties_every_panel(cockpit):
    from services.i18n_service import tr

    case = _make_dummy_case("COCKPIT-001", practice_name="Praxis Vorher")
    cockpit.on_select_case_from_list(case)

    # Precondition: the pane really is showing the case.
    assert cockpit.current_case is case
    assert case.case_id in cockpit.case_title_label.cget("text")
    assert "Praxis Vorher" in cockpit.kunde_label.cget("text")
    assert cockpit.save_btn.cget("state") == "normal"

    cockpit.clear_current_case()

    assert cockpit.current_case is None
    assert cockpit.case_title_label.cget("text") == tr(
        "cockpit.select_case_prompt", "Bitte einen Fall auswählen"
    )
    assert cockpit.kunde_label.cget("text") == ""
    assert cockpit.ansprechpartner_label.cget("text") == ""
    assert cockpit.save_btn.cget("state") == "disabled"
    # The sidebar caches which case each tab last rendered - a stale entry would
    # make the tab consider itself up to date and keep the deleted case around.
    assert cockpit._loaded_tab_case_ids == {}


def test_clear_current_case_is_safe_to_call_twice(cockpit):
    """Deleting two cases in a row must not trip over an already empty pane."""
    cockpit.on_select_case_from_list(_make_dummy_case("COCKPIT-002"))
    cockpit.clear_current_case()
    cockpit.clear_current_case()
    assert cockpit.current_case is None


def test_selecting_a_case_after_clearing_restores_the_pane(cockpit):
    cockpit.on_select_case_from_list(_make_dummy_case("COCKPIT-003"))
    cockpit.clear_current_case()

    again = _make_dummy_case("COCKPIT-004", practice_name="Praxis Nachher")
    cockpit.on_select_case_from_list(again)

    assert cockpit.current_case is again
    assert "COCKPIT-004" in cockpit.case_title_label.cget("text")
    assert "Praxis Nachher" in cockpit.kunde_label.cget("text")
    assert cockpit.save_btn.cget("state") == "normal"


# ---------------------------------------------------------------------------
# ChangePracticeDialog itself
# ---------------------------------------------------------------------------


def _full_customer(customer_id: str = "K-900", **kwargs) -> Customer:
    from models.customer import Contact

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


@pytest.fixture
def practice_dialog(tmp_path: Path):
    """Builds a real ChangePracticeDialog plus the pieces to inspect it."""
    import customtkinter as ctk
    from ui.dialogs.change_practice_dialog import ChangePracticeDialog

    app = ctk.CTk()
    app.withdraw()

    case = _make_dummy_case("CPD-001", practice_name="Praxis Start")
    customers = [_full_customer()]
    calls: list[tuple] = []

    dialog = ChangePracticeDialog(
        app,
        case=case,
        customers=customers,
        on_practice_changed=lambda cust, note: calls.append((cust, note)),
        on_customer_added=lambda c: calls.append(("added", c)),
    )
    yield dialog, case, customers, calls
    try:
        app.destroy()
    except Exception:
        pass


def test_dialog_lists_customers_with_id_in_the_label(practice_dialog):
    dialog, _case, customers, _calls = practice_dialog
    display = dialog._customer_display_name(customers[0])
    assert display == "Praxis Ziel (K-900)"
    assert display in dialog._customer_by_display


def test_dialog_search_text_covers_contacts_and_address(practice_dialog):
    dialog, _case, customers, _calls = practice_dialog
    haystack = dialog._customer_search_text(customers[0])
    # Searching by a contact or a town has to find the practice, otherwise the
    # combo is only usable for people who remember the practice name exactly.
    for needle in ("Dr. Ziel", "dr@ziel.de", "Musterstadt", "0900-111"):
        assert needle in haystack


def test_dialog_confirm_without_selection_reports_and_does_nothing(practice_dialog):
    dialog, _case, _customers, calls = practice_dialog
    dialog.customer_combo.set_selected("")

    dialog.on_confirm()

    assert dialog.error_label.cget("text") != ""
    assert calls == []


def test_dialog_confirm_declined_keeps_the_practice(practice_dialog):
    dialog, _case, customers, calls = practice_dialog
    dialog.customer_combo.set_selected(dialog._customer_display_name(customers[0]))

    with patch("ui.dialogs.confirm_dialog.ask_confirmation", return_value=False):
        dialog.on_confirm()

    assert calls == []


def test_dialog_confirm_hands_over_customer_snapshot_and_note(practice_dialog):
    dialog, _case, customers, calls = practice_dialog
    dialog.customer_combo.set_selected(dialog._customer_display_name(customers[0]))
    dialog.note_textbox.insert("1.0", "  Übernahme zum 01.10.  ")

    with patch("ui.dialogs.confirm_dialog.ask_confirmation", return_value=True), \
         patch.object(dialog, "close_dialog"):
        dialog.on_confirm()

    assert len(calls) == 1
    new_cust, note = calls[0]
    assert new_cust.customer_id == "K-900"
    assert new_cust.practice_name == "Praxis Ziel"
    # The first contact wins over the practice-level fields.
    assert new_cust.contact_person == "Dr. Ziel"
    assert new_cust.phone == "0900-222"
    assert new_cust.email == "dr@ziel.de"
    assert note == "Übernahme zum 01.10."


def test_dialog_confirm_falls_back_to_practice_contact_details(tmp_path: Path):
    """A practice without contacts still hands over its own phone and mail."""
    import customtkinter as ctk
    from ui.dialogs.change_practice_dialog import ChangePracticeDialog

    app = ctk.CTk()
    app.withdraw()
    try:
        cust = _full_customer("K-901", practice_name="Praxis Ohne", contacts=[])
        calls: list[tuple] = []
        dialog = ChangePracticeDialog(
            app,
            case=_make_dummy_case("CPD-002"),
            customers=[cust],
            on_practice_changed=lambda c, n: calls.append((c, n)),
        )
        dialog.customer_combo.set_selected(dialog._customer_display_name(cust))

        with patch("ui.dialogs.confirm_dialog.ask_confirmation", return_value=True), \
             patch.object(dialog, "close_dialog"):
            dialog.on_confirm()

        assert len(calls) == 1
        new_cust, _note = calls[0]
        assert new_cust.contact_person == ""
        assert new_cust.phone == "0900-111"
        assert new_cust.email == "praxis@ziel.de"
    finally:
        try:
            app.destroy()
        except Exception:
            pass


def test_dialog_confirm_carries_the_vip_flag(tmp_path: Path):
    import customtkinter as ctk
    from ui.dialogs.change_practice_dialog import ChangePracticeDialog

    app = ctk.CTk()
    app.withdraw()
    try:
        cust = _full_customer("K-902", practice_name="Praxis VIP", is_vip=True)
        calls: list[tuple] = []
        dialog = ChangePracticeDialog(
            app,
            case=_make_dummy_case("CPD-003"),
            customers=[cust],
            on_practice_changed=lambda c, n: calls.append((c, n)),
        )
        dialog.customer_combo.set_selected(dialog._customer_display_name(cust))

        with patch("ui.dialogs.confirm_dialog.ask_confirmation", return_value=True), \
             patch.object(dialog, "close_dialog"):
            dialog.on_confirm()

        assert calls[0][0].is_vip is True
    finally:
        try:
            app.destroy()
        except Exception:
            pass


def test_dialog_quick_added_customer_is_selected_and_reported(practice_dialog):
    dialog, _case, customers, calls = practice_dialog
    fresh = _full_customer("K-999", practice_name="Frisch Angelegt")

    dialog._on_quick_customer_created(fresh)

    assert fresh in dialog.customers
    assert ("added", fresh) in calls
    expected = dialog._customer_display_name(fresh)
    assert expected in dialog._customer_by_display
    assert dialog.customer_combo.get() == expected
