from datetime import datetime, timedelta

import pytest

from models.profile import ReminderSettings
from services.reminder_policy import should_notify_due

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
