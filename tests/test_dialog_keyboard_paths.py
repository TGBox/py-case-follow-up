"""Keyboard contract of the dialogs: Escape, Enter, delete confirmation, input grab.

Why these tests do not synthesise real key presses: tests/conftest.py force-
withdraws every window so the suite never flashes windows across the developer's
screen, and Tk does not deliver keyboard events to a non-viewable window - not
even with event_generate(..., when="now"), which was verified before writing
this file. So each test asserts two things instead: that the binding is actually
registered on the dialog, and that the handler behind it does the right thing.
That covers every way this contract has broken in practice (a lost binding, a
handler that closes despite unsaved input, Enter firing inside a note field)
without pretending to exercise the X11 input path.
"""

import customtkinter as ctk
import pytest

from ui.dialogs.base_dialog import BaseDialog
from ui.dialogs.confirm_dialog import ConfirmDialog


class KeyboardDemoDialog(BaseDialog):
    """Minimal BaseDialog subclass - the contract lives in the base class."""

    def __init__(self, parent, modal: bool = False):
        super().__init__(parent)
        self.setup_window(parent, "Tastatur-Demo", (320, 220), modal=modal)
        self.entry = ctk.CTkEntry(self)
        self.entry.pack()
        self.notes = ctk.CTkTextbox(self)
        self.notes.pack()


@pytest.fixture
def root():
    app = ctk.CTk()
    app.withdraw()
    yield app
    # Every dialog has to go before the root does: CustomTkinter's appearance and
    # scaling trackers keep class-level references to open toplevels, and tearing
    # down the interpreter underneath them leaves entries behind that make the
    # *next* test's window fail with "application has been destroyed".
    for child in list(app.winfo_children()):
        try:
            child.destroy()
        except Exception:
            pass
    try:
        app.update()
    except Exception:
        pass
    try:
        app.destroy()
    except Exception:
        pass


def _bindings(widget, sequence: str) -> int:
    bound = widget.bind(sequence)
    return len([line for line in bound.splitlines() if line.strip()]) if bound else 0


# --- Escape ---

def test_escape_is_bound_and_closes_a_clean_dialog(root):
    dialog = KeyboardDemoDialog(root)
    root.update()

    assert _bindings(dialog, "<Escape>") > 0, "Escape ist nicht gebunden"

    closed: list[str] = []
    dialog.close_dialog = lambda: closed.append("closed")
    assert dialog._on_escape() == "break", "Escape muss das Event verbrauchen"
    assert closed == ["closed"]


def test_escape_does_not_discard_unsaved_input_without_confirmation(root):
    dialog = KeyboardDemoDialog(root)
    dialog.enable_unsaved_guard()
    root.update()

    dialog.entry.insert(0, "ungespeicherte Eingabe")
    assert dialog.is_dirty() is True

    closed: list[str] = []
    dialog.close_dialog = lambda: closed.append("closed")
    dialog._confirm_discard = lambda: False        # user picks "keep editing"

    dialog._on_escape()
    assert closed == [], "Dialog wurde trotz ungespeicherter Eingabe geschlossen"

    dialog._confirm_discard = lambda: True         # user confirms discarding
    dialog._on_escape()
    assert closed == ["closed"]


def test_escape_can_be_switched_off_per_dialog(root):
    class NoEscapeDialog(KeyboardDemoDialog):
        escape_closes = False

    dialog = NoEscapeDialog(root)
    root.update()
    assert _bindings(dialog, "<Escape>") == 0


# --- Enter / primary action ---

def test_enter_is_bound_and_triggers_the_primary_action(root):
    dialog = KeyboardDemoDialog(root)
    root.update()

    fired: list[str] = []
    dialog.set_default_action(lambda: fired.append("primary"))

    assert _bindings(dialog, "<Return>") > 0, "Return ist nicht gebunden"
    assert _bindings(dialog, "<KP_Enter>") > 0, "Enter des Ziffernblocks fehlt"

    assert dialog._on_default_action() == "break"
    assert fired == ["primary"]


