"""DialogLaunchersMixin (ui/app_dialogs.py): which dialog opens for which action, and the case/data callbacks."""

import customtkinter as ctk
import pytest

import ui.app_dialogs as app_dialogs_module
from enums import Actor, BoardColumn, Channel, LayoutMode, get_layout_display
from models.case import Case, CaseCustomer, Classification, WorkflowStatus
from models.customer import Customer
from models.profile import Colleague
from services.customer_service import CustomerService
from services.scoring_service import ScoringService
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
    """Minimal SupportCockpitApp stand-in with only the attributes the mixin touches."""

    def __init__(self, storage):
        super().__init__()
        self.withdraw()
        self.storage_service = storage
        self.customer_service = CustomerService(storage)
        self.scoring_service = ScoringService()
        self.export_service = self.p2p_service = self.calendar_email_service = self.snippet_service = None
        self.profile = storage.load_profile()
        self.cases, self.customers, self.colleagues, self.schemas, self.templates = [], [], [], [], []
        self.active_case = None
        self.search_query = ""
        self.cockpit_view = _FakeCockpitView()
        self.active_view = self.cockpit_view
        self.refresh_views_calls = 0
        self.bring_to_foreground_calls = 0
        self.switch_to_cockpit_calls = []
        self.user_btn = ctk.CTkLabel(self, text="")

    def refresh_views(self, force_all: bool = False):
        self.refresh_views_calls += 1

    def bring_to_foreground(self):
        self.bring_to_foreground_calls += 1

    def switch_to_cockpit_view_for_case(self, case):
        self.switch_to_cockpit_calls.append(case)
        self.cockpit_view.current_case = case

    def load_all_data(self):
        pass


@pytest.fixture
def host(storage):
    h = _FakeHost(storage)
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


def _saved_case(host, **wf_kwargs) -> Case:
    case = _make_case(**wf_kwargs)
    host.storage_service.save_cases([case])
    host.cases = [case]
    return case


def _capture_dialog(monkeypatch, module, name):
    """Replaces a dialog class with a recorder of its constructor kwargs."""
    captured: dict = {}

    class _Recorder:
        def __init__(self, *args, **kwargs):
            captured.update(kwargs, args=args)

    monkeypatch.setattr(module, name, _Recorder)
    return captured


# --- Case selection / search / update / archive ---

def test_search_changed_sets_query_and_refreshes(host):
    host.on_search_changed("praxis alpha")
    assert host.search_query == "praxis alpha"
    assert host.refresh_views_calls == 1


def test_case_selected_switches_view_only_when_a_different_case_is_shown(host):
    case = _make_case()
    host.on_case_selected(case)
    assert host.bring_to_foreground_calls == 1
    assert host.active_case is case
    assert host.switch_to_cockpit_calls == [case]

    host.on_case_selected(case)   # already the current case in the cockpit
    assert host.switch_to_cockpit_calls == [case]


def test_case_updated_persists_and_refreshes(host):
    case = _saved_case(host)
    case.classification.title = "Geändert"
    host.on_case_updated(case)
    assert host.storage_service.load_cases()[0].classification.title == "Geändert"
    assert host.refresh_views_calls == 1


def test_archive_removes_case_only_when_archiving_succeeds(host):
    case = _saved_case(host)
    host.active_case = case

    host.on_archive_case(_make_case(case_id="DOES-NOT-EXIST"))
    assert host.cases == [case] and host.active_case is case and host.refresh_views_calls == 0

    host.on_archive_case(case)
    assert host.cases == []
    assert host.active_case is None
    assert host.refresh_views_calls == 1


@pytest.mark.parametrize("was_completed, status_word", [(False, "Erledigt"), (True, "Offen")])
def test_toggle_complete_flips_state_and_logs_timeline(host, was_completed, status_word):
    case = _saved_case(host, is_completed=was_completed, followup_at="2026-08-01T10:00:00")
    host.on_toggle_complete_for_case(case)

    assert case.workflow_status.is_completed is not was_completed
    if not was_completed:
        assert case.workflow_status.followup_at == ""
    assert len(case.timeline) == 1
    assert case.timeline[0].channel == Channel.INTERNAL_NOTE.value
    assert status_word in case.timeline[0].status_change
    assert host.refresh_views_calls == 1


# --- Follow-up / handover closures ---

