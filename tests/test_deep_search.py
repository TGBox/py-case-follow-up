import json
from pathlib import Path
from models.case import Case, CaseCustomer, Classification
from services.deep_search_service import DeepSearchService


def test_deep_search_attachment_files(tmp_path: Path):
    service = DeepSearchService(workspace_dir=tmp_path)

    # Create dummy attachment directory and log file
    att_dir = tmp_path / "data" / "attachments" / "T-2026-1001"
    att_dir.mkdir(parents=True, exist_ok=True)

    log_file = att_dir / "error_trace.log"
    log_file.write_text(
        "2026-08-24 10:00:00 [INFO] System started.\n"
        "2026-08-24 10:05:22 [ERROR] Fatal Exception: DB Connection Timeout (ErrCode AL-99)\n"
        "2026-08-24 10:06:00 [INFO] Retrying connection.\n",
        encoding="utf-8",
    )

    case = Case(
        case_id="T-2026-1001",
        customer=CaseCustomer(customer_id="K-101", practice_name="Test Praxis"),
        classification=Classification(title="Datenbank Fehler"),
        attachment_directory=str(att_dir),
    )

    matches = service.search_case_attachments(case, "AL-99")
    assert len(matches) == 1
    assert matches[0]["file_name"] == "error_trace.log"
    assert matches[0]["line_number"] == 2
    assert "ErrCode AL-99" in matches[0]["snippet"]


def test_deep_search_wiki_cache(tmp_path: Path):
    service = DeepSearchService(workspace_dir=tmp_path)

    wiki_file = tmp_path / "wiki_cache.json"
    wiki_data = [
        {
            "article_id": "W-01",
            "title": "Abrechnung Zuzahlung AL-99 Notfallanleitung",
            "content": "Tritt der Fehler AL-99 beim Export auf, muss der Server neugestartet werden.",
            "tags": ["abrechnung", "al-99"],
        }
    ]
    wiki_file.write_text(json.dumps(wiki_data), encoding="utf-8")

    matches = service.search_wiki_cache("AL-99", wiki_cache_file=wiki_file)
    assert len(matches) == 1
    assert matches[0]["article_id"] == "W-01"
    assert "Abrechnung Zuzahlung" in matches[0]["title"]


def test_perform_deep_search_aggregation(tmp_path: Path):
    service = DeepSearchService(workspace_dir=tmp_path)

    att_dir = tmp_path / "data" / "attachments" / "T-2026-1002"
    att_dir.mkdir(parents=True, exist_ok=True)
    (att_dir / "dump.sql").write_text("SELECT * FROM dbo.Kunden WHERE fehler='AL-99';", encoding="utf-8")

    case = Case(
        case_id="T-2026-1002",
        customer=CaseCustomer(customer_id="K-102", practice_name="MVZ Kardiologie"),
        classification=Classification(title="SQL Abfrage hängengeblieben"),
        attachment_directory=str(att_dir),
    )

    results = service.perform_deep_search([case], "dbo.Kunden")
    assert "T-2026-1002" in results
    att_matches = results["T-2026-1002"]["attachment_matches"]
    assert len(att_matches) == 1
    assert att_matches[0]["file_name"] == "dump.sql"
