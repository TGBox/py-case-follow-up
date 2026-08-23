import pytest
from enums import Actor, UrgencyLevel
from models.case import Case
from services.search_service import SearchService, parse_search_query


def test_search_service_filters_by_actor_and_vip():
    c1 = Case(case_id="T-001")
    c1.customer.is_vip = True
    c1.classification.title = "Datenbank Problem"
    c1.workflow_status.current_actor = Actor.DEVELOPMENT

    c2 = Case(case_id="T-002")
    c2.customer.is_vip = False
    c2.classification.title = "Support Ticket"
    c2.workflow_status.current_actor = Actor.SUPPORT

    cases = [c1, c2]
    search_svc = SearchService()

    # Query for DEV actor
    res_dev = search_svc.filter_cases(cases, "actor:dev")
    assert len(res_dev) == 1
    assert res_dev[0].case_id == "T-001"

    # Query for VIP customer
    res_vip = search_svc.filter_cases(cases, "vip:true")
    assert len(res_vip) == 1
    assert res_vip[0].case_id == "T-001"


def test_search_service_filters_by_tags_and_status():
    c1 = Case(case_id="T-100")
    c1.classification.title = "Abrechnung Fehler"
    c1.classification.tags = ["pvs", "abrechnung"]
    c1.workflow_status.is_completed = False

    c2 = Case(case_id="T-200")
    c2.classification.title = "Abrechnung Erledigt"
    c2.classification.tags = ["abrechnung"]
    c2.workflow_status.is_completed = True

    cases = [c1, c2]
    search_svc = SearchService()

    # Query by tag pvs
    res_tag = search_svc.filter_cases(cases, "tag:pvs")
    assert len(res_tag) == 1
    assert res_tag[0].case_id == "T-100"

    # Query by status done
    res_done = search_svc.filter_cases(cases, "status:done")
    assert len(res_done) == 1
    assert res_done[0].case_id == "T-200"


def test_search_service_free_text_matching():
    c1 = Case(case_id="T-301")
    c1.classification.title = "Zuzahlung im System fehlgeschlagen"

    c2 = Case(case_id="T-302")
    c2.classification.title = "Drucker verbindet nicht"

    cases = [c1, c2]
    search_svc = SearchService()

    res = search_svc.filter_cases(cases, "Zuzahlung")
    assert len(res) >= 1
    assert res[0].case_id == "T-301"
