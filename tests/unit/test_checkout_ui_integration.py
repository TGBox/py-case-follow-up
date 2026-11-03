"""Unit tests for Checkout Companion UI integration:
- Testing ProfileSettings serialization with CheckoutSettings
- Testing CheckoutPanelWidget initialization and tab structure
- Testing docked and undocked window state transitions
"""

from unittest.mock import patch

import customtkinter as ctk


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


def test_checkout_panel_settings_button_opens_settings_only_when_wired(root):
    from datetime import date
    profile = UserProfile()
    profile.checkout_settings.last_tasks_date = date.today().isoformat()
    opened = []

    with patch.object(CheckoutPanelWidget, "refresh_transit_data"), \
         patch.object(CheckoutPanelWidget, "refresh_weather_data"), \
         patch.object(CheckoutPanelWidget, "_schedule_next_transit_refresh"), \
         patch("ui.widgets.checkout_panel.get_icon", return_value=None):
        wired = CheckoutPanelWidget(
            master=root,
            profile=profile,
            on_dock_toggle=lambda: None,
            on_close=lambda: None,
            on_open_settings=lambda: opened.append(True),
        )
        plain = CheckoutPanelWidget(
            master=root,
            profile=profile,
            on_dock_toggle=lambda: None,
            on_close=lambda: None,
        )
        try:
            wired.settings_btn.invoke()
            assert opened == [True]
            assert not hasattr(plain, "settings_btn")
        finally:
            wired.destroy()
            plain.destroy()


def test_remember_visibility_round_trips_through_profile():
    profile = UserProfile()
    assert (profile.checkout_settings.remember_visibility, profile.checkout_settings.was_open) == (False, False)
    assert profile.checkout_settings.always_show is False
    profile.checkout_settings.remember_visibility = True
    profile.checkout_settings.was_open = True
    profile.checkout_settings.always_show = True
    restored = UserProfile.from_dict(profile.to_dict())
    assert (restored.checkout_settings.remember_visibility, restored.checkout_settings.was_open) == (True, True)
    assert restored.checkout_settings.always_show is True


def test_app_reopens_panel_on_start_only_when_remembered_and_open():
    from types import SimpleNamespace

    from ui.app import SupportCockpitApp

    def fake_app(remember: bool, was_open: bool, always: bool = False):
        profile = UserProfile()
        profile.checkout_settings.always_show = always
        profile.checkout_settings.remember_visibility = remember
        profile.checkout_settings.was_open = was_open
        app = SimpleNamespace(profile=profile, shown=[], persisted=[])
        app.show_checkout_panel = lambda: app.shown.append(True)
        app._persist_profile_settings = lambda: app.persisted.append(True)
        return app

    for remember, was_open, always, expected in [
        (True, True, False, [True]),
        (True, False, False, []),
        (False, True, False, []),
        (False, False, True, [True]),  # always-show opens regardless of the last state
    ]:
        app = fake_app(remember, was_open, always)
        SupportCockpitApp._restore_checkout_panel(app)  # type: ignore[arg-type]
        assert app.shown == expected

    # Opening/closing records the state and saves it only when remembering is on
    app = fake_app(True, False)
    SupportCockpitApp._remember_checkout_visibility(app, True)  # type: ignore[arg-type]
    SupportCockpitApp._remember_checkout_visibility(app, True)  # type: ignore[arg-type]  # unchanged: no save
    assert app.profile.checkout_settings.was_open is True and len(app.persisted) == 1
    app = fake_app(False, True)
    SupportCockpitApp._remember_checkout_visibility(app, False)  # type: ignore[arg-type]
    assert app.profile.checkout_settings.was_open is False and app.persisted == []


def test_always_shown_panel_cannot_be_closed_and_floating_close_docks_it():
    from types import SimpleNamespace

    from ui.app import SupportCockpitApp

    profile = UserProfile()
    profile.checkout_settings.always_show = True
    profile.checkout_settings.is_docked = False
    app = SimpleNamespace(profile=profile, _is_checkout_visible=True, docked=[], remembered=[])
    app.dock_checkout_panel = lambda: app.docked.append(True)
    app._remember_checkout_visibility = lambda is_open: app.remembered.append(is_open)

    SupportCockpitApp.hide_checkout_panel(app)  # type: ignore[arg-type]
    assert app._is_checkout_visible
    assert app.docked == [True]
    assert app.remembered == []

    profile.checkout_settings.is_docked = True
    SupportCockpitApp.hide_checkout_panel(app)  # type: ignore[arg-type]
    assert app._is_checkout_visible
    assert app.docked == [True]


