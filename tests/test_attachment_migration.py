from pathlib import Path
import json
from config import AppConfig
from models.case import Case, CaseCustomer
from services.storage_service import StorageService
from services.attachment_service import AttachmentService


def test_migrate_legacy_attachments_folder_moved(tmp_path: Path):
    """Verify legacy workspace_dir/attachments is moved into workspace_dir/data/attachments."""
    workspace = tmp_path / "workspace"
    workspace.mkdir()

    # Create legacy attachments folder with content
    legacy_att = workspace / "attachments"
    legacy_case_dir = legacy_att / "CASE-101_Praxis_Mueller"
    legacy_case_dir.mkdir(parents=True)
    sample_file = legacy_case_dir / "screenshot.png"
    sample_file.write_bytes(b"dummy image bytes")

    config = AppConfig(workspace_dir=workspace)
    assert not (workspace / "data" / "attachments").exists()

    # Initializing StorageService triggers migration
    storage = StorageService(config)

    target_case_dir = workspace / "data" / "attachments" / "CASE-101_Praxis_Mueller"
    assert target_case_dir.exists()
    assert (target_case_dir / "screenshot.png").exists()
    assert (target_case_dir / "screenshot.png").read_bytes() == b"dummy image bytes"

    # Legacy attachments folder should have been removed
    assert not legacy_att.exists()


def test_migrate_legacy_attachments_merge_existing(tmp_path: Path):
    """Verify that if target data/attachments already exists, contents are merged safely."""
    workspace = tmp_path / "workspace"
    workspace.mkdir()

    # Legacy folder
    legacy_case_dir = workspace / "attachments" / "CASE-202_Praxis"
    legacy_case_dir.mkdir(parents=True)
    (legacy_case_dir / "file_old.txt").write_text("old", encoding="utf-8")

    # Already partially existing target
    target_case_dir = workspace / "data" / "attachments" / "CASE-202_Praxis"
    target_case_dir.mkdir(parents=True)
    (target_case_dir / "file_new.txt").write_text("new", encoding="utf-8")

    config = AppConfig(workspace_dir=workspace)
    storage = StorageService(config)

    assert (target_case_dir / "file_old.txt").exists()
    assert (target_case_dir / "file_new.txt").exists()
    assert not (workspace / "attachments").exists()


def test_migrate_cases_and_archive_json_paths(tmp_path: Path):
    """Verify attachment_directory values starting with attachments/ are updated to data/attachments/."""
    workspace = tmp_path / "workspace"
    data_dir = workspace / "data"
    data_dir.mkdir(parents=True)

    # Prepare cases.json with legacy attachment_directory
    cases_payload = [
        {
            "case_id": "T-100",
            "attachment_directory": "attachments/T-100_Praxis_A",
        },
        {
            "case_id": "T-101",
            "attachment_directory": "data/attachments/T-101_Praxis_B",
        },
    ]
    (data_dir / "cases.json").write_text(json.dumps(cases_payload), encoding="utf-8")

    # Prepare archive.json with legacy attachment_directory
    archive_payload = [
        {
            "case_id": "T-099",
            "attachment_directory": "attachments/T-099_Praxis_Old",
        }
    ]
    (data_dir / "archive.json").write_text(json.dumps(archive_payload), encoding="utf-8")

    config = AppConfig(workspace_dir=workspace)
    storage = StorageService(config)

    # Check in-memory loaded cases
    cases = storage.load_cases()
    assert cases[0].attachment_directory == "data/attachments/T-100_Praxis_A"
    assert cases[1].attachment_directory == "data/attachments/T-101_Praxis_B"

    # Check on disk
    saved_cases = json.loads((data_dir / "cases.json").read_text(encoding="utf-8"))
    assert saved_cases[0]["attachment_directory"] == "data/attachments/T-100_Praxis_A"

    archive = storage.load_archive()
    assert archive[0].attachment_directory == "data/attachments/T-099_Praxis_Old"

    saved_archive = json.loads((data_dir / "archive.json").read_text(encoding="utf-8"))
    assert saved_archive[0]["attachment_directory"] == "data/attachments/T-099_Praxis_Old"


