"""Tests for GUI Modernization: F11 fullscreen mode, responsive header, filter chips, and table sort indicators."""

from pathlib import Path
import pytest
import customtkinter as ctk

from config import AppConfig
from services.attachment_service import AttachmentService
from services.scoring_service import ScoringService
from services.storage_service import StorageService
from ui.app import SupportCockpitApp
from ui.widgets.case_list_widget import CaseListWidget
from ui.views.table_view import TableView
from constants import (
    COLOR_PRIMARY,
    COLOR_MUTED_GRAY,
    HEADER_BREAKPOINT_COMPACT,
)


@pytest.fixture
def app_config(tmp_path: Path) -> AppConfig:
    config = AppConfig(workspace_dir=tmp_path, username="gui_test_agent")
    storage = StorageService(config)
    profile = storage.load_profile()
    storage.save_profile(profile)
    return config


def test_fullscreen_toggle_and_f11_support(app_config: AppConfig):
    """Verifies that toggle_fullscreen switches between true fullscreen and zoomed windowed mode."""
    app = SupportCockpitApp(app_config)
    try:
        app.update()
        assert not getattr(app, "_is_fullscreen", False)

        # Toggle to fullscreen
        app.toggle_fullscreen()
        app.update()
        assert getattr(app, "_is_fullscreen", True) is True

        # Toggle back to windowed
        app.toggle_fullscreen()
        app.update()
        assert getattr(app, "_is_fullscreen", False) is False
        assert app.state() == "zoomed"
    finally:
        app.destroy()


def test_fullscreen_button_and_tooltip_update(app_config: AppConfig):
    """Verifies that the fullscreen button exists and updates its state and tooltip."""
    app = SupportCockpitApp(app_config)
    try:
        app.update()
        assert hasattr(app, "fullscreen_btn")
        assert app.fullscreen_btn is not None
        assert hasattr(app, "fullscreen_tooltip")

        # Initial tooltip indicates fullscreen entry
        assert "F11" in app.fullscreen_tooltip.text

        # Toggle to fullscreen
        app.toggle_fullscreen()
        app.update()
        assert "F11" in app.fullscreen_tooltip.text

        # Toggle back
        app.toggle_fullscreen()
        app.update()
        assert "F11" in app.fullscreen_tooltip.text
    finally:
        app.destroy()


def test_responsive_header_mode_switching(app_config: AppConfig):
    """Verifies that header collapses into more_menu_combo when width is compact (< HEADER_BREAKPOINT_COMPACT)."""
    app = SupportCockpitApp(app_config)
    try:
        app.update()
        assert hasattr(app, "more_menu_combo")
        assert hasattr(app, "stammdaten_combo")

        # Trigger compact mode (< 1150px)
        app._update_header_responsive(HEADER_BREAKPOINT_COMPACT - 100)
        app.update()
        assert getattr(app, "_header_is_compact", False) is True

        # Trigger wide mode (>= 1150px)
        app._update_header_responsive(HEADER_BREAKPOINT_COMPACT + 100)
        app.update()
        assert getattr(app, "_header_is_compact", True) is False
    finally:
        app.destroy()


def test_case_list_quick_filter_styling(tmp_path: Path):
    """Verifies that quick filter buttons highlight the active filter."""
    root = ctk.CTk()
    try:
        widget = CaseListWidget(
            root,
            on_case_selected=lambda c: None,
            on_search_changed=lambda s: None,
        )
        widget.pack()
        root.update()

        # Default: Alle is active
        widget.apply_quick_filter("")
        root.update()
        assert widget.qfilter_all_btn.cget("fg_color") == COLOR_PRIMARY

        # Filter urgent: Dringend is active
        widget.apply_quick_filter("vip:true")
        root.update()
        assert widget.qfilter_urgent_btn.cget("fg_color") == COLOR_PRIMARY
        assert widget.qfilter_all_btn.cget("fg_color") == COLOR_MUTED_GRAY

        # Filter followup: Wiedervorlage is active
        widget.apply_quick_filter("reminder:due")
        root.update()
        assert widget.qfilter_followup_btn.cget("fg_color") == COLOR_PRIMARY
        assert widget.qfilter_urgent_btn.cget("fg_color") == COLOR_MUTED_GRAY
    finally:
        root.destroy()


def test_table_sort_arrows_indicator(tmp_path: Path):
    """Verifies that clicking column headers updates sort arrows (▲ / ▼) in TableView."""
    root = ctk.CTk()
    config = AppConfig(workspace_dir=tmp_path, username="test_author")
    scoring = ScoringService()
    attachments = AttachmentService(config)
    try:
        view = TableView(
            root,
            author_name="test_author",
            scoring_service=scoring,
            attachment_service=attachments,
            on_case_updated=lambda c: None,
            on_case_selected=lambda c: None,
            app_config=config,
        )
        view.pack()
        root.update()

        # Initial sort is score descending
        hdr_text = view.tree.heading("score", "text")
        assert "▼" in hdr_text or "▲" in hdr_text

        # Click to toggle direction
        view.on_header_click("score")
        root.update()
        hdr_text_toggled = view.tree.heading("score", "text")
        assert hdr_text_toggled != hdr_text
    finally:
        root.destroy()
