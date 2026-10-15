"""Daily backups with grandfather-father-son retention, retention settings UI, and ZIP backup export/import."""

import json
import zipfile
from datetime import date, timedelta
from pathlib import Path

import pytest

from models.case import Case
from models.profile import BackupSettings, UserProfile
from services.zip_backup_service import ZipBackupService


def _write_backups(backups_dir: Path, ref: date, days: int) -> None:
    for i in range(days):
        d = ref - timedelta(days=i)
        (backups_dir / f"cases_{d.isoformat()}.json").write_text(json.dumps([{"case_id": f"C-{d}"}]), encoding="utf-8")


def _backup_dates(backups_dir: Path) -> list[date]:
    return sorted(date.fromisoformat(f.stem.replace("cases_", "")) for f in backups_dir.glob("cases_*.json"))


# --- Settings model ----------------------------------------------------------


@pytest.mark.parametrize(
    ("raw", "expected"),
    [
        ({}, (7, 4, 6)),
        ({"daily_days": 14, "weekly_weeks": 8, "monthly_months": 12}, (14, 8, 12)),
        # daily clamped to >= 1, invalid values fall back to defaults
        ({"daily_days": -5, "weekly_weeks": "invalid", "monthly_months": None}, (1, 4, 6)),
    ],
)
def test_backup_settings_from_dict(raw, expected):
    s = BackupSettings.from_dict(raw)
    assert (s.daily_days, s.weekly_weeks, s.monthly_months) == expected


def test_backup_settings_roundtrip_through_profile():
    assert BackupSettings().to_dict() == {"daily_days": 7, "weekly_weeks": 4, "monthly_months": 6}
    profile = UserProfile()
    profile.backup_settings = BackupSettings(daily_days=10, weekly_weeks=3, monthly_months=5)
    restored = UserProfile.from_dict(profile.to_dict())
    assert restored.backup_settings.to_dict() == {"daily_days": 10, "weekly_weeks": 3, "monthly_months": 5}


# --- Pruning -----------------------------------------------------------------


def test_prune_keeps_daily_weekly_monthly_tiers(storage, config):
    config.ensure_directories()
    ref = date(2026, 9, 11)
    _write_backups(config.backups_dir, ref, 730)

    pruned = storage.prune_old_backups(reference_date=ref, settings=BackupSettings(daily_days=7, weekly_weeks=4, monthly_months=6))
    remaining = _backup_dates(config.backups_dir)
    assert len(pruned) == 730 - len(remaining)

    ages = {d: (ref - d).days for d in remaining}
    assert all(ref - timedelta(days=o) in ages for o in range(7)), "every daily backup of the last week kept"
    weekly = [d.isocalendar()[:2] for d, a in ages.items() if 7 <= a < 28]
    assert len(weekly) == len(set(weekly)) and len(weekly) >= 3
    monthly = [(d.year, d.month) for d, a in ages.items() if 28 <= a < 180]
    assert len(monthly) == len(set(monthly)) and len(monthly) >= 5
    assert max(ages.values()) < 180
    assert 14 <= len(remaining) <= 17


def test_prune_with_empty_weekly_and_monthly_tiers(storage, config):
    config.ensure_directories()
    ref = date(2026, 9, 11)
    _write_backups(config.backups_dir, ref, 30)
    pruned = storage.prune_old_backups(reference_date=ref, settings=BackupSettings(daily_days=3, weekly_weeks=0, monthly_months=0))
    assert len(_backup_dates(config.backups_dir)) == 3
    assert len(pruned) == 27


def test_prune_never_deletes_newest_or_unrelated_files(storage, config):
    config.ensure_directories()
    only = config.backups_dir / "cases_2023-01-01.json"
    only.write_text("[]", encoding="utf-8")
    assert storage.prune_old_backups(reference_date=date(2026, 9, 11)) == []
    assert only.exists(), "the newest backup survives even when far too old"

    unrelated = [
        config.backups_dir / "README.txt",
        config.backups_dir / "cases_manual_backup.zip",
        config.backups_dir / "cases_9999-99-99.json",
        config.backups_dir / "other_backup.json",
    ]
    for f in unrelated:
        f.write_text("x", encoding="utf-8")
    (config.backups_dir / "subfolder").mkdir()
    new_valid = config.backups_dir / "cases_2026-09-11.json"
    new_valid.write_text("[]", encoding="utf-8")

    pruned = storage.prune_old_backups(reference_date=date(2026, 9, 11))
    assert only in pruned and not only.exists()
    assert new_valid.exists()
    assert all(f.exists() for f in unrelated)
    assert (config.backups_dir / "subfolder").is_dir()


def test_perform_daily_backup_creates_once_and_prunes(storage, config):
    config.ensure_directories()
    storage.save_cases([Case(case_id="T-2026-1000")], sync=True)
    old = config.backups_dir / "cases_2024-01-01.json"
    old.write_text("[]", encoding="utf-8")

    res = storage.perform_daily_backup("2026-09-11")
    assert res is not None and res.name == "cases_2026-09-11.json"
    assert "T-2026-1000" in res.read_text(encoding="utf-8")
    assert not old.exists()
    assert storage.perform_daily_backup("2026-09-11") == res


