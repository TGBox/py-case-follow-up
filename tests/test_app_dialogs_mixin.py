"""Tests for src/ui/app_dialogs.py (DialogLaunchersMixin).

This module had ZERO test coverage before (confirmed via a test-coverage
audit). It's mixed into SupportCockpitApp exactly as `class
SupportCockpitApp(DialogLaunchersMixin, ctk.CTk)` (see src/ui/app.py) and
carries all "open_*_dialog" openers plus the closely related case-selection /
case-update event handlers. We test it the same way: a minimal
`class _FakeHost(DialogLaunchersMixin, ctk.CTk)` that supplies just the
`self.xxx` attributes each method touches, so the mixin's actual business
logic (not the dialogs it opens, which have their own tests) gets exercised.

Dialog classes themselves are monkeypatched with lightweight recorders where
the point of the test is "was the right dialog opened with the right
arguments" rather than the dialog's own internal behavior.
"""

from pathlib import Path
import customtkinter as ctk
import pytest

from config import AppConfig
from enums import Actor, BoardColumn, Channel
from models.case import Case, CaseCustomer, Classification, WorkflowStatus
from models.customer import Customer
from models.profile import Colleague
from services.storage_service import StorageService
from services.customer_service import CustomerService
from services.scoring_service import ScoringService

import ui.app_dialogs as app_dialogs_module
from ui.app_dialogs import DialogLaunchersMixin


class _FakeCockpitView:
    def __init__(self):
        self.current_case = None
        self.author_name = ""
        self.wiedervorlage_display_updates = 0
        self.selected_from_list = []

    def _update_wiedervorlage_display(self):
        self.wiedervorlage_display_updates += 1

    def on_select_case_from_list(self, case):
        self.selected_from_list.append(case)


class _FakeHost(DialogLaunchersMixin, ctk.CTk):
    """Minimal stand-in for SupportCockpitApp providing only the attributes
    DialogLaunchersMixin's methods actually touch."""

    def __init__(self, storage: StorageService, tmp_path: Path):
        super().__init__()
        self.withdraw()

        self.storage_service = storage
        self.customer_service = CustomerService(storage)
        self.scoring_service = ScoringService()
        self.export_service = None
        self.p2p_service = None
        self.calendar_email_service = None
        self.snippet_service = None

        self.profile = storage.load_profile()
        self.cases: list[Case] = []
        self.customers: list[Customer] = []
        self.colleagues: list[Colleague] = []
        self.schemas: list = []
        self.templates: list = []

        self.active_case = None
        self.search_query = ""

        self.cockpit_view = _FakeCockpitView()
        self.active_view = self.cockpit_view

        self.refresh_views_calls = 0
        self.bring_to_foreground_calls = 0
        self.switch_to_cockpit_calls = []

        self.user_btn = ctk.CTkLabel(self, text="")

    # --- stand-ins for methods DialogLaunchersMixin expects on `self` ---
    def refresh_views(self, force_all: bool = False):
        self.refresh_views_calls += 1

    def bring_to_foreground(self):
        self.bring_to_foreground_calls += 1

    def switch_to_cockpit_view_for_case(self, case: Case):
        self.switch_to_cockpit_calls.append(case)
        self.cockpit_view.current_case = case

    def load_all_data(self):
        pass


@pytest.fixture
def host(tmp_path: Path):
    config = AppConfig(workspace_dir=tmp_path)
    storage = StorageService(config)
    h = _FakeHost(storage, tmp_path)
    yield h
    try:
        h.destroy()
    except Exception:
        pass


def _make_case(case_id="T-APPD-01", **wf_kwargs) -> Case:
    return Case(
        case_id=case_id,
        customer=CaseCustomer(customer_id="K-1", practice_name="Praxis AppDialogs"),
        classification=Classification(title="AppDialogs Test"),
        workflow_status=WorkflowStatus(board_column=BoardColumn.NEW, **wf_kwargs),
    )


# ---------------------------------------------------------------------------
# Case selection / search / update / archive
# ---------------------------------------------------------------------------


def test_on_search_changed_sets_query_and_refreshes(host):
    host.on_search_changed("praxis alpha")
    assert host.search_query == "praxis alpha"
    assert host.refresh_views_calls == 1


