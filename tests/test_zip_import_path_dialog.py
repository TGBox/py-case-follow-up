"""Tests for ZipImportPathDialog mode switching, directory browsing, validation, and confirmation."""

import zipfile
from pathlib import Path
from tkinter import filedialog
import customtkinter as ctk
import pytest
from ui.dialogs.zip_import_dialog import ZipImportPathDialog


@pytest.fixture(scope="module")
def app_root():
    app = ctk.CTk()
    app.withdraw()
    yield app
    try:
        app.destroy()
    except Exception:
        pass


@pytest.fixture
def dummy_zip(tmp_path: Path) -> Path:
    """Creates a sample backup zip containing data and attachments."""
    zip_path = tmp_path / "sample_backup.zip"
    with zipfile.ZipFile(zip_path, "w") as zf:
        zf.writestr("data/cases.json", '{"cases": []}')
        zf.writestr("data/customers.json", '{"customers": []}')
        zf.writestr("attachments/att1.png", b"fake image bytes")
    return zip_path


def test_zip_import_dialog_initialization_and_root_mode(app_root, dummy_zip, tmp_path: Path):
    """Verify dialog inspects zip, displays summary, and confirms in default 'root' mode."""
    confirmed_calls = []

    def on_confirmed(data_dir: Path, att_dir: Path):
        confirmed_calls.append((data_dir, att_dir))

    dialog = ZipImportPathDialog(
        app_root,
        zip_file_path=dummy_zip,
        default_data_dir=tmp_path / "data",
        default_attachments_dir=tmp_path / "attachments",
        on_import_confirmed=on_confirmed,
    )

    assert dialog.mode == "root"
    assert hasattr(dialog, "root_entry")
    assert dialog.zip_info["total_files"] == 3
    assert dialog.zip_info["data_files"] == 2
    assert dialog.zip_info["attachment_files"] == 1

    # Empty root entry should prevent confirmation
    dialog.root_entry.delete(0, "end")
    dialog.on_confirm()
    assert len(confirmed_calls) == 0

    # Populate root entry and confirm
    chosen_root = tmp_path / "my_workspace"
    dialog.root_entry.insert(0, str(chosen_root))
    dialog.on_confirm()

    assert len(confirmed_calls) == 1
    data_dir, att_dir = confirmed_calls[0]
    assert data_dir == chosen_root / "data"
    assert att_dir == chosen_root / "attachments"


def test_zip_import_dialog_custom_mode(app_root, dummy_zip, tmp_path: Path):
    """Verify dialog switches to custom mode, allows separate paths, and validates."""
    confirmed_calls = []

    def on_confirmed(data_dir: Path, att_dir: Path):
        confirmed_calls.append((data_dir, att_dir))

    dialog = ZipImportPathDialog(
        app_root,
        zip_file_path=dummy_zip,
        default_data_dir=tmp_path / "data",
        default_attachments_dir=tmp_path / "attachments",
        on_import_confirmed=on_confirmed,
    )

    # Switch to custom mode
    dialog.set_mode_custom()
    assert dialog.mode == "custom"
    assert hasattr(dialog, "data_entry")
    assert hasattr(dialog, "att_entry")

    # Empty data entry -> validation fails
    dialog.data_entry.delete(0, "end")
    dialog.on_confirm()
    assert len(confirmed_calls) == 0

    # Empty att entry -> validation fails
    dialog.data_entry.insert(0, str(tmp_path / "custom_data"))
    dialog.att_entry.delete(0, "end")
    dialog.on_confirm()
    assert len(confirmed_calls) == 0

    # Both populated -> confirmation succeeds
    dialog.att_entry.insert(0, str(tmp_path / "custom_attachments"))
    dialog.on_confirm()

    assert len(confirmed_calls) == 1
    data_dir, att_dir = confirmed_calls[0]
    assert data_dir == tmp_path / "custom_data"
    assert att_dir == tmp_path / "custom_attachments"


def test_zip_import_dialog_browse_handlers(monkeypatch, app_root, dummy_zip, tmp_path: Path):
    """Verify browse buttons update corresponding path entry fields."""
    dialog = ZipImportPathDialog(
        app_root,
        zip_file_path=dummy_zip,
        default_data_dir=tmp_path / "data",
        default_attachments_dir=tmp_path / "attachments",
        on_import_confirmed=lambda d, a: None,
    )

    # 1. Browse root
    monkeypatch.setattr(filedialog, "askdirectory", lambda **k: str(tmp_path / "browsed_root"))
    dialog.browse_root_dir()
    assert dialog.root_entry.get() == str(tmp_path / "browsed_root")

    # 2. Browse custom data & attachments
    dialog.set_mode_custom()
    monkeypatch.setattr(filedialog, "askdirectory", lambda **k: str(tmp_path / "browsed_data"))
    dialog.browse_data_dir()
    assert dialog.data_entry.get() == str(tmp_path / "browsed_data")

    monkeypatch.setattr(filedialog, "askdirectory", lambda **k: str(tmp_path / "browsed_att"))
    dialog.browse_att_dir()
    assert dialog.att_entry.get() == str(tmp_path / "browsed_att")

    # Cancel browse (returns "")
    monkeypatch.setattr(filedialog, "askdirectory", lambda **k: "")
    dialog.browse_data_dir()
    assert dialog.data_entry.get() == str(tmp_path / "browsed_data")

    # Switch back to root mode
    dialog.set_mode_root()
    assert dialog.mode == "root"
    dialog.destroy()
