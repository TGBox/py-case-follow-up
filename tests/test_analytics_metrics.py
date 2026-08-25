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
