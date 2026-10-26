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


def test_ntfy_ui_filter_checkboxes_and_saving(root):
    profile = UserProfile()
    profile.reminder_settings = ReminderSettings(
        mobile_ntfy_enabled=True,
        mobile_ntfy_topic="filter-test-topic",
        mobile_ntfy_idle_minutes=5,
        mobile_ntfy_notify_followups=True,
        mobile_ntfy_notify_prio1=False,
        mobile_ntfy_notify_handovers=True,
        mobile_ntfy_notify_customer_notes=True,
    )
    mock_storage = MagicMock()

    dlg = ProfileSettingsDialog(root, profile=profile, storage_service=mock_storage)

    assert hasattr(dlg, "ntfy_cb_followups")
    assert hasattr(dlg, "ntfy_cb_prio1")
    assert hasattr(dlg, "ntfy_cb_handovers")
    assert hasattr(dlg, "ntfy_cb_notes")

    assert bool(dlg.ntfy_cb_followups.get()) is True
    assert bool(dlg.ntfy_cb_prio1.get()) is False
    assert bool(dlg.ntfy_cb_handovers.get()) is True
    assert bool(dlg.ntfy_cb_notes.get()) is True

    # Test toggling switch off disables checkboxes
    dlg.ntfy_switch.deselect()
    dlg.on_toggle_ntfy()
    assert str(dlg.ntfy_cb_followups.cget("state")) == "disabled"
    assert str(dlg.ntfy_cb_prio1.cget("state")) == "disabled"

    # Test toggling switch on enables checkboxes
    dlg.ntfy_switch.select()
    dlg.on_toggle_ntfy()
    assert str(dlg.ntfy_cb_followups.cget("state")) == "normal"

    # Modify checkbox and save
    dlg.ntfy_cb_prio1.select()
    dlg.ntfy_cb_notes.deselect()
    assert dlg.save_ui_settings() is True

    assert profile.reminder_settings.mobile_ntfy_notify_prio1 is True
    assert profile.reminder_settings.mobile_ntfy_notify_customer_notes is False

    dlg.destroy()


def test_app_check_mobile_ntfy_reminders_prio1_filter():
    from ui.app import SupportCockpitApp
    from enums import UrgencyLevel
    from constants import NTFY_PRIO_MAX, NTFY_TAG_ESCALATION

    app = MagicMock(spec=SupportCockpitApp)
    app.profile = UserProfile()
    app.profile.reminder_settings = ReminderSettings(
        mobile_ntfy_enabled=True,
        mobile_ntfy_topic="prio1-topic",
        mobile_ntfy_idle_minutes=5,
        mobile_ntfy_notify_followups=False,  # Followups disabled
        mobile_ntfy_notify_prio1=True,        # Prio 1 enabled
    )
    app._last_ntfy_notified_ids = set()

    IdleDetector.set_mock_state(idle_seconds=400.0, is_locked=False)

    prio1_case = Case(
        case_id="999",
        classification=Classification(title="Server Outage", urgency_level=UrgencyLevel.RED),
        workflow_status=WorkflowStatus(followup_at=""),
    )
    app.get_all_active_cases_for_reminder.return_value = [prio1_case]

    with patch("services.ntfy_service.NtfyService.send_notification_async") as mock_send:
        SupportCockpitApp._check_mobile_ntfy_reminders(app, [])
        assert mock_send.called
        kwargs = mock_send.call_args[1]
        assert "999" in kwargs["title"]
        assert kwargs["priority"] == NTFY_PRIO_MAX
        assert NTFY_TAG_ESCALATION in kwargs["tags"]
        assert "999" in app._last_ntfy_notified_ids


def test_app_check_mobile_ntfy_reminders_handover_filter():
    from ui.app import SupportCockpitApp
    from constants import NTFY_TAG_HANDOVER

    app = MagicMock(spec=SupportCockpitApp)
    app.profile = UserProfile()
    app.profile.user.name = "Daniel Rösch"
    app.profile.reminder_settings = ReminderSettings(
        mobile_ntfy_enabled=True,
        mobile_ntfy_topic="handover-topic",
        mobile_ntfy_idle_minutes=5,
        mobile_ntfy_notify_followups=False,
        mobile_ntfy_notify_prio1=False,
        mobile_ntfy_notify_handovers=True,
    )
    app._last_ntfy_notified_ids = set()

    IdleDetector.set_mock_state(idle_seconds=400.0, is_locked=False)

    assigned_case = Case(
        case_id="777",
        assigned_to="Daniel Rösch",
        classification=Classification(title="Client handover"),
        workflow_status=WorkflowStatus(followup_at=""),
    )
    app.get_all_active_cases_for_reminder.return_value = [assigned_case]

    with patch("services.ntfy_service.NtfyService.send_notification_async") as mock_send:
        SupportCockpitApp._check_mobile_ntfy_reminders(app, [])
        assert mock_send.called
        kwargs = mock_send.call_args[1]
        assert "777" in kwargs["title"]
        assert NTFY_TAG_HANDOVER in kwargs["tags"]
        assert "777" in app._last_ntfy_notified_ids


