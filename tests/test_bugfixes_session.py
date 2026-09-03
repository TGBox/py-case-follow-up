import sys
import importlib
from pathlib import Path
from unittest.mock import MagicMock

import pytest
import customtkinter as ctk

from services.tray_service import TrayService
from ui.widgets.case_list_widget import CaseListWidget
from models.case import Case, CaseCustomer, Classification, WorkflowStatus
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
            customer=CaseCustomer(customer_id="C01", practice_name="Test Practice"),
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


def test_report_tkinter_exception_signature():
    """Verify _report_tkinter_exception accepts both 3 args (exc, val, tb) and 4 args (self, exc, val, tb)."""
    root_dir = str(Path(__file__).parent.parent)
    if root_dir not in sys.path:
        sys.path.insert(0, root_dir)

    main_mod = importlib.import_module("main")
    _report_tkinter_exception = getattr(main_mod, "_report_tkinter_exception")

    try:
        raise ValueError("Test error for exception handler")
    except ValueError as e:
        tb = e.__traceback__
        exc_type = type(e)

        # 3 arguments call (traditional excepthook)
        _report_tkinter_exception(exc_type, e, tb)

        # 4 arguments call (Tkinter callback method style passing self)
        dummy_self = object()
        _report_tkinter_exception(dummy_self, exc_type, e, tb)


def test_render_textbox_field_height_lookup():
    """Verify rendering textbox field with UserProfile instance does not raise AttributeError."""
    from models.profile import UserProfile
    from models.schema import SchemaField
    from ui.widgets.dynamic_form_field_renderers import FieldRendererMixin

    profile = UserProfile()
    profile.ui_settings.custom_textbox_heights["test_field"] = 120

    class DummyRenderer(FieldRendererMixin):
        def __init__(self, prof):
            self.profile = prof
            self.storage_service = None

    renderer = DummyRenderer(profile)

    root = None
    try:
        root = ctk.CTk()
        root.withdraw()
    except Exception as e:
        pytest.skip(f"Tkinter environment unavailable: {e}")

    try:
        frame = ctk.CTkFrame(root)
        field = SchemaField(field_id="test_field", field_type="textbox", label="Test Textbox")
        target_dict = {}
        renderer._render_textbox_field(frame, field, "value", target_dict)
        assert "test_field" in target_dict
        ftype, textbox = target_dict["test_field"]
        assert ftype == "textbox"
        assert textbox.cget("height") == 120
    finally:
        if root is not None:
            root.destroy()
