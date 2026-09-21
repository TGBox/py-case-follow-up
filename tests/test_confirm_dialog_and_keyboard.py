"""Tests for ConfirmDialog, ask_confirmation, show_notice, and modal grab restoration."""

from unittest.mock import MagicMock
import customtkinter as ctk
import pytest
from ui.dialogs.confirm_dialog import (
    ConfirmDialog,
    _restore_parent_grab,
    ask_confirmation,
    show_notice,
)


@pytest.fixture(scope="module")
def app_root():
    app = ctk.CTk()
    app.withdraw()
    yield app
    try:
        app.destroy()
    except Exception:
        pass


def test_confirm_dialog_init_and_confirm(app_root):
    """Verify ConfirmDialog sets up widgets and on_confirm sets result to True."""
    dialog = ConfirmDialog(
        app_root,
        message="Sind Sie sicher?",
        title="Löschen bestätigen",
        confirm_text="Ja, löschen",
        cancel_text="Nein",
        danger=True,
        show_cancel=True,
    )
    assert dialog.result is False
    assert dialog.confirm_btn.cget("text") == "Ja, löschen"

    # Trigger confirm
    dialog.on_confirm()
    assert dialog.result is True # type: ignore
    dialog.destroy()


def test_confirm_dialog_cancel_button(app_root):
    """Test clicking Cancel button sets result to False."""
    dialog = ConfirmDialog(
        parent=app_root,
        title="Abbrechen Test",
        message="Möchten Sie abbrechen?",
        confirm_text="Ja",
        cancel_text="Nein",
    )
    assert dialog.result is False
    dialog.request_close()
    assert dialog.result is False # type: ignore
    dialog.destroy()


def test_confirm_dialog_info_mode(app_root):
    """Test info mode without cancel button."""
    dialog = ConfirmDialog(
        parent=app_root,
        title="Info Test",
        message="Nur zur Information",
        confirm_text="Verstanden",
        cancel_text="",
    )
    assert dialog.result is False
    # No cancel button added
    dialog.on_confirm()
    assert dialog.result is True # type: ignore
    dialog.destroy()


def test_restore_parent_grab():
    """Verify _restore_parent_grab handles previous grab widget, None, and exceptions."""
    # 1. previous is None or empty string -> no-op
    _restore_parent_grab(MagicMock(), None)
    _restore_parent_grab(MagicMock(), "")

    # 2. previous has grab_set -> called successfully
    prev_mock = MagicMock()
    parent_mock = MagicMock()
    _restore_parent_grab(parent_mock, prev_mock)
    prev_mock.grab_set.assert_called_once()
    parent_mock.grab_set.assert_not_called()

    # 3. previous.grab_set raises -> falls back to parent.grab_set
    prev_fail = MagicMock()
    prev_fail.grab_set.side_effect = RuntimeError("Grab failed")
    parent_fallback = MagicMock()
    _restore_parent_grab(parent_fallback, prev_fail)
    parent_fallback.grab_set.assert_called_once()

    # 4. parent.grab_set also raises -> caught safely without error
    parent_fail = MagicMock()
    parent_fail.grab_set.side_effect = RuntimeError("Parent grab failed")
    _restore_parent_grab(parent_fail, prev_fail)


def test_ask_confirmation_confirmed(monkeypatch, app_root):
    """Verify ask_confirmation returns True when user confirms."""
    def fake_wait_window(win):
        win.result = True

    monkeypatch.setattr(app_root, "wait_window", fake_wait_window)
    confirmed = ask_confirmation(app_root, "Fall wirklich löschen?", danger=True)
    assert confirmed is True


def test_ask_confirmation_cancelled(monkeypatch, app_root):
    """Verify ask_confirmation returns False when user cancels or closes."""
    def fake_wait_window(win):
        win.result = False

    monkeypatch.setattr(app_root, "wait_window", fake_wait_window)
    confirmed = ask_confirmation(app_root, "Fall wirklich löschen?", danger=True)
    assert confirmed is False


def test_ask_confirmation_wait_window_exception(monkeypatch, app_root):
    """Verify headless exception during wait_window is caught safely."""
    def failing_wait_window(win):
        raise RuntimeError("No event loop")

    monkeypatch.setattr(app_root, "wait_window", failing_wait_window)
    result = ask_confirmation(app_root, "Test headless")
    assert result is False


def test_show_notice(monkeypatch, app_root):
    """Verify show_notice instantiates ConfirmDialog with info defaults and runs."""
    called = []

    def fake_wait_window(win):
        called.append(win.result)

    monkeypatch.setattr(app_root, "wait_window", fake_wait_window)
    show_notice(app_root, "Dieser Vorgang ist abgeschlossen.", title="Hinweis")
    assert len(called) == 1
