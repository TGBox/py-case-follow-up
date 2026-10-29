from datetime import datetime, timedelta, timezone

from models.case import Case
from utils.datetime_utils import parse_followup_datetime


def should_notify_due(
    due_count: int,
    last_count: int | None,
    last_notified_at: datetime | None,
    now: datetime,
    repeat_minutes: int,
) -> bool:
    """Whether a due-follow-up notification is shown on this check.

    Always when the due count rises (or on the first check). While the same
    items stay due it repeats every ``repeat_minutes``, so a notification that
    was missed does not stay silent for good. ``repeat_minutes <= 0`` keeps the
    old behaviour of notifying only when the count rises.
    """
    if due_count <= 0:
        return False
    if last_count is None or due_count > last_count:
        return True
    if repeat_minutes <= 0 or last_notified_at is None:
        return False
    return now - last_notified_at >= timedelta(minutes=repeat_minutes)


_LATEST = datetime.max.replace(tzinfo=timezone.utc)


def due_group_name(case: Case) -> str:
    """The person (internal task) or practice a due follow-up belongs to; "" if neither is known."""
    if case.is_internal:
        return case.customer.contact_person.strip()
    return case.customer.practice_name.strip()


def group_due_cases(cases: list[Case]) -> list[tuple[str, list[Case]]]:
    """Due follow-ups grouped by person or practice, most overdue first.

    Inside a group the oldest follow-up comes first. The groups are ordered by
    their oldest follow-up, so the longest-waiting item is always at the top;
    cases without a name come last. A follow-up that cannot be read counts as
    the newest, rather than hiding or crashing the list.
    """
    def due_at(case: Case) -> datetime:
        return parse_followup_datetime(case.workflow_status.followup_at) or _LATEST

    groups: dict[str, list[Case]] = {}
    for case in sorted(cases, key=due_at):
        groups.setdefault(due_group_name(case), []).append(case)
    return sorted(groups.items(), key=lambda item: (item[0] == "", due_at(item[1][0])))
