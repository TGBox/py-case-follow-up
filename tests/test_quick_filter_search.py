"""Tests for quick filter search tokens (is:internal, vip:true, etc.) in SearchService."""

import pytest
from models.case import Case, CaseCustomer
from services.search_service import SearchService


def test_quick_filter_search_tokens():
    """Verify SearchService filter_cases handles tokenized queries such as is:internal and vip:true."""
    search_svc = SearchService()

    c_vip = Case(case_id="T-01", customer=CaseCustomer(is_vip=True))
    c_int = Case(case_id="T-02", customer=CaseCustomer(customer_id="INTERNAL", practice_name="Intern"))
    c_norm = Case(case_id="T-03", customer=CaseCustomer(is_vip=False))

    cases = [c_vip, c_int, c_norm]

    # Test is:internal
    res_int = search_svc.filter_cases(cases, "is:internal")
    assert len(res_int) == 1
    assert res_int[0].case_id == "T-02"

    # Test vip:true
    res_vip = search_svc.filter_cases(cases, "vip:true")
    assert len(res_vip) == 1
    assert res_vip[0].case_id == "T-01"
