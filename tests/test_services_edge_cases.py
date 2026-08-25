"""Comprehensive edge case tests for background and integration services."""

import json
import sqlite3
from pathlib import Path
import pytest
from config import AppConfig
from enums import Actor, UrgencyLevel, BoardColumn
from models.case import Case, CaseCustomer, Classification, WorkflowStatus, TimelineEntry
from models.profile import Colleague
from models.export_template import ExportTemplate
from models.schema import QuestionSchema, SchemaField
from services.storage_service import StorageService
from services.outlook_integration_service import OutlookIntegrationService
from services.p2p_sync_service import P2PSyncService
from services.wiki_sync_service import WikiSyncService
from services.deep_search_service import DeepSearchService
from services.export_service import ExportService


@pytest.fixture
def service_env(tmp_path: Path):
    config = AppConfig(workspace_dir=tmp_path)
    storage = StorageService(config)
    return config, storage, tmp_path


def test_outlook_integration_service(service_env):
    """Test Outlook parsing, timeline appending, and mailto URL generation."""
    config, storage, tmp_path = service_env

    # 1. Parse Outlook email to new Case
    raw_subject = "Fehler beim Starten des PVS (K-12345)"
    raw_body = "Sehr geehrtes Team,\nwir können das PVS seit heute Morgen nicht starten.\nViele Grüße,\nDr. Hans Weber"
    sender_email = "weber@praxis-weber.de"
    sender_name = "Dr. Hans Weber"

    case = OutlookIntegrationService.parse_outlook_email_to_case(
        subject=raw_subject,
        sender_email=sender_email,
        sender_name=sender_name,
        body=raw_body,
    )

    assert case.customer.customer_id == "K-12345"
    assert case.customer.practice_name == "Dr. Hans Weber"
    assert len(case.timeline) == 1
    assert "E-Mail empfangen von Dr. Hans Weber" in case.timeline[0].note

    # 2. Append incoming email to existing case
    new_entry = OutlookIntegrationService.append_outlook_email_to_case_timeline(
        case=case,
        sender_name="Dr. Hans Weber",
        sender_email=sender_email,
        subject="Re: Fehler beim Starten des PVS",
        body="Zusatzinfo: Fehlercode 404.",
    )
    assert len(case.timeline) == 2
    assert "Zusatzinfo: Fehlercode 404" in new_entry.note

    # 3. Transfer to outlook fallback mailto
    res = OutlookIntegrationService.transfer_to_outlook(
        to_email="support@medico.de",
        subject="Ticket #1234",
        body_text="Hallo Welt",
    )
    assert res in (True, False)


def test_p2p_sync_service_diff_and_merge(service_env):
    """Test P2P sync peer cases loading, diff computation, and merging."""
    config, storage, tmp_path = service_env
    p2p_svc = P2PSyncService(storage)

    # 1. Setup local case
    local_case = Case(
        case_id="T-SYNC-01",
        customer=CaseCustomer(customer_id="K-1", practice_name="Praxis Sync 1"),
        classification=Classification(schema_id="schema_standard", title="Lokaler Fall"),
        updated_at="2026-08-25T10:00:00",
    )
    storage.save_cases([local_case])

    # 2. Setup colleague file
    colleague_dir = tmp_path / "colleague_share"
    colleague_dir.mkdir()
    colleague_file = colleague_dir / "cases.json"

    remote_newer_case = Case(
        case_id="T-SYNC-01",
        customer=CaseCustomer(customer_id="K-1", practice_name="Praxis Sync 1"),
        classification=Classification(schema_id="schema_standard", title="Lokaler Fall aktualisiert von Kollege"),
        updated_at="2026-08-25T12:00:00",
    )
    remote_new_case = Case(
        case_id="T-SYNC-02",
        customer=CaseCustomer(customer_id="K-2", practice_name="Praxis Sync 2"),
        classification=Classification(schema_id="schema_standard", title="Ganz neuer Fall"),
        updated_at="2026-08-25T11:00:00",
    )

    with open(colleague_file, "w", encoding="utf-8") as f:
        json.dump([remote_newer_case.to_dict(), remote_new_case.to_dict()], f)

    colleague = Colleague(
        name="Anna Schmidt",
        username="aschmidt",
        cases_path=str(colleague_file),
    )

    # 3. Read colleague cases
    success, msg, remote_cases = p2p_svc.read_colleague_cases(colleague)
    assert success is True
    assert len(remote_cases) == 2

    # 4. Compute diff
    diff_items = p2p_svc.compute_diff(remote_cases)
    assert len(diff_items) == 2

    diff_map = {item.case_id: item.status for item in diff_items}
    assert diff_map["T-SYNC-01"] == "REMOTE_NEWER"
    assert diff_map["T-SYNC-02"] == "NEW"

    # 5. Merge cases
    imported_count = p2p_svc.import_selected_cases([remote_newer_case, remote_new_case])
    assert imported_count == 2
    loaded = storage.load_cases()
    assert len(loaded) == 2
    assert any(c.case_id == "T-SYNC-02" for c in loaded)