def test_on_case_selected_switches_view_when_different_case(host):
    case = _make_case()
    host.on_case_selected(case)

    assert host.bring_to_foreground_calls == 1
    assert host.active_case is case
    assert host.switch_to_cockpit_calls == [case]


def test_on_case_selected_does_not_resw_switch_when_already_current(host):
    case = _make_case()
    host.cockpit_view.current_case = case
    host.active_view = host.cockpit_view

    host.on_case_selected(case)

    assert host.active_case is case
    assert host.switch_to_cockpit_calls == []  # already showing this case


def test_on_case_updated_persists_and_refreshes(host):
    case = _make_case()
    host.storage_service.save_cases([case])
    host.cases = [case]

    case.classification.title = "Geändert"
    host.on_case_updated(case)

    reloaded = host.storage_service.load_cases()
    assert reloaded[0].classification.title == "Geändert"
    assert host.refresh_views_calls == 1


def test_on_archive_case_removes_from_list_on_success(host):
    case = _make_case()
    host.storage_service.save_cases([case])
    host.cases = [case]
    host.active_case = case

    host.on_archive_case(case)

    assert host.cases == []
    assert host.active_case is None
    assert host.refresh_views_calls == 1


def test_on_archive_case_noop_when_case_id_unknown(host):
    case = _make_case()
    host.cases = [case]
    host.active_case = case
    unknown_case = _make_case(case_id="DOES-NOT-EXIST")

    host.on_archive_case(unknown_case)

    # archive_single_case() on a never-saved case fails -> nothing changes.
    assert host.cases == [case]
    assert host.active_case is case
    assert host.refresh_views_calls == 0


# ---------------------------------------------------------------------------
# Complete / reopen toggling
# ---------------------------------------------------------------------------


def test_on_toggle_complete_marks_completed_clears_followup_and_logs_timeline(host):
    case = _make_case(is_completed=False, followup_at="2026-08-01T10:00:00")
    host.storage_service.save_cases([case])
    host.cases = [case]

    host.on_toggle_complete_for_case(case)

    assert case.workflow_status.is_completed is True
    assert case.workflow_status.followup_at == ""
    assert len(case.timeline) == 1
    assert case.timeline[0].channel == Channel.INTERNAL_NOTE.value
    assert "Erledigt" in case.timeline[0].status_change
    assert host.refresh_views_calls == 1  # on_case_updated was called


def test_on_toggle_complete_reopens_and_logs_timeline(host):
    case = _make_case(is_completed=True)
    host.storage_service.save_cases([case])
    host.cases = [case]

    host.on_toggle_complete_for_case(case)

    assert case.workflow_status.is_completed is False
    assert len(case.timeline) == 1
    assert "Offen" in case.timeline[0].status_change


# ---------------------------------------------------------------------------
# open_followup_dialog_for_case: the on_followup_set closure
# ---------------------------------------------------------------------------


def test_followup_dialog_closure_sets_date_logs_note_and_updates_view(host, monkeypatch):
    case = _make_case()
    host.storage_service.save_cases([case])
    host.cases = [case]
    host.active_case = case
    host.cockpit_view.current_case = case

    captured = {}

    class _FakeFollowupDialog:
        def __init__(self, parent, case, on_followup_set):
            captured["on_followup_set"] = on_followup_set

    import ui.dialogs.followup_dialog as followup_dialog_module
    monkeypatch.setattr(followup_dialog_module, "FollowupDialog", _FakeFollowupDialog)

    host.open_followup_dialog_for_case(case)
    assert "on_followup_set" in captured

    captured["on_followup_set"]("2026-09-20T10:00:00", "Rückruf vereinbart")

    assert case.workflow_status.followup_at == "2026-09-20T10:00:00"
    assert len(case.timeline) == 1
    assert "Rückruf vereinbart" in case.timeline[0].note
    assert host.refresh_views_calls == 1  # via on_case_updated
    # active_case is showing in cockpit view -> the follow-up display refreshes too
    assert host.cockpit_view.wiedervorlage_display_updates == 1