def test_profile_settings_dialog_edits_retention(root, storage, config):
    from ui.dialogs.profile_settings_dialog import ProfileSettingsDialog

    config.ensure_directories()
    profile = storage.load_profile()
    profile.backup_settings = BackupSettings(daily_days=14, weekly_weeks=8, monthly_months=12)
    storage.save_profile(profile, sync=True)

    dialog = ProfileSettingsDialog(parent=root, profile=profile, storage_service=storage)
    entries = (dialog.retention_daily_entry, dialog.retention_weekly_entry, dialog.retention_monthly_entry)
    assert [e.get() for e in entries] == ["14", "8", "12"]
    for entry, value in zip(entries, ("5", "2", "3"), strict=True):
        entry.delete(0, "end")
        entry.insert(0, value)
    dialog.save_settings()

    storage.invalidate_cache()
    assert storage.load_profile().backup_settings.to_dict() == {"daily_days": 5, "weekly_weeks": 2, "monthly_months": 3}

    dialog.on_click_prune_backups()
    status = dialog.status_lbl.cget("text")
    assert "Keine veralteten Backups" in status or "bereinigt" in status
    dialog.destroy()


# --- ZIP backup --------------------------------------------------------------


def test_zip_backup_export_inspect_import_roundtrip(storage, config, tmp_path: Path):
    config.ensure_directories()
    (config.data_dir / "cases.json").write_text('{"cases": ["c1"]}', encoding="utf-8")
    (config.data_dir / "customers.json").write_text('{"customers": []}', encoding="utf-8")
    att = config.attachments_dir / "c1"
    att.mkdir(parents=True, exist_ok=True)
    (att / "note.txt").write_text("Secret note", encoding="utf-8")
    (att / "doc.pdf").write_bytes(b"%PDF-1.4 dummy content")

    zip_out = tmp_path / "backup.zip"
    res = ZipBackupService.export_backup_zip(storage, zip_out)
    assert res["file_count"] >= 4 and res["total_bytes"] > 0
    with zipfile.ZipFile(zip_out) as zf:
        names = [n.replace("\\", "/") for n in zf.namelist()]
    assert "data/cases.json" in names
    assert "attachments/c1/doc.pdf" in names

    stats = ZipBackupService.inspect_backup_zip(zip_out)
    assert stats["total_files"] >= 4 and stats["total_bytes"] > 0
    assert "data_files" in stats and "attachment_files" in stats

    dest_data, dest_att = tmp_path / "dest_data", tmp_path / "dest_att"
    imp = ZipBackupService.import_backup_zip(zip_out, dest_data, dest_att)
    assert imp["extracted_data_files"] >= 1 and imp["extracted_attachment_files"] >= 1
    assert "c1" in (dest_data / "cases.json").read_text(encoding="utf-8")
    assert (dest_att / "c1" / "note.txt").read_text(encoding="utf-8") == "Secret note"


def test_zip_import_overwrites_existing_files(tmp_path: Path):
    zip_out = tmp_path / "overwrite.zip"
    with zipfile.ZipFile(zip_out, "w") as zf:
        zf.writestr("data/config.json", '{"version": 2}')
    target = tmp_path / "data_target"
    target.mkdir()
    (target / "config.json").write_text('{"version": 1}', encoding="utf-8")
    ZipBackupService.import_backup_zip(zip_out, target, tmp_path / "att_target")
    assert '{"version": 2}' in (target / "config.json").read_text(encoding="utf-8")


def test_corrupted_zip_is_rejected(tmp_path: Path):
    fake = tmp_path / "broken.zip"
    fake.write_text("This is not a zip file", encoding="utf-8")
    with pytest.raises(zipfile.BadZipFile):
        ZipBackupService.inspect_backup_zip(fake)
    with pytest.raises(zipfile.BadZipFile):
        ZipBackupService.import_backup_zip(fake, tmp_path / "d", tmp_path / "a")


def test_zip_import_path_dialog_confirms_default_paths(root, config, tmp_path: Path):
    from ui.dialogs.zip_import_dialog import ZipImportPathDialog

    zip_path = tmp_path / "backup_test.zip"
    with zipfile.ZipFile(zip_path, "w") as zf:
        zf.writestr("data/cases.json", "[]")

    confirmed: list[tuple] = []
    diag = ZipImportPathDialog(
        root,
        zip_file_path=zip_path,
        default_data_dir=config.data_dir,
        default_attachments_dir=config.attachments_dir,
        on_import_confirmed=lambda d, a: confirmed.append((d, a)),
    )
    diag.update_idletasks()
    diag.on_confirm()
    assert confirmed == [(config.data_dir, config.attachments_dir)]
    diag.destroy()