def test_app_check_mobile_ntfy_reminders_filter_disabled():
    from ui.app import SupportCockpitApp

    app = MagicMock(spec=SupportCockpitApp)
    app.profile = UserProfile()
    app.profile.reminder_settings = ReminderSettings(
        mobile_ntfy_enabled=True,
        mobile_ntfy_topic="test-topic",
        mobile_ntfy_idle_minutes=5,
        mobile_ntfy_notify_followups=False,  # Followups disabled!
        mobile_ntfy_notify_prio1=False,
        mobile_ntfy_notify_handovers=False,
        mobile_ntfy_notify_customer_notes=False,
    )
    app._last_ntfy_notified_ids = set()

    IdleDetector.set_mock_state(idle_seconds=400.0, is_locked=False)

    case = Case(
        case_id="103",
        classification=Classification(title="Regular case"),
        workflow_status=WorkflowStatus(followup_at="2026-01-01 10:00:00"),
    )
    app.get_all_active_cases_for_reminder.return_value = [case]

    with patch("services.ntfy_service.NtfyService.send_notification_async") as mock_send:
        SupportCockpitApp._check_mobile_ntfy_reminders(app, [case])
        # Nothing should be sent because all filters are False!
        assert not mock_send.called


def test_ntfy_ui_digest_controls_and_saving(root):
    profile = UserProfile()
    profile.reminder_settings = ReminderSettings(
        mobile_ntfy_enabled=True,
        mobile_ntfy_topic="desk-alert-test",
        mobile_ntfy_digest_enabled=False,
        mobile_ntfy_digest_minutes=15,
    )
    dlg = ProfileSettingsDialog(root, profile=profile, storage_service=MagicMock())
    tab = dlg

    assert hasattr(tab, "ntfy_cb_digest")
    assert hasattr(tab, "ntfy_combo_digest_minutes")

    # Initially False
    assert tab.ntfy_cb_digest.get() == 0

    # Toggle digest on
    tab.ntfy_cb_digest.select()
    tab.on_toggle_ntfy()
    assert tab.ntfy_combo_digest_minutes.cget("state") == "normal"

    tab.ntfy_combo_digest_minutes.set("30")
    tab.save_ui_settings()

    assert tab.profile.reminder_settings.mobile_ntfy_digest_enabled is True
    assert tab.profile.reminder_settings.mobile_ntfy_digest_minutes == 30

    # Retranslate labels
    tab.refresh_ui_tab_labels()
    assert "Digest" in tab.ntfy_cb_digest.cget("text") or "Sammelbericht" in tab.ntfy_cb_digest.cget("text")
    dlg.destroy()


