"""BaseDialog / ConfirmDialog contract: Escape, Enter, close protocol, grab, unsaved guard, live relabelling."""

import importlib
import inspect
from unittest.mock import MagicMock

import customtkinter as ctk
import pytest

import ui.dialogs.confirm_dialog as confirm_mod
from models.profile import UserProfile
from services.i18n_service import get_i18n
from ui.dialogs.base_dialog import BaseDialog
from ui.dialogs.confirm_dialog import ConfirmDialog, _restore_parent_grab, ask_confirmation, show_notice

# Tk does not deliver key events to the force-withdrawn test windows (see conftest), so the
# keyboard tests assert that the binding is registered and that its handler behaves correctly.


class DemoDialog(BaseDialog):
    def __init__(self, parent, modal: bool = False):
        super().__init__(parent)
        self.setup_window(parent, "Tastatur-Demo", (320, 220), modal=modal)
        self.entry = ctk.CTkEntry(self)
        self.entry.pack()
        self.notes = ctk.CTkTextbox(self)
        self.notes.pack()


@pytest.fixture(scope="module")
def _shared_root():
    # One root per module instead of conftest's per-test root: creating a CTk costs ~0.3 s.
    shared = ctk.CTk()
    shared.withdraw()
    yield shared
    try:
        shared.destroy()
    except Exception:
        pass


@pytest.fixture
def app(_shared_root):
    """Shared root; every dialog is destroyed after the test so nothing leaks into the next one."""
    root = _shared_root
    yield root
    for child in list(root.winfo_children()):
        try:
            child.destroy()
        except Exception:
            pass
    try:
        root.update()
    except Exception:
        pass


def _bindings(widget, sequence: str) -> int:
    bound = widget.bind(sequence)
    return len([line for line in bound.splitlines() if line.strip()]) if bound else 0


def _tag_dialog(parent, storage, profile=None):
    from ui.dialogs.tag_management_dialog import TagManagementDialog

    dlg = TagManagementDialog(parent, profile=profile or UserProfile(), storage_service=storage, on_tags_updated=lambda: None)
    dlg.update_idletasks()
    return dlg


# --- Window contract / Escape ---

def test_dialog_has_title_close_protocol_and_escape_closes_it(app):
    dialog = DemoDialog(app)
    app.update()

    assert dialog.wm_title() == "Tastatur-Demo"
    assert dialog.protocol("WM_DELETE_WINDOW"), "WM_DELETE_WINDOW handler missing"
    assert _bindings(dialog, "<Escape>") > 0, "Escape ist nicht gebunden"

    assert dialog._on_escape() == "break", "Escape muss das Event verbrauchen"
    app.update_idletasks()
    assert not dialog.winfo_exists()


def test_escape_can_be_switched_off_per_dialog(app):
    class NoEscapeDialog(DemoDialog):
        escape_closes = False

    dialog = NoEscapeDialog(app)
    assert _bindings(dialog, "<Escape>") == 0


def test_modal_dialog_releases_its_grab_on_close(app):
    """A grab left behind makes the window underneath ignore every click."""
    dialog = DemoDialog(app, modal=True)
    app.update()

    released: list[str] = []
    real_release = dialog.grab_release

    def spy_release():
        released.append("released")
        return real_release()

    dialog.grab_release = spy_release
    dialog.close_dialog()
    assert released == ["released"]
    assert not dialog.winfo_exists()


# --- Enter / primary action ---

def test_enter_triggers_primary_action_except_inside_multiline_field(app):
    """Otherwise Enter in a note or an e-mail body would submit the dialog."""
    dialog = DemoDialog(app)
    assert _bindings(dialog, "<Return>") == 0
    assert dialog._on_default_action() == "break", "Enter ohne Primaeraktion muss trotzdem verbraucht werden"

    fired: list[str] = []
    dialog.set_default_action(lambda: fired.append("primary"))
    assert _bindings(dialog, "<Return>") > 0
    assert _bindings(dialog, "<KP_Enter>") > 0, "Enter des Ziffernblocks fehlt"

    dialog.focus_get = lambda: dialog.notes._textbox   # tkinter.Text inside CTkTextbox
    assert dialog._on_default_action() is None
    assert fired == []

    dialog.focus_get = lambda: dialog.entry
    assert dialog._on_default_action() == "break"
    assert fired == ["primary"]


# --- ConfirmDialog ---

