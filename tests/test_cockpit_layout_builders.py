"""Tests for src/ui/views/cockpit_layout_builders.py (CockpitLayoutBuilderMixin).

This mixin is baked into every CockpitView instance (`class
CockpitView(CockpitLayoutBuilderMixin, ctk.CTkFrame)`), so its widget-building
methods (_build_paned_window/_build_left_pane/_build_center_pane/
_build_right_pane) already run indirectly whenever some other test constructs
a real CockpitView (e.g. test_wiedervorlage_wrapping.py,
test_light_dark_theme_consistency.py) - a coverage audit that only greps test
files for the literal string "cockpit_layout_builders" misses that. What is
NOT exercised anywhere else is refresh_ui_labels() (a large, branch-heavy
method) and the profile-driven pane-width calculation - this file covers
those directly, plus asserts the built widget tree has the expected shape.
"""

from pathlib import Path
import customtkinter as ctk
import pytest

from config import AppConfig
from enums import Actor, BoardColumn
from models.case import Case, CaseCustomer, Classification, WorkflowStatus
from models.profile import UserProfile
from services.storage_service import StorageService
from services.scoring_service import ScoringService
from services.attachment_service import AttachmentService
from services.wiki_sync_service import WikiSyncService
from services.i18n_service import tr
from ui.views.cockpit_view import CockpitView
from ui.widgets.case_list_widget import CaseListWidget
from ui.widgets.dynamic_form_widget import DynamicFormWidget
from ui.widgets.timeline_widget import TimelineWidget
from ui.widgets.attachment_widget import AttachmentWidget
from ui.widgets.wiki_widget import WikiWidget


@pytest.fixture
def cockpit(tmp_path: Path):
    config = AppConfig(workspace_dir=tmp_path)
    storage = StorageService(config)
    profile = storage.load_profile()
    scoring = ScoringService()
    attachment = AttachmentService(config)
    wiki = WikiSyncService(config)

    app = ctk.CTk()
    app.withdraw()

    view = CockpitView(
        app,
        author_name="Tester",
        scoring_service=scoring,
        attachment_service=attachment,
        wiki_service=wiki,
        on_case_updated=lambda c: None,
        on_case_selected=lambda c: None,
        on_search_changed=lambda s: None,
        on_open_export_dialog=lambda c: None,
        on_archive_case=lambda c: None,
        app_config=config,
        profile=profile,
        storage_service=storage,
    )
    yield view
    try:
        app.destroy()
    except Exception:
        pass


def _make_case(**wf_kwargs) -> Case:
    return Case(
        case_id="T-LAYOUT-01",
        customer=CaseCustomer(customer_id="K-1", practice_name="Praxis Layout", contact_person="Dr. Layout"),
        classification=Classification(title="Layout Test"),
        workflow_status=WorkflowStatus(board_column=BoardColumn.NEW, **wf_kwargs),
    )


# ---------------------------------------------------------------------------
# Widget tree shape (constructed via _build_paned_window/_build_left_pane/
# _build_center_pane/_build_right_pane, called from CockpitView.create_layout())
# ---------------------------------------------------------------------------


def test_layout_builds_expected_widget_tree(cockpit):
    assert isinstance(cockpit.left_frame, CaseListWidget)
    assert isinstance(cockpit.form_widget, DynamicFormWidget)
    assert isinstance(cockpit.timeline_widget, TimelineWidget)
    assert isinstance(cockpit.attachment_widget, AttachmentWidget)
    assert isinstance(cockpit.wiki_widget, WikiWidget)

    # Same internal attribute the app's own tab-renaming code in
    # cockpit_layout_builders.py already relies on (_build_right_pane /
    # refresh_ui_labels), so it's guaranteed present on this customtkinter version.
    tab_buttons = cockpit.right_tabview._segmented_button._buttons_dict
    assert "Zeitleiste" in tab_buttons
    assert "Anhänge" in tab_buttons
    assert "Wiki" in tab_buttons