def test_app_check_mobile_ntfy_reminders_digest_buffering_and_flush():
    from ui.app import SupportCockpitApp
    from constants import NTFY_TAG_DIGEST

    app = MagicMock(spec=SupportCockpitApp)
    app.profile = UserProfile()
    app.profile.reminder_settings = ReminderSettings(
        mobile_ntfy_enabled=True,
        mobile_ntfy_topic="digest-topic",
        mobile_ntfy_idle_minutes=5,
        mobile_ntfy_notify_followups=True,
        mobile_ntfy_notify_prio1=False,
        mobile_ntfy_notify_handovers=False,
        mobile_ntfy_digest_enabled=True,
        mobile_ntfy_digest_minutes=15,
    )
    app._last_ntfy_notified_ids = set()
    app._ntfy_digest_queue = []
    app._ntfy_last_digest_sent_at = 0.0

    IdleDetector.set_mock_state(idle_seconds=400.0, is_locked=False)

    case1 = Case(
        case_id="201",
        classification=Classification(title="Case 1"),
        workflow_status=WorkflowStatus(followup_at="2026-01-01 10:00:00"),
    )
    case2 = Case(
        case_id="202",
        classification=Classification(title="Case 2"),
        workflow_status=WorkflowStatus(followup_at="2026-01-01 10:00:00"),
    )
    app.get_all_active_cases_for_reminder.return_value = [case1, case2]

    # First call: events get queued in _ntfy_digest_queue, not sent immediately
    with patch("services.ntfy_service.NtfyService.send_notification_async") as mock_send:
        SupportCockpitApp._check_mobile_ntfy_reminders(app, [case1, case2])
        assert not mock_send.called
        assert len(app._ntfy_digest_queue) == 2
        assert app._ntfy_last_digest_sent_at > 0.0

    # Second call: interval elapsed (simulated by setting _ntfy_last_digest_sent_at far in the past)
    app._ntfy_last_digest_sent_at = 1.0  # Monotonic time is much larger than 1.0 + 15*60
    with patch("services.ntfy_service.NtfyService.send_notification_async") as mock_send:
        SupportCockpitApp._check_mobile_ntfy_reminders(app, [case1, case2])
        assert mock_send.called
        kwargs = mock_send.call_args[1]
        assert NTFY_TAG_DIGEST in kwargs["tags"]
        assert "2" in kwargs["title"]
        assert "201" in app._last_ntfy_notified_ids
        assert "202" in app._last_ntfy_notified_ids
        assert len(app._ntfy_digest_queue) == 0


def test_app_check_mobile_ntfy_reminders_digest_prio1_bypass():
    from ui.app import SupportCockpitApp
    from constants import NTFY_PRIO_MAX, NTFY_TAG_ESCALATION
    from enums import UrgencyLevel

    app = MagicMock(spec=SupportCockpitApp)
    app.profile = UserProfile()
    app.profile.reminder_settings = ReminderSettings(
        mobile_ntfy_enabled=True,
        mobile_ntfy_topic="bypass-topic",
        mobile_ntfy_idle_minutes=5,
        mobile_ntfy_notify_followups=True,
        mobile_ntfy_notify_prio1=True,
        mobile_ntfy_digest_enabled=True,
        mobile_ntfy_digest_minutes=15,
    )
    app._last_ntfy_notified_ids = set()
    app._ntfy_digest_queue = []
    app._ntfy_last_digest_sent_at = 0.0

    IdleDetector.set_mock_state(idle_seconds=400.0, is_locked=False)

    routine_case = Case(
        case_id="301",
        classification=Classification(title="Routine Case"),
        workflow_status=WorkflowStatus(followup_at="2026-01-01 10:00:00"),
    )
    prio1_case = Case(
        case_id="999",
        classification=Classification(title="Server Down", urgency_level=UrgencyLevel.RED),
        workflow_status=WorkflowStatus(followup_at=""),
    )
    app.get_all_active_cases_for_reminder.return_value = [routine_case, prio1_case]

    with patch("services.ntfy_service.NtfyService.send_notification_async") as mock_send:
        SupportCockpitApp._check_mobile_ntfy_reminders(app, [routine_case])
        # Prio 1 should be dispatched immediately via Sofort-Bypass!
        assert mock_send.called
        kwargs = mock_send.call_args[1]
        assert "999" in kwargs["title"]
        assert kwargs["priority"] == NTFY_PRIO_MAX
        assert NTFY_TAG_ESCALATION in kwargs["tags"]
        assert "999" in app._last_ntfy_notified_ids

        # Routine case should be queued in digest buffer
        assert any(item["case_id"] == "301" for item in app._ntfy_digest_queue)


def test_app_check_mobile_ntfy_reminders_user_not_idle_clears_digest_queue():
    from ui.app import SupportCockpitApp

    app = MagicMock(spec=SupportCockpitApp)
    app.profile = UserProfile()
    app.profile.reminder_settings = ReminderSettings(
        mobile_ntfy_enabled=True,
        mobile_ntfy_topic="test-topic",
        mobile_ntfy_idle_minutes=5,
        mobile_ntfy_digest_enabled=True,
    )
    app._ntfy_digest_queue = [{"case_id": "401", "event_type": "followup", "dedup_key": "401:followup"}]
    app._ntfy_last_digest_sent_at = 100.0

    # User active at desk (idle = 0s)
    IdleDetector.set_mock_state(idle_seconds=0.0, is_locked=False)

    with patch("services.ntfy_service.NtfyService.send_notification_async") as mock_send:
        SupportCockpitApp._check_mobile_ntfy_reminders(app, [])
        assert not mock_send.called
        assert len(app._ntfy_digest_queue) == 0
        assert app._ntfy_last_digest_sent_at == 0.0
