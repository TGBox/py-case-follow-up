"""Tests for followup due date calculations, relative German date labels,

and timeline additions without actor disruption.
"""

from datetime import datetime, date, timedelta
import pytest
from models.case import Case, TimelineEntry
from utils.datetime_utils import (
    format_german_date,
    format_german_date_with_relative,
    get_relative_date_text,
    get_local_now,
    parse_iso,
    parse_german_date,
)


def test_followup_due_calculation():
    """Verify followup past and future due calculation."""
    now = get_local_now()

    # Past due followup – use yesterday to avoid flaky failures near midnight or early morning
    past_dt = now - timedelta(days=1)
    c_due = Case(case_id="T-DUE-01")
    c_due.workflow_status.followup_at = format_german_date(past_dt) + " 09:00"

    # Future followup
    fut_dt = now + timedelta(days=3)
    c_future = Case(case_id="T-FUT-01")
    c_future.workflow_status.followup_at = format_german_date(fut_dt) + " 09:00"

    parsed_due = parse_iso(parse_german_date(c_due.workflow_status.followup_at))
    assert parsed_due <= now

    parsed_fut = parse_iso(parse_german_date(c_future.workflow_status.followup_at))
    assert parsed_fut > now


def test_timeline_note_addition_without_actor_change():
    """Verify adding notes to timeline preserves actor assignment."""
    c = Case(case_id="T-NOTE-01")
    c.workflow_status.current_actor = "SUPPORT"

    entry = TimelineEntry(
        timestamp="2026-08-23T14:00:00",
        author="Daniel Rösch",
        note="Rückmeldung vom Entwickler erhalten: Fix ist in Arbeit.",
    )
    c.timeline.append(entry)

    # Verify actor remains unchanged
    assert c.workflow_status.current_actor == "SUPPORT"
    assert len(c.timeline) == 1
    assert c.timeline[0].note == "Rückmeldung vom Entwickler erhalten: Fix ist in Arbeit."


def test_relative_date_text_calculation():
    """Verify get_relative_date_text accurately calculates today, tomorrow, day-after-tomorrow,

    yesterday, day-before-yesterday, weeks and day counts.
    """
    ref = date(2026, 8, 25)  # Tuesday

    # Today
    assert get_relative_date_text("2026-08-25T14:00:00", ref_date=ref) == "heute"
    assert get_relative_date_text("25.08.2026", ref_date=ref) == "heute"

    # Tomorrow & Day after tomorrow
    assert get_relative_date_text("2026-08-26T10:00:00", ref_date=ref) == "morgen"
    assert get_relative_date_text("2026-08-27T10:00:00", ref_date=ref) == "übermorgen"

    # Yesterday & Day before yesterday
    assert get_relative_date_text("2026-08-24T10:00:00", ref_date=ref) == "gestern"
    assert get_relative_date_text("2026-08-23T10:00:00", ref_date=ref) == "vorgestern"

    # This week / Next week
    assert get_relative_date_text("2026-08-28T10:00:00", ref_date=ref) == "diese Woche"
    assert get_relative_date_text("2026-08-31T10:00:00", ref_date=ref) == "nächste Woche"
    assert get_relative_date_text("2026-08-18T10:00:00", ref_date=ref) == "letzte Woche"

    # Distant days
    assert get_relative_date_text("2026-09-10T10:00:00", ref_date=ref) == "in 16 Tagen"
    assert get_relative_date_text("2026-08-01T10:00:00", ref_date=ref) == "vor 24 Tagen"

    # Formatted helper
    assert format_german_date_with_relative("2026-08-26T14:00:00", ref_date=ref) == "26.08.2026 (morgen)"
    assert format_german_date_with_relative("2026-08-25T14:00:00", ref_date=ref) == "25.08.2026 (heute)"
