"""SWU live departures (Stadtwerke Ulm/Neu-Ulm) to correct the EFA times of SWU buses and trams.

The bwegt EFA answer lags behind SWU's own vehicle tracking and truncates to
whole minutes, so a delayed bus often shows up a minute or more too early.
SWU publishes second-accurate departures per stop (updated every 15 s); this
service matches them to EFA departures by line and scheduled time and swaps in
the SWU time. Anything that cannot be matched keeps its EFA time, and when SWU
is unreachable nothing changes at all.
"""

from __future__ import annotations

import dataclasses
import json
import logging
import re
import urllib.parse
import urllib.request
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import TYPE_CHECKING, Any

from constants import (
    TRANSIT_SWU_CACHE_TTL_SECONDS,
    TRANSIT_SWU_DEPARTURE_LIMIT,
    TRANSIT_SWU_DEPARTURES_ENDPOINT,
    TRANSIT_SWU_EFA_STOP_ID_PREFIX,
    TRANSIT_SWU_REQUEST_TIMEOUT_SECONDS,
)

if TYPE_CHECKING:
    from services.ding_transit_service import TransitDeparture, TransitTrip

logger = logging.getLogger("SupportCockpit.transit.swu")

# EFA ids: "9001350" (departure monitor) or a DHID "de:08421:1350:1:C" (trip points)
_EFA_NUMERIC_ID = re.compile(rf"^{TRANSIT_SWU_EFA_STOP_ID_PREFIX}(\d{{4}})$")
_DHID = re.compile(r"^de:\d{5}:(\d{4})(?::|$)")
# An SWU match further away from the EFA time than this is a different trip
_MAX_MATCH_GAP = timedelta(minutes=90)


@dataclass
class SwuPassage:
    """One departure from the SWU stop monitor."""

    stop_number: int
    line: str
    direction: str
    platform: str
    scheduled: datetime
    actual: datetime
    deviation_seconds: int
    vehicle_number: int | None


