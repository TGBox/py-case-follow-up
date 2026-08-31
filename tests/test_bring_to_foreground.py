"""Tests for bring_to_foreground behavior on App and ToastNotification."""

import customtkinter as ctk
import pytest
from ui.widgets.toast_notification import ToastNotification


class DummyApp(ctk.CTk):
    """Dummy main app subclass to test bring_to_foreground functionality."""

    def __init__(self):
        super().__init__()
        self.brought_to_foreground = False

    def bring_to_foreground(self):
        self.brought_to_foreground = True


def test_toast_notification_calls_bring_to_foreground():
    """Verify clicking open on ToastNotification triggers bring_to_foreground on top window."""
    app = DummyApp()
    app.withdraw()

    opened = []
    toast = ToastNotification(
        app,
        title="🔔 Wiedervorlage fällig",
        message="Fall T-2026-001 ist zur Wiedervorlage bereit.",
        duration_ms=10000,
        on_open=lambda: opened.append(True),
    )

    toast.handle_open()

    assert app.brought_to_foreground is True
    assert len(opened) == 1

    app.destroy()
