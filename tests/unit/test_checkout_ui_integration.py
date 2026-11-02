"""Unit tests for Checkout Companion UI integration:
- Testing ProfileSettings serialization with CheckoutSettings
- Testing CheckoutPanelWidget initialization and tab structure
- Testing docked and undocked window state transitions
"""

from unittest.mock import patch


from models.profile import UserProfile
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


def test_checkout_panel_transit_selection(root):
    from datetime import datetime, timedelta
    from services.ding_transit_service import TransitDeparture

    profile = UserProfile()
    profile.checkout_settings.alarm_enabled = True
    profile.checkout_settings.walk_time_minutes = 5
    profile.checkout_settings.logout_time_minutes = 3
    profile.checkout_settings.pack_time_minutes = 2
    profile.checkout_settings.buffer_time_minutes = 0

    with patch.object(CheckoutPanelWidget, "refresh_transit_data"), \
         patch.object(CheckoutPanelWidget, "refresh_weather_data"), \
         patch.object(CheckoutPanelWidget, "_schedule_next_transit_refresh"):

        panel = CheckoutPanelWidget(
            master=root,
            profile=profile,
            on_dock_toggle=lambda: None,
            on_close=lambda: None,
        )

        dep_dt = datetime.now() + timedelta(minutes=10)
        dep = TransitDeparture(
            stop_id="9001350",
            stop_name="Ulm Ehinger Tor",
            line="1",
            destination="Söflingen",
            mot_type="Straßenbahn",
            planned_time_str=dep_dt.strftime("%H:%M"),
            real_time_str=dep_dt.strftime("%H:%M"),
            delay_minutes=0,
            platform="Bstg. A",
            countdown_minutes=10,
            raw_datetime=dep_dt,
        )

        panel._transit_departures = [dep]
        panel._render_departures()

        assert panel._selected_dep_key is None
        assert panel._selected_departure is None

        # Double click to select
        panel._on_departure_double_clicked(dep)
        expected_key = f"{dep.line}_{dep.planned_time_str}_{dep.destination}"
        assert panel._selected_dep_key == expected_key
        assert panel._selected_departure is dep
        assert "Söflingen" in panel.selected_transit_desc_lbl.cget("text")

        # Double click again toggles/deselects
        panel._on_departure_double_clicked(dep)
        assert panel._selected_dep_key is None
        assert panel._selected_departure is None

        # Select again and test manual clear
        panel._on_departure_double_clicked(dep)
        assert panel._selected_dep_key == expected_key
        panel._clear_selected_departure()
        assert panel._selected_dep_key is None

        # Re-select for staged alarm notification test
        panel._on_departure_double_clicked(dep)
        with patch("ui.widgets.toast_notification.ToastNotification") as mock_toast:
            panel._notified_stages.clear()
            panel._check_commute_alarms()
            assert "pack" in panel._notified_stages
            assert mock_toast.called

            # Check that calling again does not fire duplicate toast for the same stage
            call_count = mock_toast.call_count
            panel._check_commute_alarms()
            assert mock_toast.call_count == call_count
