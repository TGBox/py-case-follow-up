import pytest
from models.case import Case, CaseCustomer, Classification, WorkflowStatus, TimelineEntry
from enums import UrgencyLevel, BoardColumn, Actor


def test_analytics_dashboard_metrics():
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

    counts = {}
    for c in cases:
        p = c.customer.practice_name
        counts[p] = counts.get(p, 0) + 1

    assert counts["Praxis Alpha"] == 2
    assert counts["Praxis Beta"] == 1


def test_case_print_report_formatting():
    c = Case(case_id="T-PRINT-01")
    c.customer = CaseCustomer(customer_id="K-500", practice_name="Zahnarzt Dr. Sonntags", contact_person="Herr Lehmann")
    c.classification = Classification(title="PVS Serverabsturz")
    c.form_data = {"affected_user": "Dr. Sonntags", "error_code": "ERR_503"}
    c.timeline.append(TimelineEntry(timestamp="2026-08-23T10:00:00", author="Support Agent", note="Ticket aufgenommen"))
    c.timeline.append(TimelineEntry(timestamp="2026-08-23T11:30:00", author="Support Agent", note="Interner Testlauf"))

    assert c.customer.customer_id == "K-500"
    assert len(c.timeline) == 2
    assert c.form_data["error_code"] == "ERR_503"
