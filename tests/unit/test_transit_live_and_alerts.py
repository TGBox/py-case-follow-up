"""SWU live correction of EFA times and traffic notices (EFA, ding.eu, SWU) for the ÖPNV tab.

Sample payloads are trimmed copies of real answers (Ulm Ehinger Tor, 10.11.2026).
"""

from datetime import date, datetime, timedelta

import pytest

from services.ding_transit_service import DingTransitService, TransitDeparture, TransitTrip
from services.swu_realtime_service import SwuPassage, SwuRealtimeService
from services.transit_alert_service import (
    SCOPE_LINE,
    SCOPE_NETWORK,
    SCOPE_STOP,
    TransitAlert,
    TransitAlertService,
    html_to_text,
    parse_ding_notices,
    parse_efa_infos,
    parse_swu_alerts,
)

NOW = datetime(2026, 11, 10, 8, 2, 57)


def _local(iso: str) -> datetime:
    return datetime.fromisoformat(iso).astimezone().replace(tzinfo=None)


def _swu_time(hour: int, minute: int, second: int = 0) -> str:
    """An SWU timestamp for this wall-clock time in the machine's zone.

    SWU sends times with an offset (+01:00), EFA naive local times; the service
    converts SWU to local time. With a fixed "+01:00" the test would only match
    EFA on machines in Europe/Berlin, not on the UTC CI runner.
    """
    return datetime(2026, 11, 10, hour, minute, second).astimezone().isoformat()


def _dep(line="4", planned="08:04", real: tuple[int, int] = (8, 7), delay=3, destination="Wiblingen", stop_id="9001350", line_id="87004", operator="SWU") -> TransitDeparture:
    return TransitDeparture(
        stop_id=stop_id,
        stop_name="Ulm Ehinger Tor",
        line=line,
        destination=destination,
        mot_type="Stadtbus UL/NU Linie",
        planned_time_str=planned,
        real_time_str=f"{real[0]:02d}:{real[1]:02d}",
        delay_minutes=delay,
        platform="D",
        countdown_minutes=4,
        raw_datetime=datetime(2026, 11, 10, real[0], real[1]),
        line_id=line_id,
        operator=operator,
        realtime_source="efa",
    )


def _passage(
    line: str = "4",
    scheduled: tuple[int, int] = (8, 4),
    actual: tuple[int, int, int] = (8, 8, 18),
    direction: str = "Wiblingen",
    vehicle: int | None = 608,
) -> SwuPassage:
    sched = datetime(2026, 11, 10, scheduled[0], scheduled[1])
    act = datetime(2026, 11, 10, actual[0], actual[1], actual[2])
    return SwuPassage(1350, line, direction, "D", sched, act, int((act - sched).total_seconds()), vehicle)


SWU_DEPARTURES = {
    "StopPassage": {
        "ServiceCategory": "Departures",
        "StopNumber": 1350,
        "StopName": "Ehinger Tor",
        "State": "ok",
        "DepartureData": [
            {
                "StopPointNumber": 2,
                "StopPointCode": "de:08421:1350:1:D",
                "PlatformName": "D",
                "VehicleNumber": 608,
                "VehicleCategory": 5,
                "RouteNumber": 4,
                "RouteName": "4",
                "Status": 1,
                "DepartureDirectionText": "Wiblingen",
                "DepartureTimeScheduled": _swu_time(8, 4),
                "DepartureTimeActual": _swu_time(8, 8, 18),
                "DepartureCountdown": 321,
                "DepartureDeviation": 258,
            },
            {
                "StopPointNumber": 1,
                "PlatformName": "C",
                "VehicleNumber": None,
                "RouteName": "1",
                "DepartureDirectionText": "Böfingen",
                "DepartureTimeScheduled": _swu_time(8, 15),
                "DepartureTimeActual": _swu_time(8, 15),
                "DepartureDeviation": 0,
            },
        ],
    }
}


# --- SWU live times ---------------------------------------------------------------------------


