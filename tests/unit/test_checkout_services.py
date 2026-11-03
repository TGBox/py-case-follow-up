"""Unit tests for Checkout & Departure services:
- DingTransitService (parsing, lead time calculation, alarm urgency)
- WeatherService (parsing, umbrella recommendations)
- CheckoutTaskService (midnight reset, tasks CRUD, toggle, date filtering)
"""

from datetime import datetime


from models.profile import CheckoutSettings
from services.checkout_task_service import CheckoutTaskService
from services.ding_transit_service import DingTransitService, TransitDeparture
from services.weather_service import WeatherService


def test_ding_transit_parse_response():
    sample_data = {
        "departureList": [
            {
                "stopID": "9001350",
                "stopName": "Ulm Ehinger Tor",
                "platformName": "Bstg. D",
                "countdown": "3",
                "dateTime": {"year": 2026, "month": 11, "day": 2, "hour": 17, "minute": 15},
                "realDateTime": {"year": 2026, "month": 11, "day": 2, "hour": 17, "minute": 17},
                "servingLine": {
                    "number": "2",
                    "direction": "Kuhberg",
                    "name": "Straßenbahn",
                    "delay": 2,
                },
            }
        ]
    }
    departures = DingTransitService._parse_efa_response(sample_data)
    assert len(departures) == 1
    dep = departures[0]
    assert dep.line == "2"
    assert dep.destination == "Kuhberg"
    assert dep.planned_time_str == "17:15"
    assert dep.real_time_str == "17:17"
    assert dep.delay_minutes == 2
    assert dep.platform == "Bstg. D"
    assert dep.countdown_minutes == 3


def test_ding_transit_calculate_leave_info():
    now = datetime(2026, 11, 2, 17, 0, 0)
    # Departure in 20 minutes (17:20)
    dep_dt = datetime(2026, 11, 2, 17, 20, 0)
    dep = TransitDeparture(
        stop_id="1",
        stop_name="Ulm Ehinger Tor",
        line="2",
        destination="Kuhberg",
        mot_type="Straßenbahn",
        planned_time_str="17:20",
        real_time_str="17:20",
        delay_minutes=0,
        platform="Bstg. D",
        countdown_minutes=20,
        raw_datetime=dep_dt,
    )

    # Lead time: walk 5 + logout 3 + pack 4 + buffer 2 = 14 min
    # Leave time should be 17:20 - 14m = 17:06
    info = DingTransitService.calculate_leave_info(
        departure=dep,
        walk_min=5,
        logout_min=3,
        pack_min=4,
        buffer_min=2,
        now=now,
    )
    assert info["total_lead_minutes"] == 14
    assert info["leave_time_str"] == "17:06"
    assert info["minutes_until_leave"] == 6
    assert info["pack_time_str"] == "17:06"
    assert info["logout_time_str"] == "17:10"
    assert info["walk_time_str"] == "17:13"
    assert info["dep_time_str"] == "17:20"
    assert info["minutes_until_pack"] == 6
    assert info["minutes_until_logout"] == 10
    assert info["minutes_until_walk"] == 13
    assert info["status"] == "warn"  # 6 <= 10 min threshold -> warn
    assert not info["is_alarm_due"]

    # Now simulate time earlier (16:50 -> 16 min until leave time -> ok)
    now_early = datetime(2026, 11, 2, 16, 50, 0)
    info_early = DingTransitService.calculate_leave_info(
        departure=dep,
        walk_min=5,
        logout_min=3,
        pack_min=4,
        buffer_min=2,
        now=now_early,
    )
    assert info_early["minutes_until_leave"] == 16
    assert info_early["status"] == "ok"
    assert not info_early["is_alarm_due"]

    # Now simulate time being 17:05 (1 min until leave time -> urgent threshold)
    now_urgent = datetime(2026, 11, 2, 17, 5, 0)
    info_urgent = DingTransitService.calculate_leave_info(
        departure=dep,
        walk_min=5,
        logout_min=3,
        pack_min=4,
        buffer_min=2,
        now=now_urgent,
    )
    assert info_urgent["minutes_until_leave"] == 1
    assert info_urgent["status"] == "urgent"
    assert not info_urgent["is_alarm_due"]

    # Now simulate time being 17:06 (time to leave!)
    now_leave = datetime(2026, 11, 2, 17, 6, 0)
    info_leave = DingTransitService.calculate_leave_info(
        departure=dep,
        walk_min=5,
        logout_min=3,
        pack_min=4,
        buffer_min=2,
        now=now_leave,
    )
    assert info_leave["minutes_until_leave"] == 0
    assert info_leave["status"] == "urgent"
    assert info_leave["is_alarm_due"]


