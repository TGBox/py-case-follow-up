from pathlib import Path
import pytest
import zipfile
from services.storage_service import StorageService, AppConfig
from services.zip_backup_service import ZipBackupService


def test_export_backup_zip_creates_valid_archive(tmp_path: Path):
    config = AppConfig(workspace_dir=tmp_path)
    storage = StorageService(config)
    config.ensure_directories()

    # Create dummy data and attachment files
    (config.data_dir / "cases.json").write_text('{"cases": []}', encoding="utf-8")
    (config.data_dir / "customers.json").write_text('{"customers": []}', encoding="utf-8")
    (config.data_dir / "colleagues.json").write_text('{"colleagues": []}', encoding="utf-8")

    att_sub = config.attachments_dir / "case_101"
    att_sub.mkdir(parents=True, exist_ok=True)
    (att_sub / "doc.pdf").write_bytes(b"%PDF-1.4 dummy content")

    zip_out = tmp_path / "export_test.zip"
    res = ZipBackupService.export_backup_zip(storage, zip_out)

    assert zip_out.exists()
    assert res["file_count"] >= 4
    assert res["total_bytes"] > 0

    # Verify Zip structure
    with zipfile.ZipFile(zip_out, "r") as zf:
        namelist = zf.namelist()
        assert "data/cases.json" in [n.replace("\\", "/") for n in namelist]
        assert "attachments/case_101/doc.pdf" in [n.replace("\\", "/") for n in namelist]


def test_inspect_backup_zip_returns_accurate_stats(tmp_path: Path):
    config = AppConfig(workspace_dir=tmp_path)
    storage = StorageService(config)
    config.ensure_directories()

    (config.data_dir / "test.txt").write_text("Hello", encoding="utf-8")
    zip_out = tmp_path / "inspect_test.zip"
    ZipBackupService.export_backup_zip(storage, zip_out)

    stats = ZipBackupService.inspect_backup_zip(zip_out)
    assert stats["total_files"] >= 1
    assert stats["total_bytes"] > 0
    assert "data_files" in stats
    assert "attachment_files" in stats


def test_import_backup_zip_extracts_files_correctly(tmp_path: Path):
    config = AppConfig(workspace_dir=tmp_path)
    storage = StorageService(config)
    config.ensure_directories()

    (config.data_dir / "cases.json").write_text('{"cases": ["c1"]}', encoding="utf-8")
    att_dir = config.attachments_dir / "c1"
    att_dir.mkdir(parents=True, exist_ok=True)
    (att_dir / "note.txt").write_text("Secret note", encoding="utf-8")

    zip_out = tmp_path / "import_source.zip"
    ZipBackupService.export_backup_zip(storage, zip_out)

    dest_data = tmp_path / "dest_data"
    dest_att = tmp_path / "dest_attachments"

    res = ZipBackupService.import_backup_zip(zip_out, dest_data, dest_att)

    assert res["extracted_data_files"] >= 1
    assert res["extracted_attachment_files"] >= 1

    imported_cases = dest_data / "cases.json"
    assert imported_cases.exists()
    assert "c1" in imported_cases.read_text(encoding="utf-8")

    imported_att = dest_att / "c1" / "note.txt"
    assert imported_att.exists()
    assert imported_att.read_text(encoding="utf-8") == "Secret note"


def test_import_backup_zip_overwrites_existing_files(tmp_path: Path):
    zip_out = tmp_path / "overwrite_test.zip"
    with zipfile.ZipFile(zip_out, "w") as zf:
        zf.writestr("data/config.json", '{"version": 2}')

    target_data = tmp_path / "data_target"
    target_data.mkdir(parents=True, exist_ok=True)
    (target_data / "config.json").write_text('{"version": 1}', encoding="utf-8")

    target_att = tmp_path / "att_target"

    ZipBackupService.import_backup_zip(zip_out, target_data, target_att)

    updated_content = (target_data / "config.json").read_text(encoding="utf-8")
    assert '{"version": 2}' in updated_content
