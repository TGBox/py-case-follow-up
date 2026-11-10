"""Traffic notices for the ÖPNV tab: DING notices (from EFA and ding.eu) and SWU disruptions.

Three sources end up as one list of TransitAlert:
- EFA (bwegt) sends the DING EMS notices along with every departure and trip
  (stopInfos / lineInfos / tripInfos, legs' infos). No extra request.
- ding.eu/Verkehrsmeldungen lists all DING notices with their validity and
  the lines (incl. DING line id) and stops they affect, as data attributes.
- SWU publishes short-notice disruptions of its own buses and trams.

Notices that come from several sources are merged by title. A notice is shown
on a departure when it names that line (line notices), and in the notice list
when it affects a listed departure or the configured stop.
"""

from __future__ import annotations

import dataclasses
import html
import json
import logging
import re
import urllib.parse
import urllib.request
from dataclasses import dataclass
from datetime import date, datetime
from html.parser import HTMLParser
from typing import TYPE_CHECKING, Any

from constants import (
    TRANSIT_ALERT_CACHE_TTL_SECONDS,
    TRANSIT_ALERT_TEXT_MAX_CHARS,
    TRANSIT_DING_NOTICES_URL,
    TRANSIT_REQUEST_TIMEOUT_SECONDS,
    TRANSIT_SWU_ALERT_CACHE_TTL_SECONDS,
    TRANSIT_SWU_REQUEST_TIMEOUT_SECONDS,
    TRANSIT_SWU_STOP_ALERT_ENDPOINT,
    TRANSIT_SWU_UNPLANNED_ALERT_ENDPOINT,
)

if TYPE_CHECKING:
    from services.ding_transit_service import TransitDeparture

logger = logging.getLogger("SupportCockpit.transit.alerts")

SCOPE_LINE = "line"
SCOPE_STOP = "stop"
SCOPE_NETWORK = "network"
_PRIORITY_ORDER = {"veryhigh": 0, "high": 1, "normal": 2, "low": 3}
_SWU_OPERATOR = "swu"


def norm_line(text: str) -> str:
    """'Linie 4' / ' 4 ' / 'N7' -> '4' / '4' / 'n7'."""
    text = (text or "").strip().lower()
    text = re.sub(r"^(linie|line|bus|tram)\s+", "", text)
    return re.sub(r"\s+", "", text)


def norm_stop(text: str) -> str:
    """'Ulm, Ehinger Tor' / 'Ulm Ehinger Tor' -> 'ulm ehinger tor'."""
    return re.sub(r"[^0-9a-zäöüß]+", " ", (text or "").lower()).strip()


def html_to_text(raw: str) -> str:
    """Plain text from an HTML snippet: tags become spaces, entities are decoded."""
    text = re.sub(r"<(br|/p|/div|/li)\b[^>]*>", "\n", raw or "", flags=re.IGNORECASE)
    text = re.sub(r"<li\b[^>]*>", "\n• ", text, flags=re.IGNORECASE)
    text = re.sub(r"<[^>]+>", " ", text)
    text = html.unescape(text).replace("\xa0", " ")
    lines = [re.sub(r"[ \t]+", " ", line).strip() for line in text.splitlines()]
    text = "\n".join(line for line in lines if line)
    if len(text) > TRANSIT_ALERT_TEXT_MAX_CHARS:
        text = text[: TRANSIT_ALERT_TEXT_MAX_CHARS - 1].rstrip() + "…"
    return text


