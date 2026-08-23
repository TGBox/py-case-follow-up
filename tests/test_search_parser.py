from datetime import datetime, timedelta
import pytest
from models.case import Case, CaseCustomer, Classification, WorkflowStatus, TimelineEntry
from enums import UrgencyLevel, BoardColumn, Actor
from services.search_service import SearchService, parse_search_query
from utils.datetime_utils import format_iso


def test_parse_search_query():
    q = parse_search_query("vip:true actor:dev status:open error:ERR_902 Praxis Müller")
    assert q.vip is True
    assert q.actor == "dev"
    assert q.status == "open"
    assert q.error == "ERR_902"
    assert q.free_text_terms == ["Praxis", "Müller"]


def test_search_service_filtering():
    now = datetime(2026, 8, 23, 14, 0, 0)
    deadline_close = now + timedelta(hours=1)
    deadline_overdue = now - timedelta(hours=1)

    c1 = Case(
        case_id="T-001",
        customer=CaseCustomer(customer_id="K-100", practice_name="Praxis Alpha", is_vip=True),
        classification=Classification(title="Zuzahlungsfehler", deadline_callback=format_iso(deadline_close)),
        workflow_status=WorkflowStatus(current_actor=Actor.DEVELOPMENT, is_completed=False),
        form_data={"error_code": "ERR_DB_902"},
        timeline=[TimelineEntry(note="Abbruch beim Import")],
    )

    c2 = Case(
        case_id="T-002",
        customer=CaseCustomer(customer_id="K-200", practice_name="Praxis Beta", is_vip=False),
        classification=Classification(title="Rezeptdruck", deadline_callback=format_iso(deadline_overdue)),
        workflow_status=WorkflowStatus(current_actor=Actor.SUPPORT, is_completed=False),
        form_data={"error_code": "ERR_PRINT_01"},
        timeline=[TimelineEntry(note="Drucker antwortet nicht")],
    )

    cases = [c1, c2]

    # VIP filter
    res = SearchService.filter_cases(cases, "vip:true", now)
    assert len(res) == 1
    assert res[0].case_id == "T-001"

    # Actor filter
    res = SearchService.filter_cases(cases, "actor:dev", now)
    assert len(res) == 1
    assert res[0].case_id == "T-001"

    # Error code search
    res = SearchService.filter_cases(cases, "error:ERR_PRINT_01", now)
    assert len(res) == 1
    assert res[0].case_id == "T-002"

    # Deadline overdue search
    res = SearchService.filter_cases(cases, "deadline:overdue", now)
    assert len(res) == 1
    assert res[0].case_id == "T-002"

    # Free text search
    res = SearchService.filter_cases(cases, "Import", now)
    assert len(res) == 1
    assert res[0].case_id == "T-001"

    # Combined filter
    res = SearchService.filter_cases(cases, "vip:true actor:dev Zuzahlung", now)
    assert len(res) == 1
    assert res[0].case_id == "T-001"
