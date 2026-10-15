"""SupportCockpitApp window behaviour: startup/splash, maximized state, fullscreen, font zoom, responsive header, list/table chrome."""

import sys
import time
import tkinter as tk

import customtkinter as ctk
import pytest

from constants import COLOR_MUTED_GRAY, COLOR_PRIMARY, DEFAULT_FONT_SCALE, FONT_SCALE_MAX
from services.i18n_service import get_i18n, tr
from services.storage_service import StorageService
from ui.app import SupportCockpitApp

windows_only = pytest.mark.skipif(sys.platform != "win32", reason="needs the native Windows 'zoomed' window state")


@pytest.fixture
def app_config(config):
    storage = StorageService(config)
    storage.save_profile(storage.load_profile())
    return config


@pytest.fixture
def app(app_config):
    a = SupportCockpitApp(app_config)
    a.update()
    yield a
    try:
        a.destroy()
    except Exception:
        pass


# --- Startup: the main window only appears once it is complete ---
# Gemeldet: beim Start war die halbfertige Oberflaeche zu sehen. Deshalb ist der
# Ladebildschirm ein eigenes Fenster, und das Hauptfenster bleibt bis zur
# Fertigstellung unsichtbar.

def test_startup_shows_splash_first_and_reveals_the_finished_window(app_config, monkeypatch):
    """Splash before slow loading, main window hidden while built, shown only when complete and splash closed."""
    first_map: dict[str, bool] = {}
    visible_during_build: list[str] = []
    order: list[str] = []
    orig_deiconify, orig_state = tk.Wm.deiconify, tk.Wm.state
    orig_idle, orig_update = tk.Misc.update_idletasks, tk.Misc.update
    orig_load = SupportCockpitApp.load_all_data

    def record_first_map(self):
        if not first_map and isinstance(self, SupportCockpitApp):
            first_map.update(
                menu=getattr(self, "menu_frame", None) is not None,
                content=getattr(self, "container_frame", None) is not None,
                view=getattr(self, "active_view", None) is not None,
                splash_closed=getattr(self, "splash_window", None) is None,
            )

    def spy_deiconify(self):
        record_first_map(self)
        return orig_deiconify(self)

    def spy_state(self, newstate=None):
        if newstate is None:
            return orig_state(self)
        if str(newstate) != "withdrawn":
            record_first_map(self)
        return orig_state(self, newstate)

    def spy_idle(self):
        try:
            top = self.winfo_toplevel()
        except Exception:
            top = None
        if isinstance(top, SupportCockpitApp) and getattr(top, "splash_window", None) is not None:
            if top.state() != "withdrawn":
                visible_during_build.append(top.state())
        return orig_idle(self)

    def spy_update(self):
        if isinstance(self, ctk.CTkToplevel):
            order.append("splash shown")
        return orig_update(self)

    def spy_load(self):
        order.append("load data")
        return orig_load(self)

    monkeypatch.setattr(tk.Wm, "deiconify", spy_deiconify)
    monkeypatch.setattr(tk.Wm, "state", spy_state)
    monkeypatch.setattr(tk.Misc, "update_idletasks", spy_idle)
    monkeypatch.setattr(tk.Misc, "update", spy_update)
    monkeypatch.setattr(SupportCockpitApp, "load_all_data", spy_load)

    app = SupportCockpitApp(app_config)
    try:
        assert "splash shown" in order and order.index("splash shown") < order.index("load data")
        assert visible_during_build == []
        assert first_map == {"menu": True, "content": True, "view": True, "splash_closed": True}
        assert app.splash_window is None
    finally:
        monkeypatch.undo()
        app.destroy()


def test_a_splash_window_that_cannot_open_does_not_stop_the_app(app_config, monkeypatch):
    """Der Ladebildschirm ist Beiwerk - er darf den Start nie verhindern."""
    def broken(self):
        raise RuntimeError("kein Fenster moeglich")

    monkeypatch.setattr(ctk, "CTkToplevel", broken)
    app = SupportCockpitApp(app_config)
    try:
        assert app.splash_window is None
        assert app.menu_frame is not None
    finally:
        monkeypatch.undo()
        app.destroy()


# --- Maximized start (native Windows state) ---

@windows_only
@pytest.mark.parametrize("font_scale", [DEFAULT_FONT_SCALE, 1.25])
def test_app_starts_maximized_beyond_minsize(app_config, font_scale):
    """A non-default font scale must not clamp the window to its minsize."""
    storage = StorageService(app_config)
    profile = storage.load_profile()
    profile.ui_settings.font_scale = font_scale
    storage.save_profile(profile)

    app = SupportCockpitApp(app_config)
    try:
        app.update()
        assert app.state() == "zoomed"
        assert app.winfo_width() >= 1024
        assert app.winfo_height() >= 700
    finally:
        app.destroy()