@dataclass
class TransitAlert:
    alert_id: str
    source: str  # "ding" or "swu"
    title: str
    text: str = ""
    scope: str = SCOPE_LINE
    lines: frozenset[str] = frozenset()  # normalized line numbers
    line_ids: frozenset[str] = frozenset()  # DING line ids, e.g. "87004" for SWU line 4
    stops: frozenset[str] = frozenset()  # normalized stop names
    operator: str = ""  # set for SWU notices that name lines: they only apply to SWU vehicles
    valid_from: date | None = None
    valid_until: date | None = None
    priority: str = "normal"

    @property
    def key(self) -> str:
        """Merge key: the same notice from EFA and ding.eu carries the same title."""
        return norm_stop(self.title)[:120] or self.alert_id

    def is_valid_on(self, day: date) -> bool:
        if self.valid_from and day < self.valid_from:
            return False
        if self.valid_until and day > self.valid_until:
            return False
        return True

    def affects_line_of(self, dep: TransitDeparture) -> bool:
        """True when this notice names the line dep runs on."""
        if not self.lines and not self.line_ids:
            return False
        number = norm_line(dep.line)
        if self.line_ids:
            # Line numbers repeat across the network (line 4 in Ulm and in Biberach), the DING id does not.
            if not dep.line_id or dep.line_id not in self.line_ids:
                return False
            return not self.lines or number in self.lines
        if self.operator and self.operator != (dep.operator or "").strip().lower():
            return False
        return number in self.lines

    def touches_stop(self, stop_keys: set[str]) -> bool:
        return bool(self.stops & stop_keys)

    def merged_with(self, other: TransitAlert) -> TransitAlert:
        return dataclasses.replace(
            self,
            text=self.text if len(self.text) >= len(other.text) else other.text,
            lines=self.lines | other.lines,
            line_ids=self.line_ids | other.line_ids,
            stops=self.stops | other.stops,
            valid_from=self.valid_from or other.valid_from,
            valid_until=self.valid_until or other.valid_until,
            scope=SCOPE_LINE if SCOPE_LINE in (self.scope, other.scope) else self.scope,
            priority=min(self.priority, other.priority, key=lambda p: _PRIORITY_ORDER.get(p.lower(), 9)),
        )


# --- EFA (bwegt) ---------------------------------------------------------------------------------


def _efa_info_objects(raw: Any) -> list[dict[str, Any]]:
    """EFA nests notices as {"lineInfo": {...}}, {"lineInfo": [...]}, {"info": ...} or a list of those."""
    found: list[dict[str, Any]] = []
    if isinstance(raw, list):
        for item in raw:
            found.extend(_efa_info_objects(item))
    elif isinstance(raw, dict):
        if "infoText" in raw or "infoLinkText" in raw:
            found.append(raw)
        else:
            for value in raw.values():
                if isinstance(value, (dict, list)):
                    found.extend(_efa_info_objects(value))
    return found


def _efa_params(info: dict[str, Any]) -> dict[str, str]:
    params = info.get("paramList")
    if isinstance(params, dict):
        params = [params]
    result: dict[str, str] = {}
    for p in params if isinstance(params, list) else []:
        if isinstance(p, dict) and p.get("name"):
            result[str(p["name"])] = str(p.get("value") or "")
    return result


def parse_efa_infos(
    raw: Any,
    line: str = "",
    line_id: str = "",
    stop_name: str = "",
) -> list[TransitAlert]:
    """Notices from an EFA infos block of one departure or trip leg.

    A line or trip notice is tied to the line it came with, a stop notice to the stop.
    """
    alerts: list[TransitAlert] = []
    for info in _efa_info_objects(raw):
        params = _efa_params(info)
        raw_text = info.get("infoText")
        text_block: dict[str, Any] = raw_text if isinstance(raw_text, dict) else {}
        title = str(info.get("infoLinkText") or text_block.get("subtitle") or "").strip()
        body = html_to_text(str(text_block.get("htmlText") or text_block.get("content") or ""))
        if not title and not body:
            continue
        info_type = params.get("infoType", "").lower()
        is_stop = info_type == "stopinfo"
        alerts.append(
            TransitAlert(
                alert_id=params.get("infoID") or f"efa:{norm_stop(title)[:60]}",
                source="ding",
                title=title or body.split("\n", 1)[0][:120],
                text=body,
                scope=SCOPE_STOP if is_stop else SCOPE_LINE,
                lines=frozenset() if is_stop or not line else frozenset({norm_line(line)}),
                line_ids=frozenset() if is_stop or not line_id else frozenset({line_id}),
                stops=frozenset({norm_stop(stop_name)}) if is_stop and stop_name else frozenset(),
                priority=params.get("priority") or "normal",
            )
        )
    return alerts


# --- ding.eu -----------------------------------------------------------------------------------


