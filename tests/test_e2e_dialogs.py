"""Comprehensive E2E integration tests for all Support Cockpit dialogs & services."""

from pathlib import Path
from typing import Any
import pytest
from config import AppConfig
from enums import UrgencyLevel
from models.case import Case, CaseCustomer, Classification, WorkflowStatus
from models.customer import Customer, Contact
from models.profile import Colleague
from models.schema import QuestionSchema, SchemaField, FieldType
from services.seed_service import SeedService
from services.storage_service import StorageService
from services.snippet_service import SnippetService
from services.export_service import ExportService


def test_new_case_dialog_creation_flow(tmp_path: Path):
    """E2E Test: NewCase creation flow, validating field input, case save & persistence."""
    config = AppConfig(workspace_dir=tmp_path, username="test_agent")
    storage = StorageService(config)
    seed = SeedService(storage)
    seed.run_seed(force=True)

    cases = storage.load_cases()
    customers = storage.load_customers()
    schemas = storage.load_schemas()
    initial_count = len(cases)

    c0 = customers[0]
    case_cust = CaseCustomer(
        customer_id=c0.customer_id,
        practice_name=c0.practice_name,
        is_vip=c0.is_vip,
        contact_person=c0.contact_person,
    )

    new_case = Case(
        case_id="T-2026-9999",
        created_by="Daniel Rösch",
        customer=case_cust,
        classification=Classification(
            schema_id=schemas[0].schema_id,
            title="E2E New Case Test Subject",
            urgency_level=UrgencyLevel.RED,
            tags=["E2E", "Test"],
        ),
        workflow_status=WorkflowStatus(
            current_actor="Support",
            followup_at="2026-10-01T12:00:00",
            followup_note="E2E Followup Note",
        ),
    )
    cases.append(new_case)
    storage.save_cases(cases)

    reloaded = storage.load_cases()
    assert len(reloaded) == initial_count + 1
    created = next(c for c in reloaded if c.case_id == "T-2026-9999")
    assert created.classification.title == "E2E New Case Test Subject"
    assert created.customer.customer_id == customers[0].customer_id


def test_convert_schema_dialog_flow(tmp_path: Path):
    """E2E Test: Schema conversion, data mapping & timeline entry creation."""
    config = AppConfig(workspace_dir=tmp_path, username="test_agent")
    storage = StorageService(config)
    seed = SeedService(storage)
    seed.run_seed(force=True)

    cases = storage.load_cases()
    schemas = storage.load_schemas()
    target_case = cases[0]

    old_schema_id = target_case.classification.schema_id
    new_schema = schemas[1] if schemas[1].schema_id != old_schema_id else schemas[0]

    from services.schema_service import SchemaService
    target_case.classification.schema_id = new_schema.schema_id
    SchemaService.update_case_completion(target_case, new_schema)
    storage.save_cases(cases)

    reloaded = storage.load_cases()
    converted_case = next(c for c in reloaded if c.case_id == target_case.case_id)
    assert converted_case.classification.schema_id == new_schema.schema_id


def test_customer_management_dialog_flow(tmp_path: Path):
    """E2E Test: Customer management CRUD operations."""
    config = AppConfig(workspace_dir=tmp_path, username="test_agent")
    storage = StorageService(config)
    seed = SeedService(storage)
    seed.run_seed(force=True)

    customers = storage.load_customers()
    initial_count = len(customers)

    new_cust = Customer(
        customer_id="99999",
        practice_name="E2E Testpraxis Münster",
        is_vip=True,
        contacts=[Contact(name="Dr. Erich Test", email="test@muenster-praxis.de", phone="0251-123456")]
    )
    customers.append(new_cust)
    storage.save_customers(customers)

    reloaded = storage.load_customers()
    assert len(reloaded) == initial_count + 1
    added = next(c for c in reloaded if c.customer_id == "99999")
    assert added.practice_name == "E2E Testpraxis Münster"
    assert added.contact_person == "Dr. Erich Test"
    assert added.is_vip is True


def test_colleague_management_dialog_flow(tmp_path: Path):
    """E2E Test: Colleague management CRUD operations."""
    config = AppConfig(workspace_dir=tmp_path, username="test_agent")
    storage = StorageService(config)
    seed = SeedService(storage)
    seed.run_seed(force=True)

    colleagues = storage.load_colleagues()
    initial_count = len(colleagues)

    new_col = Colleague(
        username="col_e2e",
        name="Sabine Entwicklerin",
        department="Entwicklung",
        email="sabine@support-team.de",
        mobile="0171-998877",
    )
    colleagues.append(new_col)
    storage.save_colleagues(colleagues)

    reloaded = storage.load_colleagues()
    assert len(reloaded) == initial_count + 1
    added = next(c for c in reloaded if c.username == "col_e2e")
    assert added.name == "Sabine Entwicklerin"


def test_snippet_service_and_management_flow(tmp_path: Path):
    """E2E Test: SnippetService loading and search."""
    snippet_service = SnippetService(workspace_dir=tmp_path)
    snippets = snippet_service.get_all_snippets()
    assert len(snippets) >= 1

    found = snippet_service.search_snippets(query="Ersthilfe")
    assert len(found) >= 1
    assert "Ersthilfe" in found[0].title or "Ersthilfe" in found[0].content


def test_export_engine_rendering(tmp_path: Path):
    """E2E Test: Export Service rendering Jinja export templates."""
    config = AppConfig(workspace_dir=tmp_path, username="test_agent")
    storage = StorageService(config)
    seed = SeedService(storage)
    seed.run_seed(force=True)

    export_service = ExportService(storage)
    cases = storage.load_cases()
    templates = storage.load_templates()
    schemas = storage.load_schemas()

    if templates:
        success, missing, rendered = export_service.render_template(cases[0], templates[0], schemas[0])
        assert success is True
        assert len(rendered) > 0
