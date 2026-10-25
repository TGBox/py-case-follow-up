"""German date/time formatting and parsing, relative date labels, and no raw ISO strings in user-facing output."""

from datetime import date, datetime, timedelta
import re

import pytest

from enums import Actor, BoardColumn
from models.case import Case, CaseCustomer, Classification, WorkflowStatus, TimelineEntry
from services.calendar_email_service import CalendarEmailService
from utils.datetime_utils import (
    format_german_date,
    format_german_date_with_relative,
    format_german_datetime,
    format_german_time,
    get_local_now,
    get_relative_date_text,
    now_iso,
    parse_followup_datetime,
    parse_german_date,
    parse_iso,
)

ISO_PATTERN = re.compile(r"\b20\d{2}-\d{2}-\d{2}T\d{2}:\d{2}")
DT = datetime(2026, 8, 25, 14, 30, 45)


@pytest.mark.parametrize("func, value, kwargs, expected", [
    (format_german_date, "2026-08-25T14:30:00", {}, "25.08.2026"),
    (format_german_date, "2026-12-01", {}, "01.12.2026"),
    (format_german_date, DT, {}, "25.08.2026"),
    (format_german_date, "25.08.2026", {}, "25.08.2026"),
    (format_german_date, "", {}, ""),
    (format_german_date, None, {}, ""),
    (format_german_time, "2026-08-25T14:30:00", {}, "14:30 Uhr"),
    (format_german_time, "2026-08-25T09:05:00", {"with_uhr": False}, "09:05"),
    (format_german_time, "14:30", {}, "14:30 Uhr"),
    (format_german_time, "14:30 Uhr", {}, "14:30 Uhr"),
    (format_german_time, "", {}, ""),
    (format_german_time, None, {}, ""),
    (format_german_datetime, "2026-08-25T10:00:00", {}, "25.08.2026 10:00 Uhr"),
    (format_german_datetime, "2026-08-25T10:00:00", {"with_uhr": False}, "25.08.2026 10:00"),
    (format_german_datetime, "2026-08-25T10:00:00", {"include_seconds": True}, "25.08.2026 10:00:00 Uhr"),
    (format_german_datetime, DT, {}, "25.08.2026 14:30 Uhr"),
    (format_german_datetime, DT, {"with_uhr": False}, "25.08.2026 14:30"),
    (format_german_datetime, "25.08.2026 10:00", {}, "25.08.2026 10:00 Uhr"),
    (format_german_datetime, "25.08.2026 10:00 Uhr", {}, "25.08.2026 10:00 Uhr"),
    (format_german_datetime, "", {}, ""),
    (format_german_datetime, None, {}, ""),
    (parse_german_date, "25.08.2026 10:00 Uhr", {}, "2026-08-25T10:00:00"),
    (parse_german_date, "25.08.2026 10:00", {}, "2026-08-25T10:00:00"),
    (parse_german_date, "25.08.2026", {}, "2026-08-25T00:00:00"),
    (parse_german_date, "2026-08-25T10:00:00", {}, "2026-08-25T10:00:00"),
])
def test_format_and_parse(func, value, kwargs, expected):
    assert func(value, **kwargs) == expected


def test_parse_iso_and_now():
    dt = parse_iso("2026-08-23T14:30:00")
    assert (dt.year, dt.month, dt.day, dt.hour, dt.minute) == (2026, 8, 23, 14, 30)
    assert dt.tzinfo is not None  # naive input gets the local timezone
    assert get_local_now().year >= 2026
    assert parse_iso(now_iso()).date() == get_local_now().date()


@pytest.mark.parametrize("value, expected", [
    ("2026-08-23T14:30:00", (2026, 8, 23, 14, 30)),
    ("23.08.2026 14:30 Uhr", (2026, 8, 23, 14, 30)),
    ("23.08.2026 (gestern)", (2026, 8, 23, 0, 0)),
    ("23.08.2026 09:00 (morgen)", (2026, 8, 23, 9, 0)),
    (datetime(2026, 8, 23, 7, 15), (2026, 8, 23, 7, 15)),
])
def test_parse_followup_datetime(value, expected):
    dt = parse_followup_datetime(value)
    assert dt is not None
    assert (dt.year, dt.month, dt.day, dt.hour, dt.minute) == expected