def test_swu_departures_parse_to_local_naive_times():
    passages = SwuRealtimeService.parse_departures(SWU_DEPARTURES)
    assert len(passages) == 2
    first = passages[0]
    assert (first.stop_number, first.line, first.direction, first.platform) == (1350, "4", "Wiblingen", "D")
    assert first.scheduled == datetime(2026, 11, 10, 8, 4)
    assert first.actual == datetime(2026, 11, 10, 8, 8, 18)
    assert first.actual.tzinfo is None
    assert first.deviation_seconds == 258
    assert first.vehicle_number == 608
    assert passages[1].vehicle_number is None


def test_swu_offset_times_are_converted_to_local_time():
    # A foreign offset ends up as the same instant in local time
    assert SwuRealtimeService._to_local_naive("2026-11-10T08:04:00+01:00") == _local("2026-11-10T08:04:00+01:00")
    assert SwuRealtimeService._to_local_naive("2026-11-10T08:04:00") == datetime(2026, 11, 10, 8, 4)
    assert SwuRealtimeService._to_local_naive("") is None


def test_swu_answer_without_data_is_empty():
    assert SwuRealtimeService.parse_departures({"StopPassage": {"State": "No data"}}) == []
    assert SwuRealtimeService.parse_departures({}) == []


@pytest.mark.parametrize(
    ("stop_id", "expected"),
    [("9001350", 1350), ("de:08421:1350:1:C", 1350), ("de:08421:1008", 1008), ("8000170", None), ("", None), ("90013501", None)],
)
def test_swu_stop_number_from_efa_ids(stop_id, expected):
    assert SwuRealtimeService.stop_number_for_efa_id(stop_id) == expected


def test_swu_time_replaces_lagging_efa_time(monkeypatch):
    monkeypatch.setattr(SwuRealtimeService, "fetch_passages", classmethod(lambda cls, n, force_refresh=False, now=None: [_passage()]))
    [dep] = SwuRealtimeService.apply_to_departures([_dep()], now=NOW)
    assert dep.real_time_str == "08:08"
    assert dep.raw_datetime == datetime(2026, 11, 10, 8, 8, 18)
    assert dep.delay_minutes == 4
    assert dep.delay_seconds == 258
    assert dep.countdown_minutes == 5
    assert dep.realtime_source == "swu"
    # The selection key (line, planned time, direction) does not change
    assert (dep.line, dep.planned_time_str, dep.destination) == ("4", "08:04", "Wiblingen")


def test_untracked_swu_entry_keeps_efa_time(monkeypatch):
    monkeypatch.setattr(SwuRealtimeService, "fetch_passages", classmethod(lambda cls, n, force_refresh=False, now=None: [_passage(vehicle=None)]))
    [dep] = SwuRealtimeService.apply_to_departures([_dep()], now=NOW)
    assert dep.real_time_str == "08:07"
    assert dep.realtime_source == "efa"


def test_swu_unreachable_or_foreign_stop_changes_nothing(monkeypatch):
    calls = []

    def fake(cls, n, force_refresh=False, now=None):
        calls.append(n)
        return None

    monkeypatch.setattr(SwuRealtimeService, "fetch_passages", classmethod(fake))
    deps = [_dep(), _dep(stop_id="8000170")]
    assert SwuRealtimeService.apply_to_departures(deps, now=NOW) == deps
    assert calls == [1350]  # the DB stop is not asked at SWU at all


def test_same_line_same_minute_is_told_apart_by_direction(monkeypatch):
    passages = [
        _passage(direction="Böf. Süd ü. Eichberg", actual=(8, 10, 0)),
        _passage(direction="Wiblingen", actual=(8, 9, 0)),
    ]
    monkeypatch.setattr(SwuRealtimeService, "fetch_passages", classmethod(lambda cls, n, force_refresh=False, now=None: passages))
    [wib] = SwuRealtimeService.apply_to_departures([_dep(destination="Wiblingen")], now=NOW)
    [boe] = SwuRealtimeService.apply_to_departures([_dep(destination="Böfingen Süd")], now=NOW)
    assert wib.real_time_str == "08:09"
    assert boe.real_time_str == "08:10"
    # No direction to tell them apart: rather keep EFA than guess
    [unknown] = SwuRealtimeService.apply_to_departures([_dep(destination="")], now=NOW)
    assert unknown.realtime_source == "efa"