def test_enter_is_ignored_inside_a_multiline_field(root):
    """Otherwise Enter in a note or an e-mail body would submit the dialog."""
    dialog = KeyboardDemoDialog(root)
    root.update()

    fired: list[str] = []
    dialog.set_default_action(lambda: fired.append("primary"))

    dialog.focus_get = lambda: dialog.notes._textbox   # tkinter.Text inside CTkTextbox
    assert dialog._on_default_action() is None
    assert fired == [], "Enter hat im mehrzeiligen Feld die Primaeraktion ausgeloest"

    dialog.focus_get = lambda: dialog.entry
    dialog._on_default_action()
    assert fired == ["primary"]


def test_enter_without_a_default_action_does_nothing(root):
    dialog = KeyboardDemoDialog(root)
    root.update()
    assert _bindings(dialog, "<Return>") == 0
    assert dialog._on_default_action() == "break"


# --- Delete confirmation ---

def test_confirm_dialog_defaults_to_not_confirmed(root):
    """Escape, the X button and Cancel must never delete anything."""
    dialog = ConfirmDialog(root, "Wirklich loeschen?", danger=True)
    root.update()

    assert dialog.result is False
    assert _bindings(dialog, "<Escape>") > 0
    assert _bindings(dialog, "<Return>") > 0, "Enter muss die Primaeraktion ausloesen"

    dialog.close_dialog = lambda: None
    dialog._on_escape()
    assert dialog.result is False, "Escape darf nicht als Bestaetigung zaehlen"

    dialog.on_confirm()
    assert dialog.result is True
    dialog.destroy()


def test_delete_is_skipped_when_the_confirmation_is_declined(root, monkeypatch):
    """The caller must act on the answer, not on the dialog having been shown."""
    from ui.dialogs import tag_management_dialog as tmd

    deleted: list[str] = []

    class CallerStub:
        confirm_delete_tag = tmd.TagManagementDialog.confirm_delete_tag
        on_delete_tag = lambda self, name: deleted.append(name)  # noqa: E731

    monkeypatch.setattr(tmd, "ask_confirmation", lambda *a, **k: False, raising=False)
    monkeypatch.setattr("ui.dialogs.confirm_dialog.ask_confirmation", lambda *a, **k: False)
    CallerStub().confirm_delete_tag("Abrechnung")
    assert deleted == [], "Tag wurde trotz abgelehnter Rueckfrage geloescht"

    monkeypatch.setattr("ui.dialogs.confirm_dialog.ask_confirmation", lambda *a, **k: True)
    CallerStub().confirm_delete_tag("Abrechnung")
    assert deleted == ["Abrechnung"]


# --- Input grab ---

def test_modal_dialog_releases_its_grab_on_close(root):
    """A grab left behind makes the window underneath ignore every click."""
    dialog = KeyboardDemoDialog(root, modal=True)
    root.update()

    released: list[str] = []
    real_release = dialog.grab_release

    def spy_release():
        released.append("released")
        return real_release()

    # Only observe - stubbing destroy() out would leave this modal dialog alive
    # with its grab still held, and every later test would lose its input.
    dialog.grab_release = spy_release

    dialog.close_dialog()
    assert released == ["released"]
    assert not dialog.winfo_exists(), "Dialog wurde nicht geschlossen"


def test_closing_unregisters_the_language_listener(root):
    """A destroyed dialog must not keep firing on language changes."""
    from services.i18n_service import get_i18n

    class RelabelDialog(KeyboardDemoDialog):
        def refresh_ui_labels(self):
            pass

    dialog = RelabelDialog(root)
    root.update()

    listener = getattr(dialog, "_language_listener", None)
    assert listener is not None, "Dialog mit refresh_ui_labels wurde nicht registriert"
    assert listener in get_i18n()._listeners

    dialog.destroy()
    assert listener not in get_i18n()._listeners
