"""Date and time parsing, formatting, and localization utilities."""

from datetime import datetime, date, timezone
import re
from constants import ISO_DATETIME_FORMAT
from services.i18n_service import tr


def get_local_now() -> datetime:
    """Returns the current timezone-aware local datetime."""
    return datetime.now().astimezone()


def now_iso() -> str:
    """Returns current ISO 8601 formatted string (YYYY-MM-DDTHH:MM:SS)."""
    return get_local_now().strftime(ISO_DATETIME_FORMAT)


def parse_iso(iso_str: str) -> datetime:
    """Parses ISO string to timezone-aware datetime.
    If string is naive ISO format (no timezone), attaches local timezone.
    """
    if not iso_str:
        raise ValueError("ISO datetime string cannot be empty.")
    
    cleaned = iso_str.strip()
    dt = datetime.fromisoformat(cleaned)
    if dt.tzinfo is None:
        local_tz = get_local_now().tzinfo
        dt = dt.replace(tzinfo=local_tz)
    return dt


def format_iso(dt: datetime) -> str:
    """Formats datetime object to standard ISO string."""
    return dt.strftime("%Y-%m-%dT%H:%M:%S")


def calculate_idle_days(updated_at_str: str, now: datetime | None = None) -> float:
    """Calculates difference in fractional days between updated_at and now."""
    if not updated_at_str:
        return 0.0
    
    ref_now = now or get_local_now()
    if ref_now.tzinfo is None:
        ref_now = ref_now.replace(tzinfo=get_local_now().tzinfo)
        
    updated_dt = parse_iso(updated_at_str)
    diff_seconds = (ref_now - updated_dt).total_seconds()
    if diff_seconds < 0:
        return 0.0
    return diff_seconds / 86400.0


def hours_until_deadline(deadline_str: str, now: datetime | None = None) -> float:
    """Calculates remaining hours until deadline (negative if overdue)."""
    if not deadline_str:
        return float("inf")
    
    ref_now = now or get_local_now()
    if ref_now.tzinfo is None:
        ref_now = ref_now.replace(tzinfo=get_local_now().tzinfo)

    deadline_dt = parse_iso(deadline_str)
    return (deadline_dt - ref_now).total_seconds() / 3600.0


def format_german_date(val: str | datetime | None) -> str:
    """Formats ISO string or datetime to date format DD.MM.YYYY."""
    if not val:
        return ""
    if isinstance(val, datetime):
        return val.strftime("%d.%m.%Y")
    val_str = val.strip()
    if not val_str:
        return ""
    try:
        dt = parse_iso(val_str)
        return dt.strftime("%d.%m.%Y")
    except Exception:
        if re.match(r"^\d{2}\.\d{2}\.\d{4}", val_str):
            return val_str[:10]
        return val_str


def get_relative_date_text(val: str | datetime | None, ref_date: date | datetime | None = None) -> str:
    """Calculates dynamically localized relative date description e.g.
    'heute'/'today'/'idag', 'morgen'/'tomorrow'/'imorgon', 'in X Tagen'/'in X days'/'om X dagar'.
    """
    if not val:
        return ""
    try:
        if isinstance(val, datetime):
            target_dt = val
        elif isinstance(val, date):
            target_dt = datetime.combine(val, datetime.min.time())
        else:
            val_str = val.strip()
            if not val_str:
                return ""
            target_dt = parse_iso(val_str)
    except Exception:
        clean = re.sub(r"\s*(Uhr|kl\.?)\s*$", "", val, flags=re.IGNORECASE).strip() if isinstance(val, str) else ""
        if re.match(r"^\d{2}\.\d{2}\.\d{4}", clean):
            try:
                target_dt = datetime.strptime(clean[:10], "%d.%m.%Y")
            except Exception:
                return ""
        else:
            return ""

    if ref_date is None:
        today = get_local_now().date()
    elif isinstance(ref_date, datetime):
        today = ref_date.date()
    else:
        today = ref_date

    target_date = target_dt.date() if isinstance(target_dt, datetime) else target_dt
    diff_days = (target_date - today).days

    if diff_days == 0:
        return tr("datetime.today", "heute")
    if diff_days == 1:
        return tr("datetime.tomorrow", "morgen")
    if diff_days == 2:
        return tr("datetime.day_after_tomorrow", "übermorgen")
    if diff_days == -1:
        return tr("datetime.yesterday", "gestern")
    if diff_days == -2:
        return tr("datetime.day_before_yesterday", "vorgestern")

    target_year, target_week, _ = target_date.isocalendar()
    today_year, today_week, _ = today.isocalendar()

    if diff_days > 2:
        if target_year == today_year and target_week == today_week:
            return tr("datetime.this_week", "diese Woche")
        if (target_year == today_year and target_week == today_week + 1) or (
            target_year == today_year + 1 and today_week >= 52 and target_week == 1
        ):
            return tr("datetime.next_week", "nächste Woche")
        return tr("datetime.in_days", f"in {diff_days} Tagen", diff_days=diff_days)
    else:
        if target_year == today_year and target_week == today_week:
            return tr("datetime.this_week", "diese Woche")
        if (target_year == today_year and target_week == today_week - 1) or (
            target_year == today_year - 1 and today_week == 1 and target_week >= 52
        ):
            return tr("datetime.last_week", "letzte Woche")
        return tr("datetime.days_ago", f"vor {abs(diff_days)} Tagen", diff_days=abs(diff_days))