def test_swu_correction_reorders_by_real_time(monkeypatch):
    monkeypatch.setattr(SwuRealtimeService, "fetch_passages", classmethod(lambda cls, n, force_refresh=False, now=None: [_passage(actual=(8, 12, 0))]))
    other = _dep(line="2", planned="08:10", real=(8, 10), delay=0, destination="Kuhberg", line_id="87002")
    deps = SwuRealtimeService.apply_to_departures([_dep(), other], now=NOW)
    assert [d.line for d in deps] == ["2", "4"]


def _trip(dep: TransitDeparture, interchanges: int) -> TransitTrip:
    return TransitTrip(
        departure=dep,
        arrival_stop="Ulm Tannenplatz Zentrum",
        arrival_planned_str="08:18",
        arrival_real_str="08:21",
        arrival_delay_minutes=3,
        arrival_datetime=datetime(2026, 11, 10, 8, 21),
        duration_minutes=14,
        interchanges=interchanges,
        lines=["4"] * (interchanges + 1),
    )


def test_trip_without_change_moves_arrival_with_the_bus(monkeypatch):
    monkeypatch.setattr(SwuRealtimeService, "fetch_passages", classmethod(lambda cls, n, force_refresh=False, now=None: [_passage()]))
    [trip] = SwuRealtimeService.apply_to_trips([_trip(_dep(), 0)], now=NOW)
    assert trip.departure.real_time_str == "08:08"
    assert trip.arrival_datetime == datetime(2026, 11, 10, 8, 22, 18)
    assert trip.arrival_real_str == "08:22"
    assert trip.arrival_delay_minutes == 4
    assert trip.duration_minutes == 14


def test_trip_with_change_keeps_planned_arrival(monkeypatch):
    monkeypatch.setattr(SwuRealtimeService, "fetch_passages", classmethod(lambda cls, n, force_refresh=False, now=None: [_passage()]))
    [trip] = SwuRealtimeService.apply_to_trips([_trip(_dep(), 1)], now=NOW)
    assert trip.departure.real_time_str == "08:08"
    assert trip.arrival_real_str == "08:21"
    assert trip.duration_minutes == 12


def test_fetch_departures_survives_swu_failure(monkeypatch):
    efa = {
        "departureList": [
            {
                "stopID": "9001350",
                "stopName": "Ulm Ehinger Tor",
                "countdown": "4",
                "dateTime": {"year": "2026", "month": "11", "day": "10", "hour": "8", "minute": "4"},
                "realDateTime": {"year": "2026", "month": "11", "day": "10", "hour": "8", "minute": "7"},
                "servingLine": {"number": "4", "direction": "Wiblingen", "delay": "3", "realtime": "1", "liErgRiProj": {"line": "87004"}},
                "operator": {"name": "SWU"},
            }
        ]
    }

    def boom(*_a, **_k):
        raise OSError("SWU down")

    monkeypatch.setattr(DingTransitService, "_request_json", staticmethod(lambda *_a: efa))
    monkeypatch.setattr(DingTransitService, "_cached_stop_key", None)
    monkeypatch.setattr(SwuRealtimeService, "_request_json", staticmethod(boom))
    monkeypatch.setattr(SwuRealtimeService, "_cache", {})
    [dep] = DingTransitService.fetch_departures("Ulm Ehinger Tor", "Ulm", force_refresh=True)
    assert (dep.real_time_str, dep.delay_minutes, dep.realtime_source) == ("08:07", 3, "efa")