class SwuRealtimeService:
    """Fetches SWU stop departures and applies them to EFA departures and trips."""

    _cache: dict[int, tuple[datetime, list[SwuPassage]]] = {}

    @staticmethod
    def _request_json(endpoint: str, params: dict[str, str]) -> dict[str, Any]:
        url = f"{endpoint}?{urllib.parse.urlencode(params)}"
        req = urllib.request.Request(url, headers={"User-Agent": "SupportCockpit/1.0 (SwuRealtimeService)"})
        with urllib.request.urlopen(req, timeout=TRANSIT_SWU_REQUEST_TIMEOUT_SECONDS) as resp:
            data = json.loads(resp.read().decode("utf-8"), strict=False)
        return data if isinstance(data, dict) else {}

    @staticmethod
    def stop_number_for_efa_id(stop_id: str) -> int | None:
        """SWU stop number of an EFA stop id, or None when the id is not an SWU-style stop."""
        stop_id = (stop_id or "").strip()
        match = _EFA_NUMERIC_ID.match(stop_id) or _DHID.match(stop_id)
        return int(match.group(1)) if match else None

    @staticmethod
    def _to_local_naive(text: Any) -> datetime | None:
        """'2026-11-10T07:55:00+01:00' -> naive local time, like the EFA times the app works with."""
        if not isinstance(text, str) or not text.strip():
            return None
        try:
            parsed = datetime.fromisoformat(text.strip())
        except ValueError:
            return None
        if parsed.tzinfo is not None:
            parsed = parsed.astimezone().replace(tzinfo=None)
        return parsed

    @classmethod
    def parse_departures(cls, data: dict[str, Any]) -> list[SwuPassage]:
        """Parse an api.swu.de StopPassage/Departures answer."""
        raw_block = data.get("StopPassage")
        block: dict[str, Any] = raw_block if isinstance(raw_block, dict) else {}
        if str(block.get("State") or "").lower() != "ok":
            return []
        try:
            stop_number = int(block.get("StopNumber") or 0)
        except (TypeError, ValueError):
            stop_number = 0
        items = block.get("DepartureData")
        if isinstance(items, dict):
            items = [items]
        passages: list[SwuPassage] = []
        for item in items if isinstance(items, list) else []:
            if not isinstance(item, dict):
                continue
            scheduled = cls._to_local_naive(item.get("DepartureTimeScheduled"))
            actual = cls._to_local_naive(item.get("DepartureTimeActual")) or scheduled
            if scheduled is None or actual is None:
                continue
            try:
                deviation = int(item.get("DepartureDeviation") or 0)
            except (TypeError, ValueError):
                deviation = int((actual - scheduled).total_seconds())
            vehicle = item.get("VehicleNumber")
            passages.append(
                SwuPassage(
                    stop_number=stop_number,
                    line=str(item.get("RouteName") or item.get("RouteNumber") or "").strip(),
                    direction=str(item.get("DepartureDirectionText") or "").strip(),
                    platform=str(item.get("PlatformName") or "").strip(),
                    scheduled=scheduled,
                    actual=actual,
                    deviation_seconds=deviation,
                    vehicle_number=vehicle if isinstance(vehicle, int) else None,
                )
            )
        return passages

    @classmethod
    def fetch_passages(cls, stop_number: int, force_refresh: bool = False, now: datetime | None = None) -> list[SwuPassage] | None:
        """Upcoming departures at an SWU stop; None when SWU is not reachable."""
        now = now or datetime.now()
        cached = cls._cache.get(stop_number)
        if not force_refresh and cached and (now - cached[0]).total_seconds() < TRANSIT_SWU_CACHE_TTL_SECONDS:
            return list(cached[1])
        try:
            data = cls._request_json(
                TRANSIT_SWU_DEPARTURES_ENDPOINT,
                {"StopNumber": str(stop_number), "Limit": str(TRANSIT_SWU_DEPARTURE_LIMIT)},
            )
        except Exception as e:
            logger.info("SWU live departures for stop %s not available: %s", stop_number, e)
            return None
        passages = cls.parse_departures(data)
        cls._cache[stop_number] = (now, passages)
        return list(passages)

    @staticmethod
    def _norm(text: str) -> str:
        return re.sub(r"[^0-9a-zäöüß]", "", (text or "").lower())

    @classmethod
    def match(cls, dep: TransitDeparture, passages: list[SwuPassage]) -> SwuPassage | None:
        """The SWU departure for this EFA departure: same line and scheduled minute.

        Two buses of one line at the same minute (both directions) are told apart
        by the first letters of the direction; if that still leaves more than
        one, nothing is matched rather than guessing.
        """
        line = cls._norm(dep.line)
        if not line:
            return None
        candidates = [
            p
            for p in passages
            if cls._norm(p.line) == line
            and p.scheduled.strftime("%H:%M") == dep.planned_time_str
            and (dep.raw_datetime is None or abs(p.actual - dep.raw_datetime) <= _MAX_MATCH_GAP)
        ]
        if len(candidates) > 1:
            head = cls._norm(dep.destination)[:3]
            candidates = [p for p in candidates if head and cls._norm(p.direction).startswith(head)]
        return candidates[0] if len(candidates) == 1 else None

    @staticmethod
    def corrected(dep: TransitDeparture, passage: SwuPassage, now: datetime) -> TransitDeparture:
        """A copy of dep with the SWU time. Only for tracked vehicles: an untracked SWU entry is just the timetable."""
        return dataclasses.replace(
            dep,
            real_time_str=passage.actual.strftime("%H:%M"),
            raw_datetime=passage.actual,
            delay_minutes=max(0, passage.deviation_seconds // 60),
            delay_seconds=passage.deviation_seconds,
            countdown_minutes=max(0, int((passage.actual - now).total_seconds() // 60)),
            realtime_source="swu",
        )

    @classmethod
    def _passages_for(cls, stop_ids: set[str], force_refresh: bool, now: datetime) -> dict[str, list[SwuPassage]]:
        by_stop: dict[str, list[SwuPassage]] = {}
        numbers: dict[int, list[SwuPassage] | None] = {}
        for stop_id in stop_ids:
            number = cls.stop_number_for_efa_id(stop_id)
            if number is None:
                continue
            if number not in numbers:
                numbers[number] = cls.fetch_passages(number, force_refresh=force_refresh, now=now)
            passages = numbers[number]
            if passages:
                by_stop[stop_id] = passages
        return by_stop

    @classmethod
    def apply_to_departures(cls, deps: list[TransitDeparture], force_refresh: bool = False, now: datetime | None = None) -> list[TransitDeparture]:
        """deps with SWU times where SWU knows the bus; order follows the corrected times."""
        now = now or datetime.now()
        by_stop = cls._passages_for({d.stop_id for d in deps}, force_refresh, now)
        if not by_stop:
            return list(deps)
        result: list[TransitDeparture] = []
        for dep in deps:
            passage = cls.match(dep, by_stop.get(dep.stop_id, []))
            result.append(cls.corrected(dep, passage, now) if passage and passage.vehicle_number is not None else dep)
        result.sort(key=lambda d: d.raw_datetime or now)
        return result

    @classmethod
    def apply_to_trips(cls, trips: list[TransitTrip], force_refresh: bool = False, now: datetime | None = None) -> list[TransitTrip]:
        """trips with the SWU time for the first bus at the origin.

        Without a change the arrival moves by the same amount; with changes it
        stays as EFA planned it, since the connection may still be caught.
        """
        now = now or datetime.now()
        by_stop = cls._passages_for({t.departure.stop_id for t in trips}, force_refresh, now)
        if not by_stop:
            return list(trips)
        result: list[TransitTrip] = []
        for trip in trips:
            dep = trip.departure
            passage = cls.match(dep, by_stop.get(dep.stop_id, []))
            if passage is None or passage.vehicle_number is None:
                result.append(trip)
                continue
            new_dep = cls.corrected(dep, passage, now)
            changes: dict[str, Any] = {"departure": new_dep}
            if trip.interchanges == 0 and trip.arrival_datetime is not None and dep.raw_datetime is not None:
                shift = passage.actual - dep.raw_datetime
                arrival = trip.arrival_datetime + shift
                planned_arrival_delay = timedelta(minutes=trip.arrival_delay_minutes)
                changes.update(
                    arrival_datetime=arrival,
                    arrival_real_str=arrival.strftime("%H:%M"),
                    arrival_delay_minutes=max(0, int((shift + planned_arrival_delay).total_seconds() // 60)),
                )
            arrival_dt = changes.get("arrival_datetime", trip.arrival_datetime)
            if arrival_dt is not None:
                changes["duration_minutes"] = max(0, int((arrival_dt - passage.actual).total_seconds() // 60))
            result.append(dataclasses.replace(trip, **changes))
        return result