@pytest.mark.parametrize("note, timeline_len", [("Rückruf vereinbart", 1), ("", 0)])
def test_followup_dialog_callback_sets_date_and_logs_note(host, monkeypatch, note, timeline_len):
    import ui.dialogs.followup_dialog as followup_dialog_module

    case = _saved_case(host)
    host.active_case = case
    host.cockpit_view.current_case = case
    captured = _capture_dialog(monkeypatch, followup_dialog_module, "FollowupDialog")

    host.open_followup_dialog_for_case(case)
    captured["on_followup_set"]("2026-09-20T10:00:00", note)

    assert case.workflow_status.followup_at == "2026-09-20T10:00:00"
    assert len(case.timeline) == timeline_len
    if note:
        assert note in case.timeline[0].note
    assert host.refresh_views_calls == 1
    assert host.cockpit_view.wiedervorlage_display_updates == 1


def test_handover_dialog_callback_updates_actor_and_logs_timeline(host, monkeypatch):
    import ui.dialogs.handover_dialog as handover_dialog_module

    case = _saved_case(host)
    case.workflow_status.current_actor = Actor.SUPPORT
    host.colleagues = [Colleague(name="Anna Schmidt", email="anna@support.de")]
    captured = _capture_dialog(monkeypatch, handover_dialog_module, "HandoverDialog")

    host.open_handover_dialog_for_case(case)
    assert captured["colleagues"] == host.colleagues
    captured["on_handover_confirmed"](Actor.DEVELOPMENT, "E-Mail", "Max Mustermann", "Bitte prüfen")

    assert case.workflow_status.current_actor == Actor.DEVELOPMENT
    assert case.workflow_status.actor_since != ""
    assert "Max Mustermann" in case.timeline[0].note and "Bitte prüfen" in case.timeline[0].note
    assert host.refresh_views_calls == 1


# --- Data-refresh callbacks ---

def test_customer_callbacks_persist_and_reload(host):
    host.storage_service.save_customers([Customer(customer_id="K-9", practice_name="Praxis Neu")])
    host.on_customers_updated()
    host.on_cobra_import_completed(host.customers + [Customer(customer_id="K-COBRA", practice_name="Cobra")])
    host.on_quick_customer_added(Customer(customer_id="K-QUICK", practice_name="Quick Praxis"))

    ids = {c.customer_id for c in host.customers}
    assert {"K-9", "K-COBRA", "K-QUICK"} <= ids
    assert {"K-9", "K-COBRA", "K-QUICK"} <= {c.customer_id for c in host.storage_service.load_customers()}


def test_case_created_is_saved_appended_and_selected(host):
    new_case = _make_case(case_id="T-NEW-01")
    host.on_case_created(new_case)
    assert new_case in host.cases
    assert host.refresh_views_calls == 1
    assert host.cockpit_view.selected_from_list == [new_case]
    assert any(c.case_id == "T-NEW-01" for c in host.storage_service.load_cases())


def test_colleague_and_tag_callbacks_reload_from_storage(host):
    host.storage_service.save_colleagues([Colleague(name="Bernd Weber", email="bernd@support.de")])
    host.on_colleagues_updated()
    assert any(c.name == "Bernd Weber" for c in host.colleagues)

    profile = host.storage_service.load_profile()
    profile.available_tags = ["PVS", "Telematik"]
    host.storage_service.save_profile(profile)
    host.on_tags_updated()
    assert host.profile.available_tags == ["PVS", "Telematik"]


def test_tag_added_persists_without_duplicates(host):
    host.profile.available_tags = ["PVS"]
    host.on_tag_added("Telematik")
    host.on_tag_added("PVS")
    assert host.profile.available_tags == ["PVS", "Telematik"]
    assert "Telematik" in host.storage_service.load_profile().available_tags


def test_schema_template_and_p2p_callbacks_refresh_views(host):
    host.on_schemas_updated(["schema-a", "schema-b"])
    host.on_templates_updated(["tpl-a"])
    host.on_p2p_sync_completed()
    assert host.schemas == ["schema-a", "schema-b"]
    assert host.templates == ["tpl-a"]
    assert host.refresh_views_calls == 3


# --- Dialog openers ---

def test_openers_wire_the_right_dialog_with_services_and_callbacks(host, monkeypatch):
    import ui.dialogs.snippet_picker_dialog as snippet_picker_module

    help_dlg = _capture_dialog(monkeypatch, app_dialogs_module, "HelpDialog")
    host.open_help_dialog()
    assert help_dlg["args"] == (host,)

    cust = _capture_dialog(monkeypatch, app_dialogs_module, "CustomerManagementDialog")
    host.open_customer_management_dialog()
    assert cust["customer_service"] is host.customer_service
    assert cust["on_customers_updated"] == host.on_customers_updated

    picker = _capture_dialog(monkeypatch, snippet_picker_module, "SnippetPickerDialog")

    def on_text(text):
        pass

    host.open_snippet_picker_dialog(on_text)
    assert picker["snippet_service"] is host.snippet_service
    assert picker["on_snippet_selected"] is on_text


