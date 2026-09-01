import pytest
from models.profile import UISettings, UserProfile
from models.case import Case, WorkflowStatus, Classification, CaseCustomer
from services.scoring_service import ScoringService
from utils.ui_utils import get_app_monitor_bounds, center_window
from unittest.mock import MagicMock


def test_ui_settings_popup_display_target():
    # Test default
    ui = UISettings()
    assert ui.popup_display_target == "APP_SCREEN"

    # Test serialization
    data = ui.to_dict()
    assert data["popup_display_target"] == "APP_SCREEN"

    # Test deserialization with custom value
    data["popup_display_target"] = "PRIMARY_SCREEN"
    restored = UISettings.from_dict(data)
    assert restored.popup_display_target == "PRIMARY_SCREEN"

    # Test deserialization fallback on invalid string
    data["popup_display_target"] = "INVALID_SCREEN"
    restored_fallback = UISettings.from_dict(data)
    assert restored_fallback.popup_display_target == "APP_SCREEN"

    # Test reset_column_widths resets popup_display_target to default
    restored.reset_column_widths()
    assert restored.popup_display_target == "APP_SCREEN"


def test_get_app_monitor_bounds_fallback():
    mock_app = MagicMock()
    mock_app.winfo_toplevel.return_value = mock_app
    mock_app._last_geometry = None
    mock_app.winfo_x.return_value = 100
    mock_app.winfo_y.return_value = 150
    mock_app.winfo_width.return_value = 1200
    mock_app.winfo_height.return_value = 800
    mock_app.winfo_screenwidth.return_value = 1920
    mock_app.winfo_screenheight.return_value = 1080

    x, y, w, h = get_app_monitor_bounds(mock_app)
    assert (x, y, w, h) == (100, 150, 1200, 800)


def test_get_app_monitor_bounds_minimized_uses_last_geometry():
    mock_app = MagicMock()
    mock_app.winfo_toplevel.return_value = mock_app
    mock_app._last_geometry = (250, 300, 1400, 900)
    mock_app.winfo_x.return_value = -32000
    mock_app.winfo_y.return_value = -32000
    mock_app.winfo_width.return_value = 1
    mock_app.winfo_height.return_value = 1
    mock_app.winfo_screenwidth.return_value = 1920
    mock_app.winfo_screenheight.return_value = 1080

    x, y, w, h = get_app_monitor_bounds(mock_app)
    assert (x, y, w, h) == (250, 300, 1400, 900)


def test_case_completion_resets_followup_and_adds_timeline():
    case = Case(
        case_id="CASE-999",
        customer=CaseCustomer(customer_id="CUST-1", practice_name="Test Praxis", is_vip=True),
        classification=Classification(title="Test Ticket"),
        workflow_status=WorkflowStatus(
            is_completed=False,
            followup_at="2026-09-02T10:00:00",
            followup_note="Bitte anrufen",
        ),
    )

    scoring_service = ScoringService()
    assert scoring_service.calculate_score(case) > 0

    # Simulate marking as done
    new_state = not case.workflow_status.is_completed
    case.workflow_status.is_completed = new_state

    note_text = "Fall wieder geöffnet."
    change_text = "STATUS: Offen"
    if new_state:
        case.workflow_status.followup_at = ""
        note_text = "Fall auf erledigt gesetzt."
        change_text = "STATUS: Erledigt"

    from models.case import TimelineEntry
    from utils.datetime_utils import now_iso
    from enums import Channel

    entry = TimelineEntry(
        timestamp=now_iso(),
        author="Support Agent",
        channel=Channel.INTERNAL_NOTE.value,
        note=note_text,
        status_change=change_text,
    )
    case.timeline.append(entry)

    assert case.workflow_status.is_completed is True
    assert case.workflow_status.followup_at == ""
    assert len(case.timeline) == 1
    assert case.timeline[0].status_change == "STATUS: Erledigt"
    assert case.timeline[0].note == "Fall auf erledigt gesetzt."
    assert scoring_service.calculate_score(case) == 0.0
