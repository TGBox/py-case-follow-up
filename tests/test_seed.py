import sqlite3
import pytest
from pathlib import Path
from config import AppConfig
from services.storage_service import StorageService
from services.seed_service import SeedService


def test_seed_generation(tmp_path: Path):
    config = AppConfig(workspace_dir=tmp_path, username="test_agent")
    storage = StorageService(config)
    seed_service = SeedService(storage)

    summary = seed_service.run_seed(force=True)

    assert summary["customers"] == 5
    assert summary["cases"] == 8
    assert summary["schemas"] == 3
    assert summary["templates"] == 4

    # Check files exist
    assert config.cases_path.exists()
    assert config.customers_path.exists()
    assert config.question_schemas_path.exists()
    assert config.export_templates_path.exists()
    assert config.wiki_db_path.exists()

    # Check loaded data
    cases = storage.load_cases()
    assert len(cases) == 8

    # Test SQLite Wiki FTS5 query
    conn = sqlite3.connect(config.wiki_db_path)
    cursor = conn.cursor()
    cursor.execute("SELECT page_id, title FROM wiki_fts WHERE wiki_fts MATCH 'ERR_DB_EXPORT_902'")
    results = cursor.fetchall()
    conn.close()

    assert len(results) >= 1
    assert "Abrechnungs-Engine" in results[0][1]