def test_apply_checkout_settings_rebinds_panel_and_opens_always_shown_panel():
    from types import SimpleNamespace

    from ui.app import SupportCockpitApp

    profile = UserProfile()
    profile.checkout_settings.always_show = True
    calls = []
    panel = SimpleNamespace(
        winfo_exists=lambda: True,
        rebind_profile=lambda p: calls.append(("rebind", p)),
        set_closable=lambda c: calls.append(("closable", c)),
    )
    app = SimpleNamespace(profile=profile, checkout_panel=panel, _is_checkout_visible=False)
    app.show_checkout_panel = lambda: calls.append(("show", None))

    SupportCockpitApp.apply_checkout_settings(app)  # type: ignore[arg-type]
    assert calls == [("rebind", profile), ("closable", False), ("show", None)]


def test_panel_close_button_toggles_and_rebind_refreshes_on_new_stop(root):
    from datetime import date
    profile = UserProfile()
    profile.checkout_settings.last_tasks_date = date.today().isoformat()

    with patch.object(CheckoutPanelWidget, "refresh_transit_data") as refresh, \
         patch.object(CheckoutPanelWidget, "refresh_weather_data"), \
         patch.object(CheckoutPanelWidget, "_schedule_next_transit_refresh"), \
         patch("ui.widgets.checkout_panel.get_icon", return_value=None):
        panel = CheckoutPanelWidget(master=root, profile=profile, on_dock_toggle=lambda: None, on_close=lambda: None)
        try:
            assert panel.close_btn.winfo_manager() == "pack"
            panel.set_closable(False)
            assert not panel.close_btn.winfo_manager()
            panel.set_closable(True)
            assert panel.close_btn.winfo_manager() == "pack"

            refresh.reset_mock()
            same = UserProfile.from_dict(profile.to_dict())
            panel.rebind_profile(same)
            assert panel.settings is same.checkout_settings and not refresh.called

            moved = UserProfile.from_dict(profile.to_dict())
            moved.checkout_settings.stops = [{"name": "Edisonallee", "place": "Neu-Ulm"}]
            panel.rebind_profile(moved)
            refresh.assert_called_once_with(force=True)
        finally:
            panel.destroy()


def test_no_departure_is_chosen_or_announced_without_a_double_click(root):
    from datetime import date, datetime, timedelta

    from services.ding_transit_service import TransitDeparture

    profile = UserProfile()
    profile.checkout_settings.last_tasks_date = date.today().isoformat()
    profile.checkout_settings.alarm_enabled = True
    soon = datetime.now() + timedelta(minutes=2)  # well inside the lead time: would be "due"
    dep = TransitDeparture("1", "Edisonallee", "5", "Ulm Hbf", "Bus", soon.strftime("%H:%M"), soon.strftime("%H:%M"), 0, "", 2, soon)

    with patch.object(CheckoutPanelWidget, "refresh_transit_data"), \
         patch.object(CheckoutPanelWidget, "refresh_weather_data"), \
         patch.object(CheckoutPanelWidget, "_schedule_next_transit_refresh"), \
         patch("ui.widgets.checkout_panel.get_icon", return_value=None), \
         patch("ui.widgets.toast_notification.ToastNotification") as toast:
        panel = CheckoutPanelWidget(master=root, profile=profile, on_dock_toggle=lambda: None, on_close=lambda: None)
        try:
            panel._on_transit_data_loaded([dep])
            assert panel._selected_departure is None
            assert not toast.called
            # Hint is shown instead of the (empty) selection card
            assert panel.transit_hint_lbl.winfo_manager() == "pack"
            assert not panel.selected_transit_card.winfo_manager()

            panel._on_departure_double_clicked(dep)
            assert toast.called
            assert panel.selected_transit_card.winfo_manager() == "pack"
            assert not panel.transit_hint_lbl.winfo_manager()

            panel._clear_selected_departure()
            assert panel.transit_hint_lbl.winfo_manager() == "pack"
            assert not panel.selected_transit_card.winfo_manager()
        finally:
            panel.destroy()


