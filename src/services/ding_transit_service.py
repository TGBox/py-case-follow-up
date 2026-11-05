"""DING transit service for live departures and departure alarms in the Ulm / Neu-Ulm region.

Uses the standardized bwegt / EFA-BW JSON endpoint covering the DING network.
Provides error-resilient fetching, parsing, caching, and commute alarm calculations.
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
    TRANSIT_STOP_SUGGESTION_LIMIT,
    TRANSIT_REQUEST_TIMEOUT_SECONDS,
)

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


@dataclass
class TransitStop:
    """A stop suggestion from the EFA stop finder."""

    name: str
    place: str
    stop_id: str = ""


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

    @staticmethod
    def _request_json(endpoint: str, params: dict[str, str]) -> dict[str, Any]:
        url = f"{endpoint}?{urllib.parse.urlencode(params)}"
        req = urllib.request.Request(
            url,
            headers={"User-Agent": "SupportCockpit/1.0 (DingTransitService)"},
        )
        with urllib.request.urlopen(req, timeout=TRANSIT_REQUEST_TIMEOUT_SECONDS) as resp:
            data = json.loads(resp.read().decode("utf-8"))
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
            return list(cls._cached_departures)

        try:
            data = cls._request_json(
                TRANSIT_EFA_ENDPOINT, cls._departure_params(stop_name, place, limit, departure_time)
            )
            parsed = cls._parse_efa_response(data, trust_countdown=departure_time is None)
            cls._cached_departures = parsed
            cls._last_fetch_time = now
            cls._cached_stop_key = stop_key
            return parsed
        except Exception as e:
            logger.warning("Failed to fetch DING live departures: %s", e)
            return list(cls._cached_departures)

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
            serving_line = item.get("servingLine", {})
            line_number = str(serving_line.get("number") or serving_line.get("symbol") or "")
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