def test_fetch_departures_applies_swu(monkeypatch):
    efa = {
        "departureList": [
            {
                "stopID": "9001350",
                "stopName": "Ulm Ehinger Tor",
                "dateTime": {"year": "2026", "month": "11", "day": "10", "hour": "8", "minute": "4"},
                "realDateTime": {"year": "2026", "month": "11", "day": "10", "hour": "8", "minute": "7"},
                "servingLine": {"number": "4", "direction": "Wiblingen", "delay": "3", "realtime": "1"},
            }
        ]
    }
    asked = []

    def swu(endpoint, params):
        asked.append(params["StopNumber"])
        return SWU_DEPARTURES

    monkeypatch.setattr(DingTransitService, "_request_json", staticmethod(lambda *_a: efa))
    monkeypatch.setattr(DingTransitService, "_cached_stop_key", None)
    monkeypatch.setattr(SwuRealtimeService, "_request_json", staticmethod(swu))
    monkeypatch.setattr(SwuRealtimeService, "_cache", {})
    [dep] = DingTransitService.fetch_departures("Ulm Ehinger Tor", "Ulm", force_refresh=True)
    assert asked == ["1350"]
    assert dep.realtime_source == "swu"
    assert dep.raw_datetime == datetime(2026, 11, 10, 8, 8, 18)
    assert dep.delay_seconds == 258


# --- EFA notices and ids ---------------------------------------------------------------------

EFA_LINE_INFO = {
    "lineInfo": {
        "infoLinkText": "Linie 5: Kürzung bei Stau bis auf Weiteres",
        "infoText": {"subtitle": "Linie 5: Kürzung bei Stau bis auf Weiteres", "htmlText": "<div>Derzeit kommt es vermehrt zu PKW-R&uuml;ckstau.</div>"},
        "paramList": [
            {"type": "addInfoParam", "name": "infoType", "value": "lineInfo"},
            {"type": "system", "name": "infoID", "value": "ems-11123"},
            {"type": "addInfoParam", "name": "priority", "value": "veryHigh"},
        ],
    }
}
EFA_STOP_INFO = {
    "stopInfo": [
        {
            "infoLinkText": "Ehinger Tor: Einschränkungen ab 01.08.2026",
            "infoText": {"htmlText": "<ul><li>Die Linie 4 Ri. Wiblingen verkehrt von Steig D.</li></ul>"},
            "paramList": [{"name": "infoType", "value": "stopInfo"}, {"name": "infoID", "value": "ems-1013823"}],
        }
    ]
}


def test_efa_departure_carries_line_id_operator_source_and_notices():
    data = {
        "departureList": [
            {
                "stopID": "9001008",
                "stopName": "Ulm Hauptbahnhof",
                "dateTime": {"year": "2026", "month": "11", "day": "10", "hour": "8", "minute": "5"},
                "realDateTime": {"year": "2026", "month": "11", "day": "10", "hour": "8", "minute": "6"},
                "servingLine": {"number": "5", "direction": "Ludwigsfeld", "delay": "1", "realtime": "1", "liErgRiProj": {"line": "87005"}},
                "operator": {"name": "SWU"},
                "lineInfos": EFA_LINE_INFO,
                "stopInfos": EFA_STOP_INFO,
            },
            {
                "stopID": "9001008",
                "stopName": "Ulm Hauptbahnhof",
                "dateTime": {"year": "2026", "month": "11", "day": "10", "hour": "8", "minute": "17"},
                "servingLine": {"number": "11", "direction": "ZOB", "realtime": "0"},
            },
        ]
    }
    first, second = DingTransitService._parse_efa_response(data)
    assert (first.line_id, first.operator, first.realtime_source) == ("87005", "SWU", "efa")
    assert {a.alert_id: a.scope for a in first.alerts} == {"ems-11123": SCOPE_LINE, "ems-1013823": SCOPE_STOP}
    line_alert = next(a for a in first.alerts if a.scope == SCOPE_LINE)
    assert line_alert.line_ids == {"87005"} and line_alert.lines == {"5"}
    assert line_alert.priority == "veryHigh"
    assert "Rückstau" in line_alert.text
    assert second.realtime_source == "" and second.alerts == []


