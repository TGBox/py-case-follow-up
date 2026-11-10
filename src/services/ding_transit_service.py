"""DING transit service for live departures, trips to a destination and departure alarms in the Ulm / Neu-Ulm region.

Uses the standardized bwegt / EFA-BW JSON endpoint covering the DING network.
Provides error-resilient fetching, parsing, caching, and commute alarm calculations.
Times of SWU buses and trams are corrected from SWU's own live data (see
swu_realtime_service), since EFA lags behind and truncates to minutes.
"""

from __future__ import annotations

import json
import logging
import urllib.parse
import urllib.request
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Any

from constants import (
    CHECKOUT_ALARM_URGENT_THRESHOLD_MINUTES,
    CHECKOUT_ALARM_WARN_THRESHOLD_MINUTES,
    TRANSIT_DEFAULT_STOP_NAME,
    TRANSIT_DEFAULT_STOP_PLACE,
    TRANSIT_EFA_ENDPOINT,
    TRANSIT_EFA_STOPFINDER_ENDPOINT,
    TRANSIT_EFA_TRIP_ENDPOINT,
    TRANSIT_FOOTPATH_MOT_TYPES,
    TRANSIT_STOP_SUGGESTION_LIMIT,
    TRANSIT_REQUEST_TIMEOUT_SECONDS,
)
from services.transit_alert_service import TransitAlert, parse_efa_infos

logger = logging.getLogger("SupportCockpit.transit")


@dataclass
class TransitDeparture:
    stop_id: str
    stop_name: str
    line: str
    destination: str
    mot_type: str
    planned_time_str: str
    real_time_str: str
    delay_minutes: int
    platform: str
    countdown_minutes: int
    raw_datetime: datetime | None = None
    # DING line id ("87004" = SWU line 4); line numbers alone repeat across the network
    line_id: str = ""
    operator: str = ""
    # Exact delay when SWU knows it; delay_minutes is the whole minutes of it
    delay_seconds: int | None = None
    # Where real_time_str comes from: "swu" (SWU live), "efa" (EFA live) or "" (timetable only)
    realtime_source: str = ""
    alerts: list[TransitAlert] = field(default_factory=list)


@dataclass
class TransitStop:
    """A stop suggestion from the EFA stop finder."""

    name: str
    place: str
    stop_id: str = ""


@dataclass
class TransitTrip:
    """A connection from the configured stop to the destination, possibly with changes.

    departure carries the start of the trip at the origin stop in the shape the
    departure list uses, so selection, lead-time alarms and countdowns work for
    trips unchanged. Its line is the first line ridden and its destination the
    direction shown on that bus.
    """

    departure: TransitDeparture
    arrival_stop: str
    arrival_planned_str: str
    arrival_real_str: str
    arrival_delay_minutes: int
    arrival_datetime: datetime | None
    duration_minutes: int
    interchanges: int
    lines: list[str] = field(default_factory=list)


@dataclass
class StopCheckResult:
    """Outcome of looking up departures for a configured stop.

    status is one of: "ok" (departures found), "no_departures" (stop resolved
    but nothing leaves soon), "ambiguous" (several stops match, see
    candidates), "not_found" (no stop by that name) or "error" (service not
    reachable).
    """

    status: str
    departure_count: int = 0
    resolved_name: str = ""
    candidates: list[TransitStop] = field(default_factory=list)


