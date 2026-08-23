import pytest
from pathlib import Path
from models.case import Case, CaseCustomer, Classification, WorkflowStatus
from services.search_service import SearchService, parse_search_query
from services.storage_service import StorageService, AppConfig


def test_internal_case_customer_validation():
    cust_internal = CaseCustomer(customer_id="INTERNAL", practice_name="Intern / Keine Praxis")
    errors = cust_internal.validate()
    assert len(errors) == 0

    cust_invalid = CaseCustomer(customer_id="", practice_name="")
    errors_inv = cust_invalid.validate()
    assert len(errors_inv) >= 1


def test_case_is_internal_property():
    c_internal = Case(case_id="T-INT-01")
    c_internal.customer = CaseCustomer(customer_id="INTERNAL", practice_name="Intern / Keine Praxis")
    assert c_internal.is_internal is True

    c_customer = Case(case_id="T-CUST-01")
    c_customer.customer = CaseCustomer(customer_id="K-10001", practice_name="Zahnarztpraxis Dr. Weiss")
    assert c_customer.is_internal is False


def test_search_service_filters_internal_cases():
    c1 = Case(case_id="T-01")
    c1.customer = CaseCustomer(customer_id="INTERNAL", practice_name="Intern / Keine Praxis")
    c1.classification.title = "Server-Wartung DB-Migration"

    c2 = Case(case_id="T-02")
    c2.customer = CaseCustomer(customer_id="K-10200", practice_name="Praxis Alpha")
    c2.classification.title = "Rechnungsabgleich"

    cases = [c1, c2]
    search_svc = SearchService()

    # Query for internal cases
    res_int = search_svc.filter_cases(cases, "is:internal")
    assert len(res_int) == 1
    assert res_int[0].case_id == "T-01"

    # Query for customer cases
    res_cust = search_svc.filter_cases(cases, "is:customer")
    assert len(res_cust) == 1
    assert res_cust[0].case_id == "T-02"


def test_storage_saves_and_loads_internal_case(tmp_path: Path):
    config = AppConfig(workspace_dir=tmp_path)
    storage = StorageService(config)

    c_int = Case(
        case_id="T-INT-999",
        customer=CaseCustomer(customer_id="INTERNAL", practice_name="Intern / Keine Praxis"),
        classification=Classification(schema_id="schema_internal_task", title="Prozess-Dokumentation erstellen"),
    )

    storage.save_cases([c_int])

    loaded_cases = storage.load_cases()
    assert len(loaded_cases) == 1
    assert loaded_cases[0].is_internal is True
    assert loaded_cases[0].customer.customer_id == "INTERNAL"
    assert loaded_cases[0].classification.title == "Prozess-Dokumentation erstellen"