@pytest.mark.parametrize("value", [None, ""])
def test_parse_followup_datetime_empty(value):
    assert parse_followup_datetime(value) is None


def test_german_followup_input_round_trips_relative_to_now():
    now = get_local_now()
    past = parse_iso(parse_german_date(format_german_date(now - timedelta(days=1)) + " 09:00"))
    future = parse_iso(parse_german_date(format_german_date(now + timedelta(days=3)) + " 09:00"))
    assert past <= now < future


@pytest.mark.parametrize("value, expected", [
    ("2026-08-25T14:00:00", "heute"),
    ("25.08.2026", "heute"),
    ("2026-08-26T10:00:00", "morgen"),
    ("2026-08-27T10:00:00", "übermorgen"),
    ("2026-08-24T10:00:00", "gestern"),
    ("2026-08-23T10:00:00", "vorgestern"),
    ("2026-08-28T10:00:00", "diese Woche"),
    ("2026-08-31T10:00:00", "nächste Woche"),
    ("2026-08-18T10:00:00", "letzte Woche"),
    ("2026-09-10T10:00:00", "in 16 Tagen"),
    ("2026-08-01T10:00:00", "vor 24 Tagen"),
])
def test_relative_date_text(value, expected):
    assert get_relative_date_text(value, ref_date=date(2026, 8, 25)) == expected  # a Tuesday


def test_format_german_date_with_relative():
    ref = date(2026, 8, 25)
    assert format_german_date_with_relative("2026-08-26T14:00:00", ref_date=ref) == "26.08.2026 (morgen)"
    assert format_german_date_with_relative("2026-08-25T14:00:00", ref_date=ref) == "25.08.2026 (heute)"


def _case() -> Case:
    return Case(
        case_id="T-2026-1214",
        customer=CaseCustomer(customer_id="00121", practice_name="Praxis Wolf", contact_person="Frau Müller",
                              email="wolf@praxis.de"),
        classification=Classification(title="Verschwundene Rechnung", deadline_callback="2026-08-25T10:00:00"),
        workflow_status=WorkflowStatus(board_column=BoardColumn.ACTION_REQUIRED, current_actor=Actor.SUPPORT,
                                       followup_at="2026-08-25T14:30:00", followup_note="Test"),
        created_at="2026-08-24T08:00:00",
        updated_at="2026-08-24T12:00:00",
        created_by="Daniel Rösch",
        timeline=[TimelineEntry(timestamp="2026-08-24T08:30:00", author="Tester", note="Notiz 1")],
    )


def test_case_formatted_properties_and_email_draft_use_german_format():
    """Anti-regression: no raw ISO 8601 strings in user-facing text."""
    case = _case()
    assert case.formatted_deadline == "25.08.2026 10:00 Uhr"
    assert case.formatted_followup == "25.08.2026 14:30 Uhr"
    assert case.formatted_created_at == "24.08.2026 08:00 Uhr"
    assert case.formatted_updated_at == "24.08.2026 12:00 Uhr"

    body = CalendarEmailService().generate_email_draft(case, user_name="Daniel Rösch")["body"]
    assert "Geplante Rückruf-Deadline: 25.08.2026 10:00 Uhr" in body
    assert "Aktueller Status: Aktion erforderlich" in body
    assert not ISO_PATTERN.search(body)

    # without a contact person the salutation falls back to the practice
    case.customer.contact_person = ""
    body = CalendarEmailService().generate_email_draft(case, user_name="Daniel Rösch")["body"]
    assert "Sehr geehrte Damen und Herren (Praxis Wolf)," in body