class DingTransitService:
    """Service to fetch and calculate live transit departures and commute alarms."""

    _cached_departures: list[TransitDeparture] = []
    _last_fetch_time: datetime | None = None
    _cached_stop_key: tuple[str, str, str] | None = None
    _cache_ttl_seconds: float = 30.0
    _cached_trips: list[TransitTrip] = []
    _last_trip_fetch_time: datetime | None = None
    _cached_trip_key: tuple[str, ...] | None = None

    @staticmethod
    def _request_json(endpoint: str, params: dict[str, str]) -> dict[str, Any]:
        url = f"{endpoint}?{urllib.parse.urlencode(params)}"
        req = urllib.request.Request(
            url,
            headers={"User-Agent": "SupportCockpit/1.0 (DingTransitService)"},
        )
        with urllib.request.urlopen(req, timeout=TRANSIT_REQUEST_TIMEOUT_SECONDS) as resp:
            data = json.loads(resp.read().decode("utf-8"), strict=False)
        return data if isinstance(data, dict) else {}

    @staticmethod
    def _departure_params(
        stop_name: str, place: str, limit: int, departure_time: datetime | None = None
    ) -> dict[str, str]:
        params = {
            "outputFormat": "JSON",
            "type_dm": "stop",
            "name_dm": stop_name,
            "place_dm": place,
            "useRealtime": "1",
            "mode": "direct",
            "limit": str(limit),
        }
        if departure_time is not None:
            # Without these EFA answers with the next departures from now.
            params["itdDate"] = departure_time.strftime("%Y%m%d")
            params["itdTime"] = departure_time.strftime("%H%M")
            params["itdDateTimeDepArr"] = "dep"
        return params

    @classmethod
    def fetch_departures(
        cls,
        stop_name: str = TRANSIT_DEFAULT_STOP_NAME,
        place: str = TRANSIT_DEFAULT_STOP_PLACE,
        limit: int = 15,
        force_refresh: bool = False,
        departure_time: datetime | None = None,
    ) -> list[TransitDeparture]:
        """Fetch live departures from the EFA endpoint for the given stop and place.

        departure_time: list departures from this moment on instead of from now.
        """
        now = datetime.now()
        planned_key = departure_time.strftime("%Y%m%d%H%M") if departure_time else ""
        stop_key = (stop_name.strip().lower(), place.strip().lower(), planned_key)
        # A different stop (or planned time) must never be answered from the previous cache.
        if cls._cached_stop_key != stop_key:
            cls._cached_departures = []
            cls._last_fetch_time = None
        if (
            not force_refresh
            and cls._last_fetch_time is not None
            and (now - cls._last_fetch_time).total_seconds() < cls._cache_ttl_seconds
            and cls._cached_departures
        ):
            return cls._with_swu_departures(list(cls._cached_departures), force_refresh)

        try:
            data = cls._request_json(
                TRANSIT_EFA_ENDPOINT, cls._departure_params(stop_name, place, limit, departure_time)
            )
            parsed = cls._parse_efa_response(data, trust_countdown=departure_time is None)
            cls._cached_departures = parsed
            cls._last_fetch_time = now
            cls._cached_stop_key = stop_key
            return cls._with_swu_departures(list(parsed), force_refresh)
        except Exception as e:
            logger.warning("Failed to fetch DING live departures: %s", e)
            return cls._with_swu_departures(list(cls._cached_departures), force_refresh)

    @staticmethod
    def _with_swu_departures(deps: list[TransitDeparture], force_refresh: bool) -> list[TransitDeparture]:
        """deps with SWU's live times for SWU buses; unchanged if SWU fails."""
        if not deps:
            return deps
        try:
            from services.swu_realtime_service import SwuRealtimeService

            return SwuRealtimeService.apply_to_departures(deps, force_refresh=force_refresh)
        except Exception as e:
            logger.warning("SWU live correction failed, keeping EFA times: %s", e)
            return deps

    @staticmethod
    def _with_swu_trips(trips: list[TransitTrip], force_refresh: bool) -> list[TransitTrip]:
        if not trips:
            return trips
        try:
            from services.swu_realtime_service import SwuRealtimeService

            return SwuRealtimeService.apply_to_trips(trips, force_refresh=force_refresh)
        except Exception as e:
            logger.warning("SWU live correction failed, keeping EFA times: %s", e)
            return trips

    @staticmethod
    def _trip_params(
        origin_name: str,
        origin_place: str,
        dest_name: str,
        dest_place: str,
        limit: int,
        departure_time: datetime | None = None,
    ) -> dict[str, str]:
        when = departure_time or datetime.now()
        return {
            "outputFormat": "JSON",
            "locationServerActive": "1",
            "type_origin": "stop",
            "name_origin": origin_name,
            "place_origin": origin_place,
            "type_destination": "stop",
            "name_destination": dest_name,
            "place_destination": dest_place,
            "itdDate": when.strftime("%Y%m%d"),
            "itdTime": when.strftime("%H%M"),
            "itdTripDateTimeDepArr": "dep",
            "useRealtime": "1",
            "calcNumberOfTrips": str(limit),
        }

    @classmethod
    def fetch_trips(
        cls,
        origin_name: str,
        origin_place: str,
        dest_name: str,
        dest_place: str = "",
        limit: int = 6,
        force_refresh: bool = False,
        departure_time: datetime | None = None,
    ) -> list[TransitTrip]:
        """Connections from the origin stop to the destination, earliest first.

        Only trips that start at the origin in a useful direction come back,
        since EFA plans the route to the destination. Changes are allowed.
        departure_time: plan from this moment on instead of from now.
        """
        now = datetime.now()
        planned_key = departure_time.strftime("%Y%m%d%H%M") if departure_time else ""
        key = tuple(
            v.strip().lower() for v in (origin_name, origin_place, dest_name, dest_place)
        ) + (planned_key,)
        if cls._cached_trip_key != key:
            cls._cached_trips = []
            cls._last_trip_fetch_time = None
        if (
            not force_refresh
            and cls._last_trip_fetch_time is not None
            and (now - cls._last_trip_fetch_time).total_seconds() < cls._cache_ttl_seconds
            and cls._cached_trips
        ):
            return cls._with_swu_trips(list(cls._cached_trips), force_refresh)

        try:
            data = cls._request_json(
                TRANSIT_EFA_TRIP_ENDPOINT,
                cls._trip_params(origin_name, origin_place, dest_name, dest_place, limit, departure_time),
            )
            # Without a planned time EFA may start a little before now; drop what has already left.
            earliest = departure_time or (now - timedelta(minutes=1))
            parsed = [
                t
                for t in cls._parse_trip_response(data)
                if t.departure.raw_datetime is None or t.departure.raw_datetime >= earliest
            ]
            parsed.sort(key=lambda t: (t.departure.raw_datetime or now, t.arrival_datetime or now))
            # The same first bus can come back with several onward connections: keep the earliest arrival,
            # so every row (and the selection key line_time_direction) stands for one bus.
            seen: set[tuple[str, str, str]] = set()
            unique: list[TransitTrip] = []
            for t in parsed:
                dep_key = (t.departure.line, t.departure.planned_time_str, t.departure.destination)
                if dep_key not in seen:
                    seen.add(dep_key)
                    unique.append(t)
            parsed = unique
            cls._cached_trips = parsed
            cls._last_trip_fetch_time = now
            cls._cached_trip_key = key
            return cls._with_swu_trips(list(parsed), force_refresh)
        except Exception as e:
            logger.warning("Failed to fetch DING trips: %s", e)
            return cls._with_swu_trips(list(cls._cached_trips), force_refresh)

    @staticmethod
    def _as_list(raw: Any, inner_key: str) -> list[Any]:
        """EFA wraps lists as a list, as {inner_key: [...]}, as {inner_key: {...}} or as null."""
        if isinstance(raw, dict):
            raw = raw.get(inner_key)
        if isinstance(raw, dict):
            return [raw]
        return raw if isinstance(raw, list) else []

    @staticmethod
    def _parse_point_time(dt_dict: Any, realtime: bool) -> datetime | None:
        """Reads a trip point time: {"date": "05.11.2026", "time": "16:58", "rtDate", "rtTime"}
        or the departure-monitor shape {"year", "month", "day", "hour", "minute"}."""
        if not isinstance(dt_dict, dict):
            return None
        if "hour" in dt_dict:
            try:
                return datetime(
                    int(dt_dict["year"]), int(dt_dict["month"]), int(dt_dict["day"]),
                    int(dt_dict["hour"]), int(dt_dict["minute"]),
                )
            except (KeyError, TypeError, ValueError):
                return None
        date_str = str((dt_dict.get("rtDate") if realtime else None) or dt_dict.get("date") or "").strip()
        time_str = str((dt_dict.get("rtTime") if realtime else None) or dt_dict.get("time") or "").strip()
        if not date_str or not time_str:
            return None
        for fmt in ("%d.%m.%Y %H:%M", "%Y%m%d %H:%M", "%Y-%m-%d %H:%M"):
            try:
                return datetime.strptime(f"{date_str} {time_str}", fmt)
            except ValueError:
                continue
        return None

    @classmethod
    def _parse_trip_response(cls, data: dict[str, Any]) -> list[TransitTrip]:
        """Parse an EFA XML_TRIP_REQUEST2 JSON answer into TransitTrip objects.

        Trips without a single ridden leg (pure footpaths) are skipped.
        """
        now = datetime.now()
        trips: list[TransitTrip] = []
        for trip in cls._as_list(data.get("trips"), "trip"):
            if not isinstance(trip, dict):
                continue
            legs = [leg for leg in cls._as_list(trip.get("legs"), "leg") if isinstance(leg, dict)]
            if not legs:
                continue

            ridden: list[dict[str, Any]] = []
            for leg in legs:
                raw_mode = leg.get("mode")
                mode: dict[str, Any] = raw_mode if isinstance(raw_mode, dict) else {}
                line = str(mode.get("number") or mode.get("symbol") or "").strip()
                if line and str(mode.get("type") or "") not in TRANSIT_FOOTPATH_MOT_TYPES:
                    ridden.append(leg)
            if not ridden:
                continue

            def endpoint(leg: dict[str, Any], usage: str) -> dict[str, Any]:
                points = [p for p in cls._as_list(leg.get("points"), "point") if isinstance(p, dict)]
                for p in points:
                    if str(p.get("usage") or "").lower() == usage:
                        return p
                if not points:
                    return {}
                return points[0] if usage == "departure" else points[-1]

            start = endpoint(legs[0], "departure")
            end = endpoint(legs[-1], "arrival")
            first_mode = ridden[0].get("mode") or {}

            dep_planned = cls._parse_point_time(start.get("dateTime"), realtime=False)
            dep_real = cls._parse_point_time(start.get("dateTime"), realtime=True) or dep_planned
            arr_planned = cls._parse_point_time(end.get("dateTime"), realtime=False)
            arr_real = cls._parse_point_time(end.get("dateTime"), realtime=True) or arr_planned
            if dep_real is None:
                continue

            def minutes_between(later: datetime | None, earlier: datetime | None) -> int:
                if later is None or earlier is None:
                    return 0
                return int((later - earlier).total_seconds() // 60)

            lines = [str((leg.get("mode") or {}).get("number") or (leg.get("mode") or {}).get("symbol")) for leg in ridden]
            raw_diva = first_mode.get("diva") if isinstance(first_mode, dict) else None
            diva: dict[str, Any] = raw_diva if isinstance(raw_diva, dict) else {}
            alerts: list[TransitAlert] = []
            for leg, leg_line in zip(ridden, lines, strict=True):
                raw_leg_mode = leg.get("mode")
                leg_mode: dict[str, Any] = raw_leg_mode if isinstance(raw_leg_mode, dict) else {}
                raw_leg_diva = leg_mode.get("diva")
                leg_diva: dict[str, Any] = raw_leg_diva if isinstance(raw_leg_diva, dict) else {}
                alerts.extend(parse_efa_infos(leg.get("infos"), line=leg_line, line_id=str(leg_diva.get("line") or "")))
            departure = TransitDeparture(
                stop_id=str((start.get("ref") or {}).get("id") or "") if isinstance(start.get("ref"), dict) else "",
                stop_name=str(start.get("name") or ""),
                line=lines[0],
                destination=str(first_mode.get("destination") or ""),
                mot_type=str(first_mode.get("name") or ""),
                planned_time_str=(dep_planned or dep_real).strftime("%H:%M"),
                real_time_str=dep_real.strftime("%H:%M"),
                delay_minutes=max(0, minutes_between(dep_real, dep_planned)),
                platform=str(start.get("platformName") or start.get("platform") or ""),
                countdown_minutes=max(0, int((dep_real - now).total_seconds() / 60)),
                raw_datetime=dep_real,
                line_id=str(diva.get("line") or ""),
                operator=str(diva.get("operator") or ""),
                realtime_source="efa" if str(first_mode.get("realtime") or "") == "1" else "",
                alerts=alerts,
            )
            trips.append(
                TransitTrip(
                    departure=departure,
                    arrival_stop=str(end.get("name") or ""),
                    arrival_planned_str=arr_planned.strftime("%H:%M") if arr_planned else "",
                    arrival_real_str=arr_real.strftime("%H:%M") if arr_real else "",
                    arrival_delay_minutes=max(0, minutes_between(arr_real, arr_planned)),
                    arrival_datetime=arr_real,
                    duration_minutes=max(0, minutes_between(arr_real, dep_real)),
                    interchanges=len(ridden) - 1,
                    lines=lines,
                )
            )
        return trips

    @classmethod
    def find_stops(cls, query: str, limit: int = TRANSIT_STOP_SUGGESTION_LIMIT) -> list[TransitStop] | None:
        """Stop suggestions for a partial name. Returns None when the service is unreachable."""
        query = query.strip()
        if not query:
            return []
        params = {
            "outputFormat": "JSON",
            "type_sf": "any",
            "name_sf": query,
            "anyObjFilter_sf": "2",  # stops only
            "anyMaxSizeHitList": str(limit),
            "locationServerActive": "1",
        }
        try:
            data = cls._request_json(TRANSIT_EFA_STOPFINDER_ENDPOINT, params)
        except Exception as e:
            logger.warning("Stop search failed: %s", e)
            return None
        return cls._parse_stop_points(data.get("stopFinder") or data)[:limit]

    @classmethod
    def check_stop(cls, stop_name: str, place: str) -> StopCheckResult:
        """Looks up the stop live, bypassing the cache, and reports whether it works."""
        try:
            data = cls._request_json(TRANSIT_EFA_ENDPOINT, cls._departure_params(stop_name, place, 10))
        except Exception as e:
            logger.warning("Stop check failed: %s", e)
            return StopCheckResult(status="error")

        departures = cls._parse_efa_response(data)
        raw_dm = data.get("dm")
        dm: dict[str, Any] = raw_dm if isinstance(raw_dm, dict) else {}
        candidates = cls._parse_stop_points(dm)
        raw_points = dm.get("points")
        ambiguous = isinstance(raw_points, list) and len(candidates) > 1

        if departures:
            resolved = departures[0].stop_name or (candidates[0].name if len(candidates) == 1 else stop_name)
            return StopCheckResult(status="ok", departure_count=len(departures), resolved_name=resolved)
        if ambiguous:
            return StopCheckResult(status="ambiguous", candidates=candidates)
        if candidates:
            return StopCheckResult(status="no_departures", resolved_name=candidates[0].name)
        return StopCheckResult(status="not_found")

    @staticmethod
    def _parse_stop_points(container: Any) -> list[TransitStop]:
        """Reads stop entries from an EFA stop finder (or ODV) block.

        EFA returns ``points`` as a list when several stops match, as
        ``{"point": {...}}`` for exactly one, and as null for none. The
        rapidJSON variant uses ``locations`` instead.
        """
        if not isinstance(container, dict):
            return []
        raw: Any = container.get("points")
        if isinstance(raw, dict):
            raw = raw.get("point")
        if isinstance(raw, dict):
            raw = [raw]
        if not isinstance(raw, list):
            raw = container.get("locations") if isinstance(container.get("locations"), list) else []

        stops: list[TransitStop] = []
        seen: set[tuple[str, str]] = set()
        for item in raw:
            if not isinstance(item, dict):
                continue
            kind = str(item.get("anyType") or item.get("type") or "stop").lower()
            if kind not in ("stop", "any"):
                continue
            raw_ref = item.get("ref")
            raw_parent = item.get("parent")
            ref: dict[str, Any] = raw_ref if isinstance(raw_ref, dict) else {}
            parent: dict[str, Any] = raw_parent if isinstance(raw_parent, dict) else {}
            full_name = str(item.get("name") or "").strip()
            name = str(item.get("object") or item.get("disassembledName") or "").strip()
            place = str(item.get("mainLoc") or ref.get("place") or parent.get("name") or "").strip()
            if not name and full_name:
                # "Neu-Ulm, Edisonallee" -> place "Neu-Ulm", name "Edisonallee"
                head, sep, tail = full_name.partition(", ")
                name, place = (tail, place or head) if sep else (full_name, place)
            if not name:
                continue
            key = (name.lower(), place.lower())
            if key in seen:
                continue
            seen.add(key)
            stops.append(TransitStop(name=name, place=place, stop_id=str(ref.get("id") or item.get("id") or "")))
        return stops

    @classmethod
    def _parse_efa_response(
        cls, data: dict[str, Any], trust_countdown: bool = True
    ) -> list[TransitDeparture]:
        """Parse raw EFA JSON dictionary into a list of TransitDeparture objects.

        trust_countdown: EFA counts its "countdown" from the *requested* time, so
        for a request with itdTime it is wrong (a 16:13 bus queried for 16:10
        shows "3 Min." at noon). Pass False then to count from now instead.
        """
        results: list[TransitDeparture] = []
        raw_list = data.get("departureList")
        if not raw_list:
            return results

        if isinstance(raw_list, dict):
            # When only one departure is returned, EFA sometimes wraps it in a single dict or sub-list
            entries = raw_list.get("departure", [])
            if isinstance(entries, dict):
                entries = [entries]
        elif isinstance(raw_list, list):
            entries = raw_list
        else:
            entries = []

        now = datetime.now()
        for item in entries:
            if not isinstance(item, dict):
                continue
            serving_line = item.get("servingLine") or {}
            line_number = str(serving_line.get("number") or serving_line.get("symbol") or "")
            raw_ids = serving_line.get("liErgRiProj")
            line_id = str(raw_ids.get("line") or "") if isinstance(raw_ids, dict) else ""
            raw_operator = item.get("operator")
            operator = str(raw_operator.get("name") or "") if isinstance(raw_operator, dict) else ""
            destination = str(serving_line.get("direction") or "")
            mot_type = str(serving_line.get("name") or "")
            delay = int(serving_line.get("delay") or 0)
            platform = str(item.get("platformName") or item.get("platform") or "")
            stop_id = str(item.get("stopID") or "")
            stop_name = str(item.get("stopName") or "")

            # Time parsing
            dt_dict = item.get("realDateTime") or item.get("dateTime") or {}
            year = int(dt_dict.get("year", now.year))
            month = int(dt_dict.get("month", now.month))
            day = int(dt_dict.get("day", now.day))
            hour = int(dt_dict.get("hour", now.hour))
            minute = int(dt_dict.get("minute", now.minute))

            try:
                dep_dt = datetime(year, month, day, hour, minute)
            except ValueError:
                dep_dt = now

            planned_dict = item.get("dateTime") or {}
            planned_h = int(planned_dict.get("hour", hour))
            planned_m = int(planned_dict.get("minute", minute))
            planned_str = f"{planned_h:02d}:{planned_m:02d}"
            real_str = f"{hour:02d}:{minute:02d}"

            # Countdown
            raw_countdown = item.get("countdown") if trust_countdown else None
            if raw_countdown is not None:
                try:
                    countdown = int(raw_countdown)
                except (ValueError, TypeError):
                    countdown = max(0, int((dep_dt - now).total_seconds() / 60))
            else:
                countdown = max(0, int((dep_dt - now).total_seconds() / 60))

            results.append(
                TransitDeparture(
                    stop_id=stop_id,
                    stop_name=stop_name,
                    line=line_number,
                    destination=destination,
                    mot_type=mot_type,
                    planned_time_str=planned_str,
                    real_time_str=real_str,
                    delay_minutes=delay,
                    platform=platform,
                    countdown_minutes=countdown,
                    raw_datetime=dep_dt,
                    line_id=line_id,
                    operator=operator,
                    realtime_source="efa" if str(serving_line.get("realtime") or "") == "1" and item.get("realDateTime") else "",
                    alerts=parse_efa_infos(item.get("lineInfos"), line=line_number, line_id=line_id)
                    + parse_efa_infos(item.get("tripInfos"), line=line_number, line_id=line_id)
                    + parse_efa_infos(item.get("stopInfos"), stop_name=stop_name),
                )
            )
        return results

    @classmethod
    def calculate_leave_info(
        cls,
        departure: TransitDeparture,
        walk_min: int,
        logout_min: int,
        pack_min: int,
        buffer_min: int,
        now: datetime | None = None,
    ) -> dict[str, Any]:
        """Calculate lead times, leave deadline, countdown, and alarm urgency for a departure."""
        if now is None:
            now = datetime.now()

        total_lead = max(0, walk_min + logout_min + pack_min + buffer_min)

        if departure.raw_datetime is not None:
            dep_dt = departure.raw_datetime
        else:
            try:
                parts = departure.real_time_str.split(":")
                dep_dt = now.replace(hour=int(parts[0]), minute=int(parts[1]), second=0, microsecond=0)
            except Exception:
                dep_dt = now + timedelta(minutes=departure.countdown_minutes)

        leave_dt = dep_dt - timedelta(minutes=total_lead)
        seconds_until_leave = (leave_dt - now).total_seconds()
        minutes_until_leave = int(seconds_until_leave // 60)

        pack_lead = max(0, walk_min + logout_min + pack_min + buffer_min)
        logout_lead = max(0, walk_min + logout_min + buffer_min)
        walk_lead = max(0, walk_min + buffer_min)

        pack_dt = dep_dt - timedelta(minutes=pack_lead)
        logout_dt = dep_dt - timedelta(minutes=logout_lead)
        walk_dt = dep_dt - timedelta(minutes=walk_lead)

        minutes_until_pack = int((pack_dt - now).total_seconds() // 60)
        minutes_until_logout = int((logout_dt - now).total_seconds() // 60)
        minutes_until_walk = int((walk_dt - now).total_seconds() // 60)

        seconds_until_dep = (dep_dt - now).total_seconds()
        minutes_until_dep = int(seconds_until_dep // 60)

        if minutes_until_dep < 0:
            status = "departed"
            is_due = False
        elif minutes_until_leave <= CHECKOUT_ALARM_URGENT_THRESHOLD_MINUTES:
            status = "urgent"
            is_due = minutes_until_leave <= 0
        elif minutes_until_leave <= CHECKOUT_ALARM_WARN_THRESHOLD_MINUTES:
            status = "warn"
            is_due = False
        else:
            status = "ok"
            is_due = False

        return {
            "total_lead_minutes": total_lead,
            "leave_datetime": leave_dt,
            "leave_time_str": leave_dt.strftime("%H:%M"),
            "minutes_until_leave": minutes_until_leave,
            "minutes_until_dep": minutes_until_dep,
            "status": status,
            "is_alarm_due": is_due,
            "pack_time_str": pack_dt.strftime("%H:%M"),
            "logout_time_str": logout_dt.strftime("%H:%M"),
            "walk_time_str": walk_dt.strftime("%H:%M"),
            "dep_time_str": dep_dt.strftime("%H:%M"),
            "minutes_until_pack": minutes_until_pack,
            "minutes_until_logout": minutes_until_logout,
            "minutes_until_walk": minutes_until_walk,
        }