class _DingNoticeParser(HTMLParser):
    """Reads the <article class="c-detail-list-card"> cards of ding.eu/Verkehrsmeldungen."""

    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.cards: list[dict[str, Any]] = []
        self._card: dict[str, Any] | None = None
        self._depth = 0
        self._capture: str | None = None
        self._capture_depth = 0

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        a = {k: (v or "") for k, v in attrs}
        classes = a.get("class", "").split()
        if self._card is None:
            if tag == "article" and "c-detail-list-card" in classes:
                self._card = {"attrs": a, "title": [], "text": []}
                self._depth = 1
            return
        if tag in ("br", "img", "input", "meta", "link", "hr", "source", "path", "rect", "polyline"):
            if tag == "br" and self._capture == "text":
                self._card["text"].append("\n")
            return
        self._depth += 1
        if self._capture is None:
            if "c-detail-list-card__full-title" in classes:
                self._capture, self._capture_depth = "title", self._depth
            elif "c-detail-list-card__content" in classes:
                self._capture, self._capture_depth = "text", self._depth
        elif self._capture == "text" and tag in ("p", "div", "li"):
            self._card["text"].append("\n• " if tag == "li" else "\n")

    def handle_startendtag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if self._card is not None and tag == "br" and self._capture == "text":
            self._card["text"].append("\n")

    def handle_endtag(self, tag: str) -> None:
        if self._card is None:
            return
        if tag in ("br", "img", "input", "meta", "link", "hr", "source", "path", "rect", "polyline"):
            return
        if self._capture is not None and self._depth == self._capture_depth:
            self._capture = None
        self._depth -= 1
        if self._depth <= 0:
            self.cards.append(self._card)
            self._card = None

    def handle_data(self, data: str) -> None:
        if self._card is not None and self._capture is not None:
            self._card[self._capture].append(data)


def _json_list(raw: str) -> list[str]:
    try:
        value = json.loads(raw or "[]")
    except ValueError:
        return []
    return [str(v) for v in value] if isinstance(value, list) else []


def _iso_date(raw: str) -> date | None:
    try:
        return date.fromisoformat(raw.strip()) if raw and raw.strip() else None
    except ValueError:
        return None


def parse_ding_notices(page: str) -> list[TransitAlert]:
    parser = _DingNoticeParser()
    parser.feed(page or "")
    parser.close()
    alerts: list[TransitAlert] = []
    for card in parser.cards:
        attrs = card["attrs"]
        title = re.sub(r"\s+", " ", "".join(card["title"])).strip()
        text = html_to_text("".join(card["text"]).replace("\n", "<br>"))
        lines: set[str] = set()
        line_ids: set[str] = set()
        for entry in _json_list(attrs.get("data-lines", "")):
            # "4|stadtbus ul/nu|din|87004": number | product | network | DING line id
            parts = entry.split("|")
            if parts and parts[0].strip():
                lines.add(norm_line(parts[0]))
            if len(parts) >= 4 and parts[3].strip():
                line_ids.add(parts[3].strip())
        stops = {norm_stop(s) for s in _json_list(attrs.get("data-stops", "")) if s.strip()}
        if not title:
            continue
        alerts.append(
            TransitAlert(
                alert_id=f"ding:{norm_stop(title)[:80]}:{attrs.get('data-valid-from', '')}",
                source="ding",
                title=title,
                text=text,
                scope=SCOPE_LINE if lines else SCOPE_STOP if stops else SCOPE_NETWORK,
                lines=frozenset(lines),
                line_ids=frozenset(line_ids),
                stops=frozenset(stops),
                valid_from=_iso_date(attrs.get("data-valid-from", "")),
                valid_until=_iso_date(attrs.get("data-valid-until", "")),
            )
        )
    return alerts


# --- SWU ----------------------------------------------------------------------------------------

_SWU_TITLE_KEYS = ("AlertTitle", "Title", "Header", "Headline", "Subject", "AlertHeader")
_SWU_TEXT_KEYS = ("AlertText", "Text", "Content", "Message", "Description", "AlertDescription")


def _swu_alert_items(raw: Any) -> list[Any]:
    """The alert entries of an SWU answer, whatever wrapper they come in.

    UnplannedAlert: {"PassengerAlert": []} when quiet, {"PassengerAlert": {"AlertData": [...]}} otherwise;
    TDI PassengerAlert: {"PassengerAlert": {"State": ..., "PassengerAlertStop": [...]}}.
    """
    if isinstance(raw, list):
        return raw
    if not isinstance(raw, dict):
        return []
    items: list[Any] = []
    for key, value in raw.items():
        if key in ("State", "Type", "StopNumber", "StopName", "VehicleNumber"):
            continue
        if isinstance(value, list) and (key == "AlertData" or key.startswith("PassengerAlert")):
            items.extend(value)
        elif isinstance(value, dict):
            items.extend(_swu_alert_items(value))
    return items