def test_followup_dialog_closure_skips_timeline_note_when_note_empty(host, monkeypatch):
    case = _make_case()
    host.storage_service.save_cases([case])
    host.cases = [case]

    captured = {}

    class _FakeFollowupDialog:
        def __init__(self, parent, case, on_followup_set):
            captured["on_followup_set"] = on_followup_set

    import ui.dialogs.followup_dialog as followup_dialog_module
    monkeypatch.setattr(followup_dialog_module, "FollowupDialog", _FakeFollowupDialog)

    host.open_followup_dialog_for_case(case)
    captured["on_followup_set"]("2026-09-20T10:00:00", "")

    assert case.workflow_status.followup_at == "2026-09-20T10:00:00"
    assert len(case.timeline) == 0  # no note text -> no timeline entry logged


# ---------------------------------------------------------------------------
# open_handover_dialog_for_case: the on_confirmed closure
# ---------------------------------------------------------------------------


def test_handover_dialog_closure_updates_actor_and_logs_timeline(host, monkeypatch):
    case = _make_case()
    case.workflow_status.current_actor = Actor.SUPPORT
    host.storage_service.save_cases([case])
    host.cases = [case]
    host.colleagues = [Colleague(name="Anna Schmidt", email="anna@support.de")]

    captured = {}

    class _FakeHandoverDialog:
        def __init__(self, parent, case, colleagues, on_handover_confirmed):
            captured["on_confirmed"] = on_handover_confirmed

    import ui.dialogs.handover_dialog as handover_dialog_module
    monkeypatch.setattr(handover_dialog_module, "HandoverDialog", _FakeHandoverDialog)

    host.open_handover_dialog_for_case(case)
    assert "on_confirmed" in captured

    captured["on_confirmed"](Actor.DEVELOPMENT, "E-Mail", "Max Mustermann", "Bitte prüfen")

    assert case.workflow_status.current_actor == Actor.DEVELOPMENT
    assert case.workflow_status.actor_since != ""
    assert len(case.timeline) == 1
    assert "Max Mustermann" in case.timeline[0].note
    assert "Bitte prüfen" in case.timeline[0].note
    assert host.refresh_views_calls == 1


# ---------------------------------------------------------------------------
# Data-refresh callbacks used by several dialogs
# ---------------------------------------------------------------------------


def test_on_customers_updated_reloads_from_storage(host):
    host.storage_service.save_customers([Customer(customer_id="K-9", practice_name="Praxis Neu")])
    host.on_customers_updated()
    assert any(c.customer_id == "K-9" for c in host.customers)


def test_on_cobra_import_completed_saves_and_reloads(host):
    merged = [Customer(customer_id="K-COBRA", practice_name="Cobra Praxis")]
    host.on_cobra_import_completed(merged)
    assert any(c.customer_id == "K-COBRA" for c in host.customers)


def test_on_quick_customer_added_saves_and_reloads(host):
    new_customer = Customer(customer_id="K-QUICK", practice_name="Quick Praxis")
    host.on_quick_customer_added(new_customer)
    assert any(c.customer_id == "K-QUICK" for c in host.customers)


def test_on_case_created_scores_saves_appends_and_selects(host):
    new_case = _make_case(case_id="T-NEW-01")
    host.on_case_created(new_case)

    assert new_case in host.cases
    assert host.refresh_views_calls == 1
    assert host.cockpit_view.selected_from_list == [new_case]
    reloaded = host.storage_service.load_cases()
    assert any(c.case_id == "T-NEW-01" for c in reloaded)


def test_on_colleagues_updated_reloads_from_storage(host):
    host.storage_service.save_colleagues([Colleague(name="Bernd Weber", email="bernd@support.de")])
    host.on_colleagues_updated()
    assert any(c.name == "Bernd Weber" for c in host.colleagues)


def test_on_tags_updated_reloads_profile(host):
    profile = host.storage_service.load_profile()
    profile.available_tags = ["PVS", "Telematik"]
    host.storage_service.save_profile(profile)

    host.on_tags_updated()

    assert host.profile.available_tags == ["PVS", "Telematik"]


def test_on_tag_added_appends_new_tag_and_persists(host):
    host.profile.available_tags = ["PVS"]
    host.on_tag_added("Telematik")

    assert "Telematik" in host.profile.available_tags
    reloaded = host.storage_service.load_profile()
    assert "Telematik" in reloaded.available_tags


