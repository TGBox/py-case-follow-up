"""AttachmentService (paths, copy, clipboard, explorer) and legacy attachments-folder migration."""

import json
import os
import subprocess
from pathlib import Path
from unittest.mock import MagicMock

import pytest
from PIL import Image

from config import AppConfig
from models.case import Case, CaseCustomer
from services.attachment_service import AttachmentService, sanitize_filename
from services.storage_service import StorageService


@pytest.fixture
def service(config) -> AttachmentService:
    return AttachmentService(config)


# --- Legacy migration --------------------------------------------------------


def test_legacy_attachments_folder_is_moved_into_data(tmp_path: Path):
    workspace = tmp_path / "workspace"
    legacy_case = workspace / "attachments" / "CASE-101_Praxis_Mueller"
    legacy_case.mkdir(parents=True)
    (legacy_case / "screenshot.png").write_bytes(b"dummy image bytes")
    assert not (workspace / "data" / "attachments").exists()

    StorageService(AppConfig(workspace_dir=workspace))

    moved = workspace / "data" / "attachments" / "CASE-101_Praxis_Mueller" / "screenshot.png"
    assert moved.read_bytes() == b"dummy image bytes"
    assert not (workspace / "attachments").exists()


def test_legacy_migration_merges_and_never_loses_data(tmp_path: Path):
    """Regression: colliding names and nested folders must survive the migration - nothing is deleted."""
    workspace = tmp_path / "workspace"
    legacy_case = workspace / "attachments" / "CASE-404_Praxis"
    (legacy_case / "sub").mkdir(parents=True)
    (legacy_case / "rechnung.pdf").write_text("ALT", encoding="utf-8")
    (legacy_case / "sub" / "log.txt").write_text("NESTED-ALT", encoding="utf-8")
    (legacy_case / "same.txt").write_text("gleich", encoding="utf-8")
    (legacy_case / "file_old.txt").write_text("old", encoding="utf-8")

    target_case = workspace / "data" / "attachments" / "CASE-404_Praxis"
    (target_case / "sub").mkdir(parents=True)
    (target_case / "rechnung.pdf").write_text("NEU", encoding="utf-8")
    (target_case / "same.txt").write_text("gleich", encoding="utf-8")
    (target_case / "file_new.txt").write_text("new", encoding="utf-8")

    StorageService(AppConfig(workspace_dir=workspace))

    assert (target_case / "file_old.txt").exists() and (target_case / "file_new.txt").exists()
    assert (target_case / "rechnung.pdf").read_text(encoding="utf-8") == "NEU"
    assert (target_case / "rechnung_legacy.pdf").read_text(encoding="utf-8") == "ALT"
    assert (target_case / "sub" / "log.txt").read_text(encoding="utf-8") == "NESTED-ALT"
    assert (target_case / "same.txt").read_text(encoding="utf-8") == "gleich"
    assert not (target_case / "same_legacy.txt").exists()
    assert not (workspace / "attachments").exists()


def test_legacy_migration_repeated_conflicts_get_unique_names(tmp_path: Path):
    """Regression: a second collision must not overwrite an earlier '_legacy' copy."""
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


def test_legacy_attachment_paths_in_cases_and_archive_are_rewritten(tmp_path: Path):
    workspace = tmp_path / "workspace"
    data_dir = workspace / "data"
    data_dir.mkdir(parents=True)
    (data_dir / "cases.json").write_text(json.dumps([
        {"case_id": "T-100", "attachment_directory": "attachments/T-100_Praxis_A"},
        {"case_id": "T-101", "attachment_directory": "data/attachments/T-101_Praxis_B"},
    ]), encoding="utf-8")
    (data_dir / "archive.json").write_text(json.dumps([
        {"case_id": "T-099", "attachment_directory": "attachments/T-099_Praxis_Old"},
    ]), encoding="utf-8")

    storage = StorageService(AppConfig(workspace_dir=workspace))

    assert [c.attachment_directory for c in storage.load_cases()] == [
        "data/attachments/T-100_Praxis_A", "data/attachments/T-101_Praxis_B",
    ]
    assert storage.load_archive()[0].attachment_directory == "data/attachments/T-099_Praxis_Old"
    on_disk_cases = json.loads((data_dir / "cases.json").read_text(encoding="utf-8"))
    on_disk_archive = json.loads((data_dir / "archive.json").read_text(encoding="utf-8"))
    assert on_disk_cases[0]["attachment_directory"] == "data/attachments/T-100_Praxis_A"
    assert on_disk_archive[0]["attachment_directory"] == "data/attachments/T-099_Praxis_Old"


