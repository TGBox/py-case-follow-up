import json
from datetime import date, datetime, timedelta
from pathlib import Path
from unittest.mock import MagicMock

import pytest

from config import AppConfig
from models.case import Case
from models.profile import BackupSettings, UserProfile
from services.storage_service import StorageService


def test_backup_settings_model():
    # Defaults
    settings = BackupSettings()
    assert settings.daily_days == 7
    assert settings.weekly_weeks == 4
    assert settings.monthly_months == 6

    # Serialization
    d = settings.to_dict()
    assert d == {"daily_days": 7, "weekly_weeks": 4, "monthly_months": 6}

    # Deserialization with valid values
    loaded = BackupSettings.from_dict({"daily_days": 14, "weekly_weeks": 8, "monthly_months": 12})
    assert loaded.daily_days == 14
    assert loaded.weekly_weeks == 8
    assert loaded.monthly_months == 12

    # Sanitization of invalid/negative/non-int values
    sanitized = BackupSettings.from_dict({"daily_days": -5, "weekly_weeks": "invalid", "monthly_months": None})
    assert sanitized.daily_days == 1  # Daily days clamped to at least 1
    assert sanitized.weekly_weeks == 4  # Fallback to default
    assert sanitized.monthly_months == 6  # Fallback to default

    # Empty dict
    default_loaded = BackupSettings.from_dict({})
    assert default_loaded.daily_days == 7
    assert default_loaded.weekly_weeks == 4
    assert default_loaded.monthly_months == 6


def test_user_profile_backup_settings_integration():
    profile = UserProfile()
    assert isinstance(profile.backup_settings, BackupSettings)
    assert profile.backup_settings.daily_days == 7

    profile.backup_settings.daily_days = 10
    profile.backup_settings.weekly_weeks = 3
    profile.backup_settings.monthly_months = 5

    p_dict = profile.to_dict()
    assert "backup_settings" in p_dict
    assert p_dict["backup_settings"]["daily_days"] == 10

    restored = UserProfile.from_dict(p_dict)
    assert restored.backup_settings.daily_days == 10
    assert restored.backup_settings.weekly_weeks == 3
    assert restored.backup_settings.monthly_months == 5


def test_prune_old_backups_grandfather_father_son(tmp_path: Path):
    config = AppConfig(workspace_dir=tmp_path)
    config.ensure_directories()
    storage = StorageService(config)

    ref_date = date(2026, 9, 11)

    # Create 730 daily backups (2 full years)
    start_date = ref_date - timedelta(days=729)
    created_files: list[Path] = []
    curr = start_date
    while curr <= ref_date:
        f = config.backups_dir / f"cases_{curr.isoformat()}.json"
        f.write_text(json.dumps([{"case_id": f"C-{curr.isoformat()}"}]), encoding="utf-8")
        created_files.append(f)
        curr += timedelta(days=1)

    assert len(created_files) == 730
    assert len(list(config.backups_dir.glob("cases_*.json"))) == 730

    # Prune with standard settings: 7 days daily, 4 weeks weekly (days 7-28), 6 months monthly (days 28-180)
    settings = BackupSettings(daily_days=7, weekly_weeks=4, monthly_months=6)
    pruned = storage.prune_old_backups(reference_date=ref_date, settings=settings)

    remaining_files = sorted(list(config.backups_dir.glob("cases_*.json")))
    assert len(pruned) == 730 - len(remaining_files)

    # 1. Verify Daily Tier (last 7 days: 0 to 6 days old)
    for offset in range(7):
        d = ref_date - timedelta(days=offset)
        expected_file = config.backups_dir / f"cases_{d.isoformat()}.json"
        assert expected_file.exists(), f"Daily backup {expected_file.name} must exist"

    # 2. Verify Weekly Tier (days 7 to 27)
    # Between 7 and 28 days old: exactly 1 file per ISO calendar week
    weekly_files = []
    for f in remaining_files:
        d_str = f.stem.replace("cases_", "")
        d = date.fromisoformat(d_str)
        age = (ref_date - d).days
        if 7 <= age < 28:
            weekly_files.append((f, d))

    weekly_iso_weeks = [d.isocalendar()[:2] for _, d in weekly_files]
    assert len(weekly_iso_weeks) == len(set(weekly_iso_weeks)), "Only 1 backup per calendar week in weekly tier"
    assert len(weekly_iso_weeks) >= 3, "Should have 3-4 weekly backups preserved"

    # 3. Verify Monthly Tier (days 28 to 180)
    # Between 28 and 180 days old: exactly 1 file per calendar month
    monthly_files = []
    for f in remaining_files:
        d_str = f.stem.replace("cases_", "")
        d = date.fromisoformat(d_str)
        age = (ref_date - d).days
        if 28 <= age < 180:
            monthly_files.append((f, d))

    monthly_months = [(d.year, d.month) for _, d in monthly_files]
    assert len(monthly_months) == len(set(monthly_months)), "Only 1 backup per calendar month in monthly tier"
    assert len(monthly_months) >= 5, "Should have ~5 monthly backups preserved"

    # 4. Verify no backups older than 180 days exist
    for f in remaining_files:
        d_str = f.stem.replace("cases_", "")
        d = date.fromisoformat(d_str)
        age = (ref_date - d).days
        assert age < 180, f"Backup {f.name} is {age} days old and should have been pruned"

    # Total remaining files should be roughly 7 daily + 3 weekly + 5 monthly = 15-16 files
    assert 14 <= len(remaining_files) <= 17


