"""Unit tests for Checkout & Departure services:
- DingTransitService (parsing, lead time calculation, alarm urgency)
- WeatherService (parsing, umbrella recommendations)
- CheckoutTaskService (midnight reset, tasks CRUD, toggle, date filtering)
"""

import json
from datetime import datetime, timedelta


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


def test_departure_params_with_planned_time():
    from datetime import datetime

    params = DingTransitService._departure_params("Wiley Süd", "Neu-Ulm", 15, datetime(2026, 11, 5, 16, 50))
    assert params["itdDate"] == "20261105"
    assert params["itdTime"] == "1650"
    assert params["itdDateTimeDepArr"] == "dep"
    assert "itdTime" not in DingTransitService._departure_params("Wiley Süd", "Neu-Ulm", 15)


def test_departure_cache_is_per_planned_time(monkeypatch):
    from datetime import datetime

    calls = []

    def fake(_endpoint, params):
        calls.append(params.get("itdTime"))
        return {"departureList": [dict(_ONE_DEPARTURE)]}

    monkeypatch.setattr(DingTransitService, "_request_json", staticmethod(fake))
    monkeypatch.setattr(DingTransitService, "_cached_departures", [])
    monkeypatch.setattr(DingTransitService, "_last_fetch_time", None)
    monkeypatch.setattr(DingTransitService, "_cached_stop_key", None)

    DingTransitService.fetch_departures("Ehinger Tor", "Ulm")
    DingTransitService.fetch_departures("Ehinger Tor", "Ulm", departure_time=datetime(2026, 11, 5, 17, 0))
    DingTransitService.fetch_departures("Ehinger Tor", "Ulm", departure_time=datetime(2026, 11, 5, 17, 0))  # cached
    assert calls == [None, "1700"]


def test_countdown_counts_from_now_for_a_planned_request():
    from datetime import timedelta

    # EFA counts "countdown" from the requested time; for a planned request it must come from now.
    dep_at = datetime.now().replace(second=0, microsecond=0) + timedelta(hours=4, minutes=1)
    data = {
        "departureList": [
            dict(
                _ONE_DEPARTURE,
                countdown="3",
                dateTime={"year": dep_at.year, "month": dep_at.month, "day": dep_at.day, "hour": dep_at.hour, "minute": dep_at.minute},
            )
        ]
    }
    assert DingTransitService._parse_efa_response(data)[0].countdown_minutes == 3
    assert DingTransitService._parse_efa_response(data, trust_countdown=False)[0].countdown_minutes >= 240


# --- Trips to a destination (XML_TRIP_REQUEST2) ---

def _trip_point(name, usage, date_str, time_str, rt_time=None, platform=""):
    dt = {"date": date_str, "time": time_str}
    if rt_time:
        dt.update(rtDate=date_str, rtTime=rt_time)
    return {"name": name, "usage": usage, "dateTime": dt, "platformName": platform}


def _sample_trip_response(day):
    d = day.strftime("%d.%m.%Y")
    return {
        "trips": [
            {   # one change, first bus 2 min late, leading footpath before it
                "legs": [
                    {
                        "mode": {"type": "99", "name": "Fussweg"},
                        "points": [
                            _trip_point("Ulm, Ehinger Tor", "departure", d, "16:55"),
                            _trip_point("Ulm, Ehinger Tor Bstg. D", "arrival", d, "16:57"),
                        ],
                    },
                    {
                        "mode": {"type": "5", "name": "Bus 4", "number": "4", "destination": "Kuhberg"},
                        "points": [
                            _trip_point("Ulm, Ehinger Tor", "departure", d, "16:58", "17:00", "Bstg. D"),
                            _trip_point("Ulm, Hauptbahnhof", "arrival", d, "17:03", "17:05"),
                        ],
                    },
                    {
                        "mode": {"type": "4", "name": "Straßenbahn 2", "number": "2", "destination": "Wiley"},
                        "points": {"point": [
                            _trip_point("Ulm, Hauptbahnhof", "departure", d, "17:10"),
                            _trip_point("Neu-Ulm, Wiley Süd", "arrival", d, "17:24", "17:26"),
                        ]},
                    },
                ]
            },
            {   # pure footpath: no bus, must be skipped
                "legs": [{"mode": {"type": "100", "name": "Fussweg"}, "points": [
                    _trip_point("Ulm, Ehinger Tor", "departure", d, "17:00"),
                    _trip_point("Neu-Ulm, Wiley Süd", "arrival", d, "17:40"),
                ]}]
            },
        ]
    }


def test_trip_response_parses_lines_times_changes_and_skips_footpaths():
    day = datetime.now() + timedelta(days=1)
    trips = DingTransitService._parse_trip_response(_sample_trip_response(day))
    assert len(trips) == 1
    trip = trips[0]
    assert trip.lines == ["4", "2"]
    assert trip.interchanges == 1
    # The trip starts at the origin with the footpath; the alarm counts back from there.
    assert trip.departure.real_time_str == "16:55"
    assert trip.departure.line == "4"
    assert trip.departure.destination == "Kuhberg"
    assert trip.arrival_stop == "Neu-Ulm, Wiley Süd"
    assert (trip.arrival_planned_str, trip.arrival_real_str, trip.arrival_delay_minutes) == ("17:24", "17:26", 2)
    assert trip.duration_minutes == 31