@windows_only
def test_font_zoom_keeps_the_window_maximized(app):
    initial_width = app.winfo_width()
    app.zoom_font(0.1)
    app.update()
    assert app.state() == "zoomed"
    assert app.winfo_width() == initial_width


def test_font_zoom_is_clamped_persisted_and_resettable(app, app_config):
    def saved_scale():
        app.storage_service.flush_all_saves()
        return StorageService(app_config).load_profile().ui_settings.font_scale

    try:
        app.zoom_font(10.0)
        assert saved_scale() == FONT_SCALE_MAX
        assert app.state() == "zoomed"
    finally:
        app.zoom_font(0.0, reset=True)  # set_widget_scaling is global - never leak it into other tests
    assert saved_scale() == DEFAULT_FONT_SCALE


# --- Fullscreen (F11) ---

@pytest.mark.parametrize("start_state", ["zoomed", "normal"])
def test_fullscreen_round_trip_restores_previous_state_and_tooltip(app, start_state):
    """Leaving fullscreen returns to exactly the previous state; a restored-down window must not be maximized."""
    enter_text = tr("menu.fullscreen", "Vollbild (F11)")
    leave_text = tr("menu.windowed", "Fenstermodus (F11)")
    assert app.state() == "zoomed"  # starts maximized
    app.state(start_state)
    app.update()
    assert app.state() == start_state  # restore-down is not forced back
    assert app.fullscreen_tooltip.text == enter_text

    app.toggle_fullscreen()
    app.update()
    assert app._is_fullscreen is True
    assert app.fullscreen_tooltip.text == leave_text

    app.toggle_fullscreen()
    app.update()
    assert app._is_fullscreen is False
    assert app.state() == start_state
    assert app.fullscreen_tooltip.text == enter_text


# --- Responsive header ---

def _assert_header_packed(app, compact: bool) -> None:
    grouped = (app.stammdaten_combo, app.vorlagen_combo, app.datenaustausch_combo)
    assert app.more_menu_combo.winfo_manager() == ("pack" if compact else "")
    assert all(combo.winfo_manager() == ("" if compact else "pack") for combo in grouped)


def test_header_collapses_into_more_menu_when_narrow_and_survives_menu_rebuild(app, monkeypatch):
    """Header collapses once the window is narrower than the full header needs; a language change
    rebuilds the menu bar and a compact header must stay compact afterwards.

    The requirement is measured instead of a fixed breakpoint: with Windows display scaling the
    full header did not fit on Full HD any more, but stayed wide and pack squeezed the user button.
    """
    required = app._header_required_width()
    assert required > 0

    app._update_header_responsive(required)
    app.update()
    _assert_header_packed(app, compact=False)

    app._update_header_responsive(required - 1)
    app.update()
    _assert_header_packed(app, compact=True)
    # Measured for the wide layout, whichever mode is active
    assert app._header_required_width() == required

    # The rebuild re-measures with the new labels; English is shorter than German, so a window
    # just below the German requirement may legitimately fit. Use one that fits in no language.
    monkeypatch.setattr(app, "winfo_width", lambda: required // 2)
    get_i18n().current_language = "en"
    end = time.monotonic() + 0.15  # also lets the deferred cockpit sash restore run on the rebuilt UI
    while time.monotonic() < end:
        app.update()
        time.sleep(0.01)
    _assert_header_packed(app, compact=True)


def test_header_requirement_grows_with_scaling(app):
    """At a larger scaling the full header needs more room, so it collapses earlier."""
    required_100 = app._header_required_width()
    try:
        ctk.set_widget_scaling(1.5)
        app.update()
        assert app._header_required_width() > required_100
    finally:
        ctk.set_widget_scaling(1.0)


# --- Case list quick filters and table sort arrows ---

def test_case_list_quick_filter_highlights_the_active_chip(root):
    from ui.widgets.case_list_widget import CaseListWidget

    widget = CaseListWidget(root, on_case_selected=lambda c: None, on_search_changed=lambda s: None)
    widget.pack()
    chips = {"": widget.qfilter_all_btn, "vip:true": widget.qfilter_urgent_btn, "reminder:due": widget.qfilter_followup_btn}
    for query, active in chips.items():
        widget.apply_quick_filter(query)
        root.update()
        for chip in chips.values():
            assert chip.cget("fg_color") == (COLOR_PRIMARY if chip is active else COLOR_MUTED_GRAY), query


def test_table_header_click_flips_the_sort_arrow(root, config):
    from services.attachment_service import AttachmentService
    from services.scoring_service import ScoringService
    from ui.views.table_view import TableView

    view = TableView(root, author_name="test_agent", scoring_service=ScoringService(),
                     attachment_service=AttachmentService(config), on_case_updated=lambda c: None,
                     on_case_selected=lambda c: None, app_config=config)
    view.pack()
    root.update()
    before = view.tree.heading("score", "text")
    assert "▼" in before or "▲" in before

    view.on_header_click("score")
    root.update()
    assert view.tree.heading("score", "text") != before
