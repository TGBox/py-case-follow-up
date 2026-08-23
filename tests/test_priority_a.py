import pytest
from datetime import datetime, timedelta
from models.case import Case, TimelineEntry
from utils.datetime_utils import format_german_date, get_local_now, parse_iso, parse_german_date


def test_followup_due_calculation():
    now = get_local_now()

    # Past due followup
    past_dt = now - timedelta(hours=2)
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