def test_trip_legs_bring_line_id_and_notices():
    point_dt = {"date": "10.11.2026", "time": "08:05", "rtDate": "10.11.2026", "rtTime": "08:06"}
    data = {
        "trips": [
            {
                "legs": [
                    {
                        "mode": {"number": "5", "type": "3", "destination": "Ludwigsfeld", "realtime": "1", "diva": {"line": "87005", "operator": "SWU"}},
                        "infos": {"info": EFA_LINE_INFO["lineInfo"]},
                        "points": [
                            {"name": "Ulm Hauptbahnhof", "usage": "departure", "dateTime": point_dt, "ref": {"id": "9001008"}},
                            {"name": "Neu-Ulm Edisoncenter", "usage": "arrival", "dateTime": {"date": "10.11.2026", "time": "08:15"}},
                        ],
                    }
                ]
            }
        ]
    }
    [trip] = DingTransitService._parse_trip_response(data)
    dep = trip.departure
    assert (dep.stop_id, dep.line_id, dep.operator, dep.realtime_source) == ("9001008", "87005", "SWU", "efa")
    assert [a.alert_id for a in dep.alerts] == ["ems-11123"]


def test_html_to_text_keeps_list_items_and_decodes_entities():
    text = html_to_text("<div>Ab dem 12.08. gilt:</div><ul><li>Steige B, C und D&nbsp;wieder regul&auml;r.</li></ul>")
    assert text == "Ab dem 12.08. gilt:\n• Steige B, C und D wieder regulär."


# --- ding.eu ----------------------------------------------------------------------------------

DING_PAGE = """
<html><body><main>
<article class="c-detail-list-card" data-info-detail-list-target="item" data-mot="[&quot;bus&quot;]"
  data-lines="[&quot;4|stadtbus ul\\/nu|din|87004&quot;,&quot;n7|nachtbus|din|87007&quot;]"
  data-stops="[&quot;ulm, theater&quot;]" data-valid-from="2026-11-01" data-valid-until="2026-11-30" data-valid-today="true">
 <details><summary><div class="c-detail-list-card__header"><div class="c-detail-list-card__heading">
  <h3 title="Ehinger Tor: Umleitung"><span aria-hidden="true">Ehinger Tor: Uml…</span>
  <span class="c-detail-list-card__full-title">Ehinger Tor: Umleitung wegen Bauarbeiten</span></h3>
  <span class="c-detail-list-card__chevron" uk-icon="icon: chevron-down"><svg width="20" height="20"><polyline points="16 7 10 13 4 7"></polyline></svg></span>
 </div>
 <div class="c-detail-list-card__lines"><span class="c-icon c-icon-bus"><svg><rect width="32" height="32" rx="4"/><g><path d="M7 18"/></g></svg></span><span>Bus: 4</span></div>
 </div></summary>
 <div class="c-detail-list-card__content c-text-content">
  An der Haltestelle Ulm, Ehinger Tor kommt es zu einer Umleitung.<br>Betroffen ist die Linie 4.
 </div></details>
</article>
<article class="c-detail-list-card" data-lines="[&quot;4|stadtbus bc|din|21004&quot;]" data-stops="[]" data-valid-from="2026-12-01" data-valid-until="">
 <details><summary><span class="c-detail-list-card__full-title">Biberach Linie 4: Haltausfall</span></summary>
 <div class="c-detail-list-card__content"><p>Fällt aus.</p></div></details>
</article>
<article class="c-detail-list-card" data-lines="[]" data-stops="[&quot;neu-ulm, edisoncenter&quot;]" data-valid-from="2026-10-01" data-valid-until="">
 <details><summary><span class="c-detail-list-card__full-title">Edisoncenter: Steig verlegt</span></summary>
 <div class="c-detail-list-card__content">Steig A entfällt.</div></details>
</article>
</main></body></html>
"""


def test_ding_page_notices_are_parsed_from_their_data_attributes():
    alerts = parse_ding_notices(DING_PAGE)
    assert [a.title for a in alerts] == ["Ehinger Tor: Umleitung wegen Bauarbeiten", "Biberach Linie 4: Haltausfall", "Edisoncenter: Steig verlegt"]
    ulm = alerts[0]
    assert ulm.lines == {"4", "n7"}
    assert ulm.line_ids == {"87004", "87007"}
    assert ulm.stops == {"ulm theater"}
    assert (ulm.valid_from, ulm.valid_until) == (date(2026, 11, 1), date(2026, 11, 30))
    assert ulm.text == "An der Haltestelle Ulm, Ehinger Tor kommt es zu einer Umleitung.\nBetroffen ist die Linie 4."
    assert ulm.scope == SCOPE_LINE
    assert alerts[1].valid_until is None and alerts[1].text == "Fällt aus."
    assert alerts[2].scope == SCOPE_STOP and alerts[2].stops == {"neu ulm edisoncenter"}


