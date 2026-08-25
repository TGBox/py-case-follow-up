from datetime import datetime, timezone
import re


def get_local_now() -> datetime:
    """Returns the current timezone-aware local datetime."""
    return datetime.now().astimezone()


def now_iso() -> str:
    """Returns current ISO 8601 formatted string (YYYY-MM-DDTHH:MM:SS)."""
    return get_local_now().strftime("%Y-%m-%dT%H:%M:%S")


def parse_iso(iso_str: str) -> datetime:
    """Parses ISO string to timezone-aware datetime.
    If string is naive ISO format (no timezone), attaches local timezone.
    """
    if not iso_str:
        raise ValueError("ISO datetime string cannot be empty.")
    
    # Clean possible whitespace
    cleaned = iso_str.strip()
    
    # Handle standard ISO formats
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
    """Formats ISO string or datetime to German date format DD.MM.YYYY."""
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
        # Check if already DD.MM.YYYY
        if re.match(r"^\d{2}\.\d{2}\.\d{4}", val_str):
            return val_str[:10]
        return val_str


def format_german_time(val: str | datetime | None, include_seconds: bool = False, with_uhr: bool = True) -> str:
    """Formats ISO string or datetime to German time format HH:MM(:SS) [Uhr]."""
    if not val:
        return ""
    suffix = " Uhr" if with_uhr else ""
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
        clean = val_str.replace("Uhr", "").strip()
        if re.match(r"^\d{1,2}:\d{2}", clean):
            return f"{clean[:5]}{suffix}"
        return val_str


def format_german_datetime(
    val: str | datetime | None,
    include_seconds: bool = False,
    with_uhr: bool = True,
) -> str:
    """Formats ISO string or datetime to German format DD.MM.YYYY HH:MM(:SS) [Uhr]."""
    if not val:
        return ""
    suffix = " Uhr" if with_uhr else ""
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
        clean = val_str.replace("Uhr", "").strip()
        if re.match(r"^\d{2}\.\d{2}\.\d{4}\s+\d{1,2}:\d{2}", clean):
            return f"{clean}{suffix}"
        return val_str


def parse_german_date(german_str: str) -> str:
    """Parses German format DD.MM.YYYY [HH:MM] into ISO format string YYYY-MM-DD[THH:MM:SS]."""
    if not german_str or not german_str.strip():
        return ""
    cleaned = german_str.replace("Uhr", "").strip()
    # Try DD.MM.YYYY HH:MM:SS
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

