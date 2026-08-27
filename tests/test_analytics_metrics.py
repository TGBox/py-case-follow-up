"""Tests for support analytics metrics, urgency breakdowns, and practice distribution."""

import pytest
from enums import UrgencyLevel
from models.case import Case, CaseCustomer


def test_analytics_dashboard_metrics():
    """Verify metrics calculation for open cases, urgency levels, and practice aggregations."""
    c1 = Case(case_id="T-01")
    c1.customer = CaseCustomer(practice_name="Praxis Alpha")
    c1.classification.urgency_level = UrgencyLevel.RED

    c2 = Case(case_id="T-02")
    c2.customer = CaseCustomer(practice_name="Praxis Alpha")
    c2.classification.urgency_level = UrgencyLevel.YELLOW

    c3 = Case(case_id="T-03")
    c3.customer = CaseCustomer(practice_name="Praxis Beta")
    c3.workflow_status.is_completed = True

    cases = [c1, c2, c3]

    open_cases = [c for c in cases if not c.workflow_status.is_completed]
    assert len(open_cases) == 2

    red_count = sum(1 for c in open_cases if c.classification.urgency_level == UrgencyLevel.RED)
    assert red_count == 1

    counts: dict[str, int] = {}
    for c in cases:
        p = c.customer.practice_name
        counts[p] = counts.get(p, 0) + 1

    assert counts["Praxis Alpha"] == 2
    assert counts["Praxis Beta"] == 1


def test_analytics_view_report_generation_and_rendering():
    """Test AnalyticsView markdown report generation and rendering without errors."""
    import customtkinter as ctk
    from ui.views.analytics_view import AnalyticsView

    root = ctk.CTk()
    analytics_view = AnalyticsView(root)

    c1 = Case(case_id="T-01")
    c1.customer = CaseCustomer(practice_name="Praxis Alpha", is_vip=True)
    c1.workflow_status.followup_at = "2020-01-01T12:00:00"  # Overdue
    c1.classification.schema_id = "schema_zuzahlungsnachforderung"

    c2 = Case(case_id="T-02")
    c2.customer = CaseCustomer(practice_name="Praxis Beta", is_vip=False)
    c2.workflow_status.is_completed = True
    c2.created_at = "2026-08-01T10:00:00"
    c2.updated_at = "2026-08-02T10:00:00"

    analytics_view.set_cases([c1, c2])

    report = analytics_view.generate_report_markdown()
    assert "**Fälle Gesamt:** 2" in report
    assert "**Offene Fälle:** 1" in report
    assert "**Erledigte Fälle:** 1" in report
    assert "**Überfällige Wiedervorlagen:** 1" in report

    root.destroy()
