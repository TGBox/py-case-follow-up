"""Comprehensive edge case, invalid input handling, and error recovery test suite."""

import json
from pathlib import Path
from typing import Any
import pytest
from config import AppConfig
from enums import SyncMode
from models.case import Case
from models.profile import UserProfile
from services.seed_service import SeedService
from services.storage_service import StorageService
from services.zip_backup_service import ZipBackupService
from services.wiki_sync_service import WikiSyncService


def test_corrupted_profile_json_recovery(tmp_path: Path):
    """Test storage service recovering gracefully from a corrupted app_profile.json file."""
    config = AppConfig(workspace_dir=tmp_path, username="test_agent")
    storage = StorageService(config)

    # Write broken invalid JSON to app_profile.json
    profile_file = config.app_profile_path
    profile_file.parent.mkdir(parents=True, exist_ok=True)
    profile_file.write_text("{ INVALID JSON BROKEN ... ", encoding="utf-8")

    # Storage load_profile should not crash, but fallback gracefully to default UserProfile
    profile = storage.load_profile()
    assert isinstance(profile, UserProfile)
    assert profile.ui_settings.theme in ["SYSTEM", "DARK", "LIGHT", "dark", "light", "system"]


def test_corrupted_cases_json_recovery(tmp_path: Path):
    """Test storage service handling corrupted or empty cases.json files."""
    config = AppConfig(workspace_dir=tmp_path, username="test_agent")
    storage = StorageService(config)

    cases_file = config.cases_path
    cases_file.parent.mkdir(parents=True, exist_ok=True)
    cases_file.write_text("NOT_JSON", encoding="utf-8")

    loaded_cases = storage.load_cases()
    assert isinstance(loaded_cases, list)
    assert len(loaded_cases) == 0


def test_wiki_sync_offline_fallback_handling(tmp_path: Path):
    """Test WikiSyncService initializing and searching offline SQLite DB."""
    config = AppConfig(workspace_dir=tmp_path, username="offline_user")
    storage = StorageService(config)
    seed = SeedService(storage)
    seed.run_seed(force=True)

    wiki_service = WikiSyncService(config)
    results = wiki_service.search("PVS")
    assert isinstance(results, list)


def test_zip_backup_and_corrupted_restore_recovery(tmp_path: Path):
    """Test ZipBackupService creating a valid backup archive and failing gracefully on invalid zip restore."""
    config = AppConfig(workspace_dir=tmp_path, username="test_agent")
    storage = StorageService(config)
    config.ensure_directories()

    (config.data_dir / "cases.json").write_text('{"cases": []}', encoding="utf-8")

    backup_file = tmp_path / "valid_backup.zip"
    res = ZipBackupService.export_backup_zip(storage, backup_file)
    assert backup_file.exists()
    assert res["file_count"] >= 1

    # Test corrupted zip file restore
    corrupt_file = tmp_path / "corrupt_test.zip"
    corrupt_file.write_text("THIS IS NOT A ZIP", encoding="utf-8")
    restore_data_target = tmp_path / "restored_data"
    restore_att_target = tmp_path / "restored_att"
    try:
        ZipBackupService.import_backup_zip(corrupt_file, restore_data_target, restore_att_target)
        success_corrupt = True
    except Exception:
        success_corrupt = False
    assert success_corrupt is False
