"""Tests for ensuring the application window reliably starts and remains in maximized/fullscreen mode."""

from pathlib import Path
import pytest

from config import AppConfig
from services.storage_service import StorageService
import customtkinter as ctk
from ui.app import SupportCockpitApp


@pytest.fixture
def app_config(tmp_path: Path) -> AppConfig:
    config = AppConfig(workspace_dir=tmp_path, username="test_agent")
    storage = StorageService(config)
    profile = storage.load_profile()
    storage.save_profile(profile)
    return config


def test_app_starts_in_zoomed_fullscreen(app_config: AppConfig):
    """Verifies that SupportCockpitApp starts automatically in zoomed (maximized) state."""
    app = SupportCockpitApp(app_config)
    try:
        app.update()
        assert app.state() == "zoomed"
        # Ensure it expanded beyond the minsize (900x650)
        assert app.winfo_width() >= 1024
        assert app.winfo_height() >= 700
    finally:
        app.destroy()


def test_app_starts_zoomed_with_custom_font_scale(app_config: AppConfig):
    """Verifies that non-default font scale does not clamp window dimensions to minsize."""
    storage = StorageService(app_config)
    profile = storage.load_profile()
    profile.ui_settings.font_scale = 1.25
    storage.save_profile(profile)

    app = SupportCockpitApp(app_config)
    try:
        app.update()
        assert app.state() == "zoomed"
        assert app.winfo_width() >= 1024
        assert app.winfo_height() >= 700
    finally:
        app.destroy()


def test_app_allows_restore_down_to_normal_state(app_config: AppConfig):
    """Verifies that users can freely unmaximize (Restore Down) without being forced back to zoomed."""
    app = SupportCockpitApp(app_config)
    try:
        app.update()
        assert app.state() == "zoomed"

        # User unmaximizes window
        app.state("normal")
        app.update()
        assert app.state() == "normal"
    finally:
        app.destroy()


def test_app_font_zoom_maintains_zoomed_state(app_config: AppConfig):
    """Verifies that dynamically adjusting font scale preserves zoomed state."""
    app = SupportCockpitApp(app_config)
    try:
        app.update()
        assert app.state() == "zoomed"
        initial_width = app.winfo_width()

        app.zoom_font(0.1)
        app.update()
        assert app.state() == "zoomed"
        assert app.winfo_width() == initial_width
    finally:
        app.destroy()


# --- Der Ladebildschirm ist ein eigenes Fenster ---
#
# Gemeldet: beim Start ist die halbfertige Oberflaeche zu sehen - erst die
# Menueleiste ueber dem Ladebildschirm, spaeter ein schwarzes Fenster, zuletzt
# eine leere Fallliste im Moment des Aufdeckens. Ein Overlay *im* Hauptfenster
# kann das prinzipiell nicht verhindern: es kann das Fenster nur verdecken,
# nicht sein Zeichnen unterbinden, und beim Entfernen muss alles darunter neu
# gezeichnet werden. Deshalb ist der Ladebildschirm jetzt ein eigenes kleines
# Fenster, und das Hauptfenster bleibt bis zur Fertigstellung unsichtbar.

def _record_first_mapping(monkeypatch):
    """Haelt fest, wie weit der Aufbau ist, wenn das Hauptfenster erscheint."""
    import tkinter as tk

    erste = {}
    orig_deiconify = tk.Wm.deiconify
    orig_state = tk.Wm.state

    def merken(self):
        if not erste and isinstance(self, SupportCockpitApp):
            erste["menue_da"] = getattr(self, "menu_frame", None) is not None
            erste["inhalt_da"] = getattr(self, "container_frame", None) is not None
            erste["view_da"] = getattr(self, "active_view", None) is not None
            erste["splash_zu"] = getattr(self, "splash_window", None) is None

    def spy_deiconify(self):
        merken(self)
        return orig_deiconify(self)

    def spy_state(self, newstate=None):
        if newstate is not None and str(newstate) != "withdrawn":
            merken(self)
        return orig_state(self, newstate) if newstate is not None else orig_state(self)

    monkeypatch.setattr(tk.Wm, "deiconify", spy_deiconify)
    monkeypatch.setattr(tk.Wm, "state", spy_state)
    return erste


