import pytest
from unittest.mock import MagicMock
import customtkinter as ctk

from models.profile import UserInfo, UserProfile
from models.case import Case, CaseCustomer, Classification, TimelineEntry
from ui.widgets.timeline_widget import TimelineWidget
from ui.widgets.case_list_widget import CaseListWidget
from ui.views.board_view import KanbanCardWidget
from ui.dialogs.profile_settings_dialog import ProfileSettingsDialog
from services.storage_service import StorageService
from services.i18n_service import get_i18n


@pytest.fixture(autouse=True)
def reset_locale():
    i18n = get_i18n()
    i18n.current_language = "de"
    yield
    i18n.current_language = "de"


@pytest.fixture
def headless_root():
    """Provide a headless Tk/CustomTkinter root window."""
    root = ctk.CTk()
    root.withdraw()
    yield root
    try:
        root.destroy()
    except Exception:
        pass


@pytest.fixture
def storage_service_mock(tmp_path):
    svc = MagicMock(spec=StorageService)
    svc.config = MagicMock()
    svc.config.workspace_dir = tmp_path / "workspace"
    svc.config.data_dir = tmp_path / "workspace" / "data"
    svc.config.attachments_dir = tmp_path / "workspace" / "attachments"
    svc.config.custom_cases_path = None
    svc.config.custom_customers_path = None
    svc.config.custom_wiki_db_path = None
    svc.list_profiles.return_value = ["Test User", "Second User"]
    return svc


def test_user_info_color_marker_serialization():
    user = UserInfo(name="Daniel", user_color="#10b981", color_marker_enabled=True)
    d = user.to_dict()
    assert d["user_color"] == "#10b981"
    assert d["color_marker_enabled"] is True

    loaded = UserInfo.from_dict(d)
    assert loaded.name == "Daniel"
    assert loaded.user_color == "#10b981"
    assert loaded.color_marker_enabled is True

    # Default fallback
    loaded_empty = UserInfo.from_dict({"name": "Anna"})
    assert loaded_empty.user_color == "#3b82f6"
    assert loaded_empty.color_marker_enabled is False


def test_timeline_widget_redesigned_card_layout(headless_root):
    get_i18n().current_language = "de"
    updated_entries = []
    widget = TimelineWidget(
        parent=headless_root,
        author_name="Daniel Rösch",
        on_timeline_updated=lambda entries: updated_entries.extend(entries),
        user_color="#ef4444",
        color_marker_enabled=True,
    )

    entries = [
        TimelineEntry(
            timestamp="2026-08-25T14:44:26",
            author="Daniel Rösch",
            channel="EMAIL",
            note="Test note by Daniel",
        ),
        TimelineEntry(
            timestamp="2026-08-25T11:18:59",
            author="Felipe",
            channel="INTERNAL_NOTE",
            note="Test note by Felipe",
        ),
    ]
    widget.load_timeline(entries)

    # 2 cards in scroll_frame
    cards = widget.scroll_frame.winfo_children()
    assert len(cards) == 2

    # reversed(entries) -> Felipe first, Daniel second
    felipe_card = cards[0]
    daniel_card = cards[1]

    def find_colored_frames(parent):
        found = []
        for child in parent.winfo_children():
            if isinstance(child, ctk.CTkFrame):
                try:
                    if child.cget("fg_color") == "#ef4444":
                        found.append(child)
                except Exception:
                    pass
                found.extend(find_colored_frames(child))
        return found

    daniel_tiles = find_colored_frames(daniel_card)
    assert len(daniel_tiles) == 1, "Expected 1 colored tile for Daniel's note"

    felipe_tiles = find_colored_frames(felipe_card)
    assert len(felipe_tiles) == 0, "Expected 0 colored tiles for Felipe's note"

    # Test toggling color_marker_enabled off
    widget.set_user_color_settings(user_color="#ef4444", color_marker_enabled=False)
    cards_disabled = widget.scroll_frame.winfo_children()
    daniel_card_disabled = cards_disabled[1]
    assert len(find_colored_frames(daniel_card_disabled)) == 0


