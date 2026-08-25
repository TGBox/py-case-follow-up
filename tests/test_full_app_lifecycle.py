"""Comprehensive full application lifecycle and workspace integration tests."""

from pathlib import Path
from typing import Any
import pytest
from config import AppConfig
from enums import LayoutMode, get_layout_display
from models.case import Case, Classification, WorkflowStatus
from services.seed_service import SeedService
from services.storage_service import StorageService
from services.scoring_service import ScoringService
from services.deep_search_service import DeepSearchService


def test_app_lifecycle_daily_backup_and_auto_archive(tmp_path: Path):
    """Test full app lifecycle startup tasks: daily backup and auto-archiving completed cases >= 30 days old."""
    config = AppConfig(workspace_dir=tmp_path, username="test_agent")
    storage = StorageService(config)
    seed = SeedService(storage)
    seed.run_seed(force=True)

    # 1. Perform daily backup
    backup_file = storage.perform_daily_backup()
    assert backup_file is not None
    assert backup_file.exists()

    # 2. Add an old completed case (idle 35 days old)
    cases = storage.load_cases()
    old_completed_case = Case(
        case_id="T-2026-OLD1",
        created_at="2026-06-01T10:00:00",
        updated_at="2026-06-01T10:00:00",
        classification=Classification(title="Old Case"),
        workflow_status=WorkflowStatus(is_completed=True, followup_at=""),
    )
    cases.append(old_completed_case)
    storage.save_cases(cases)

    # Auto archive completed cases >= 30 days
    archived_count = storage.auto_archive_completed_cases(threshold_days=30)
    assert archived_count >= 1

    reloaded_active = storage.load_cases()
    assert not any(c.case_id == "T-2026-OLD1" for c in reloaded_active)


def test_deep_search_across_attachments(tmp_path: Path):
    """Test DeepSearchService searching across case attachment text files."""
    config = AppConfig(workspace_dir=tmp_path, username="test_agent")
    storage = StorageService(config)
    seed = SeedService(storage)
    seed.run_seed(force=True)

    cases = storage.load_cases()
    target_case = cases[0]

    # Create dummy attachment directory and log file
    att_dir = config.attachments_dir / target_case.case_id
    att_dir.mkdir(parents=True, exist_ok=True)
    (att_dir / "system.log").write_text("Line 1: Normal log\nLine 2: Spezifisches_Suchwort_XYZ Error\nLine 3: End log", encoding="utf-8")
    target_case.attachment_directory = str(att_dir)

    deep_search = DeepSearchService(tmp_path)
    matches = deep_search.search_case_attachments(target_case, "Spezifisches_Suchwort_XYZ")

    assert len(matches) >= 1
    assert matches[0]["file_name"] == "system.log"
    assert "Spezifisches_Suchwort_XYZ" in matches[0]["snippet"]


def test_user_profile_sash_width_persistence_lifecycle(tmp_path: Path):
    """Test user profile UI column_widths load, update, save & persistence across app restarts."""
    config = AppConfig(workspace_dir=tmp_path, username="test_agent")
    storage = StorageService(config)
    seed = SeedService(storage)
    seed.run_seed(force=True)

    profile = storage.load_profile()
    profile.ui_settings.column_widths["cockpit_left"] = 380
    profile.ui_settings.column_widths["cockpit_right"] = 420
    storage.save_profile(profile)

    reloaded_profile = storage.load_profile()
    assert reloaded_profile.ui_settings.column_widths["cockpit_left"] == 380
    assert reloaded_profile.ui_settings.column_widths["cockpit_right"] == 420


def test_hourly_scoring_timer_execution_lifecycle(tmp_path: Path):
    """Test hourly scoring service recalculation across all active cases."""
    config = AppConfig(workspace_dir=tmp_path, username="test_agent")
    storage = StorageService(config)
    seed = SeedService(storage)
    seed.run_seed(force=True)

    cases = storage.load_cases()
    profile = storage.load_profile()
    scoring_service = ScoringService(profile.scoring_matrix)

    for c in cases:
        if not c.workflow_status.is_completed:
            scoring_service.update_case_scoring(c)

    storage.save_cases(cases)

    reloaded = storage.load_cases()
    for c in reloaded:
        if not c.workflow_status.is_completed:
            assert c.classification.calculated_score >= 0