def test_weather_service_parse_response():
    data = {
        "current": {"temperature_2m": 18.4, "weather_code": 61},
        "hourly": {
            "precipitation_probability": [10, 10, 20, 45, 60, 50, 20],
        },
    }
    weather = WeatherService._parse_weather_response(data)
    assert weather.temperature == 18.4
    assert weather.condition_code == 61
    assert "Regen" in weather.condition_text
    assert weather.umbrella_recommended


def test_checkout_task_service_crud_and_toggle():
    settings = CheckoutSettings()
    assert len(settings.recurring_tasks) == 3

    # Add dated task
    task = CheckoutTaskService.add_dated_task(settings, "Brief zur Post bringen", "2026-11-02")
    assert task["text"] == "Brief zur Post bringen"
    assert task["date"] == "2026-11-02"
    assert not task["done"]

    # Toggle task
    toggled = CheckoutTaskService.toggle_task(settings, task["id"])
    assert toggled
    assert task["done"]

    # Add recurring task
    rec = CheckoutTaskService.add_recurring_task(settings, "Kaffeemaschine ausschalten")
    assert rec["text"] == "Kaffeemaschine ausschalten"
    assert not rec["done"]

    # Filter by date
    recs, dated = CheckoutTaskService.get_tasks_for_date(settings, "2026-11-02")
    assert len(recs) == 4
    assert len(dated) == 1
    assert dated[0]["id"] == task["id"]

    # Delete task
    deleted = CheckoutTaskService.delete_task(settings, task["id"])
    assert deleted
    _, dated_after = CheckoutTaskService.get_tasks_for_date(settings, "2026-11-02")
    assert len(dated_after) == 0


def test_checkout_task_service_midnight_reset():
    settings = CheckoutSettings(
        last_tasks_date="2026-11-01",
        daily_note_text="Gestrige Notiz",
        daily_note_keep_overnight=False,
    )
    # Check off recurring task
    settings.recurring_tasks[0]["done"] = True

    # Rollover to 2026-11-02
    changed = CheckoutTaskService.check_and_perform_midnight_reset(settings, "2026-11-02")
    assert changed
    assert settings.last_tasks_date == "2026-11-02"
    assert not settings.recurring_tasks[0]["done"]
    assert settings.daily_note_text == ""

    # Second run on same day should do nothing
    changed_again = CheckoutTaskService.check_and_perform_midnight_reset(settings, "2026-11-02")
    assert not changed_again


def test_checkout_task_service_keep_overnight():
    settings = CheckoutSettings(
        last_tasks_date="2026-11-01",
        daily_note_text="Wichtige dauerhafte Info",
        daily_note_keep_overnight=True,
    )
    changed = CheckoutTaskService.check_and_perform_midnight_reset(settings, "2026-11-02")
    assert changed
    assert settings.daily_note_text == "Wichtige dauerhafte Info"


# --- Stop search and live check -------------------------------------------

_ONE_DEPARTURE = {
    "stopName": "Neu-Ulm, Edisonallee",
    "countdown": "4",
    "dateTime": {"year": 2026, "month": 11, "day": 3, "hour": 16, "minute": 40},
    "servingLine": {"number": "5", "direction": "Ulm Hbf", "name": "Bus"},
}


