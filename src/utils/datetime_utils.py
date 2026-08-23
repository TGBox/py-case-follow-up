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
