import pytest
import customtkinter as ctk
from unittest.mock import MagicMock

from services.tray_service import TrayService
from ui.widgets.case_list_widget import CaseListWidget
from models.case import Case, Classification, WorkflowStatus
from models.customer import Customer
from enums import UrgencyLevel, Actor


def test_tray_service_single_start():
    """Verify TrayService does not launch duplicate threads when start() is called multiple times."""
    service = TrayService()
    mock_restore = MagicMock()
    mock_quit = MagicMock()

    service.start(on_restore=mock_restore, on_quit=mock_quit)
    first_thread = service._thread

    # Call start again
    service.start(on_restore=mock_restore, on_quit=mock_quit)
    assert service._thread is first_thread

    # Clean up
    service.stop()
    assert service._icon is None
    assert service._thread is None


def test_case_list_widget_score_label_packing_order(monkeypatch):
    """Verify score_lbl is packed before dot and case_id_lbl in top_row."""
    root = ctk.CTk()
    root.withdraw()
    try:
        dummy_case = Case(
            case_id="TEST-001",
            customer=Customer(customer_id="C01", practice_name="Test Practice"),
            classification=Classification(title="Test", calculated_score=85.0, urgency_level=UrgencyLevel.RED),
            workflow_status=WorkflowStatus(current_actor=Actor.SUPPORT),
        )

        widget = CaseListWidget(root, on_case_selected=lambda c: None, on_search_changed=lambda s: None)
        widget.set_cases([dummy_case])

        # Get card top row frame
        scroll_children = widget.scroll_frame.winfo_children()
        assert len(scroll_children) == 1
        card = scroll_children[0]
        card_children = card.winfo_children()
        top_row = card_children[0]

        top_row_children = top_row.winfo_children()
        assert len(top_row_children) == 3

        # First child of top_row must be the score label (packed side="right" first)
        first_child = top_row_children[0]
        assert "Pkt.: 85" in first_child.cget("text")
    finally:
        root.destroy()
