from datetime import datetime, timedelta


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
