import pytest
from pathlib import Path
from models.profile import WikiSettings
from services.wiki_sync_service import WikiSyncService
from services.storage_service import AppConfig


class MockBookStackClient:
    def get_pages(self):
        return [
            {
                "id": 101,
                "book_id": 1,
                "name": "Zuzahlungsnachforderung im PVS",
                "slug": "zuzahlung-pvs",
                "url": "https://wiki.intern/zuzahlung",
                "updated_at": "2026-08-20T10:00:00",
            },
            {
                "id": 102,
                "book_id": 1,
                "name": "GitLab Bug-Report erstellen",
                "slug": "gitlab-bug",
                "url": "https://wiki.intern/gitlab-bug",
                "updated_at": "2026-08-21T12:00:00",
            },
        ]

    def get_page_content(self, page_id: int):
        if page_id == 101:
            return "Detaillierte Anleitung für Zuzahlungsnachforderung im PVS System."
        return "Tipps zum Erstellen von Bug-Reports in GitLab."


def test_wiki_sync_service_search_and_offline_cache(tmp_path: Path):
    config = AppConfig(workspace_dir=tmp_path)
    config.ensure_directories()

    settings = WikiSettings(api_url="https://wiki.test", sync_mode="FULL_OFFLINE")
    wiki_service = WikiSyncService(config, settings)

    mock_client = MockBookStackClient()
    success, msg = wiki_service.sync_from_bookstack(mock_client=mock_client)

    assert success is True
    assert "2 pages" in msg

    # Search in offline SQLite database
    res_zuzahlung = wiki_service.search("Zuzahlung")
    assert len(res_zuzahlung) >= 1
    assert res_zuzahlung[0]["page_id"] == 101
    assert "Zuzahlung" in res_zuzahlung[0]["title"]

    res_gitlab = wiki_service.search("GitLab")
    assert len(res_gitlab) >= 1
    assert res_gitlab[0]["page_id"] == 102
