"""Deep storage robustness, data corruption recovery, and edge case resilience test suite."""

import json
import zipfile
from pathlib import Path
import pytest
from config import AppConfig
from models.case import Case, Classification, CaseCustomer, TimelineEntry
from models.customer import Customer, Contact
from models.snippet import Snippet
from models.schema import QuestionSchema, SchemaField
from models.export_template import ExportTemplate
from models.profile import Colleague, UserProfile
from services.storage_service import StorageService
from services.snippet_service import SnippetService
from services.zip_backup_service import ZipBackupService
from services.p2p_sync_service import P2PSyncService
from services.cobra_crm_import_service import CobraCrmImportService
from services.export_service import ExportService


def test_corrupted_customers_json_fallback(tmp_path: Path):
    """Test storage service recovering gracefully from a corrupted customers.json file."""
    config = AppConfig(workspace_dir=tmp_path, username="agent")
    storage = StorageService(config)

    cust_file = config.customers_path
    cust_file.parent.mkdir(parents=True, exist_ok=True)
    cust_file.write_text("{ MALFORMED JSON DATA ...", encoding="utf-8")

    customers = storage.load_customers()
    assert isinstance(customers, list)
    assert len(customers) == 0


def test_corrupted_snippets_json_fallback(tmp_path: Path):
    """Test snippet service recovering gracefully from a corrupted snippets.json file by seeding default snippets."""
    config = AppConfig(workspace_dir=tmp_path, username="agent")

    snip_file = config.data_dir / "snippets.json"
    snip_file.parent.mkdir(parents=True, exist_ok=True)
    snip_file.write_text("[INVALID_ARRAY_ENTRY...", encoding="utf-8")

    snippet_service = SnippetService(workspace_dir=tmp_path)
    snippets = snippet_service.load_snippets()
    assert isinstance(snippets, list)
    assert len(snippets) > 0  # Fallback to default seeded snippets


def test_corrupted_schemas_json_fallback(tmp_path: Path):
    """Test storage service recovering gracefully from a corrupted question_schemas.json file."""
    config = AppConfig(workspace_dir=tmp_path, username="agent")
    storage = StorageService(config)

    schema_file = config.question_schemas_path
    schema_file.parent.mkdir(parents=True, exist_ok=True)
    schema_file.write_text("{BROKEN_SCHEMA_JSON}", encoding="utf-8")

    schemas = storage.load_schemas()
    assert isinstance(schemas, list)
    assert len(schemas) == 0


def test_corrupted_templates_json_fallback(tmp_path: Path):
    """Test storage service recovering gracefully from a corrupted export_templates.json file."""
    config = AppConfig(workspace_dir=tmp_path, username="agent")
    storage = StorageService(config)

    tpl_file = config.export_templates_path
    tpl_file.parent.mkdir(parents=True, exist_ok=True)
    tpl_file.write_text("NOT_EVEN_JSON", encoding="utf-8")

    templates = storage.load_templates()
    assert isinstance(templates, list)
    assert len(templates) == 0


def test_corrupted_colleagues_json_fallback(tmp_path: Path):
    """Test storage service recovering gracefully from a corrupted colleagues.json file."""
    config = AppConfig(workspace_dir=tmp_path, username="agent")
    storage = StorageService(config)

    col_file = config.colleagues_path
    col_file.parent.mkdir(parents=True, exist_ok=True)
    col_file.write_text("<<<XML>>>", encoding="utf-8")

    colleagues = storage.load_colleagues()
    assert isinstance(colleagues, list)
    assert len(colleagues) == 0


def test_cases_json_with_invalid_field_types(tmp_path: Path):
    """Test parsing cases when JSON fields have mismatched types (e.g., string instead of list)."""
    config = AppConfig(workspace_dir=tmp_path, username="agent")
    storage = StorageService(config)

    cases_file = config.cases_path
    cases_file.parent.mkdir(parents=True, exist_ok=True)

    bad_data = [
        {
            "case_id": "CASE-999",
            "customer": {"customer_id": "C-1", "practice_name": "Test Praxis"},
            "classification": {
                "schema_id": "general",
                "title": "Bad Types Test",
                "tags": "invalid_string_instead_of_list",
            },
            "timeline": "invalid_timeline_instead_of_list",
        }
    ]
    cases_file.write_text(json.dumps(bad_data), encoding="utf-8")

    cases = storage.load_cases()
    assert len(cases) == 1
    assert cases[0].case_id == "CASE-999"
    assert isinstance(cases[0].classification.tags, list)
    assert isinstance(cases[0].timeline, list)


def test_zip_backup_inspect_corrupted_file(tmp_path: Path):
    """Test ZipBackupService handling inspection of a corrupted non-zip file."""
    fake_zip = tmp_path / "broken_backup.zip"
    fake_zip.write_text("This is not a zip file", encoding="utf-8")

    with pytest.raises(zipfile.BadZipFile):
        ZipBackupService.inspect_backup_zip(fake_zip)


def test_p2p_sync_corrupted_colleague_file(tmp_path: Path):
    """Test P2PSyncService handling a colleague whose case file is corrupted."""
    config = AppConfig(workspace_dir=tmp_path, username="my_user")
    storage = StorageService(config)

    colleague_dir = tmp_path / "colleague_share"
    colleague_dir.mkdir(parents=True, exist_ok=True)
    colleague_cases = colleague_dir / "cases.json"
    colleague_cases.write_text("CORRUPTED_JSON_CONTENT", encoding="utf-8")

    colleague = Colleague(username="colleague1", name="Colleague One", cases_path=str(colleague_cases))
    p2p_service = P2PSyncService(storage)

    success, msg, remote_cases = p2p_service.read_colleague_cases(colleague)
    assert success is True  # safe_read_json renames corrupted file and returns empty list gracefully
    assert len(remote_cases) == 0


def test_cobra_import_latin1_encoding_file(tmp_path: Path):
    """Test CobraCrmImportService parsing a file encoded in Latin-1 / CP1252 with special characters."""
    csv_file = tmp_path / "cobra_export_latin1.csv"
    content = "Kunden_Nr;Firma;Ansprechpartner;Telefon\nK-101;Praxis Dr. Mueller & Co.;Baerbel Schuetz;030-123456"
    csv_file.write_bytes(content.encode("latin-1"))

    raw_rows, headers = CobraCrmImportService.parse_file(csv_file)
    assert len(raw_rows) == 1
    mapping = CobraCrmImportService.auto_detect_mapping(headers)

    customers = CobraCrmImportService.map_rows_to_customers(raw_rows, mapping)
    assert len(customers) == 1
    assert customers[0].customer_id == "K-101"


def test_export_service_render_missing_fields(tmp_path: Path):
    """Test ExportService rendering a case with missing schema fields or empty values."""
    config = AppConfig(workspace_dir=tmp_path, username="agent")
    storage = StorageService(config)
    export_service = ExportService(storage)

    case = Case(
        case_id="CASE-ROBUST-1",
        customer=CaseCustomer(customer_id="C-55", practice_name="Test Praxis"),
        classification=Classification(schema_id="standard", title="Minimal Case"),
    )

    template = ExportTemplate(
        template_id="tpl_test",
        display_name="Test Template",
        template_string="Fall-ID: {{ case.case_id }} | Praxis: {{ case.customer.practice_name }}",
    )

    ok, missing, rendered = export_service.render_template(case, template)
    assert ok is True
    assert "Fall-ID: CASE-ROBUST-1" in rendered
    assert "Praxis: Test Praxis" in rendered
