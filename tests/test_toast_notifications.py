"""Tests for ToastNotification positioning, packing order, and button visibility."""

import customtkinter as ctk
from ui.widgets.toast_notification import ToastNotification


class CardOnlyApp(ctk.CTk):
    """Parent that asks for the in-app card instead of the native Windows toast.

    On Windows the toast now goes to the OS and no card is built at all - it used
    to be built and thrown away, which cost two frames, two buttons and four
    labels per notification. This test is about the card's layout, so it turns
    OS popups off through the same setting the user has in the profile dialog.
    """

    def __init__(self):
        super().__init__()
        self.profile = type(
            "P", (), {"reminder_settings": type("R", (), {"os_popup_enabled": False})()}
        )()


def test_toast_notification_button_visibility():
    """Verify ToastNotification initializes with spacious geometry and fully visible button."""
    app = CardOnlyApp()
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
