from unittest.mock import MagicMock, patch
import pytest

from constants import (
    NTFY_TOPIC_PREFIX,
)
from models.case import Case, Classification, WorkflowStatus
from models.profile import ReminderSettings, UserProfile
from ui.dialogs.profile_settings_dialog import ProfileSettingsDialog
from utils.idle_detector import IdleDetector


@pytest.fixture(autouse=True)
def cleanup():
    IdleDetector.reset_mock()
    yield
    IdleDetector.reset_mock()


def test_ntfy_profile_ui_initialization_and_random_btn(root):
    profile = UserProfile()
    profile.reminder_settings = ReminderSettings(
        mobile_ntfy_enabled=True,
        mobile_ntfy_topic="desk-alert-12345678",
        mobile_ntfy_idle_minutes=10,
    )
    mock_storage = MagicMock()

    dlg = ProfileSettingsDialog(root, profile=profile, storage_service=mock_storage)

    assert hasattr(dlg, "ntfy_switch")
    assert bool(dlg.ntfy_switch.get()) is True
    assert dlg.ntfy_topic_entry.get() == "desk-alert-12345678"

    # Click random topic button
    dlg.on_generate_random_ntfy_topic()
    new_topic = dlg.ntfy_topic_entry.get()
    assert new_topic.startswith(NTFY_TOPIC_PREFIX)
    assert new_topic != "desk-alert-12345678"

    # Test saving UI settings
    dlg.ntfy_idle_combo.set("15 Min.")
    assert dlg.save_ui_settings() is True
    assert profile.reminder_settings.mobile_ntfy_topic == new_topic
    assert profile.reminder_settings.mobile_ntfy_idle_minutes == 15

    dlg.destroy()


@patch("services.ntfy_service.urlopen")
def test_ntfy_test_button_success(mock_urlopen, root):
    mock_resp = MagicMock()
    mock_resp.status = 200
    mock_resp.__enter__.return_value = mock_resp
    mock_urlopen.return_value = mock_resp

    profile = UserProfile()
    mock_storage = MagicMock()
    dlg = ProfileSettingsDialog(root, profile=profile, storage_service=mock_storage)

    dlg.ntfy_topic_entry.delete(0, "end")
    dlg.ntfy_topic_entry.insert(0, "my-test-topic")

    with patch("ui.widgets.toast_notification.ToastNotification") as mock_toast:
        dlg.on_send_ntfy_test()
        assert mock_urlopen.called
        assert mock_toast.called

    dlg.destroy()


def test_app_check_mobile_ntfy_reminders_when_active():
    from ui.app import SupportCockpitApp

    app = MagicMock(spec=SupportCockpitApp)
    app.profile = UserProfile()
    app.profile.reminder_settings = ReminderSettings(
        mobile_ntfy_enabled=True,
        mobile_ntfy_topic="test-topic",
        mobile_ntfy_idle_minutes=5,
    )
    app._last_ntfy_notified_ids = set()

    # User is active (not idle)
    IdleDetector.set_mock_state(idle_seconds=10.0, is_locked=False)

    case = Case(
        case_id="101",
        classification=Classification(title="Sensitive Praxis Issue", urgency_level="Hoch"),
        workflow_status=WorkflowStatus(followup_at="2026-01-01 10:00:00"),
    )

    with patch("services.ntfy_service.NtfyService.send_notification_async") as mock_send:
        SupportCockpitApp._check_mobile_ntfy_reminders(app, [case])
        assert not mock_send.called
        assert "101" not in app._last_ntfy_notified_ids


def test_app_check_mobile_ntfy_reminders_when_idle():
    from ui.app import SupportCockpitApp

    app = MagicMock(spec=SupportCockpitApp)
    app.profile = UserProfile()
    app.profile.reminder_settings = ReminderSettings(
        mobile_ntfy_enabled=True,
        mobile_ntfy_topic="test-topic",
        mobile_ntfy_idle_minutes=5,
    )
    app._last_ntfy_notified_ids = set()

    # User is idle (350s > 300s)
    IdleDetector.set_mock_state(idle_seconds=350.0, is_locked=False)

    case = Case(
        case_id="101",
        classification=Classification(title="Sensitive Praxis Issue", urgency_level="Hoch"),
        workflow_status=WorkflowStatus(followup_at="2026-01-01 10:00:00"),
    )

    with patch("services.ntfy_service.NtfyService.send_notification_async") as mock_send:
        SupportCockpitApp._check_mobile_ntfy_reminders(app, [case])
        assert mock_send.called
        call_kwargs = mock_send.call_args[1]
        assert call_kwargs["topic"] == "test-topic"
        assert "101" in call_kwargs["title"]
        # Verify privacy: sensitive title must NOT be in message or title!
        assert "Sensitive Praxis Issue" not in call_kwargs["title"]
        assert "Sensitive Praxis Issue" not in call_kwargs["message"]
        assert "101" in app._last_ntfy_notified_ids

        # Second call should not re-notify the same case
        mock_send.reset_mock()
        SupportCockpitApp._check_mobile_ntfy_reminders(app, [case])
        assert not mock_send.called


def test_app_check_mobile_ntfy_reminders_when_locked():
    from ui.app import SupportCockpitApp

    app = MagicMock(spec=SupportCockpitApp)
    app.profile = UserProfile()
    app.profile.reminder_settings = ReminderSettings(
        mobile_ntfy_enabled=True,
        mobile_ntfy_topic="test-topic",
        mobile_ntfy_idle_minutes=15,
    )
    app._last_ntfy_notified_ids = set()

    # User locked the screen (Win + L) even if idle time is low (e.g. 5 seconds)
    IdleDetector.set_mock_state(idle_seconds=5.0, is_locked=True)

    case = Case(
        case_id="102",
        classification=Classification(title="Urgent DB Migration", urgency_level="Prio 1"),
        workflow_status=WorkflowStatus(followup_at="2026-01-01 10:00:00"),
    )

    with patch("services.ntfy_service.NtfyService.send_notification_async") as mock_send:
        SupportCockpitApp._check_mobile_ntfy_reminders(app, [case])
        assert mock_send.called
        assert "102" in app._last_ntfy_notified_ids
