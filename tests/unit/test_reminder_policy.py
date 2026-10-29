from datetime import datetime, timedelta

import pytest

from constants import INTERNAL_CUSTOMER_ID
from models.case import Case, CaseCustomer, Classification, WorkflowStatus
from models.profile import ReminderSettings
from services.reminder_policy import due_group_name, group_due_cases, should_notify_due

NOW = datetime(2026, 10, 29, 12, 0, 0)


def test_nothing_due_never_notifies():
    assert should_notify_due(0, None, None, NOW, 30) is False
    assert should_notify_due(0, 3, NOW - timedelta(hours=5), NOW, 30) is False


def test_first_check_with_something_due_notifies():
    assert should_notify_due(1, None, None, NOW, 30) is True


def test_a_rising_count_notifies_immediately():
    assert should_notify_due(3, 2, NOW - timedelta(minutes=1), NOW, 30) is True
    assert should_notify_due(3, 2, NOW - timedelta(minutes=1), NOW, 0) is True


def test_the_same_items_stay_quiet_until_the_interval_has_passed():
    assert should_notify_due(2, 2, NOW - timedelta(minutes=29), NOW, 30) is False
    assert should_notify_due(2, 2, NOW - timedelta(minutes=30), NOW, 30) is True
    assert should_notify_due(2, 2, NOW - timedelta(hours=3), NOW, 30) is True


def test_a_falling_count_does_not_notify_before_the_interval():
    assert should_notify_due(1, 2, NOW - timedelta(minutes=5), NOW, 30) is False


@pytest.mark.parametrize("repeat", [0, -5])
def test_repeat_off_keeps_the_old_behaviour(repeat):
    assert should_notify_due(2, 2, NOW - timedelta(days=2), NOW, repeat) is False


def test_without_a_previous_notification_time_it_cannot_repeat():
    assert should_notify_due(2, 2, None, NOW, 30) is False


def test_reminder_settings_default_to_thirty_minutes():
    assert ReminderSettings().followup_repeat_minutes == 30
    assert ReminderSettings.from_dict({}).followup_repeat_minutes == 30


def test_reminder_settings_round_trip_the_repeat_interval():
    settings = ReminderSettings.from_dict({"followup_repeat_minutes": 60})
    assert settings.followup_repeat_minutes == 60
    assert ReminderSettings.from_dict(settings.to_dict()).followup_repeat_minutes == 60


def test_zero_is_a_valid_choice_and_means_off():
    assert ReminderSettings.from_dict({"followup_repeat_minutes": 0}).followup_repeat_minutes == 0


@pytest.mark.parametrize("junk", [-1, "abc", None, True, 2.5, [30]])
def test_unusable_stored_values_fall_back_to_the_default(junk):
    assert ReminderSettings.from_dict({"followup_repeat_minutes": junk}).followup_repeat_minutes == 30


# --- grouping of due follow-ups -------------------------------------------------------------

def _due_case(case_id, followup_at, practice="Praxis A", person="", internal=False):
    customer = CaseCustomer(customer_id=INTERNAL_CUSTOMER_ID, practice_name="Intern / Keine Praxis", contact_person=person) if internal \
        else CaseCustomer(customer_id="K-1", practice_name=practice)
    return Case(case_id=case_id, customer=customer, classification=Classification(schema_id="s", title=case_id),
                workflow_status=WorkflowStatus(followup_at=followup_at))


def _ids(groups):
    return [(name, [c.case_id for c in cases]) for name, cases in groups]


def test_a_customer_case_is_grouped_by_practice_and_an_internal_one_by_person():
    assert due_group_name(_due_case("1", "2026-10-29T08:00:00", practice="Praxis A")) == "Praxis A"
    assert due_group_name(_due_case("2", "2026-10-29T08:00:00", internal=True, person="Anna")) == "Anna"
    assert due_group_name(_due_case("3", "2026-10-29T08:00:00", internal=True)) == ""


def test_the_longest_waiting_item_comes_first_in_and_between_groups():
    cases = [
        _due_case("late-a", "2026-10-29T11:00:00", practice="Praxis A"),
        _due_case("old-b", "2026-10-27T09:00:00", practice="Praxis B"),
        _due_case("early-a", "2026-10-28T09:00:00", practice="Praxis A"),
    ]
    assert _ids(group_due_cases(cases)) == [("Praxis B", ["old-b"]), ("Praxis A", ["early-a", "late-a"])]


def test_tasks_with_a_person_join_the_customers_in_one_ordering_and_unnamed_ones_come_last():
    cases = [
        _due_case("nobody", "2026-10-20T09:00:00", internal=True),
        _due_case("anna", "2026-10-28T09:00:00", internal=True, person="Anna"),
        _due_case("praxis", "2026-10-27T09:00:00", practice="Praxis A"),
    ]
    assert _ids(group_due_cases(cases)) == [("Praxis A", ["praxis"]), ("Anna", ["anna"]), ("", ["nobody"])]


def test_an_unreadable_follow_up_does_not_break_the_list_and_sorts_last():
    cases = [_due_case("broken", "kein Datum", practice="Praxis A"), _due_case("ok", "2026-10-28T09:00:00", practice="Praxis A")]
    assert _ids(group_due_cases(cases)) == [("Praxis A", ["ok", "broken"])]


def test_no_cases_give_no_groups():
    assert group_due_cases([]) == []


def test_grouping_does_not_change_the_callers_list():
    cases = [_due_case("b", "2026-10-29T10:00:00"), _due_case("a", "2026-10-28T10:00:00")]
    group_due_cases(cases)
    assert [c.case_id for c in cases] == ["b", "a"]
