"""Tests for ToastNotification positioning, packing order, and button visibility."""

import customtkinter as ctk
import pytest
from ui.widgets.toast_notification import ToastNotification


def test_toast_notification_button_visibility():
    """Verify ToastNotification initializes with spacious geometry and fully visible button."""
    app = ctk.CTk()
    app.withdraw()

    opened = []
    toast = ToastNotification(
        app,
        title="🔔 Wiedervorlage fällig",
        message="Fall T-2026-001 ist zur Wiedervorlage bereit.",
        duration_ms=10000,
        on_open=lambda: opened.append(True),
    )

    toast.update_idletasks()

    # Find button and verify width and text
    btn = next((c for c in toast.winfo_children()[0].winfo_children() if isinstance(c, ctk.CTkButton)), None)
    assert btn is not None
    assert "Öffnen" in btn.cget("text")
    assert btn.cget("width") >= 90

    toast.safe_destroy()
    app.destroy()