def test_ding_page_without_cards_gives_nothing():
    assert parse_ding_notices("<html><body>Wartungsarbeiten</body></html>") == []
    assert parse_ding_notices("") == []


# --- SWU notices ------------------------------------------------------------------------------


def test_swu_quiet_answers_give_no_notices():
    assert parse_swu_alerts({"PassengerAlert": []}) == []
    assert parse_swu_alerts({"PassengerAlert": {"State": "No PassengerAlert for this stop found!", "StopNumber": 1350}}, stop_name="Ehinger Tor") == []


def test_swu_unplanned_alerts_as_text_and_with_routes():
    data = {
        "PassengerAlert": {
            "AlertData": [
                "<p>Wegen eines Unfalls in der Karlstraße kommt es zu Verspätungen.</p>",
                {"AlertTitle": "Linie 2: Umleitung", "AlertText": "Die Linie 2 fährt über den Kuhberg.", "Routes": [{"RouteNumber": 2}]},
            ]
        }
    }
    network, line2 = parse_swu_alerts(data)
    assert network.scope == SCOPE_NETWORK and network.source == "swu"
    assert network.title.startswith("Wegen eines Unfalls")
    assert line2.scope == SCOPE_LINE and line2.lines == {"2"} and line2.operator == "swu"
    assert line2.text == "Die Linie 2 fährt über den Kuhberg."


def test_swu_stop_alerts_belong_to_the_stop():
    data = {"PassengerAlert": {"State": "ok", "PassengerAlertStop": [{"AlertText": "Steig C gesperrt."}]}}
    [alert] = parse_swu_alerts(data, stop_name="Ulm Ehinger Tor")
    assert alert.scope == SCOPE_STOP and alert.stops == {"ulm ehinger tor"}


# --- assignment --------------------------------------------------------------------------------


def test_line_notices_go_to_matching_departures_only():
    pool = parse_ding_notices(DING_PAGE)
    ulm4 = _dep()
    biberach4 = _dep(line="4", line_id="21004", operator="Stadtwerke Biberach", stop_id="9002222")
    tram1 = _dep(line="1", line_id="87001", destination="Böfingen")
    deps, listed = TransitAlertService.assign([ulm4, biberach4, tram1], pool, "Ulm Ehinger Tor", "Ulm", today=date(2026, 11, 10))
    assert [a.title for a in deps[0].alerts] == ["Ehinger Tor: Umleitung wegen Bauarbeiten"]
    assert deps[1].alerts == []  # Biberach line 4 notice starts in December, and Ulm's does not concern it
    assert deps[2].alerts == []
    assert [a.title for a in listed] == ["Ehinger Tor: Umleitung wegen Bauarbeiten"]


def test_stop_notices_are_listed_but_not_put_on_every_departure():
    stop_notice = TransitAlert("ems-1", "ding", "Ehinger Tor: Einschränkungen", scope=SCOPE_STOP, stops=frozenset({"ulm ehinger tor"}))
    elsewhere = TransitAlert("ems-2", "ding", "Edisoncenter: Steig verlegt", scope=SCOPE_STOP, stops=frozenset({"neu ulm edisoncenter"}))
    deps, listed = TransitAlertService.assign([_dep()], [stop_notice, elsewhere], "Ehinger Tor", "Ulm", today=date(2026, 11, 10))
    assert deps[0].alerts == []
    assert [a.alert_id for a in listed] == ["ems-1"]