def test_on_tag_added_does_not_duplicate_existing_tag(host):
    host.profile.available_tags = ["PVS"]
    host.on_tag_added("PVS")
    assert host.profile.available_tags.count("PVS") == 1


def test_on_schemas_updated_replaces_list_and_refreshes(host):
    host.on_schemas_updated(["schema-a", "schema-b"])
    assert host.schemas == ["schema-a", "schema-b"]
    assert host.refresh_views_calls == 1


def test_on_templates_updated_replaces_list_and_refreshes(host):
    host.on_templates_updated(["tpl-a"])
    assert host.templates == ["tpl-a"]
    assert host.refresh_views_calls == 1


def test_on_p2p_sync_completed_reloads_and_refreshes(host):
    host.on_p2p_sync_completed()
    assert host.refresh_views_calls == 1


# ---------------------------------------------------------------------------
# A representative sample of the simple dialog openers (wiring, not the
# dialog's own internals - those are covered by the dialogs' own tests).
# ---------------------------------------------------------------------------


def test_open_help_dialog_constructs_help_dialog(host, monkeypatch):
    captured = {}

    class _FakeHelpDialog:
        def __init__(self, parent):
            captured["parent"] = parent

    monkeypatch.setattr(app_dialogs_module, "HelpDialog", _FakeHelpDialog)
    host.open_help_dialog()
    assert captured["parent"] is host


def test_open_customer_management_dialog_wires_service_and_callback(host, monkeypatch):
    captured = {}

    class _FakeCustomerManagementDialog:
        def __init__(self, parent, customer_service, on_customers_updated):
            captured["customer_service"] = customer_service
            captured["on_customers_updated"] = on_customers_updated

    monkeypatch.setattr(app_dialogs_module, "CustomerManagementDialog", _FakeCustomerManagementDialog)
    host.open_customer_management_dialog()

    assert captured["customer_service"] is host.customer_service
    assert captured["on_customers_updated"] == host.on_customers_updated


def test_open_export_dialog_does_nothing_without_a_target_case(host, monkeypatch):
    captured = {"called": False}

    class _FakeExportDialog:
        def __init__(self, *a, **k):
            captured["called"] = True

    monkeypatch.setattr(app_dialogs_module, "ExportDialog", _FakeExportDialog)
    host.active_case = None

    host.open_export_dialog(case=None)

    assert captured["called"] is False


def test_open_export_dialog_uses_active_case_when_no_case_passed(host, monkeypatch):
    case = _make_case()
    host.active_case = case
    captured = {}

    class _FakeExportDialog:
        def __init__(self, parent, case, templates, schemas, export_service, on_case_updated):
            captured["case"] = case

    monkeypatch.setattr(app_dialogs_module, "ExportDialog", _FakeExportDialog)
    host.open_export_dialog(case=None)

    assert captured["case"] is case


def test_open_case_print_dialog_does_nothing_without_a_target_case(host, monkeypatch):
    captured = {"called": False}

    class _FakeCasePrintDialog:
        def __init__(self, *a, **k):
            captured["called"] = True

    import ui.dialogs.case_print_dialog as case_print_dialog_module
    monkeypatch.setattr(case_print_dialog_module, "CasePrintDialog", _FakeCasePrintDialog)
    host.active_case = None

    host.open_case_print_dialog(case=None)

    assert captured["called"] is False


def test_open_snippet_picker_dialog_wires_service_and_callback(host, monkeypatch):
    captured = {}

    class _FakeSnippetPickerDialog:
        def __init__(self, parent, snippet_service, on_snippet_selected):
            captured["snippet_service"] = snippet_service
            captured["on_snippet_selected"] = on_snippet_selected

    import ui.dialogs.snippet_picker_dialog as snippet_picker_dialog_module
    monkeypatch.setattr(snippet_picker_dialog_module, "SnippetPickerDialog", _FakeSnippetPickerDialog)

    def my_callback(text):
        pass

    host.open_snippet_picker_dialog(my_callback)

    assert captured["snippet_service"] is host.snippet_service
    assert captured["on_snippet_selected"] is my_callback
