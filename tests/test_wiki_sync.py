import pytest
from pathlib import Path
from src.config import AppConfig
from src.enums import SyncMode
from src.models.profile import WikiSettings
from src.services.wiki_sync_service import WikiSyncService


class MockBookStackClient:
    def get_pages(self):
        return [
            {"id": 1, "book_id": 10, "name": "Abrechnung FAQ", "slug": "abrechnung-faq", "url": "http://wiki/pages/1", "updated_at": "2026-08-01"},
            {"id": 2, "book_id": 10, "name": "Fehlercode ERR_DB_902", "slug": "err-db-902", "url": "http://wiki/pages/2", "updated_at": "2026-08-02"},
        ]

    def get_page_content(self, page_id):
        if page_id == 1:
            return "Anleitung zur KV-Abrechnung und Nachforderungsdateien."
        return "Detailierte Beschreibung von ERR_DB_902 und Datenbank-Patches."


def test_wiki_sync_metadata(tmp_path: Path):
    config = AppConfig(workspace_dir=tmp_path)
    settings = WikiSettings(api_url="http://wiki", sync_mode=SyncMode.METADATA_ONLY)
    service = WikiSyncService(config, settings)

    mock_client = MockBookStackClient()
    success, msg = service.sync_from_bookstack(mock_client=mock_client)

    assert success is True
    assert "2 pages" in msg

    results = service.search("Abrechnung")
    assert len(results) >= 1
    assert "Abrechnung FAQ" in results[0]["title"]


def test_wiki_sync_full_offline(tmp_path: Path):
    config = AppConfig(workspace_dir=tmp_path)
    settings = WikiSettings(api_url="http://wiki", sync_mode=SyncMode.FULL_OFFLINE)
    service = WikiSyncService(config, settings)

    mock_client = MockBookStackClient()
    success, msg = service.sync_from_bookstack(mock_client=mock_client)

    assert success is True

    results = service.search("ERR_DB_902")
    assert len(results) >= 1
    assert "ERR_DB_902" in results[0]["title"]