def test_notice_about_the_own_stop_is_listed_without_row_badges():
    rebuild = TransitAlert(
        "ding:umbau",
        "ding",
        "Ehinger Tor: Einschränkungen ab 01.08.2026",
        lines=frozenset({"1", "2", "4"}),
        line_ids=frozenset({"87001", "87002", "87004"}),
        stops=frozenset({"ulm ehinger tor"}),
    )
    deps, listed = TransitAlertService.assign([_dep()], [rebuild], "Ulm Ehinger Tor", "Ulm", today=date(2026, 11, 10))
    assert deps[0].alerts == []
    assert [a.alert_id for a in listed] == ["ding:umbau"]


def test_same_notice_from_efa_and_ding_is_merged():
    efa = parse_efa_infos(
        {"lineInfo": {"infoLinkText": "Ehinger Tor: Umleitung wegen Bauarbeiten", "paramList": [{"name": "priority", "value": "veryHigh"}]}},
        line="4",
        line_id="87004",
    )
    dep = _dep()
    dep.alerts = efa
    deps, listed = TransitAlertService.assign([dep], efa + parse_ding_notices(DING_PAGE), "Ulm Ehinger Tor", "Ulm", today=date(2026, 11, 10))
    assert len(listed) == 1
    merged = listed[0]
    assert merged.priority == "veryHigh"
    assert merged.valid_until == date(2026, 11, 30)  # from ding.eu
    assert "Umleitung" in merged.text
    assert len(deps[0].alerts) == 1


def test_expired_notices_are_dropped():
    old = TransitAlert("x", "ding", "Linie 4: alt", lines=frozenset({"4"}), line_ids=frozenset({"87004"}), valid_until=date(2026, 11, 9))
    deps, listed = TransitAlertService.assign([_dep()], [old], "Ulm Ehinger Tor", today=date(2026, 11, 10))
    assert deps[0].alerts == [] and listed == []


def test_swu_line_notice_only_hits_swu_vehicles():
    swu = TransitAlert("s", "swu", "Linie 4: Umleitung", lines=frozenset({"4"}), operator="swu")
    network = TransitAlert("n", "swu", "Störung im Netz", scope=SCOPE_NETWORK)
    regional = _dep(line="4", line_id="", operator="DB Regio Bus")
    deps, listed = TransitAlertService.assign([_dep(), regional], [swu, network], "Ulm Ehinger Tor", today=date(2026, 11, 10))
    assert [a.alert_id for a in deps[0].alerts] == ["s"]
    assert deps[1].alerts == []
    assert {a.alert_id for a in listed} == {"s", "n"}


def test_collect_never_raises_and_combines_sources(monkeypatch):
    monkeypatch.setattr(TransitAlertService, "fetch_ding_notices", classmethod(lambda cls, now=None: parse_ding_notices(DING_PAGE)))
    monkeypatch.setattr(TransitAlertService, "fetch_swu_alerts", classmethod(lambda cls, numbers, now=None: [TransitAlert("n", "swu", "Störung im Netz", scope=SCOPE_NETWORK)]))
    today = date.today()
    pool_dep = _dep()
    deps, listed = TransitAlertService.collect([pool_dep], "Ulm Ehinger Tor", "Ulm")
    titles = {a.title for a in listed}
    assert "Störung im Netz" in titles
    if date(2026, 11, 1) <= today <= date(2026, 11, 30):
        assert "Ehinger Tor: Umleitung wegen Bauarbeiten" in titles

    def boom(cls, now=None):
        raise RuntimeError("parser broke")

    monkeypatch.setattr(TransitAlertService, "fetch_ding_notices", classmethod(boom))
    deps, listed = TransitAlertService.collect([pool_dep], "Ulm Ehinger Tor", "Ulm")
    assert deps == [pool_dep] and listed == []


def test_ding_fetch_error_keeps_last_notices(monkeypatch):
    monkeypatch.setattr(TransitAlertService, "_ding_cache", None)
    monkeypatch.setattr(TransitAlertService, "_request_text", staticmethod(lambda url, timeout: DING_PAGE))
    assert len(TransitAlertService.fetch_ding_notices(now=NOW)) == 3

    def boom(url, timeout):
        raise OSError("offline")

    monkeypatch.setattr(TransitAlertService, "_request_text", staticmethod(boom))
    assert len(TransitAlertService.fetch_ding_notices(now=NOW + timedelta(hours=1))) == 3
