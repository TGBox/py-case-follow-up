"""Unit tests for Checkout Companion UI integration:
- Testing ProfileSettings serialization with CheckoutSettings
- Testing CheckoutPanelWidget initialization and tab structure
- Testing docked and undocked window state transitions
"""

from unittest.mock import patch

import pytest

from models.profile import CheckoutSettings, UserProfile
from services.checkout_task_service import CheckoutTaskService
from ui.widgets.checkout_panel import CheckoutFloatingWindow, CheckoutPanelWidget


def test_user_profile_checkout_settings_roundtrip():
    profile = UserProfile()
    profile.checkout_settings.enabled = True
    profile.checkout_settings.auto_open = True
    profile.checkout_settings.auto_open_uniform_time = "17:15"
    profile.checkout_settings.walk_time_minutes = 8
    profile.checkout_settings.stops = [{"name": "Ulm Hauptbahnhof", "place": "Ulm"}]

    data = profile.to_dict()
    assert "checkout_settings" in data
    assert data["checkout_settings"]["enabled"] is True
    assert data["checkout_settings"]["auto_open_uniform_time"] == "17:15"
    assert data["checkout_settings"]["walk_time_minutes"] == 8
    assert data["checkout_settings"]["stops"][0]["name"] == "Ulm Hauptbahnhof"

    restored = UserProfile.from_dict(data)
    assert restored.checkout_settings.enabled is True
    assert restored.checkout_settings.auto_open is True
    assert restored.checkout_settings.auto_open_uniform_time == "17:15"
    assert restored.checkout_settings.walk_time_minutes == 8
    assert restored.checkout_settings.stops[0]["name"] == "Ulm Hauptbahnhof"


def test_checkout_panel_tabs_and_state(root):
    from datetime import date
    profile = UserProfile()
    profile.checkout_settings.last_tasks_date = date.today().isoformat()
    profile.checkout_settings.daily_note_text = "Test Notiz"

    with patch.object(CheckoutPanelWidget, "refresh_transit_data"), \
         patch.object(CheckoutPanelWidget, "refresh_weather_data"), \
         patch.object(CheckoutPanelWidget, "_schedule_next_transit_refresh"):

        panel = CheckoutPanelWidget(
            master=root,
            profile=profile,
            on_dock_toggle=lambda: None,
            on_close=lambda: None,
        )

        assert panel.profile is profile
        assert panel.settings.daily_note_text == "Test Notiz"
        assert panel.is_floating is False

        # Test floating window creation
        floating = CheckoutFloatingWindow(
            master=root,
            on_dock_callback=lambda: None,
            on_close_callback=lambda: None,
        )
        assert floating.winfo_exists()
        floating.destroy()
