"""Light/dark appearance switching, colour contrast and fixed widget sizing across views, dialogs and cards."""

from typing import Any
from unittest.mock import MagicMock

import customtkinter as ctk
import pytest

from constants import (
    COLOR_CARD_BG,
    COLOR_CARD_BORDER,
    COLOR_PANEL_BG,
    COLOR_URGENCY_GREEN,
    COLOR_URGENCY_RED,
    COLOR_URGENCY_YELLOW,
    COLOR_WARNING_ORANGE,
)
from models.case import Case
from models.profile import UserInfo, UserProfile
from models.schema import QuestionSchema, SchemaField
from config import AppConfig
from services.storage_service import StorageService

LIGHT_TAB = ("gray86", "gray10")  # (label bg, label fg) on a tab in light mode
DARK_TAB = ("gray17", "#DCE4EE")


@pytest.fixture(autouse=True)
def _restore_appearance_mode():
    before = ctk.get_appearance_mode()
    yield
    ctk.set_appearance_mode(before)


def _label_colors(lbl: Any) -> tuple[str, str]:
    return lbl._label.cget("bg"), lbl._label.cget("fg")


def _frames(parent) -> list:
    found = []
    for w in parent.winfo_children():
        if isinstance(w, ctk.CTkFrame):
            found.append(w)
        found.extend(_frames(w))
    return found


def test_ui_components_build_in_light_and_dark_mode(tmp_path):
    """Core views and dialogs must build cleanly in both appearance modes."""
    from enums import Actor, UrgencyLevel
    from models.case import CaseCustomer, Classification, WorkflowStatus
    from services.attachment_service import AttachmentService
    from services.calendar_email_service import CalendarEmailService
    from services.scoring_service import ScoringService
    from services.snippet_service import SnippetService
    from services.wiki_sync_service import WikiSyncService
    from ui.dialogs.calendar_export_dialog import CalendarExportDialog
    from ui.dialogs.case_print_dialog import CasePrintDialog
    from ui.dialogs.email_draft_dialog import EmailDraftDialog
    from ui.dialogs.help_dialog import HelpDialog
    from ui.views.cockpit_view import CockpitView
    from ui.widgets.case_list_widget import CaseListWidget
    from ui.widgets.date_picker import CalendarDialog
    from ui.widgets.toast_notification import ToastNotification

    config = AppConfig(workspace_dir=tmp_path)
    storage = StorageService(config)
    att_svc = AttachmentService(config)
    cal_svc = CalendarEmailService(config)
    case = Case(
        case_id="T-THEME-01",
        customer=CaseCustomer(customer_id="K-77", practice_name="Praxis Theme Test", is_vip=True),
        classification=Classification(title="Theme Switch Test", urgency_level=UrgencyLevel.YELLOW),
        workflow_status=WorkflowStatus(current_actor=Actor.SUPPORT, followup_at="2026-08-26T10:00:00"),
    )

    for mode in ("Dark", "Light"):
        ctk.set_appearance_mode(mode)
        app = ctk.CTk()  # fresh root per mode so every widget is first drawn in that mode
        app.withdraw()
        cockpit = CockpitView(
            app, author_name="DaniBani", scoring_service=ScoringService(), attachment_service=att_svc,
            wiki_service=WikiSyncService(config), app_config=config, storage_service=storage,
        )
        cockpit.on_select_case_from_list(case)
        cockpit.update_idletasks()
        case_list = CaseListWidget(app, on_case_selected=lambda c: None, on_search_changed=lambda s: None)
        case_list.set_cases([case])
        case_list.update_idletasks()
        for build in (
            lambda: CalendarDialog(app, initial_date="2026-08-25T14:30:00", include_time=True),
            lambda: EmailDraftDialog(app, case, calendar_email_service=cal_svc, user_name="DaniBani", snippet_service=SnippetService(tmp_path)),
            lambda: CalendarExportDialog(app, case, calendar_email_service=cal_svc),
            lambda: CasePrintDialog(app, case, attachment_service=att_svc),
            lambda: HelpDialog(app),
        ):
            dlg = build()
            dlg.update_idletasks()
            dlg.destroy()
        toast = ToastNotification(app, title="Theme Test", message="Modus: " + mode, on_open=lambda: None)
        toast.update_idletasks()
        toast.safe_destroy()
        cockpit.destroy()
        case_list.destroy()
        app.destroy()


