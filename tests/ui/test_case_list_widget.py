"""CaseListWidget: card rendering, wrapping, filtering, language refresh and the personal colour marker on case/kanban cards."""

from unittest.mock import MagicMock

import customtkinter as ctk
import pytest

from enums import Actor, UrgencyLevel
from models.case import Case, CaseCustomer, Classification, WorkflowStatus
from models.profile import UserInfo, UserProfile
from services.i18n_service import get_i18n
from services.storage_service import StorageService
from ui.views.board_view import KanbanCardWidget
from ui.widgets.case_list_widget import CaseListWidget


def _colored_frames(parent, color):
    found = []
    for child in parent.winfo_children():
        if isinstance(child, ctk.CTkFrame):
            try:
                if child.cget("fg_color") == color:
                    found.append(child)
            except Exception:
                pass
            found.extend(_colored_frames(child, color))
    return found


def _case(case_id, assigned_to="", **wf):
    return Case(
        case_id=case_id,
        assigned_to=assigned_to,
        customer=CaseCustomer(customer_id=f"C-{case_id}", practice_name=f"Praxis {case_id}"),
        classification=Classification(schema_id="s1", title=f"Title {case_id}"),
        workflow_status=WorkflowStatus(**wf),
    )


def test_followup_card_wraps_over_three_lines_and_rewraps_on_resize(root):
    widget = CaseListWidget(root, on_case_selected=lambda c: None, on_search_changed=lambda s: None)
    case = Case(
        case_id="T-2026-100",
        customer=CaseCustomer(customer_id="K-1", practice_name="Gemeinschaftspraxis Nord"),
        classification=Classification(title="Zuzahlungsfehler", urgency_level=UrgencyLevel.YELLOW),
        workflow_status=WorkflowStatus(
            followup_at="2026-08-26T14:30:00",
            followup_note="Wegen Rückmeldung anrufen",
            current_actor=Actor.SUPPORT,
        ),
    )
    widget.set_cases([case])

    texts = [lbl.cget("text") for lbl in widget.wrap_labels]
    assert len(texts) >= 3
    for expected in ("🔔 Nachfragen am:", "26.08.2026", "14:30 Uhr", "Wegen Rückmeldung anrufen"):
        assert any(expected in t for t in texts), expected

    widget._last_wrap_width = 100
    widget.configure(width=400)
    widget._on_widget_configure(None)
    assert widget.wrap_labels[0].cget("wraplength") >= 160


def test_quick_filters_and_language_refresh(root):
    widget = CaseListWidget(root, on_case_selected=lambda c: None, on_search_changed=lambda q: None)
    cases = [
        Case(
            case_id=f"CASE-{i:03d}",
            customer=CaseCustomer(customer_id=f"CUST-{i}", practice_name=f"Practice {i}"),
            classification=Classification(
                title=f"Issue {i}",
                urgency_level=(UrgencyLevel.RED, UrgencyLevel.YELLOW, UrgencyLevel.GREEN)[i % 3],
                calculated_score=float(100 - i),
            ),
            workflow_status=WorkflowStatus(
                current_actor=Actor.SUPPORT if i % 2 == 0 else Actor.DEVELOPMENT,
                is_completed=(i % 5 == 0),
            ),
        )
        for i in range(20)
    ]
    widget.set_cases(cases)

    for lang, filt in (("de", ""), ("en", "vip:true"), ("sv", "reminder:due")):
        get_i18n().current_language = lang
        widget.apply_quick_filter(filt)
        widget.refresh_ui_labels()
    assert "Sök" in widget.search_entry.cget("placeholder_text")

    get_i18n().current_language = "en"
    widget.refresh_ui_labels()
    assert "Search" in widget.search_entry.cget("placeholder_text")


# --- personal colour marker -------------------------------------------------

def test_case_list_marks_own_cases_with_user_color(root):
    widget = CaseListWidget(
        parent=root,
        on_case_selected=MagicMock(),
        on_search_changed=MagicMock(),
        current_user_name="Daniel Rösch",
        user_color="#8b5cf6",
        color_marker_enabled=True,
    )
    widget.set_cases([_case("FALL-001", "Daniel Rösch"), _case("FALL-002", "Robert")])
    assert len(_colored_frames(widget.scroll_frame, "#8b5cf6")) >= 1


@pytest.mark.parametrize(("assigned_to", "tiles"), [("Daniel Rösch", 1), ("Other Person", 0)])
def test_kanban_card_marks_only_own_cases(root, assigned_to, tiles):
    card = KanbanCardWidget(
        parent=root,
        case=_case("FALL-100", assigned_to),
        on_select_case=MagicMock(),
        on_switch_to_cockpit=MagicMock(),
        on_open_followup=MagicMock(),
        on_toggle_complete=MagicMock(),
        on_change_actor=MagicMock(),
        current_user_name="Daniel Rösch",
        user_color="#f59e0b",
        color_marker_enabled=True,
    )
    assert len(_colored_frames(card, "#f59e0b")) == tiles


def test_user_color_settings_roundtrip():
    loaded = UserInfo.from_dict(UserInfo(name="Daniel", user_color="#10b981", color_marker_enabled=True).to_dict())
    assert (loaded.name, loaded.user_color, loaded.color_marker_enabled) == ("Daniel", "#10b981", True)

    defaults = UserInfo.from_dict({"name": "Anna"})
    assert (defaults.user_color, defaults.color_marker_enabled) == ("#3b82f6", False)


def test_profile_settings_color_marker_section(root, tmp_path):
    from ui.dialogs.profile_settings_dialog import ProfileSettingsDialog

    svc = MagicMock(spec=StorageService)
    svc.config = MagicMock()
    svc.config.workspace_dir = tmp_path / "workspace"
    svc.config.data_dir = tmp_path / "workspace" / "data"
    svc.config.attachments_dir = tmp_path / "workspace" / "attachments"
    svc.config.custom_cases_path = None
    svc.config.custom_customers_path = None
    svc.config.custom_wiki_db_path = None
    svc.list_profiles.return_value = ["Test User", "Second User"]

    profile = UserProfile(user=UserInfo(name="Daniel Rösch", user_color="#ef4444", color_marker_enabled=True))
    dialog = ProfileSettingsDialog(root, profile=profile, storage_service=svc)
    assert dialog.color_marker_switch.get() == 1
    assert dialog.preview_tile.cget("fg_color") == "#ef4444"

    dialog.set_selected_user_color("#10b981")
    assert dialog.preview_tile.cget("fg_color") == "#10b981"

    dialog.color_marker_switch.deselect()
    assert dialog.save_user_settings() is True
    assert dialog.profile.user.user_color == "#10b981"
    assert dialog.profile.user.color_marker_enabled is False

    get_i18n().current_language = "en"
    dialog.refresh_ui_labels()
    assert "Personal Color Tag" in dialog.color_marker_hdr_lbl.cget("text")
    assert "Choose color" in dialog.btn_pick_color.cget("text")
    assert "Preview" in dialog.preview_lbl.cget("text")
    dialog.destroy()
