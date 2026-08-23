import pytest
from enums import Actor, ACTOR_DISPLAY, get_actor_display, get_actor_val_from_display
from models.case import Case, TimelineEntry


def test_actor_enum_conversions_and_display_names():
    assert get_actor_display(Actor.SUPPORT) == "Support"
    assert get_actor_display(Actor.DEVELOPMENT) == "Entwicklung"
    assert ACTOR_DISPLAY[Actor.SUPPORT] == "Support"
    assert ACTOR_DISPLAY[Actor.DEVELOPMENT] == "Entwicklung"

    assert get_actor_val_from_display("Entwicklung") == Actor.DEVELOPMENT
    assert get_actor_val_from_display("Support") == Actor.SUPPORT


def test_case_handover_timeline_log_entry():
    c = Case(case_id="T-2026-999")
    assert c.workflow_status.current_actor == Actor.SUPPORT

    # Perform handover log
    c.workflow_status.current_actor = Actor.DEVELOPMENT
    c.timeline.append(
        TimelineEntry(
            timestamp="2026-08-23T10:00:00",
            author="Daniel Rösch",
            note="Fall an Hr. Becker übergeben (Kanal: GitLab Issue).",
            status_change="ZUSTÄNDIGKEIT: Support -> Entwicklung",
        )
    )

    assert c.workflow_status.current_actor == Actor.DEVELOPMENT
    assert len(c.timeline) >= 1

    last_entry = c.timeline[-1]
    assert last_entry.author == "Daniel Rösch"
    assert last_entry.status_change == "ZUSTÄNDIGKEIT: Support -> Entwicklung"
    assert "Hr. Becker" in last_entry.note
