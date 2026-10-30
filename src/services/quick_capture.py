"""Builds the internal task that the quick-capture window saves.

Kept free of any UI so the rules (title, reminder presets, case id) can be
tested without a window.
"""

from datetime import datetime, timedelta

from constants import (
    CASE_ID_PREFIX,
    DEFAULT_INTERNAL_TASK_CATEGORIES,
    FOLLOWUP_PRESET_HOURS_1,
    FOLLOWUP_PRESET_HOURS_2,
    FOLLOWUP_TIME_0800,
    FOLLOWUP_TIME_1630,
    INITIAL_STATUS_CHANGE_NOTE,
    INTERNAL_ATTACHMENT_SUFFIX,
    INTERNAL_CUSTOMER_ID,
    INTERNAL_PRACTICE_NAME,
    ISO_DATETIME_FORMAT,
    QUICK_CAPTURE_PRESETS,
    QUICK_CAPTURE_TITLE_MAX_CHARS,
    REL_ATTACHMENTS_DIR,
    TIMESTAMP_FORMAT_CASE_ID,
)
from enums import Actor, BoardColumn, Channel
from models.case import Case, CaseCustomer, Classification, TimelineEntry, WorkflowStatus
from services.i18n_service import tr
from utils.datetime_utils import format_german_datetime

INTERNAL_TASK_SCHEMA_ID = "schema_internal_task"


def resolve_reminder(preset: str, now: datetime) -> datetime | None:
    """The reminder time for a preset key, or None for "no reminder".

    A fixed clock time that has already passed today moves to tomorrow, so a
    reminder never fires the moment it is saved.
    """
    if preset not in QUICK_CAPTURE_PRESETS:
        raise ValueError(f"Unknown reminder preset: {preset!r}")
    if preset == "1h":
        return now + timedelta(hours=FOLLOWUP_PRESET_HOURS_1)
    if preset == "2h":
        return now + timedelta(hours=FOLLOWUP_PRESET_HOURS_2)
    if preset == "none":
        return None
    clock = FOLLOWUP_TIME_1630 if preset == "today_1630" else FOLLOWUP_TIME_0800
    hour, minute = (int(part) for part in clock.split(":"))
    target = now.replace(hour=hour, minute=minute, second=0, microsecond=0)
    if preset == "tomorrow_0800" or target <= now:
        target += timedelta(days=1)
    return target


def build_title(text: str, person: str = "") -> str:
    """First non-empty line of the text, shortened, prefixed with the person."""
    first = next((line.strip() for line in text.splitlines() if line.strip()), "")
    if len(first) > QUICK_CAPTURE_TITLE_MAX_CHARS:
        first = first[: QUICK_CAPTURE_TITLE_MAX_CHARS - 1].rstrip() + "…"
    person = person.strip()
    return f"{person}: {first}" if person else first


def new_case_id(taken: set[str], now: datetime) -> str:
    """Case id in the same shape as the new-case dialog; a taken id gets a running suffix."""
    base_id = f"{CASE_ID_PREFIX}{now.year}-{now.strftime(TIMESTAMP_FORMAT_CASE_ID)}"
    case_id = base_id
    suffix = 2
    while case_id in taken:
        case_id = f"{base_id}-{suffix}"
        suffix += 1
    return case_id


def build_quick_case(
    text: str,
    person: str,
    reminder: datetime | None,
    created_by: str,
    taken_ids: set[str],
    now: datetime,
) -> Case:
    """An internal task (no customer) with the text as its first note."""
    text = text.strip()
    if not text:
        raise ValueError("A quick-capture task needs some text.")
    person = person.strip()
    case_id = new_case_id(taken_ids, now)
    now_str = now.strftime(ISO_DATETIME_FORMAT)
    category = DEFAULT_INTERNAL_TASK_CATEGORIES[0]

    return Case(
        case_id=case_id,
        created_at=now_str,
        updated_at=now_str,
        created_by=created_by,
        assigned_to=created_by,
        # The person sits in the contact field: it is part of the full-text
        # search, so "what is open with XY" is one search away.
        customer=CaseCustomer(
            customer_id=INTERNAL_CUSTOMER_ID,
            practice_name=INTERNAL_PRACTICE_NAME,
            contact_person=person,
        ),
        classification=Classification(
            schema_id=INTERNAL_TASK_SCHEMA_ID,
            title=build_title(text, person),
        ),
        workflow_status=WorkflowStatus(
            board_column=BoardColumn.ACTION_REQUIRED,
            current_actor=Actor.SUPPORT,
            actor_since=now_str,
            is_data_complete=True,
            followup_at=format_german_datetime(reminder) if reminder else "",
        ),
        form_data={
            "internal_category": tr(f"internal_task_categories.{category}", default=category),
            "description": text,
        },
        attachment_directory=f"{REL_ATTACHMENTS_DIR}/{case_id}{INTERNAL_ATTACHMENT_SUFFIX}",
        timeline=[
            TimelineEntry(
                timestamp=now_str,
                author=created_by,
                channel=Channel.INTERNAL_NOTE,
                note=text,
                status_change=INITIAL_STATUS_CHANGE_NOTE,
            )
        ],
    )