def test_case_list_widget_color_marker(headless_root):
    cases = [
        Case(
            case_id="FALL-001",
            assigned_to="Daniel Rösch",
            customer=CaseCustomer(customer_id="C1", practice_name="Praxis A"),
            classification=Classification(schema_id="s1", title="Title 1"),
        ),
        Case(
            case_id="FALL-002",
            assigned_to="Robert",
            customer=CaseCustomer(customer_id="C2", practice_name="Praxis B"),
            classification=Classification(schema_id="s2", title="Title 2"),
        ),
    ]

    list_widget = CaseListWidget(
        parent=headless_root,
        on_case_selected=MagicMock(),
        on_search_changed=MagicMock(),
        current_user_name="Daniel Rösch",
        user_color="#8b5cf6",
        color_marker_enabled=True,
    )
    list_widget.set_cases(cases)

    def find_colored_frames(parent, color):
        found = []
        for child in parent.winfo_children():
            if isinstance(child, ctk.CTkFrame):
                try:
                    if child.cget("fg_color") == color:
                        found.append(child)
                except Exception:
                    pass
                found.extend(find_colored_frames(child, color))
        return found

    tiles = find_colored_frames(list_widget.scroll_frame, "#8b5cf6")
    assert len(tiles) >= 1, "Expected color tile for Daniel's case in case list"


def test_kanban_card_color_marker(headless_root):
    case_own = Case(
        case_id="FALL-100",
        assigned_to="Daniel Rösch",
        customer=CaseCustomer(customer_id="C1", practice_name="Praxis Own"),
        classification=Classification(schema_id="s1", title="Title Own"),
    )
    card_own = KanbanCardWidget(
        parent=headless_root,
        case=case_own,
        on_select_case=MagicMock(),
        on_switch_to_cockpit=MagicMock(),
        on_open_followup=MagicMock(),
        on_toggle_complete=MagicMock(),
        on_change_actor=MagicMock(),
        current_user_name="Daniel Rösch",
        user_color="#f59e0b",
        color_marker_enabled=True,
    )

    def find_colored_frames(parent, color):
        found = []
        for child in parent.winfo_children():
            if isinstance(child, ctk.CTkFrame):
                try:
                    if child.cget("fg_color") == color:
                        found.append(child)
                except Exception:
                    pass
                found.extend(find_colored_frames(child, color))
        return found

    assert len(find_colored_frames(card_own, "#f59e0b")) == 1

    case_other = Case(
        case_id="FALL-101",
        assigned_to="Other Person",
        customer=CaseCustomer(customer_id="C2", practice_name="Praxis Other"),
        classification=Classification(schema_id="s2", title="Title Other"),
    )
    card_other = KanbanCardWidget(
        parent=headless_root,
        case=case_other,
        on_select_case=MagicMock(),
        on_switch_to_cockpit=MagicMock(),
        on_open_followup=MagicMock(),
        on_toggle_complete=MagicMock(),
        on_change_actor=MagicMock(),
        current_user_name="Daniel Rösch",
        user_color="#f59e0b",
        color_marker_enabled=True,
    )
    assert len(find_colored_frames(card_other, "#f59e0b")) == 0


def test_profile_settings_user_color_marker_tab(headless_root, storage_service_mock):
    profile = UserProfile(user=UserInfo(name="Daniel Rösch", user_color="#ef4444", color_marker_enabled=True))
    dialog = ProfileSettingsDialog(headless_root, profile=profile, storage_service=storage_service_mock)

    # Check color switch and preview tile exist
    assert hasattr(dialog, "color_marker_switch")
    assert dialog.color_marker_switch.get() == 1
    assert hasattr(dialog, "preview_tile")
    assert dialog.preview_tile.cget("fg_color") == "#ef4444"

    # Select preset color
    dialog.set_selected_user_color("#10b981")
    assert dialog.selected_user_color == "#10b981"
    assert dialog.preview_tile.cget("fg_color") == "#10b981"

    # Save settings
    dialog.color_marker_switch.deselect()
    ok = dialog.save_user_settings()
    assert ok is True
    assert dialog.profile.user.user_color == "#10b981"
    assert dialog.profile.user.color_marker_enabled is False

    # Dynamic refresh
    get_i18n().current_language = "en"
    dialog.refresh_ui_labels()
    assert "Personal Color Tag" in dialog.color_marker_hdr_lbl.cget("text")
    assert "Choose color" in dialog.btn_pick_color.cget("text")
    assert "Preview" in dialog.preview_lbl.cget("text")

    dialog.destroy()
