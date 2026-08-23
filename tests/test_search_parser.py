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


def test_search_by_tag():
    c1 = Case(
        case_id="T-010",
        customer=CaseCustomer(practice_name="Praxis Tag Test"),
        classification=Classification(tags=["Abrechnung", "KV-BW"]),
    )
    c2 = Case(
        case_id="T-011",
        customer=CaseCustomer(practice_name="Praxis Bug Test"),
        classification=Classification(tags=["Hardware", "Drucker"]),
    )
    cases = [c1, c2]

    res = SearchService.filter_cases(cases, "tag:Abrechnung")
    assert len(res) == 1
    assert res[0].case_id == "T-010"

    res = SearchService.filter_cases(cases, "Drucker")
    assert len(res) == 1
    assert res[0].case_id == "T-011"


def test_search_by_followup_reminder():
    now = datetime(2026, 8, 23, 14, 0, 0)
    c1 = Case(
        case_id="T-020",
        customer=CaseCustomer(practice_name="Praxis Reminder"),
        workflow_status=WorkflowStatus(followup_at="2026-08-22T09:00:00", followup_note="Beim Dev nachfragen"),
    )
    c2 = Case(
        case_id="T-021",
        customer=CaseCustomer(practice_name="Praxis Clean"),
        workflow_status=WorkflowStatus(followup_at="", followup_note=""),
    )
    cases = [c1, c2]

    res = SearchService.filter_cases(cases, "reminder:due", now)
    assert len(res) == 1
    assert res[0].case_id == "T-020"

    res = SearchService.filter_cases(cases, "Dev nachfragen", now)
    assert len(res) == 1
    assert res[0].case_id == "T-020"


def test_search_contact_person_and_phone():
    c1 = Case(
        case_id="T-030",
        customer=CaseCustomer(practice_name="Praxis Dr. Weber", contact_person="Dr. Sabine Weber", phone="+49 731 123456"),
    )
    cases = [c1]

    assert len(SearchService.filter_cases(cases, "Sabine")) == 1
    assert len(SearchService.filter_cases(cases, "123456")) == 1
    assert len(SearchService.filter_cases(cases, "NichtVorhanden")) == 0


def test_search_empty_query_returns_all():
    cases = [Case(case_id="T-1"), Case(case_id="T-2")]
    assert len(SearchService.filter_cases(cases, "")) == 2
    assert len(SearchService.filter_cases(cases, "   ")) == 2


def test_search_malformed_token_fallback():
    cases = [Case(case_id="T-1", customer=CaseCustomer(practice_name="Sonderfall"), form_data={"note": "value"})]
    res = SearchService.filter_cases(cases, "unknown_key:value Sonderfall")
    assert len(res) == 1
    assert res[0].case_id == "T-1"