def format_german_date_with_relative(val: str | datetime | None, ref_date: date | datetime | None = None) -> str:
    """Formats date to 'DD.MM.YYYY (Relativ)' e.g. '26.08.2026 (morgen)' or '26.08.2026 (tomorrow)'."""
    d_str = format_german_date(val)
    if not d_str:
        return ""
    rel = get_relative_date_text(val, ref_date=ref_date)
    return f"{d_str} ({rel})" if rel else d_str


def format_german_time(val: str | datetime | None, include_seconds: bool = False, with_uhr: bool = True) -> str:
    """Formats ISO string or datetime to time format HH:MM(:SS) [Uhr] dynamically localized."""
    if not val:
        return ""
    o_clock = tr("datetime.o_clock", "Uhr").strip() if with_uhr else ""
    suffix = f" {o_clock}" if o_clock else ""
    fmt = f"%H:%M:%S{suffix}" if include_seconds else f"%H:%M{suffix}"
    if isinstance(val, datetime):
        return val.strftime(fmt)
    val_str = val.strip()
    if not val_str:
        return ""
    try:
        dt = parse_iso(val_str)
        return dt.strftime(fmt)
    except Exception:
        clean = re.sub(r"\s*(Uhr|kl\.?)\s*$", "", val_str, flags=re.IGNORECASE).strip()
        if re.match(r"^\d{1,2}:\d{2}", clean):
            return f"{clean[:5]}{suffix}"
        return val_str


def format_german_datetime(
    val: str | datetime | None,
    include_seconds: bool = False,
    with_uhr: bool = True,
) -> str:
    """Formats ISO string or datetime to format DD.MM.YYYY HH:MM(:SS) [Uhr] dynamically localized."""
    if not val:
        return ""
    o_clock = tr("datetime.o_clock", "Uhr").strip() if with_uhr else ""
    suffix = f" {o_clock}" if o_clock else ""
    fmt = f"%d.%m.%Y %H:%M:%S{suffix}" if include_seconds else f"%d.%m.%Y %H:%M{suffix}"
    if isinstance(val, datetime):
        return val.strftime(fmt)
    val_str = val.strip()
    if not val_str:
        return ""
    try:
        dt = parse_iso(val_str)
        return dt.strftime(fmt)
    except Exception:
        clean = re.sub(r"\s*(Uhr|kl\.?)\s*$", "", val_str, flags=re.IGNORECASE).strip()
        if re.match(r"^\d{2}\.\d{2}\.\d{4}\s+\d{1,2}:\d{2}", clean):
            return f"{clean}{suffix}"
        return val_str


def parse_german_date(german_str: str) -> str:
    """Parses date format DD.MM.YYYY [HH:MM] into ISO format string YYYY-MM-DD[THH:MM:SS]."""
    if not german_str or not german_str.strip():
        return ""
    cleaned = re.sub(r"\s*(Uhr|kl\.?)\s*$", "", german_str, flags=re.IGNORECASE).strip()
    for fmt, iso_fmt in [
        ("%d.%m.%Y %H:%M:%S", "%Y-%m-%dT%H:%M:%S"),
        ("%d.%m.%Y %H:%M", "%Y-%m-%dT%H:%M:00"),
        ("%d.%m.%Y", "%Y-%m-%dT00:00:00"),
        ("%Y-%m-%dT%H:%M:%S", "%Y-%m-%dT%H:%M:%S"),
        ("%Y-%m-%d", "%Y-%m-%dT00:00:00"),
    ]:
        try:
            dt = datetime.strptime(cleaned, fmt)
            return dt.strftime(iso_fmt)
        except ValueError:
            continue
    return cleaned


# Generic and modern aliases
format_date = format_german_date
format_time = format_german_time
format_datetime = format_german_datetime
format_date_with_relative = format_german_date_with_relative
parse_date = parse_german_date