def test_attachment_service_on_the_fly_folder_migration(tmp_path: Path):
    """Verify AttachmentService.get_case_attachment_dir moves legacy folder on-the-fly."""
    workspace = tmp_path / "workspace"
    workspace.mkdir()

    # Legacy folder on disk
    old_dir = workspace / "attachments" / "CASE-303_Praxis"
    old_dir.mkdir(parents=True)
    (old_dir / "data.log").write_text("log content", encoding="utf-8")

    case = Case(
        case_id="CASE-303",
        attachment_directory="attachments/CASE-303_Praxis",
        customer=CaseCustomer(practice_name="Praxis"),
    )

    config = AppConfig(workspace_dir=workspace)
    service = AttachmentService(config)

    resolved_dir = service.get_case_attachment_dir(case)

    # Should have migrated to data/attachments
    expected_dir = workspace / "data" / "attachments" / "CASE-303_Praxis"
    assert resolved_dir == expected_dir
    assert expected_dir.exists()
    assert (expected_dir / "data.log").read_text(encoding="utf-8") == "log content"
    assert case.attachment_directory == "data/attachments/CASE-303_Praxis"


def test_migrate_legacy_attachments_conflicts_never_lose_data(tmp_path: Path):
    """Colliding names and nested folders must survive the migration - nothing is deleted."""
    workspace = tmp_path / "workspace"
    legacy_case = workspace / "attachments" / "CASE-404_Praxis"
    (legacy_case / "sub").mkdir(parents=True)
    (legacy_case / "rechnung.pdf").write_text("ALT", encoding="utf-8")
    (legacy_case / "sub" / "log.txt").write_text("NESTED-ALT", encoding="utf-8")
    (legacy_case / "same.txt").write_text("gleich", encoding="utf-8")

    target_case = workspace / "data" / "attachments" / "CASE-404_Praxis"
    (target_case / "sub").mkdir(parents=True)
    (target_case / "rechnung.pdf").write_text("NEU", encoding="utf-8")
    (target_case / "same.txt").write_text("gleich", encoding="utf-8")

    StorageService(AppConfig(workspace_dir=workspace))

    # Existing target file untouched, legacy version kept under a new name
    assert (target_case / "rechnung.pdf").read_text(encoding="utf-8") == "NEU"
    assert (target_case / "rechnung_legacy.pdf").read_text(encoding="utf-8") == "ALT"
    # Nested file from an already existing subfolder is merged, not dropped
    assert (target_case / "sub" / "log.txt").read_text(encoding="utf-8") == "NESTED-ALT"
    # Byte-identical duplicate is collapsed into one file
    assert (target_case / "same.txt").read_text(encoding="utf-8") == "gleich"
    assert not (target_case / "same_legacy.txt").exists()
    # Legacy tree is empty now and therefore removed
    assert not (workspace / "attachments").exists()


def test_migrate_legacy_attachments_repeated_conflicts_get_unique_names(tmp_path: Path):
    """A second collision must not overwrite an earlier '_legacy' copy."""
    workspace = tmp_path / "workspace"
    (workspace / "attachments").mkdir(parents=True)
    (workspace / "attachments" / "notiz.txt").write_text("ALT-2", encoding="utf-8")

    target = workspace / "data" / "attachments"
    target.mkdir(parents=True)
    (target / "notiz.txt").write_text("NEU", encoding="utf-8")
    (target / "notiz_legacy.txt").write_text("ALT-1", encoding="utf-8")

    StorageService(AppConfig(workspace_dir=workspace))

    assert (target / "notiz.txt").read_text(encoding="utf-8") == "NEU"
    assert (target / "notiz_legacy.txt").read_text(encoding="utf-8") == "ALT-1"
    assert (target / "notiz_legacy2.txt").read_text(encoding="utf-8") == "ALT-2"