def _collect_route_numbers(item: dict[str, Any]) -> set[str]:
    lines: set[str] = set()
    for key, value in item.items():
        if "route" not in key.lower() or "direction" in key.lower():
            continue
        values = value if isinstance(value, list) else [value]
        for v in values:
            if isinstance(v, dict):
                v = v.get("RouteName") or v.get("RouteNumber")
            if isinstance(v, (int, str)) and str(v).strip():
                lines.add(norm_line(str(v)))
    return lines


def parse_swu_alerts(data: Any, stop_name: str = "") -> list[TransitAlert]:
    """SWU disruptions. Without named lines a notice counts for the stop it was asked for, else for the whole network."""
    root = data.get("PassengerAlert") if isinstance(data, dict) else data
    alerts: list[TransitAlert] = []
    for item in _swu_alert_items(root):
        if isinstance(item, str):
            title, body, lines = "", html_to_text(item), set()
        elif isinstance(item, dict):
            title = next((html_to_text(str(item[k])) for k in _SWU_TITLE_KEYS if item.get(k)), "")
            body = next((html_to_text(str(item[k])) for k in _SWU_TEXT_KEYS if item.get(k)), "")
            lines = _collect_route_numbers(item)
        else:
            continue
        if not title and not body:
            continue
        title = title or body.split("\n", 1)[0][:120]
        scope = SCOPE_LINE if lines else SCOPE_STOP if stop_name else SCOPE_NETWORK
        alerts.append(
            TransitAlert(
                alert_id=f"swu:{norm_stop(title)[:80]}",
                source="swu",
                title=title,
                text=body if body != title else "",
                scope=scope,
                lines=frozenset(lines),
                stops=frozenset({norm_stop(stop_name)}) if scope == SCOPE_STOP else frozenset(),
                operator=_SWU_OPERATOR if lines else "",
                priority="high",
            )
        )
    return alerts


# --- service ------------------------------------------------------------------------------------


