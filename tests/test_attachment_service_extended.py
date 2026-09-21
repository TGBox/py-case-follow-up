"""Extended tests for AttachmentService, filename sanitization, collision handling, and clipboard saving."""

import os
import subprocess
from pathlib import Path
from unittest.mock import MagicMock
from PIL import Image
from config import AppConfig
from models.case import Case, CaseCustomer
from services.attachment_service import AttachmentService, sanitize_filename


def test_sanitize_filename_edge_cases():
    """Verify sanitize_filename handles empty, invalid characters, reserved names, and length limits."""
    # Empty
    assert sanitize_filename("") == "unnamed"
    assert sanitize_filename("   ") == "safe_"

    # Reserved Windows names
    assert sanitize_filename("CON") == "safe_CON"
    assert sanitize_filename("prn") == "safe_prn"
    assert sanitize_filename("aux") == "safe_aux"
    assert sanitize_filename("Nul") == "safe_Nul"
    assert sanitize_filename("COM1") == "safe_COM1"
    assert sanitize_filename("LPT9") == "safe_LPT9"

    # Invalid characters and whitespaces
    assert sanitize_filename('Praxis <Dr. "Müller"> & Co:?*') == "Praxis_Dr._Müller_&_Co"

    # Length truncation at 50 chars
    long_name = "A" * 70
    assert len(sanitize_filename(long_name)) == 50

    # Leading/trailing dots and underscores
    assert sanitize_filename("...my_file___") == "my_file"


def test_get_case_attachment_dir_with_existing(tmp_path: Path):
    """Verify get_case_attachment_dir uses case.attachment_directory if already present."""
    config = AppConfig(workspace_dir=tmp_path)
    service = AttachmentService(config)

    case = Case(case_id="FALL-01", attachment_directory="custom_attachments/FALL-01")
    target_dir = service.get_case_attachment_dir(case)

    assert target_dir == tmp_path / "custom_attachments" / "FALL-01"
    assert target_dir.exists()


def test_get_case_attachment_dir_new(tmp_path: Path):
    """Verify get_case_attachment_dir creates directory based on practice name when none is set."""
    config = AppConfig(workspace_dir=tmp_path)
    service = AttachmentService(config)

    case = Case(
        case_id="FALL-02",
        customer=CaseCustomer(practice_name="Gemeinschaftspraxis Dr. Weber"),
    )
    target_dir = service.get_case_attachment_dir(case)

    assert "FALL-02_Gemeinschaftspraxis_Dr._Weber" in target_dir.name
    assert target_dir.exists()
    assert case.attachment_directory == str(target_dir.relative_to(tmp_path))


def test_list_attachments_empty_and_populated(monkeypatch, tmp_path: Path):
    """Verify list_attachments returns empty list when directory does not exist, is empty, and files when populated."""
    config = AppConfig(workspace_dir=tmp_path)
    service = AttachmentService(config)
    case = Case(case_id="FALL-03")

    # Directory does not exist on disk
    monkeypatch.setattr(service, "get_case_attachment_dir", lambda c: tmp_path / "never_created_dir")
    assert service.list_attachments(case) == []

    # Restore real method
    monkeypatch.undo()

    # Directory created, empty
    files = service.list_attachments(case)
    assert files == []

    # Add a file and a subdirectory
    case_dir = service.get_case_attachment_dir(case)
    test_file = case_dir / "report.pdf"
    test_file.write_text("dummy content", encoding="utf-8")
    sub_dir = case_dir / "nested_folder"
    sub_dir.mkdir()

    files = service.list_attachments(case)
    assert len(files) == 1
    assert files[0].name == "report.pdf"


def test_copy_attachment_and_collision_handling(tmp_path: Path):
    """Verify copy_attachment handles initial copy and appends timestamp on filename collision."""
    config = AppConfig(workspace_dir=tmp_path)
    service = AttachmentService(config)
    case = Case(case_id="FALL-04")

    # Create source file
    src_file = tmp_path / "screenshot.png"
    src_file.write_text("image bytes", encoding="utf-8")

    # Initial copy
    dest1 = service.copy_attachment(case, src_file)
    assert dest1.name == "screenshot.png"
    assert dest1.exists()

    # Second copy with same name causes collision
    dest2 = service.copy_attachment(case, src_file)
    assert dest2.name != dest1.name
    assert dest2.name.startswith("screenshot_")
    assert dest2.name.endswith(".png")
    assert dest2.exists()


def test_save_clipboard_image_success(monkeypatch, tmp_path: Path):
    """Verify save_clipboard_image saves image when PIL ImageGrab returns an image."""
    config = AppConfig(workspace_dir=tmp_path)
    service = AttachmentService(config)
    case = Case(case_id="FALL-05")

    img_mock = Image.new("RGB", (10, 10), color="blue")
    monkeypatch.setattr("PIL.ImageGrab.grabclipboard", lambda: img_mock)

    dest = service.save_clipboard_image(case)
    assert dest is not None
    assert dest.exists()
    assert dest.suffix == ".png"


def test_save_clipboard_image_no_image_or_exception(monkeypatch, tmp_path: Path):
    """Verify save_clipboard_image returns None when clipboard has text or fails."""
    config = AppConfig(workspace_dir=tmp_path)
    service = AttachmentService(config)
    case = Case(case_id="FALL-06")

    # Clipboard contains string, not image
    monkeypatch.setattr("PIL.ImageGrab.grabclipboard", lambda: "some copied text")
    assert service.save_clipboard_image(case) is None

    # Clipboard raises error
    def failing_grab():
        raise RuntimeError("Clipboard locked")

    monkeypatch.setattr("PIL.ImageGrab.grabclipboard", failing_grab)
    assert service.save_clipboard_image(case) is None


def test_open_in_explorer(monkeypatch, tmp_path: Path):
    """Verify open_in_explorer calls os.startfile or fallback subprocess."""
    config = AppConfig(workspace_dir=tmp_path)
    service = AttachmentService(config)
    case = Case(case_id="FALL-07")

    # 1. os.startfile available
    mock_startfile = MagicMock()
    monkeypatch.setattr(os, "startfile", mock_startfile, raising=False)
    service.open_in_explorer(case)
    mock_startfile.assert_called_once()

    # 2. os.startfile not available -> fallback to subprocess.run
    monkeypatch.delattr(os, "startfile", raising=False)
    mock_subproc = MagicMock()
    monkeypatch.setattr(subprocess, "run", mock_subproc)
    service.open_in_explorer(case)
    mock_subproc.assert_called_once()
