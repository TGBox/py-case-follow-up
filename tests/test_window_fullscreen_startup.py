"""Tests for ensuring the application window reliably starts and remains in maximized/fullscreen mode."""

from pathlib import Path
import pytest

from config import AppConfig
from services.storage_service import StorageService
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


# --- Der Ladebildschirm muss vor der GUI da sein ---
#
# Gemeldet: beim Start sind Menueleiste und Dropdowns zu sehen, bevor der
# Ladebildschirm sie verdeckt. Drei Ursachen, die nacheinander gefunden wurden:
#   1. wm state "zoomed" blendet das Fenster auf Windows ein wie deiconify() -
#      das geschah, bevor es ueberhaupt etwas zu zeigen gab.
#   2. Tk stapelt Geschwister in Erzeugungsreihenfolge. Der Ladebildschirm wurde
#      vor der Menueleiste erzeugt und lag darunter; ein lift() danach kommt zu
#      spaet, weil CustomTkinter schon waehrend des Baus neu zeichnet.
#   3. Nach dem Einblenden fehlte ein volles update(), sodass das Ergebnis des
#      Maximierens nie verarbeitet und das Fenster gar nicht bemalt wurde.

def _record_first_mapping(monkeypatch):
    """Haelt fest, was im Fenster steht, wenn es zum ersten Mal eingeblendet wird."""
    import tkinter as tk

    erste = {}
    orig_deiconify = tk.Wm.deiconify
    orig_state = tk.Wm.state

    def merken(self):
        if not erste and isinstance(self, SupportCockpitApp):
            overlay = getattr(self, "splash_overlay", None)
            kinder = list(self.winfo_children())
            erste["splash"] = overlay is not None
            erste["splash_oben"] = bool(kinder) and kinder[-1] is overlay
            erste["menue_da"] = getattr(self, "menu_frame", None) is not None
            erste["inhalt_da"] = getattr(self, "container_frame", None) is not None

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


def test_the_splash_screen_exists_before_the_window_is_shown(app_config, monkeypatch):
    erste = _record_first_mapping(monkeypatch)

    app = SupportCockpitApp(app_config)
    try:
        app.update()
        assert erste, "Fenster wurde nie eingeblendet"
        assert erste["splash"] is True, "Fenster wird gezeigt, bevor der Ladebildschirm existiert"
    finally:
        app.destroy()


def test_the_gui_is_already_built_and_covered_when_the_window_is_shown(app_config, monkeypatch):
    """Menueleiste und Inhaltsbereich muessen fertig und verdeckt sein.

    Wird frueher eingeblendet, zeichnet CustomTkinter die Knoepfe und Dropdowns
    der Menueleiste sichtbar, bevor der Ladebildschirm darueber liegt - genau das
    war der gemeldete Blitzer.
    """
    erste = _record_first_mapping(monkeypatch)

    app = SupportCockpitApp(app_config)
    try:
        app.update()
        assert erste["menue_da"] is True, "Fenster erscheint, bevor die Menueleiste gebaut ist"
        assert erste["inhalt_da"] is True, "Fenster erscheint, bevor der Inhaltsbereich gebaut ist"
        assert erste["splash_oben"] is True, "Ladebildschirm liegt beim Einblenden nicht obenauf"
    finally:
        app.destroy()


def test_the_splash_stays_on_top_while_the_gui_is_built(app_config, monkeypatch):
    """Menueleiste und Inhaltsbereich entstehen nach dem Overlay und laegen sonst darueber.

    winfo_children() liefert die Stapelreihenfolge von unten nach oben, das
    Overlay muss also bei jedem Neuzeichnen das letzte Element sein. Geprueft
    wird bei jedem update_idletasks() waehrend des Aufbaus - genau dann kann
    etwas sichtbar werden.
    """
    import tkinter as tk

    verstoesse = []
    orig = tk.Misc.update_idletasks

    def spy(self):
        # CustomTkinter zeichnet ueber das jeweilige Kind-Widget neu, nicht ueber
        # das Hauptfenster - deshalb wird von dort nach oben aufgeloest.
        try:
            top = self.winfo_toplevel()
        except Exception:
            top = None
        overlay = getattr(top, "splash_overlay", None)
        # Nur solange das Fenster sichtbar ist - vorher kann nichts aufblitzen.
        if isinstance(top, SupportCockpitApp) and overlay is not None and top.state() != "withdrawn":
            kinder = list(top.winfo_children())
            if kinder and kinder[-1] is not overlay:
                verstoesse.append([c.__class__.__name__ for c in kinder])
        return orig(self)

    monkeypatch.setattr(tk.Misc, "update_idletasks", spy)

    app = SupportCockpitApp(app_config)
    try:
        assert verstoesse == [], f"Ladebildschirm lag beim Neuzeichnen nicht oben: {verstoesse}"
    finally:
        monkeypatch.undo()
        app.destroy()


def test_lifting_the_splash_after_it_is_gone_is_harmless(app_config):
    app = SupportCockpitApp(app_config)
    try:
        app.update()
        app._lift_splash()
    finally:
        app.destroy()


def test_the_window_is_fully_updated_when_it_is_revealed(app_config, monkeypatch):
    """Nach dem Einblenden muss ein volles update() laufen, nicht nur update_idletasks().

    Maximieren erledigt der Fenstermanager, das Ergebnis kommt als Ereignis
    zurueck. update_idletasks() arbeitet nur die Leerlauf-Warteschlange ab und
    laesst dieses Ereignis liegen: das Fenster behielt die Groesse, in der es
    gezeichnet wurde, und blieb danach waehrend des gesamten View-Aufbaus
    unbemalt - schwarz, ohne je den Ladebildschirm zu zeigen. Geprueft wird hier
    der Mechanismus, weil das Ergebnis nur auf Windows sichtbar ist.
    """
    import tkinter as tk

    ablauf = []
    orig_update = tk.Misc.update
    orig_deiconify = tk.Wm.deiconify

    def spy_update(self):
        if isinstance(self, SupportCockpitApp):
            ablauf.append("update")
        return orig_update(self)

    def spy_deiconify(self):
        if isinstance(self, SupportCockpitApp):
            ablauf.append("deiconify")
        return orig_deiconify(self)

    monkeypatch.setattr(tk.Misc, "update", spy_update)
    monkeypatch.setattr(tk.Wm, "deiconify", spy_deiconify)

    app = SupportCockpitApp(app_config)
    try:
        assert "deiconify" in ablauf, "Fenster wurde nie eingeblendet"
        nach_dem_einblenden = ablauf[ablauf.index("deiconify"):]
        assert "update" in nach_dem_einblenden, (
            "nach dem Einblenden folgt kein volles update() - das Fenster bleibt unbemalt"
        )
    finally:
        monkeypatch.undo()
        app.destroy()