def test_trip_response_handles_single_trip_dict_and_departure_monitor_times():
    day = datetime.now() + timedelta(days=1)
    stamp = {"year": day.year, "month": day.month, "day": day.day}
    data = {"trips": {"trip": {"legs": {"leg": {
        "mode": {"type": "5", "number": "5", "destination": "Wiblingen"},
        "points": [
            {"name": "Ehinger Tor", "usage": "departure", "dateTime": dict(stamp, hour=18, minute=1)},
            {"name": "Wiblingen", "usage": "arrival", "dateTime": dict(stamp, hour=18, minute=20)},
        ],
    }}}}}
    trips = DingTransitService._parse_trip_response(data)
    assert [(t.departure.real_time_str, t.arrival_real_str, t.interchanges) for t in trips] == [("18:01", "18:20", 0)]


def test_trip_response_without_trips_is_empty():
    # e.g. an ambiguous or unknown destination: EFA answers without "trips"
    assert DingTransitService._parse_trip_response({"destination": {"points": []}}) == []
    assert DingTransitService._parse_trip_response({"trips": None}) == []


def test_trip_params_name_origin_destination_and_time():
    params = DingTransitService._trip_params("Ehinger Tor", "Ulm", "Wiley Süd", "Neu-Ulm", 6, datetime(2026, 11, 5, 16, 50))
    assert (params["name_origin"], params["place_origin"]) == ("Ehinger Tor", "Ulm")
    assert (params["name_destination"], params["place_destination"]) == ("Wiley Süd", "Neu-Ulm")
    assert (params["itdDate"], params["itdTime"], params["itdTripDateTimeDepArr"]) == ("20261105", "1650", "dep")
    assert params["calcNumberOfTrips"] == "6"


def test_trip_cache_is_per_destination_and_errors_keep_last_result(monkeypatch):
    day = datetime.now() + timedelta(days=1)
    calls = []

    def fake(_endpoint, params):
        calls.append(params["name_destination"])
        if params["name_destination"] == "kaputt":
            raise TimeoutError
        return _sample_trip_response(day)

    monkeypatch.setattr(DingTransitService, "_request_json", staticmethod(fake))
    monkeypatch.setattr(DingTransitService, "_cached_trips", [])
    monkeypatch.setattr(DingTransitService, "_last_trip_fetch_time", None)
    monkeypatch.setattr(DingTransitService, "_cached_trip_key", None)

    assert len(DingTransitService.fetch_trips("Ehinger Tor", "Ulm", "Wiley Süd", "Neu-Ulm")) == 1
    assert len(DingTransitService.fetch_trips("Ehinger Tor", "Ulm", "Wiley Süd", "Neu-Ulm")) == 1  # cached
    DingTransitService.fetch_trips("Ehinger Tor", "Ulm", "Hauptbahnhof", "Ulm")
    assert calls == ["Wiley Süd", "Hauptbahnhof"]
    # a different destination never reuses another destination's trips
    assert DingTransitService.fetch_trips("Ehinger Tor", "Ulm", "kaputt") == []


def test_trips_that_already_left_are_dropped(monkeypatch):
    # The sample trip leaves at 16:55 yesterday, so it is gone for sure.
    yesterday = datetime.now() - timedelta(days=1)
    monkeypatch.setattr(DingTransitService, "_request_json", staticmethod(lambda *_a: _sample_trip_response(yesterday)))
    monkeypatch.setattr(DingTransitService, "_cached_trip_key", None)
    assert DingTransitService.fetch_trips("Ehinger Tor", "Ulm", "Wiley Süd", force_refresh=True) == []


def test_destination_defaults_overrides_for_today_and_round_trips():
    cs = CheckoutSettings()
    assert cs.effective_destination() == {"name": "", "place": ""}
    cs.destination = {"name": "Wiley Süd", "place": "Neu-Ulm"}
    assert cs.effective_destination()["name"] == "Wiley Süd"

    cs.destination_today = {"name": "", "place": ""}
    cs.destination_today_date = "2026-11-05"
    assert cs.effective_destination(today="2026-11-05")["name"] == ""  # no destination today
    assert cs.effective_destination(today="2026-11-06")["name"] == "Wiley Süd"  # next day: default again

    restored = CheckoutSettings.from_dict(cs.to_dict())
    assert restored.destination == {"name": "Wiley Süd", "place": "Neu-Ulm"}
    assert restored.destination_today_date == "2026-11-05"
    # old profiles without the fields
    assert CheckoutSettings.from_dict({}).destination == {"name": "", "place": ""}


def test_same_first_bus_with_two_onward_connections_is_listed_once(monkeypatch):
    day = datetime.now() + timedelta(days=1)
    data = _sample_trip_response(day)
    slower = json.loads(json.dumps(data["trips"][0]))
    slower["legs"][-1]["points"]["point"][-1]["dateTime"]["rtTime"] = "17:40"
    data["trips"].insert(0, slower)
    monkeypatch.setattr(DingTransitService, "_request_json", staticmethod(lambda *_a: data))
    monkeypatch.setattr(DingTransitService, "_cached_trip_key", None)
    trips = DingTransitService.fetch_trips("Ehinger Tor", "Ulm", "Wiley Süd", force_refresh=True)
    assert [t.arrival_real_str for t in trips] == ["17:26"]