@pytest.mark.parametrize(
    "action, expected",
    [("on_confirm", True), ("_on_default_action", True), ("request_close", False), ("_on_escape", False)],
)
def test_confirm_dialog_is_only_confirmed_by_confirm_or_enter(app, action, expected):
    """Escape, the X button and Cancel must never confirm a destructive action."""
    dialog = ConfirmDialog(app, "Wirklich loeschen?", title="Loeschen", confirm_text="Ja, loeschen", danger=True)
    app.update_idletasks()
    assert dialog.result is False
    assert dialog.confirm_btn.cget("text") == "Ja, loeschen"
    assert _bindings(dialog, "<Escape>") > 0 and _bindings(dialog, "<Return>") > 0

    getattr(dialog, action)()
    app.update_idletasks()
    assert dialog.result is expected
    assert not dialog.winfo_exists()


def test_confirm_dialog_enter_inside_textbox_does_not_confirm(app):
    dialog = ConfirmDialog(app, "Wirklich?")
    textbox = ctk.CTkTextbox(dialog)
    dialog.focus_get = lambda: textbox
    assert dialog._on_default_action() is None
    assert dialog.result is False


def test_notice_offers_exactly_one_button(app):
    dialog = ConfirmDialog(app, "Hinweis", danger=False, show_cancel=False)
    app.update_idletasks()
    buttons = [
        child for container in dialog.winfo_children() for child in container.winfo_children()
        if isinstance(child, ctk.CTkButton)
    ]
    assert len(buttons) == 1


def test_restore_parent_grab_falls_back_to_parent():
    _restore_parent_grab(MagicMock(), None)
    _restore_parent_grab(MagicMock(), "")

    prev, parent = MagicMock(), MagicMock()
    _restore_parent_grab(parent, prev)
    prev.grab_set.assert_called_once()
    parent.grab_set.assert_not_called()

    failing = MagicMock()
    failing.grab_set.side_effect = RuntimeError("Grab failed")
    parent = MagicMock()
    _restore_parent_grab(parent, failing)
    parent.grab_set.assert_called_once()

    parent.grab_set.side_effect = RuntimeError("Parent grab failed")
    _restore_parent_grab(parent, failing)   # must not raise


@pytest.mark.parametrize("answer", [True, False, "raise"])
def test_ask_confirmation_returns_the_users_answer(app, monkeypatch, answer):
    def fake_wait_window(win):
        if answer == "raise":
            raise RuntimeError("No event loop")
        win.result = answer

    monkeypatch.setattr(app, "wait_window", fake_wait_window)
    assert ask_confirmation(app, "Fall wirklich loeschen?", danger=True) is (answer is True)


def test_show_notice_waits_for_the_dialog(app, monkeypatch):
    shown = []
    monkeypatch.setattr(app, "wait_window", lambda win: shown.append(win.confirm_btn.cget("text")))
    show_notice(app, "Dieser Vorgang ist abgeschlossen.", title="Hinweis")
    assert len(shown) == 1


# --- Unsaved-changes guard ---

def test_unsaved_guard_detects_typing_only_once_enabled(app):
    dialog = DemoDialog(app)
    dialog.entry.insert(0, "Ohne Guard")
    assert dialog.is_dirty() is False, "the guard must stay off until enable_unsaved_guard()"

    dialog.enable_unsaved_guard()
    assert dialog.is_dirty() is False
    dialog.entry.insert("end", " mehr")
    assert dialog.is_dirty() is True
    dialog.mark_clean()
    assert dialog.is_dirty() is False

    dialog.notes.insert("1.0", "Notiz")
    assert dialog.is_dirty() is True, "Mehrzeiliges Feld wird nicht erkannt"
    dialog.mark_clean()

    late = ctk.CTkEntry(dialog)
    late.insert(0, "nachtraeglich hinzugefuegt")
    late.pack()
    assert dialog.is_dirty() is True, "neues, befuelltes Feld wird nicht erkannt"


def test_escape_with_unsaved_input_asks_before_discarding(app, monkeypatch):
    dialog = DemoDialog(app)
    dialog.enable_unsaved_guard()
    dialog.entry.insert(0, "ungespeicherte Eingabe")

    monkeypatch.setattr(confirm_mod, "ask_confirmation", lambda *a, **k: False)
    dialog._on_escape()
    app.update_idletasks()
    assert dialog.winfo_exists(), "Dialog wurde trotz ungespeicherter Eingabe geschlossen"

    monkeypatch.setattr(confirm_mod, "ask_confirmation", lambda *a, **k: True)
    dialog.request_close()
    app.update_idletasks()
    assert not dialog.winfo_exists()