def test_tabview_keeps_color_tuple_and_label_follows_mode(root):
    """Patched CTkTabview: no white label boxes after switching to dark mode."""
    ctk.set_appearance_mode("Light")
    tv = ctk.CTkTabview(root)
    tv.pack()
    tab: Any = tv.add("TestTab")
    scroll = ctk.CTkScrollableFrame(tab, fg_color="transparent")
    scroll.pack()
    lbl = ctk.CTkLabel(scroll, text="Test Label")
    lbl.pack()
    root.update_idletasks()
    assert tuple(tab._fg_color) == ("gray86", "gray17")
    assert _label_colors(lbl)[0] == LIGHT_TAB[0]

    for mode, expected in [("Dark", DARK_TAB), ("Light", LIGHT_TAB)]:
        ctk.set_appearance_mode(mode)
        root.update_idletasks()
        assert tuple(tab._fg_color) == ("gray86", "gray17")
        assert _label_colors(lbl) == expected
    tv.destroy()


def test_profile_settings_dialog_follows_appearance_switch(root, tmp_path):
    from ui.dialogs.profile_settings_dialog import ProfileSettingsDialog

    storage = MagicMock(spec=StorageService)
    storage.list_profiles.return_value = ["Daniel Rösch"]
    storage.config = MagicMock()
    storage.config.workspace_dir = tmp_path / "workspace"
    storage.config.custom_cases_path = storage.config.custom_customers_path = storage.config.custom_wiki_db_path = None

    ctk.set_appearance_mode("Light")
    d = ProfileSettingsDialog(root, profile=UserProfile(user=UserInfo(name="Daniel Rösch")), storage_service=storage)
    root.update_idletasks()

    ctk.set_appearance_mode("Dark")
    root.update_idletasks()
    assert _label_colors(d.user_tab_hdr_lbl) == DARK_TAB
    assert _label_colors(d.app_shortcuts_hdr_lbl) == DARK_TAB
    assert tuple(d.tab_paths._fg_color) == ("gray86", "gray17")
    assert d.paths_scroll._parent_canvas.cget("bg") == "gray17"

    # Export/import cards on the paths tab are bordered panels
    cards = [f for f in _frames(d.paths_scroll) if f.cget("corner_radius") == 8]
    assert len(cards) >= 2
    assert all(c.cget("border_width") == 1 and c.cget("fg_color") == COLOR_PANEL_BG for c in cards)

    ctk.set_appearance_mode("Light")
    root.update_idletasks()
    assert _label_colors(d.user_tab_hdr_lbl) == LIGHT_TAB
    assert _label_colors(d.app_shortcuts_hdr_lbl) == LIGHT_TAB
    d.destroy()


def test_cockpit_panes_follow_appearance_mode(root):
    from ui.views.cockpit_view import CockpitView

    ctk.set_appearance_mode("Dark")
    cv = CockpitView(root, "Test", MagicMock(), MagicMock(), MagicMock())
    root.update_idletasks()

    for mode, paned_bg, canvas_bg in [("Light", "#ebebeb", "gray92"), ("Dark", "#2b2b2b", "#2b2b2b")]:
        ctk.set_appearance_mode(mode)
        cv.update_sash_color()
        root.update_idletasks()
        assert cv.paned.cget("bg") == paned_bg
        for pane in (cv.left_frame, cv.center_frame, cv.right_tabview):
            assert pane._canvas.cget("bg") == canvas_bg  # type: ignore[attr-defined]
    cv.destroy()