def test_safety_newest_backup_never_deleted(tmp_path: Path):
    config = AppConfig(workspace_dir=tmp_path)
    config.ensure_directories()
    storage = StorageService(config)

    # Old backup from 3 years ago
    old_backup = config.backups_dir / "cases_2023-01-01.json"
    old_backup.write_text("[]", encoding="utf-8")

    ref_date = date(2026, 9, 11)
    # Even though it is 3 years old (> 180 days), it is the newest and only backup!
    pruned = storage.prune_old_backups(reference_date=ref_date)

    assert len(pruned) == 0
    assert old_backup.exists()


def test_safety_unrelated_files_never_touched(tmp_path: Path):
    config = AppConfig(workspace_dir=tmp_path)
    config.ensure_directories()
    storage = StorageService(config)

    # Unrelated files and folders in backups directory
    readme = config.backups_dir / "README.txt"
    readme.write_text("Do not touch", encoding="utf-8")

    manual_zip = config.backups_dir / "cases_manual_backup.zip"
    manual_zip.write_text("archive", encoding="utf-8")

    invalid_date = config.backups_dir / "cases_9999-99-99.json"
    invalid_date.write_text("{}", encoding="utf-8")

    other_json = config.backups_dir / "other_backup.json"
    other_json.write_text("{}", encoding="utf-8")

    sub_dir = config.backups_dir / "subfolder"
    sub_dir.mkdir()

    # Also add a valid very old backup and a new backup
    old_valid = config.backups_dir / "cases_2024-01-01.json"
    old_valid.write_text("[]", encoding="utf-8")
    new_valid = config.backups_dir / "cases_2026-09-11.json"
    new_valid.write_text("[]", encoding="utf-8")

    pruned = storage.prune_old_backups(reference_date=date(2026, 9, 11))

    assert old_valid in pruned
    assert not old_valid.exists()
    assert new_valid.exists()

    # All unrelated items MUST still exist!
    assert readme.exists()
    assert manual_zip.exists()
    assert invalid_date.exists()
    assert other_json.exists()
    assert sub_dir.exists()


def test_custom_retention_settings_empty_tiers(tmp_path: Path):
    config = AppConfig(workspace_dir=tmp_path)
    config.ensure_directories()
    storage = StorageService(config)

    ref_date = date(2026, 9, 11)

    # Create daily backups for 30 days
    for i in range(30):
        d = ref_date - timedelta(days=i)
        f = config.backups_dir / f"cases_{d.isoformat()}.json"
        f.write_text("[]", encoding="utf-8")

    # Only keep 3 daily days, 0 weekly, 0 monthly
    settings = BackupSettings(daily_days=3, weekly_weeks=0, monthly_months=0)
    pruned = storage.prune_old_backups(reference_date=ref_date, settings=settings)

    remaining = sorted(list(config.backups_dir.glob("cases_*.json")))
    assert len(remaining) == 3
    assert len(pruned) == 27


def test_perform_daily_backup_creates_and_prunes(tmp_path: Path):
    config = AppConfig(workspace_dir=tmp_path)
    config.ensure_directories()
    storage = StorageService(config)

    # Add a case
    case = Case(case_id="T-2026-1000")
    storage.save_cases([case], sync=True)

    # Seed an old backup that should be pruned
    old_f = config.backups_dir / "cases_2024-01-01.json"
    old_f.write_text("[]", encoding="utf-8")

    # Call perform_daily_backup for today
    today_str = "2026-09-11"
    res = storage.perform_daily_backup(today_str)

    assert res is not None
    assert res.name == f"cases_{today_str}.json"
    assert res.exists()

    # Old backup from 2024 should have been pruned!
    assert not old_f.exists()

    # Second call returns existing backup without error
    res2 = storage.perform_daily_backup(today_str)
    assert res2 == res


def test_profile_settings_dialog_retention_ui(tmp_path: Path):
    import customtkinter as ctk
    from ui.dialogs.profile_settings_dialog import ProfileSettingsDialog

    config = AppConfig(workspace_dir=tmp_path)
    config.ensure_directories()
    storage = StorageService(config)

    # Save profile with non-default settings
    profile = storage.load_profile()
    profile.backup_settings = BackupSettings(daily_days=14, weekly_weeks=8, monthly_months=12)
    storage.save_profile(profile, sync=True)

    root = ctk.CTk()
    root.withdraw()

    try:
        dialog = ProfileSettingsDialog(
            parent=root,
            profile=profile,
            storage_service=storage,
        )

        # Verify entry widgets initialized with profile values
        assert hasattr(dialog, "retention_daily_entry")
        assert hasattr(dialog, "retention_weekly_entry")
        assert hasattr(dialog, "retention_monthly_entry")

        assert dialog.retention_daily_entry.get() == "14"
        assert dialog.retention_weekly_entry.get() == "8"
        assert dialog.retention_monthly_entry.get() == "12"

        # Change values
        dialog.retention_daily_entry.delete(0, "end")
        dialog.retention_daily_entry.insert(0, "5")

        dialog.retention_weekly_entry.delete(0, "end")
        dialog.retention_weekly_entry.insert(0, "2")

        dialog.retention_monthly_entry.delete(0, "end")
        dialog.retention_monthly_entry.insert(0, "3")

        # Save settings
        dialog.save_settings()

        # Check in memory and re-loaded
        assert dialog.profile.backup_settings.daily_days == 5
        assert dialog.profile.backup_settings.weekly_weeks == 2
        assert dialog.profile.backup_settings.monthly_months == 3

        storage.invalidate_cache()
        reloaded = storage.load_profile()
        assert reloaded.backup_settings.daily_days == 5
        assert reloaded.backup_settings.weekly_weeks == 2
        assert reloaded.backup_settings.monthly_months == 3

        # Test on_click_prune_backups
        dialog.on_click_prune_backups()
        assert "Keine veralteten Backups" in dialog.status_lbl.cget("text") or "bereinigt" in dialog.status_lbl.cget("text")

        dialog.destroy()
    finally:
        root.destroy()
