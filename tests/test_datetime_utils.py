import pytest
from datetime import datetime
from utils.datetime_utils import (
    format_german_date,
    format_german_datetime,
    parse_german_date,
    parse_iso,
    get_local_now,
)


def test_format_german_date_and_datetime():
    dt = datetime(2026, 8, 23, 14, 30, 45)

    g_date = format_german_date(dt)
    assert g_date == "23.08.2026"

    g_dt = format_german_datetime(dt)
    assert g_dt == "23.08.2026 14:30 Uhr"
    assert format_german_datetime(dt, with_uhr=False) == "23.08.2026 14:30"


def test_parse_german_date_to_iso():
    # German date only
    iso_date = parse_german_date("23.08.2026")
    assert iso_date.startswith("2026-08-23")

    # German date with time
    iso_dt = parse_german_date("23.08.2026 14:30")
    assert "2026-08-23T14:30" in iso_dt


def test_parse_iso_string_to_datetime():
    iso_str = "2026-08-23T14:30:00"
    dt = parse_iso(iso_str)

    assert dt.year == 2026
    assert dt.month == 8
    assert dt.day == 23
    assert dt.hour == 14
    assert dt.minute == 30


def test_get_local_now_returns_valid_datetime():
    now = get_local_now()
    assert isinstance(now, datetime)
    assert now.year >= 2026