def test_build_paned_window_uses_profile_column_widths(cockpit):
    cockpit.profile.ui_settings.column_widths = {"cockpit_left": 250, "cockpit_right": 400}
    w_left, w_right = cockpit._build_paned_window()
    assert (w_left, w_right) == (250, 400)


def test_build_paned_window_falls_back_to_defaults_without_profile(cockpit):
    cockpit.profile = None
    cockpit.app_config = None
    w_left, w_right = cockpit._build_paned_window()
    assert (w_left, w_right) == (300, 320)


# ---------------------------------------------------------------------------
# refresh_ui_labels(): complete/reopen button text, actor combo, title/info
# ---------------------------------------------------------------------------


def test_refresh_ui_labels_shows_complete_text_when_no_active_case(cockpit):
    cockpit.current_case = None
    cockpit.refresh_ui_labels()
    assert cockpit.complete_btn.cget("text") == tr("cockpit.complete", "✓ Erledigt")
    assert cockpit.case_title_label.cget("text") == tr("cockpit.select_case_prompt", "Bitte einen Fall auswählen")


def test_refresh_ui_labels_shows_reopen_text_for_completed_case(cockpit):
    case = _make_case(is_completed=True, current_actor=Actor.SUPPORT)
    cockpit.current_case = case
    cockpit.refresh_ui_labels()
    assert cockpit.complete_btn.cget("text") == tr("cockpit.reopen", "✓ Wieder öffnen")


def test_refresh_ui_labels_shows_complete_text_for_open_case(cockpit):
    case = _make_case(is_completed=False, current_actor=Actor.SUPPORT)
    cockpit.current_case = case
    cockpit.refresh_ui_labels()
    assert cockpit.complete_btn.cget("text") == tr("cockpit.complete", "✓ Erledigt")


def test_refresh_ui_labels_sets_actor_combo_to_current_actor(cockpit):
    from enums import get_actor_display

    case = _make_case(current_actor=Actor.DEVELOPMENT)
    cockpit.current_case = case
    cockpit.refresh_ui_labels()
    assert cockpit.actor_combo.get() == get_actor_display(Actor.DEVELOPMENT)


def test_refresh_ui_labels_shows_customer_info_with_vip_marker(cockpit):
    case = _make_case()
    case.customer.is_vip = True
    cockpit.current_case = case
    cockpit.refresh_ui_labels()

    kunde_text = cockpit.kunde_label.cget("text")
    assert "Praxis Layout" in kunde_text
    assert "K-1" in kunde_text
    assert "VIP" in kunde_text


def test_refresh_ui_labels_shows_internal_task_label_for_internal_case(cockpit):
    case = _make_case()
    case.customer.customer_id = "INTERNAL"
    assert case.is_internal
    cockpit.current_case = case
    cockpit.refresh_ui_labels()

    kunde_text = cockpit.kunde_label.cget("text")
    assert tr("cockpit.internal_task_title", "INTERNE AUFGABE / VORGANG") in kunde_text


def test_refresh_ui_labels_updates_more_actions_dropdown_and_toolbar_buttons(cockpit):
    cockpit.refresh_ui_labels()
    assert cockpit.more_actions_combo.get() == tr("cockpit.more_actions", "⚙ Weitere Aktionen...")
    assert cockpit.email_btn.cget("text") == tr("cockpit.email_ai", "✉ E-Mail & 🤖 KI")
    assert cockpit.cal_btn.cget("text") == tr("cockpit.calendar", "📅 Kalender")
    assert cockpit.followup_btn.cget("text") == tr("cockpit.followup", "🔔 Wiedervorlage")
    assert cockpit.save_btn.cget("text") == tr("cockpit.save", "💾 Speichern")
    assert cockpit.archive_btn.cget("text") == tr("cockpit.archive", "📦 Archivieren")