def test_case_dialogs_open_only_with_a_target_case(host, monkeypatch):
    import ui.dialogs.case_print_dialog as case_print_module

    export = _capture_dialog(monkeypatch, app_dialogs_module, "ExportDialog")
    printing = _capture_dialog(monkeypatch, case_print_module, "CasePrintDialog")

    host.active_case = None
    host.open_export_dialog(case=None)
    host.open_case_print_dialog(case=None)
    assert export == {} and printing == {}

    host.active_case = case = _make_case()
    host.open_export_dialog(case=None)
    assert export["case"] is case


# --- App shell: lazy view construction ---

def test_app_builds_only_the_active_layout_and_caches_views(config):
    from ui.app import SupportCockpitApp

    app = SupportCockpitApp(config)
    app.withdraw()
    try:
        built = [k for k in ("COCKPIT", "BOARD", "TABLE", "ANALYTICS") if app.is_view_built(k)]
        assert len(built) == 1, f"expected exactly one view at startup, got {built}"

        for value in ("BOARD", "TABLE", "ANALYTICS", "COCKPIT"):
            app.switch_layout(get_layout_display(value))
            assert app.is_view_built(value)
        first = app.board_view
        app.switch_layout(get_layout_display(LayoutMode.BOARD.value))
        assert app.board_view is first, "the view was rebuilt instead of reused"

        # Header icons are rendered once; asking again reuses the cached images.
        from utils.icon_utils import _PIL_ICON_CACHE, get_icon
        key, (light, _dark) = next(iter(_PIL_ICON_CACHE.items()))
        assert get_icon(key[0], key[1], key[2], key[3])._light_image is light
    finally:
        try:
            app.destroy()
        except Exception:
            pass


# --- data replaced on disk (ZIP import) --------------------------------------------------

class _ClearableCockpit:
    def __init__(self, open_case: Case | None):
        self.current_case: Case | None = open_case
        self.cleared = 0

    def clear_current_case(self) -> None:
        self.cleared += 1
        self.current_case = None


class _ReplacedDataHost:
    """Only what _drop_open_case_if_replaced touches - no window needed."""

    def __init__(self, storage, cases: list[Case], open_case: Case | None):
        self.storage_service = storage
        self.cases = cases
        self.active_case: Case | None = open_case
        self.cockpit_view = _ClearableCockpit(open_case)

    @property
    def cleared(self) -> int:
        return self.cockpit_view.cleared

    def is_view_built(self, key: str) -> bool:
        return key == LayoutMode.COCKPIT.value


def test_open_case_survives_an_ordinary_settings_save(storage):
    """Saving the settings rereads the lists too (new objects), but from the open case's own data - it must stay open."""
    open_case = _make_case()
    host = _ReplacedDataHost(storage, cases=[_make_case()], open_case=open_case)
    DialogLaunchersMixin._drop_open_case_if_replaced(host)  # type: ignore[arg-type]
    assert host.cleared == 0
    assert host.active_case is open_case and host.cockpit_view.current_case is open_case


def test_open_case_is_closed_once_the_data_was_replaced_on_disk(storage):
    """After a ZIP import the pane holds a case from before; saving it would put the old state over the imported one."""
    open_case = _make_case()
    host = _ReplacedDataHost(storage, cases=[open_case], open_case=open_case)
    storage.reload_from_disk()
    host.cases = [_make_case()]  # what load_all_data() reread: same id, another object

    DialogLaunchersMixin._drop_open_case_if_replaced(host)  # type: ignore[arg-type]
    assert host.cleared == 1
    assert host.active_case is None and host.cockpit_view.current_case is None

    # Handled once: the next ordinary settings save leaves a newly opened case alone.
    reopened = host.cases[0]
    host.active_case = host.cockpit_view.current_case = reopened
    DialogLaunchersMixin._drop_open_case_if_replaced(host)  # type: ignore[arg-type]
    assert host.cleared == 1 and host.cockpit_view.current_case is reopened


def test_a_case_that_is_still_loaded_stays_open_after_a_reload(storage):
    """Archived cases can be open as well; one the reload still knows is not closed."""
    archived = _make_case("T-APPD-ARCH", is_archived=True, is_completed=True)
    storage.save_archive([archived], sync=True)
    storage.reload_from_disk()
    still_loaded = storage.load_archive()[0]
    host = _ReplacedDataHost(storage, cases=[], open_case=still_loaded)

    DialogLaunchersMixin._drop_open_case_if_replaced(host)  # type: ignore[arg-type]
    assert host.cleared == 0 and host.cockpit_view.current_case is still_loaded