def test_transit_tab_puts_the_departure_list_right_below_the_header(root):
    from datetime import date

    profile = UserProfile()
    profile.checkout_settings.last_tasks_date = date.today().isoformat()
    with patch.object(CheckoutPanelWidget, "refresh_transit_data"), \
         patch.object(CheckoutPanelWidget, "refresh_weather_data"), \
         patch.object(CheckoutPanelWidget, "_schedule_next_transit_refresh"), \
         patch("ui.widgets.checkout_panel.get_icon", return_value=None):
        panel = CheckoutPanelWidget(master=root, profile=profile, on_dock_toggle=lambda: None, on_close=lambda: None)
        try:
            packed = [w for w in panel.tab_transit.pack_slaves()]
            # header card, hint, list: no empty placeholder frame in between
            assert packed[0] is panel.transit_card
            assert packed[1] is panel.transit_hint_lbl
            assert len(packed) == 3
            assert panel.transit_status_lbl.master.master is panel.transit_card
            assert panel.transit_refresh_btn.master.master is panel.transit_card
        finally:
            panel.destroy()


def _build_panel(root, profile, floating: bool):
    from datetime import date

    profile.checkout_settings.last_tasks_date = date.today().isoformat()
    return CheckoutPanelWidget(
        master=root, profile=profile, on_dock_toggle=lambda: None, on_close=lambda: None, is_floating=floating
    )


def test_docked_panel_shows_everything_in_one_column_and_floating_keeps_tabs(root):
    with patch.object(CheckoutPanelWidget, "refresh_transit_data"), \
         patch.object(CheckoutPanelWidget, "refresh_weather_data"), \
         patch.object(CheckoutPanelWidget, "_schedule_next_transit_refresh"), \
         patch("ui.widgets.checkout_panel.get_icon", return_value=None):
        docked = _build_panel(root, UserProfile(), floating=False)
        floating = _build_panel(root, UserProfile(), floating=True)
        try:
            assert docked.tabview is None
            assert list(docked._sections) == ["transit", "tasks", "note", "tomorrow"]
            assert all(s.expanded for s in docked._sections.values())
            # Weather and working time sit in the summary strip instead of own tabs
            assert docked.weather_temp_lbl.winfo_manager() == "pack"
            assert "Feierabend" in docked.worktime_end_lbl.cget("text")
            # Lists are plain frames: the column scrolls as a whole
            assert not isinstance(docked.transit_scroll, ctk.CTkScrollableFrame)

            assert floating.tabview is not None
            assert isinstance(floating.transit_scroll, ctk.CTkScrollableFrame)
        finally:
            docked.destroy()
            floating.destroy()


def test_folded_sections_are_remembered_and_note_title_shows_the_badge(root):
    profile = UserProfile()
    profile.checkout_settings.collapsed_sections = ["tomorrow"]
    saved = []
    with patch.object(CheckoutPanelWidget, "refresh_transit_data"), \
         patch.object(CheckoutPanelWidget, "refresh_weather_data"), \
         patch.object(CheckoutPanelWidget, "_schedule_next_transit_refresh"), \
         patch("ui.widgets.checkout_panel.get_icon", return_value=None):
        panel = _build_panel(root, profile, floating=False)
        panel.on_persist_callback = lambda: saved.append(True)
        try:
            assert not panel._sections["tomorrow"].expanded
            panel._sections["tasks"].toggle()
            assert profile.checkout_settings.collapsed_sections == ["tomorrow", "tasks"]
            panel._sections["tomorrow"].toggle()
            assert profile.checkout_settings.collapsed_sections == ["tasks"]
            assert len(saved) == 2

            panel._update_note_tab_badge(True)
            assert "●" in panel._sections["note"].header_btn.cget("text")
        finally:
            panel.destroy()

    restored = UserProfile.from_dict(profile.to_dict())
    assert restored.checkout_settings.collapsed_sections == ["tasks"]


def test_docked_column_shows_fewer_departures_than_the_tab(root):
    from datetime import datetime, timedelta

    from services.ding_transit_service import TransitDeparture

    now = datetime.now()
    deps = [
        TransitDeparture("1", "Stop", "5", f"Ziel {i}", "Bus", "", (now + timedelta(minutes=i)).strftime("%H:%M"), 0, "", i, now + timedelta(minutes=i))
        for i in range(15)
    ]
    with patch.object(CheckoutPanelWidget, "refresh_transit_data"), \
         patch.object(CheckoutPanelWidget, "refresh_weather_data"), \
         patch.object(CheckoutPanelWidget, "_schedule_next_transit_refresh"), \
         patch("ui.widgets.checkout_panel.get_icon", return_value=None):
        docked = _build_panel(root, UserProfile(), floating=False)
        floating = _build_panel(root, UserProfile(), floating=True)
        try:
            for panel in (docked, floating):
                panel._on_transit_data_loaded(deps)
            assert len(docked.transit_scroll.winfo_children()) == 6
            assert len(floating.transit_scroll.winfo_children()) == 12
        finally:
            docked.destroy()
            floating.destroy()