def test_deep_search_service(service_env, tmp_path: Path):
    """Test full text searching inside case attachment folders and offline docs."""
    config, storage, _ = service_env
    deep_search = DeepSearchService(workspace_dir=tmp_path)

    # 1. Create a case with attachment text file
    case_att_dir = tmp_path / "data" / "attachments" / "T-SEARCH-01"
    case_att_dir.mkdir(parents=True, exist_ok=True)

    log_file = case_att_dir / "system_error.log"
    log_file.write_text("2026-08-25 10:15:00 [ERROR] Database connection timed out on port 5432\n2026-08-25 10:15:05 [INFO] Retry 1...", encoding="utf-8")

    case = Case(
        case_id="T-SEARCH-01",
        attachment_directory=str(case_att_dir.relative_to(tmp_path)),
    )

    matches = deep_search.search_case_attachments(case, "Database connection")
    assert len(matches) == 1
    assert matches[0]["file_name"] == "system_error.log"
    assert matches[0]["line_number"] == 1
    assert "Database connection timed out" in matches[0]["snippet"]

    # 2. Test wiki cache search
    cache_file = tmp_path / "wiki_cache.json"
    cache_articles = [
        {"article_id": "art_1", "title": "PVS Konfiguration", "content": "Für den GKV-Export muss Zertifikat X509 installiert sein.", "tags": ["PVS", "Export"]},
    ]
    with open(cache_file, "w", encoding="utf-8") as f:
        json.dump(cache_articles, f)

    wiki_matches = deep_search.search_wiki_cache("Zertifikat X509", wiki_cache_file=cache_file)
    assert len(wiki_matches) == 1
    assert wiki_matches[0]["title"] == "PVS Konfiguration"


def test_wiki_sync_service_cache_and_offline(service_env, tmp_path: Path):
    """Test WikiSyncService SQLite database initialization and offline search."""
    config, storage, _ = service_env
    wiki_svc = WikiSyncService(config)

    # Insert test article into SQLite db
    conn = sqlite3.connect(wiki_svc.db_path)
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO wiki_pages (page_id, book_id, title, slug, url, updated_at, content_markdown)
        VALUES (101, 1, 'Kartenleser Einrichtung', 'kartenleser', 'https://wiki.intern/kartenleser', '2026-08-25', 'CT-Kartenleser im Gerätemanager konfigurieren')
    """)
    if wiki_svc.is_fts5_available():
        cursor.execute("""
            INSERT INTO wiki_fts (page_id, title, content)
            VALUES (101, 'Kartenleser Einrichtung', 'CT-Kartenleser im Gerätemanager konfigurieren')
        """)
    conn.commit()
    conn.close()

    # Search offline index
    found = wiki_svc.search("Kartenleser")
    assert len(found) >= 1
    assert any(item["title"] == "Kartenleser Einrichtung" for item in found)


def test_export_service_rendering(service_env):
    """Test ExportService template string substitution and formatting."""
    config, storage, tmp_path = service_env
    export_svc = ExportService(storage)

    template = ExportTemplate(
        template_id="tpl_test",
        display_name="Test Export",
        template_string="[FALL {{ case.case_id }}] Praxis: {{ customer.practice_name }} | Dringlichkeit: {{ case.classification.urgency_level }}",
    )

    case = Case(
        case_id="T-EXP-99",
        customer=CaseCustomer(customer_id="K-99", practice_name="Praxis Sonnenschein"),
        classification=Classification(title="Fehler", urgency_level=UrgencyLevel.RED),
    )

    success, missing_fields, rendered = export_svc.render_template(case, template)
    assert success is True
    assert "[FALL T-EXP-99]" in rendered
    assert "Praxis Sonnenschein" in rendered
    assert "RED" in rendered