class TransitAlertService:
    _ding_cache: tuple[datetime, list[TransitAlert]] | None = None
    _swu_cache: dict[str, tuple[datetime, list[TransitAlert]]] = {}

    @staticmethod
    def _request_text(url: str, timeout: float) -> str:
        req = urllib.request.Request(url, headers={"User-Agent": "SupportCockpit/1.0 (TransitAlertService)"})
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            return resp.read().decode("utf-8", errors="replace")

    @classmethod
    def fetch_ding_notices(cls, now: datetime | None = None) -> list[TransitAlert]:
        now = now or datetime.now()
        if cls._ding_cache and (now - cls._ding_cache[0]).total_seconds() < TRANSIT_ALERT_CACHE_TTL_SECONDS:
            return list(cls._ding_cache[1])
        try:
            alerts = parse_ding_notices(cls._request_text(TRANSIT_DING_NOTICES_URL, TRANSIT_REQUEST_TIMEOUT_SECONDS))
        except Exception as e:
            logger.info("DING notices not available: %s", e)
            return list(cls._ding_cache[1]) if cls._ding_cache else []
        cls._ding_cache = (now, alerts)
        return list(alerts)

    @classmethod
    def _fetch_swu(cls, cache_key: str, url: str, stop_name: str, now: datetime) -> list[TransitAlert]:
        cached = cls._swu_cache.get(cache_key)
        if cached and (now - cached[0]).total_seconds() < TRANSIT_SWU_ALERT_CACHE_TTL_SECONDS:
            return list(cached[1])
        try:
            data = json.loads(cls._request_text(url, TRANSIT_SWU_REQUEST_TIMEOUT_SECONDS), strict=False)
        except Exception as e:
            logger.info("SWU disruptions not available (%s): %s", cache_key, e)
            return list(cached[1]) if cached else []
        alerts = parse_swu_alerts(data, stop_name=stop_name)
        cls._swu_cache[cache_key] = (now, alerts)
        return list(alerts)

    @classmethod
    def fetch_swu_alerts(cls, stop_numbers: dict[int, str], now: datetime | None = None) -> list[TransitAlert]:
        """Network-wide SWU disruptions plus those for the given SWU stops ({number: stop name})."""
        now = now or datetime.now()
        alerts = cls._fetch_swu("unplanned", f"{TRANSIT_SWU_UNPLANNED_ALERT_ENDPOINT}?ContentScope=extended", "", now)
        for number, name in stop_numbers.items():
            url = f"{TRANSIT_SWU_STOP_ALERT_ENDPOINT}?{urllib.parse.urlencode({'StopNumber': number})}"
            alerts.extend(cls._fetch_swu(f"stop:{number}", url, name, now))
        return alerts

    @staticmethod
    def merge(alerts: list[TransitAlert]) -> list[TransitAlert]:
        merged: dict[str, TransitAlert] = {}
        for alert in alerts:
            existing = merged.get(alert.key)
            merged[alert.key] = existing.merged_with(alert) if existing else alert
        return list(merged.values())

    @staticmethod
    def _sort_key(alert: TransitAlert) -> tuple[int, int, str]:
        scope_rank = {SCOPE_STOP: 0, SCOPE_LINE: 1, SCOPE_NETWORK: 2}.get(alert.scope, 3)
        return (_PRIORITY_ORDER.get(alert.priority.lower(), 9), scope_rank, alert.title.lower())

    @classmethod
    def assign(
        cls,
        deps: list[TransitDeparture],
        pool: list[TransitAlert],
        stop_name: str,
        stop_place: str = "",
        today: date | None = None,
    ) -> tuple[list[TransitDeparture], list[TransitAlert]]:
        """Puts each valid notice on the departures whose line it names and returns the notices worth listing.

        Listed are notices that hit a shown departure or the configured stop, and
        SWU network-wide disruptions when SWU buses are shown. Notices about the
        configured stop itself (e.g. a rebuilt stop naming every line that serves
        it) are listed but not put on every single departure: the ⚠ on a row is
        kept for trouble somewhere else on that line.
        """
        today = today or date.today()
        valid = [a for a in cls.merge(pool) if a.is_valid_on(today)]
        stop_keys = {norm_stop(stop_name)} | {norm_stop(d.stop_name) for d in deps if d.stop_name}
        if stop_place and norm_stop(stop_place) not in norm_stop(stop_name):
            stop_keys.add(norm_stop(f"{stop_place} {stop_name}"))
        stop_keys.discard("")

        new_deps: list[TransitDeparture] = []
        listed: dict[str, TransitAlert] = {}
        row_candidates = [a for a in valid if a.scope != SCOPE_STOP and not a.touches_stop(stop_keys)]
        for dep in deps:
            own_keys = {a.key for a in dep.alerts if a.scope != SCOPE_STOP}
            hits = [a for a in row_candidates if a.key in own_keys or a.affects_line_of(dep)]
            hits.sort(key=cls._sort_key)
            new_deps.append(dataclasses.replace(dep, alerts=hits))
            for a in hits:
                listed[a.key] = a
        shows_swu = any((d.operator or "").strip().lower() == _SWU_OPERATOR for d in deps)
        for a in valid:
            if a.touches_stop(stop_keys) or (a.source == "swu" and a.scope == SCOPE_NETWORK and shows_swu):
                listed.setdefault(a.key, a)
        return new_deps, sorted(listed.values(), key=cls._sort_key)

    @classmethod
    def collect(
        cls,
        deps: list[TransitDeparture],
        stop_name: str,
        stop_place: str = "",
        include_ding: bool = True,
        include_swu: bool = True,
    ) -> tuple[list[TransitDeparture], list[TransitAlert]]:
        """Fetches the notice sources and assigns them. Never raises: on any error the departures come back unchanged."""
        try:
            pool: list[TransitAlert] = [a for d in deps for a in d.alerts]
            if include_ding:
                pool.extend(cls.fetch_ding_notices())
            if include_swu:
                from services.swu_realtime_service import SwuRealtimeService

                numbers: dict[int, str] = {}
                for d in deps:
                    n = SwuRealtimeService.stop_number_for_efa_id(d.stop_id)
                    if n is not None and (d.operator or "").strip().lower() == _SWU_OPERATOR:
                        numbers.setdefault(n, d.stop_name)
                if numbers or any((d.operator or "").strip().lower() == _SWU_OPERATOR for d in deps):
                    pool.extend(cls.fetch_swu_alerts(numbers))
            return cls.assign(deps, pool, stop_name, stop_place)
        except Exception as e:
            logger.warning("Collecting traffic notices failed: %s", e)
            return list(deps), []