def test_read_only_and_excluded_widgets_are_never_unsaved_input(app):
    """Search boxes, filter bars and display-only fields navigate - they do not edit."""
    dialog = DemoDialog(app)
    filterleiste = ctk.CTkFrame(dialog)
    filterleiste.pack()
    filter_feld = ctk.CTkEntry(filterleiste)
    filter_feld.pack()
    dialog.exclude_from_unsaved_guard(filterleiste)
    dialog.enable_unsaved_guard()

    anzeige = ctk.CTkEntry(dialog)
    anzeige.insert(0, "nur zur Anzeige")
    anzeige.configure(state="disabled")
    anzeige.pack()
    filter_feld.insert(0, "Suchbegriff")
    assert dialog.is_dirty() is False

    dialog.exclude_from_unsaved_guard(dialog.entry)   # excluding after enabling re-baselines
    dialog.entry.insert(0, "x")
    assert dialog.is_dirty() is False

    dialog.notes.insert("1.0", "echte Eingabe")
    assert dialog.is_dirty() is True


GUARDED_FORM_DIALOGS = [
    "customer_management_dialog", "colleague_management_dialog", "snippet_management_dialog",
    "template_manager_dialog", "schema_builder_dialog", "followup_dialog", "handover_dialog",
    "new_case_dialog", "email_draft_dialog",
]


def test_every_form_dialog_arms_the_unsaved_guard():
    """A form dialog that forgets the guard discards typed input without asking."""
    missing = [
        name for name in GUARDED_FORM_DIALOGS
        if "enable_unsaved_guard()" not in inspect.getsource(importlib.import_module(f"ui.dialogs.{name}"))
    ]
    assert not missing, f"Dialoge ohne Unsaved-Guard: {missing}"


# --- Language listener and live relabelling ---

def test_language_listener_is_removed_on_close_and_does_not_leak(app):
    """A destroyed dialog must not keep firing on language changes."""
    class RelabelDialog(DemoDialog):
        def refresh_ui_labels(self):
            pass

    listeners = get_i18n()._listeners
    baseline = len(listeners)
    # Leak regression: repeated open/close must not accumulate listeners; 3 cycles are enough.
    for _ in range(3):
        dialog = RelabelDialog(app)
        assert dialog._language_listener in listeners
        dialog.destroy()
    assert len(listeners) == baseline



def test_listener_of_a_dead_window_unsubscribes_itself(app):
    dialog = DemoDialog(app)
    listener = dialog._language_listener
    assert listener in get_i18n()._listeners
    dialog.winfo_exists = lambda: False
    get_i18n().current_language = "en"    # must not raise on the dead window
    assert listener not in get_i18n()._listeners
    dialog.destroy()


def test_open_dialog_relabels_widgets_and_title_on_language_switch(app, storage):
    i18n = get_i18n()
    dlg = _tag_dialog(app, storage)
    assert dlg._i18n_widgets, "no widget registered its translation key"

    def labels():
        return [w.cget(attr) for w, attr, *_ in dlg._i18n_widgets if w.winfo_exists()]

    german, german_title = labels(), dlg.wm_title()
    titles = {}
    for lang in ("en", "sv"):
        i18n.current_language = lang
        app.update_idletasks()
        titles[lang] = dlg.wm_title()
        if lang == "en":
            assert any(a != b for a, b in zip(german, labels(), strict=False)), "no label changed"
    assert titles["en"] != german_title, "the window title did not follow the language"
    assert len({german_title, *titles.values()}) >= 2

    i18n.current_language = "de"
    app.update_idletasks()
    assert labels() == german, "switching back did not restore the German labels"


def test_rebuilt_rows_are_pruned_from_the_i18n_registry(app, storage):
    dlg = _tag_dialog(app, storage)
    before = len(dlg._i18n_widgets)
    dlg.render_tags_list()
    dlg.render_tags_list()
    get_i18n().current_language = "en"
    app.update_idletasks()

    assert before > 0
    assert all(entry[0].winfo_exists() for entry in dlg._i18n_widgets), "registry still holds destroyed widgets"


def test_rapid_language_cycling_with_open_dialogs_keeps_them_alive(app, storage):
    i18n = get_i18n()
    dialogs = [_tag_dialog(app, storage) for _ in range(2)]
    for i in range(6):
        i18n.current_language = ("de", "en", "sv")[i % 3]
    app.update_idletasks()
    assert all(d.winfo_exists() for d in dialogs)
