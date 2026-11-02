"""DING transit service for live departures and departure alarms in the Ulm / Neu-Ulm region.

Uses the standardized bwegt / EFA-BW JSON endpoint covering the DING network.
Provides error-resilient fetching, parsing, caching, and commute alarm calculations.
"""

from __future__ import annotations

import json
import logging
import urllib.parse
import urllib.request
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Any

from constants import (
    CHECKOUT_ALARM_URGENT_THRESHOLD_MINUTES,
    CHECKOUT_ALARM_WARN_THRESHOLD_MINUTES,
    TRANSIT_DEFAULT_STOP_NAME,
    TRANSIT_DEFAULT_STOP_PLACE,
    TRANSIT_EFA_ENDPOINT,
    TRANSIT_REQUEST_TIMEOUT_SECONDS,
)

logger = logging.getLogger(__name__)


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


class DingTransitService:
    """Service to fetch and calculate live transit departures and commute alarms."""

    _cached_departures: list[TransitDeparture] = []
    _last_fetch_time: datetime | None = None
    _cache_ttl_seconds: float = 30.0

    @classmethod
    def fetch_departures(
        cls,
        stop_name: str = TRANSIT_DEFAULT_STOP_NAME,
        place: str = TRANSIT_DEFAULT_STOP_PLACE,
        limit: int = 15,
        force_refresh: bool = False,
    ) -> list[TransitDeparture]:
        """Fetch live departures from the EFA endpoint for the given stop and place."""
        now = datetime.now()
        if (
            not force_refresh
            and cls._last_fetch_time is not None
            and (now - cls._last_fetch_time).total_seconds() < cls._cache_ttl_seconds
            and cls._cached_departures
        ):
            return list(cls._cached_departures)

        params = {
            "outputFormat": "JSON",
            "type_dm": "stop",
            "name_dm": stop_name,
            "place_dm": place,
            "useRealtime": "1",
            "mode": "direct",
            "limit": str(limit),
        }
        url = f"{TRANSIT_EFA_ENDPOINT}?{urllib.parse.urlencode(params)}"

        try:
            req = urllib.request.Request(
                url,
                headers={"User-Agent": "SupportCockpit/1.0 (DingTransitService)"},
            )
            with urllib.request.urlopen(req, timeout=TRANSIT_REQUEST_TIMEOUT_SECONDS) as resp:
                data = json.loads(resp.read().decode("utf-8"))

            parsed = cls._parse_efa_response(data)
            cls._cached_departures = parsed
            cls._last_fetch_time = now
            return parsed
        except Exception as e:
            logger.warning("Failed to fetch DING live departures: %s", e)
            return list(cls._cached_departures)

    @classmethod
    def _parse_efa_response(cls, data: dict[str, Any]) -> list[TransitDeparture]:
        """Parse raw EFA JSON dictionary into a list of TransitDeparture objects."""
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
            raw_countdown = item.get("countdown")
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
        }