def test_stop_finder_parses_list_single_point_and_rapid_json():
    as_list = {
        "points": [
            {"anyType": "stop", "name": "Neu-Ulm, Edisonallee", "object": "Edisonallee", "mainLoc": "Neu-Ulm", "ref": {"id": "9001234"}},
            {"anyType": "stop", "name": "Neu-Ulm, Edisonallee", "object": "Edisonallee", "mainLoc": "Neu-Ulm"},  # duplicate
            {"anyType": "street", "name": "Neu-Ulm, Edisonallee", "object": "Edisonallee"},  # not a stop
            {"anyType": "stop", "name": "Ulm, Ehinger Tor"},  # no object: split the full name
        ]
    }
    stops = DingTransitService._parse_stop_points(as_list)
    assert [(s.name, s.place, s.stop_id) for s in stops] == [("Edisonallee", "Neu-Ulm", "9001234"), ("Ehinger Tor", "Ulm", "")]

    single = {"points": {"point": {"anyType": "stop", "object": "Edisonallee", "ref": {"place": "Neu-Ulm"}}}}
    assert [(s.name, s.place) for s in DingTransitService._parse_stop_points(single)] == [("Edisonallee", "Neu-Ulm")]

    rapid = {"locations": [{"type": "stop", "disassembledName": "Edisonallee", "parent": {"name": "Neu-Ulm"}, "id": "de:09775"}]}
    assert [(s.name, s.place, s.stop_id) for s in DingTransitService._parse_stop_points(rapid)] == [("Edisonallee", "Neu-Ulm", "de:09775")]

    assert DingTransitService._parse_stop_points({"points": None}) == []
    assert DingTransitService._parse_stop_points(None) == []


def test_find_stops_reports_unreachable_service_as_none(monkeypatch):
    def boom(*_a, **_k):
        raise OSError("offline")

    monkeypatch.setattr(DingTransitService, "_request_json", staticmethod(boom))
    assert DingTransitService.find_stops("Edison") is None
    assert DingTransitService.find_stops("   ") == []

    monkeypatch.setattr(
        DingTransitService,
        "_request_json",
        staticmethod(lambda _e, params: {"stopFinder": {"points": [{"anyType": "stop", "object": params["name_sf"], "mainLoc": "Neu-Ulm"}]}}),
    )
    assert [s.name for s in DingTransitService.find_stops("Edisonallee") or []] == ["Edisonallee"]


def test_check_stop_distinguishes_all_outcomes(monkeypatch):
    def respond(payload):
        monkeypatch.setattr(DingTransitService, "_request_json", staticmethod(lambda *_a: payload))

    respond({"departureList": [_ONE_DEPARTURE, _ONE_DEPARTURE]})
    ok = DingTransitService.check_stop("Edisonallee", "Neu-Ulm")
    assert (ok.status, ok.departure_count, ok.resolved_name) == ("ok", 2, "Neu-Ulm, Edisonallee")

    respond({"dm": {"points": {"point": {"anyType": "stop", "name": "Neu-Ulm, Edisonallee"}}}, "departureList": None})
    quiet = DingTransitService.check_stop("Edisonallee", "Neu-Ulm")
    assert (quiet.status, quiet.resolved_name) == ("no_departures", "Edisonallee")

    respond({"dm": {"points": [
        {"anyType": "stop", "object": "Bahnhof", "mainLoc": "Ulm"},
        {"anyType": "stop", "object": "Bahnhof", "mainLoc": "Neu-Ulm"},
    ]}})
    many = DingTransitService.check_stop("Bahnhof", "")
    assert many.status == "ambiguous" and [c.place for c in many.candidates] == ["Ulm", "Neu-Ulm"]

    respond({"dm": {"points": None}})
    assert DingTransitService.check_stop("Edisnalle", "Neu-Ulm").status == "not_found"

    def boom(*_a, **_k):
        raise TimeoutError

    monkeypatch.setattr(DingTransitService, "_request_json", staticmethod(boom))
    assert DingTransitService.check_stop("Edisonallee", "Neu-Ulm").status == "error"


def test_departure_cache_is_per_stop(monkeypatch):
    calls = []

    def fake(_endpoint, params):
        calls.append(params["name_dm"])
        return {"departureList": [dict(_ONE_DEPARTURE, stopName=params["name_dm"])]}

    monkeypatch.setattr(DingTransitService, "_request_json", staticmethod(fake))
    monkeypatch.setattr(DingTransitService, "_cached_departures", [])
    monkeypatch.setattr(DingTransitService, "_last_fetch_time", None)
    monkeypatch.setattr(DingTransitService, "_cached_stop_key", None)

    assert DingTransitService.fetch_departures("Ehinger Tor", "Ulm")[0].stop_name == "Ehinger Tor"
    assert DingTransitService.fetch_departures("Ehinger Tor", "Ulm")[0].stop_name == "Ehinger Tor"  # cached
    assert DingTransitService.fetch_departures("Edisonallee", "Neu-Ulm")[0].stop_name == "Edisonallee"
    assert calls == ["Ehinger Tor", "Edisonallee"]
