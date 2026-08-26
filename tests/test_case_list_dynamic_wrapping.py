"""Tests for dynamic wraplength recalculation on configure and 3-line followup cards in CaseListWidget."""

import customtkinter as ctk
import pytest
from enums import Actor, UrgencyLevel
from models.case import Case, CaseCustomer, Classification, WorkflowStatus
from ui.widgets.case_list_widget import CaseListWidget


def test_case_list_widget_3_line_followup_and_dynamic_wrapping():
    """Verify CaseListWidget renders followups across 3 lines and dynamically adjusts wraplength on configure."""
    app = ctk.CTk()
    app.withdraw()

    selected_cases = []
    widget = CaseListWidget(
        app,
        on_case_selected=lambda c: selected_cases.append(c),
        on_search_changed=lambda s: None,
    )

    case = Case(
        case_id="T-2026-100",
        customer=CaseCustomer(customer_id="K-1", practice_name="Gemeinschaftspraxis Nord"),
        classification=Classification(title="Zuzahlungsfehler", urgency_level=UrgencyLevel.YELLOW),
        workflow_status=WorkflowStatus(
            followup_at="2026-08-26T14:30:00",
            followup_note="Wegen Rückmeldung anrufen",
            current_actor=Actor.SUPPORT,
        ),
    )

    widget.set_cases([case])

    # Verify wrap labels are registered
    assert len(widget.wrap_labels) >= 3

    # Check 3-line followup label texts
    all_texts = [lbl.cget("text") for lbl in widget.wrap_labels]
    assert any("🔔 Nachfragen am:" in t for t in all_texts)
    assert any("26.08.2026" in t for t in all_texts)
    assert any("14:30 Uhr" in t for t in all_texts)
    assert any("Wegen Rückmeldung anrufen" in t for t in all_texts)

    # Test dynamic configure resize
    initial_wrap = widget.wrap_labels[0].cget("wraplength")
    widget._last_wrap_width = 100
    widget.configure(width=400)

    class DummyEvent:
        pass

    widget._on_widget_configure(DummyEvent())
    assert widget.wrap_labels[0].cget("wraplength") >= 160

    widget.destroy()
    app.destroy()