def test_cards_have_contrast_borders_across_views(root):
    """Cards keep their border and panel colour; built in dark mode so the dark icon variants render too."""
    from models.case import TimelineEntry
    from ui.views.analytics_view import AnalyticsView
    from ui.views.board_view import KanbanCardWidget
    from ui.widgets.timeline_widget import TimelineWidget

    ctk.set_appearance_mode("Dark")
    case = Case(
        case_id="T-1",
        classification=MagicMock(calculated_score=50.0, title="Title"),
        customer=MagicMock(is_vip=False, practice_name="Praxis"),
        workflow_status=MagicMock(current_actor="support", followup_at=None, is_completed=False),
    )
    k_card = KanbanCardWidget(root, case, MagicMock(), MagicMock(), MagicMock(), MagicMock(), MagicMock())
    assert (k_card.cget("border_width"), k_card.cget("border_color"), k_card.cget("fg_color")) == (1, COLOR_CARD_BORDER, COLOR_CARD_BG)
    k_card.destroy()

    tl = TimelineWidget(root, "Author", MagicMock())
    tl.load_timeline([TimelineEntry(timestamp="2026-09-11T12:00:00", author="Tester", channel="phone_inbound", note="Test Note")])
    tl_card = next(w for w in tl.scroll_frame.winfo_children() if isinstance(w, ctk.CTkFrame))
    assert (tl_card.cget("border_width"), tl_card.cget("border_color"), tl_card.cget("fg_color")) == (1, COLOR_CARD_BORDER, COLOR_CARD_BG)
    tl.destroy()

    view = AnalyticsView(root)
    view.set_cases([Case(case_id="C-1", classification=MagicMock(), customer=MagicMock(), workflow_status=MagicMock())])
    panels = [f for f in _frames(view.scroll_frame) if f.cget("border_width") == 1]
    assert len(panels) >= 3
    assert all(p.cget("fg_color") == COLOR_PANEL_BG for p in panels)
    view.destroy()


def _contrast(h1: str, h2: str) -> float:
    def lum(h: str) -> float:
        h = h.lstrip("#")
        vals = [int(h[i:i + 2], 16) / 255.0 for i in (0, 2, 4)]
        vals = [s / 12.92 if s <= 0.04045 else ((s + 0.055) / 1.055) ** 2.4 for s in vals]
        return 0.2126 * vals[0] + 0.7152 * vals[1] + 0.0722 * vals[2]

    l1, l2 = lum(h1), lum(h2)
    return (max(l1, l2) + 0.05) / (min(l1, l2) + 0.05)


@pytest.mark.parametrize("token", [COLOR_URGENCY_RED, COLOR_URGENCY_YELLOW, COLOR_URGENCY_GREEN, COLOR_WARNING_ORANGE])
def test_urgency_and_warning_tokens_meet_wcag_aa(token):
    assert _contrast(token[0], "#d4d4d8") >= 4.5  # light variant on light panel
    assert _contrast(token[1], "#333333") >= 4.5  # dark variant on dark panel


def test_dynamic_form_fields_have_fixed_widths(root):
    from ui.widgets.dynamic_form_widget import DynamicFormWidget

    schema = QuestionSchema(
        schema_id="schema_test_widths",
        display_name="Breitentest Formular",
        fields=[
            SchemaField(field_id="f_text", label="Textfeld", field_type="text", order=1),
            SchemaField(field_id="f_num", label="Zahlenfeld", field_type="number", order=2),
            SchemaField(field_id="f_drop", label="Dropdown", field_type="dropdown", options=["Opt 1", "Opt 2"], order=3),
            SchemaField(field_id="f_date", label="Datum", field_type="date", order=4),
            SchemaField(field_id="f_file", label="Datei", field_type="file", order=5),
            SchemaField(field_id="f_details", label="Genaue Begründung", field_type="text", order=6),  # multi-line keyword
        ],
    )
    form = DynamicFormWidget(root)
    form.load_schema(schema, form_data={})
    widths = {fid: w.cget("width") for fid, (_, w) in form.field_widgets.items()}
    assert widths == {"f_text": 400, "f_num": 400, "f_drop": 400, "f_date": 295, "f_file": 280, "f_details": 520}
    form.destroy()