def test_the_main_window_appears_only_when_it_is_complete(app_config, monkeypatch):
    """Menueleiste, Inhaltsbereich und die Startansicht muessen fertig sein."""
    erste = _record_first_mapping(monkeypatch)

    app = SupportCockpitApp(app_config)
    try:
        assert erste, "Hauptfenster wurde nie eingeblendet"
        assert erste["menue_da"] is True, "Fenster erscheint vor der Menueleiste"
        assert erste["inhalt_da"] is True, "Fenster erscheint vor dem Inhaltsbereich"
        assert erste["view_da"] is True, "Fenster erscheint, bevor eine Ansicht aufgebaut ist"
    finally:
        app.destroy()


def test_the_splash_is_a_separate_window_and_is_closed_first(app_config, monkeypatch):
    """Sonst liegt der Ladebildschirm ueber dem fertigen Fenster."""
    erste = _record_first_mapping(monkeypatch)

    app = SupportCockpitApp(app_config)
    try:
        assert erste["splash_zu"] is True, "Ladebildschirm steht beim Einblenden noch offen"
        assert app.splash_window is None
    finally:
        app.destroy()


def test_the_main_window_stays_hidden_while_the_gui_is_built(app_config, monkeypatch):
    """Waehrend des Aufbaus darf vom Hauptfenster nichts zu sehen sein."""
    import tkinter as tk

    sichtbar_waehrend_aufbau = []
    orig = tk.Misc.update_idletasks

    def spy(self):
        try:
            top = self.winfo_toplevel()
        except Exception:
            top = None
        if isinstance(top, SupportCockpitApp) and getattr(top, "splash_window", None) is not None:
            if top.state() != "withdrawn":
                sichtbar_waehrend_aufbau.append(top.state())
        return orig(self)

    monkeypatch.setattr(tk.Misc, "update_idletasks", spy)

    app = SupportCockpitApp(app_config)
    try:
        assert sichtbar_waehrend_aufbau == [], (
            f"Hauptfenster war waehrend des Aufbaus sichtbar: {sichtbar_waehrend_aufbau}"
        )
    finally:
        monkeypatch.undo()
        app.destroy()


def test_the_splash_window_is_shown_before_the_slow_work_starts(app_config, monkeypatch):
    """Sonst steht der Nutzer waehrend des Ladens vor einem leeren Desktop."""
    import tkinter as tk

    ablauf = []
    orig_update = tk.Misc.update
    orig_load = SupportCockpitApp.load_all_data

    def spy_update(self):
        if isinstance(self, ctk.CTkToplevel):
            ablauf.append("splash sichtbar")
        return orig_update(self)

    def spy_load(self):
        ablauf.append("daten laden")
        return orig_load(self)

    monkeypatch.setattr(tk.Misc, "update", spy_update)
    monkeypatch.setattr(SupportCockpitApp, "load_all_data", spy_load)

    app = SupportCockpitApp(app_config)
    try:
        assert "splash sichtbar" in ablauf, "Ladebildschirm wird nie gezeigt"
        assert ablauf.index("splash sichtbar") < ablauf.index("daten laden"), (
            "Ladebildschirm erscheint erst nach dem Laden der Daten"
        )
    finally:
        monkeypatch.undo()
        app.destroy()


def test_a_splash_window_that_cannot_open_does_not_stop_the_app(app_config, monkeypatch):
    """Der Ladebildschirm ist Beiwerk - er darf den Start nie verhindern."""
    def kaputt(self):
        raise RuntimeError("kein Fenster moeglich")

    monkeypatch.setattr(ctk, "CTkToplevel", kaputt)

    app = SupportCockpitApp(app_config)
    try:
        assert app.splash_window is None
        assert app.menu_frame is not None, "App ist nicht fertig gestartet"
    finally:
        monkeypatch.undo()
        app.destroy()
