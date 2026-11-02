"""Weather service for commute conditions and umbrella forecasts.

Queries Open-Meteo API (free, open, keyless) for Ulm / Neu-Ulm coordinates.
"""

from __future__ import annotations

import json
import logging
import urllib.parse
import urllib.request
from dataclasses import dataclass
from datetime import datetime
from typing import Any

from constants import (
    WEATHER_DEFAULT_LATITUDE,
    WEATHER_DEFAULT_LONGITUDE,
    WEATHER_OPEN_METEO_ENDPOINT,
    WEATHER_REQUEST_TIMEOUT_SECONDS,
)

logger = logging.getLogger(__name__)

# WMO Weather interpretation codes (WW) to German description
WMO_WEATHER_CODES: dict[int, str] = {
    0: "Klarer Himmel ☀",
    1: "Hauptsächlich klar 🌤",
    2: "Teilweise bewölkt ⛅",
    3: "Bedeckt ☁",
    45: "Nebel 🌫",
    48: "Raureif-Nebel 🌫",
    51: "Leichter Nieselregen 🌦",
    53: "Mäßiger Nieselregen 🌧",
    55: "Dichter Nieselregen 🌧",
    61: "Leichter Regen 🌧",
    63: "Mäßiger Regen 🌧",
    65: "Starker Regen 🌧",
    71: "Leichter Schneefall 🌨",
    73: "Mäßiger Schneefall 🌨",
    75: "Starker Schneefall ❄",
    77: "Schneegriesel ❄",
    80: "Leichte Regenschauer 🌦",
    81: "Mäßige Regenschauer 🌧",
    82: "Heftige Regenschauer 🌧",
    85: "Leichte Schneeschauer 🌨",
    86: "Starke Schneeschauer ❄",
    95: "Gewitter ⛈",
    96: "Gewitter mit leichtem Hagel ⛈",
    99: "Gewitter mit schwerem Hagel ⛈",
}


@dataclass
class WeatherInfo:
    temperature: float
    condition_code: int
    condition_text: str
    rain_probability_max: int
    umbrella_recommended: bool


class WeatherService:
    """Provides weather forecasting for the commute home."""

    _cached_weather: WeatherInfo | None = None
    _last_fetch_time: datetime | None = None
    _cache_ttl_seconds: float = 900.0  # 15 minutes

    @classmethod
    def fetch_weather(
        cls,
        lat: float = WEATHER_DEFAULT_LATITUDE,
        lon: float = WEATHER_DEFAULT_LONGITUDE,
        force_refresh: bool = False,
    ) -> WeatherInfo:
        """Fetch current weather and rain probability for the commute."""
        now = datetime.now()
        if (
            not force_refresh
            and cls._last_fetch_time is not None
            and (now - cls._last_fetch_time).total_seconds() < cls._cache_ttl_seconds
            and cls._cached_weather is not None
        ):
            return cls._cached_weather

        params = {
            "latitude": f"{lat:.4f}",
            "longitude": f"{lon:.4f}",
            "current": "temperature_2m,weather_code",
            "hourly": "precipitation_probability,weather_code",
            "forecast_days": "1",
            "timezone": "Europe/Berlin",
        }
        url = f"{WEATHER_OPEN_METEO_ENDPOINT}?{urllib.parse.urlencode(params)}"

        try:
            req = urllib.request.Request(
                url,
                headers={"User-Agent": "SupportCockpit/1.0 (WeatherService)"},
            )
            with urllib.request.urlopen(req, timeout=WEATHER_REQUEST_TIMEOUT_SECONDS) as resp:
                data = json.loads(resp.read().decode("utf-8"))

            parsed = cls._parse_weather_response(data)
            cls._cached_weather = parsed
            cls._last_fetch_time = now
            return parsed
        except Exception as e:
            logger.warning("Failed to fetch commute weather: %s", e)
            if cls._cached_weather is not None:
                return cls._cached_weather
            return WeatherInfo(
                temperature=15.0,
                condition_code=0,
                condition_text="Wetterdaten nicht verfügbar",
                rain_probability_max=0,
                umbrella_recommended=False,
            )

    @classmethod
    def _parse_weather_response(cls, data: dict[str, Any]) -> WeatherInfo:
        current = data.get("current", {})
        temp = float(current.get("temperature_2m", 15.0))
        code = int(current.get("weather_code", 0))
        cond_text = WMO_WEATHER_CODES.get(code, "Bewölkt ⛅")

        hourly = data.get("hourly", {})
        rain_probs = hourly.get("precipitation_probability", [])
        if rain_probs and isinstance(rain_probs, list):
            # Take max rain probability over the afternoon/evening hours (e.g. from now until 22:00)
            now_hour = datetime.now().hour
            future_probs = rain_probs[now_hour : min(now_hour + 6, len(rain_probs))]
            max_prob = max(future_probs) if future_probs else 0
        else:
            max_prob = 0

        # Umbrella recommended if rain probability >= 35% or current code is rain/drizzle/shower/thunderstorm
        umbrella = max_prob >= 35 or code in {51, 53, 55, 61, 63, 65, 80, 81, 82, 95, 96, 99}

        return WeatherInfo(
            temperature=round(temp, 1),
            condition_code=code,
            condition_text=cond_text,
            rain_probability_max=int(max_prob),
            umbrella_recommended=umbrella,
        )