def test_get_case_attachment_dir_migrates_legacy_folder_on_the_fly(tmp_path: Path):
    workspace = tmp_path / "workspace"
    old_dir = workspace / "attachments" / "CASE-303_Praxis"
    old_dir.mkdir(parents=True)
    (old_dir / "data.log").write_text("log content", encoding="utf-8")
    case = Case(case_id="CASE-303", attachment_directory="attachments/CASE-303_Praxis",
                customer=CaseCustomer(practice_name="Praxis"))

    resolved = AttachmentService(AppConfig(workspace_dir=workspace)).get_case_attachment_dir(case)

    expected = workspace / "data" / "attachments" / "CASE-303_Praxis"
    assert resolved == expected
    assert (expected / "data.log").read_text(encoding="utf-8") == "log content"
    assert case.attachment_directory == "data/attachments/CASE-303_Praxis"


# --- AttachmentService -------------------------------------------------------


@pytest.mark.parametrize(
    ("raw", "expected"),
    [
        ("", "unnamed"),
        ("   ", "safe_"),
        ("CON", "safe_CON"),
        ("prn", "safe_prn"),
        ("Nul", "safe_Nul"),
        ("COM1", "safe_COM1"),
        ("LPT9", "safe_LPT9"),
        ('Praxis <Dr. "Müller"> & Co:?*', "Praxis_Dr._Müller_&_Co"),
        ("...my_file___", "my_file"),
        ("A" * 70, "A" * 50),
    ],
)
def test_sanitize_filename(raw, expected):
    assert sanitize_filename(raw) == expected


def test_get_case_attachment_dir_existing_and_new(service, tmp_path: Path):
    existing = Case(case_id="FALL-01", attachment_directory="custom_attachments/FALL-01")
    assert service.get_case_attachment_dir(existing) == tmp_path / "custom_attachments" / "FALL-01"
    assert (tmp_path / "custom_attachments" / "FALL-01").is_dir()

    new = Case(case_id="FALL-02", customer=CaseCustomer(practice_name="Gemeinschaftspraxis Dr. Weber"))
    target = service.get_case_attachment_dir(new)
    assert "FALL-02_Gemeinschaftspraxis_Dr._Weber" in target.name
    assert target.is_dir()
    assert new.attachment_directory == str(target.relative_to(tmp_path))


def test_list_and_copy_attachments(service, monkeypatch, tmp_path: Path):
    case = Case(case_id="FALL-03")
    with monkeypatch.context() as m:
        m.setattr(service, "get_case_attachment_dir", lambda c: tmp_path / "never_created_dir")
        assert service.list_attachments(case) == []
    assert service.list_attachments(case) == []

    src = tmp_path / "screenshot.png"
    src.write_text("image bytes", encoding="utf-8")
    first = service.copy_attachment(case, src)
    second = service.copy_attachment(case, src)
    assert first.name == "screenshot.png"
    assert second.name != first.name and second.name.startswith("screenshot_") and second.suffix == ".png"
    (service.get_case_attachment_dir(case) / "nested_folder").mkdir()

    assert sorted(f.name for f in service.list_attachments(case)) == sorted([first.name, second.name])


@pytest.mark.parametrize("clipboard", ["image", "text", "error"])
def test_save_clipboard_image(service, monkeypatch, clipboard):
    def grab():
        if clipboard == "error":
            raise RuntimeError("Clipboard locked")
        return Image.new("RGB", (10, 10), color="blue") if clipboard == "image" else "some copied text"

    monkeypatch.setattr("PIL.ImageGrab.grabclipboard", grab)
    dest = service.save_clipboard_image(Case(case_id="FALL-05"))
    if clipboard == "image":
        assert dest is not None and dest.exists() and dest.suffix == ".png"
    else:
        assert dest is None


def test_open_in_explorer_uses_startfile_or_subprocess(service, monkeypatch):
    case = Case(case_id="FALL-07")
    startfile = MagicMock()
    monkeypatch.setattr(os, "startfile", startfile, raising=False)
    service.open_in_explorer(case)
    startfile.assert_called_once()

    monkeypatch.delattr(os, "startfile", raising=False)
    run = MagicMock()
    monkeypatch.setattr(subprocess, "run", run)
    service.open_in_explorer(case)
    run.assert_called_once()
