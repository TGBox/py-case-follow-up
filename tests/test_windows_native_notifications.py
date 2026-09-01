"""Tests for Windows native system notifications via TrayService and ToastNotification dispatch."""

import sys
import customtkinter as ctk
import pytest
from services.tray_service import TrayService
from ui.widgets.toast_notification import ToastNotification


class DummyIcon:
    """Mock pystray Icon to verify notification calls."""

    def __init__(self):
        self.last_notification = None

    def notify(self, message: str, title: str | None = None):
        self.last_notification = {"title": title, "message": message}


class DummyAppWithTray(ctk.CTk):
    """Dummy main app window with mock tray service."""

    def __init__(self):
        super().__init__()
        self.tray_service = TrayService()
        self.tray_service._icon = DummyIcon()
        self.brought_to_foreground = False
        self._pending_notification_callback = None

    def bring_to_foreground(self):
        self.brought_to_foreground = True

    def _on_restore_from_tray(self):
        self.bring_to_foreground()
        if hasattr(self, "_pending_notification_callback") and self._pending_notification_callback:
            cb = self._pending_notification_callback
            self._pending_notification_callback = None
            cb()


def test_tray_service_notify_method():
    """Verify TrayService.notify delegates to underlying icon.notify."""
    service = TrayService()
    dummy_icon = DummyIcon()
    service._icon = dummy_icon

    success = service.notify(title="Test Titel", message="Test Inhalt")

    assert success is True
    assert dummy_icon.last_notification == {"title": "Test Titel", "message": "Test Inhalt"}


def test_toast_notification_dispatches_native_when_win(monkeypatch):
    """Verify ToastNotification invokes native notification on Windows when tray service is present."""
    monkeypatch.setattr(sys, "platform", "win32")

    app = DummyAppWithTray()
    app.withdraw()

    opened = []
    toast = ToastNotification(
        app,
        title="🔔 Wiedervorlage fällig",
        message="Fall T-2026-001 ist bereit.",
        on_open=lambda: opened.append(True),
    )

    # Check mock icon received native notification call
    icon = app.tray_service._icon
    assert icon.last_notification == {
        "title": "🔔 Wiedervorlage fällig",
        "message": "Fall T-2026-001 ist bereit.",
    }
    assert app._pending_notification_callback is not None

    # Simulate restoring from tray notification click
    app._on_restore_from_tray()

    assert app.brought_to_foreground is True
    assert len(opened) == 1
    assert app._pending_notification_callback is None

    app.destroy()


def test_toast_notification_fallback_without_tray():
    """Verify ToastNotification falls back to CTk window overlay when tray service is inactive."""
    app = ctk.CTk()
    app.withdraw()

    toast = ToastNotification(
        app,
        title="Status",
        message="In-App Nachricht",
    )
    toast.update_idletasks()

    assert toast.winfo_exists()
    toast.safe_destroy()
    app.destroy()
