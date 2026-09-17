"""Tests for CobraImportDialog: CSV loading, column mapping UI, conflict modes, preview, and execution."""

from pathlib import Path
from tkinter import filedialog
import customtkinter as ctk
import pytest
from models.customer import Contact, Customer
from ui.dialogs.cobra_import_dialog import CobraImportDialog


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
def sample_cobra_csv(tmp_path: Path) -> Path:
    csv_file = tmp_path / "cobra_export.csv"
    csv_file.write_text(
        "Kunden-Nr;Firma;Ansprechpartner;Telefon;E-Mail;VIP\n"
        "K-1001;Praxis Dr. Alpha;Dr. Alpha;01234;alpha@praxis.de;Ja\n"
        "K-1002;Zentrum Beta;Fr. Beta;05678;beta@praxis.de;Nein\n",
        encoding="utf-8",
    )
    return csv_file


def test_cobra_import_dialog_load_and_preview(monkeypatch, app_root, sample_cobra_csv):
    """Verify CobraImportDialog loads file, maps headers, and renders preview summary."""
    existing = [
        Customer(
            customer_id="K-1001",
            practice_name="Praxis Dr. Alpha (Alt)",
            contacts=[Contact(name="Dr. Alpha Alt", email="old@praxis.de")],
        )
    ]
    imported_result = []

    def on_done(customers):
        imported_result.append(customers)

    dialog = CobraImportDialog(
        app_root,
        existing_customers=existing,
        on_import_completed=on_done,
    )

    # 1. No file selected: click import does nothing
    dialog.on_click_import()
    assert len(imported_result) == 0

    # 2. Browse and load sample CSV
    monkeypatch.setattr(filedialog, "askopenfilename", lambda **k: str(sample_cobra_csv))
    dialog.on_browse_file()
    assert len(dialog.raw_rows) == 2
    assert "Firma" in dialog.headers
    assert dialog.mapping["practice_name"] == "Firma"

    # Preview label should show 1 existing conflict and 1 new practice
    summary_text = dialog.summary_lbl.cget("text")
    assert "1 neue" in summary_text
    assert "1 bereits vorhandene" in summary_text

    # Test on_mapping_changed
    dialog.on_mapping_changed("practice_name", "(Keine Zuordnung)")
    assert dialog.mapping["practice_name"] == ""
    dialog.on_mapping_changed("practice_name", "Firma")
    assert dialog.mapping["practice_name"] == "Firma"

    # 3. Switch mode to Skip
    dialog.mode_combo.set(dialog.mode_combo.cget("values")[1])  # Skip
    dialog.update_preview()

    # 4. Switch mode to All New
    dialog.mode_combo.set(dialog.mode_combo.cget("values")[2])  # All new
    dialog.update_preview()

    # 5. Execute import with Update mode
    dialog.mode_combo.set(dialog.mode_combo.cget("values")[0])  # Update
    dialog.update_preview()
    dialog.on_click_import()

    assert len(imported_result) == 1
    final_customers = imported_result[0]
    assert len(final_customers) == 2
    # K-1001 should be updated
    alpha = next(c for c in final_customers if c.customer_id == "K-1001")
    assert alpha.practice_name == "Praxis Dr. Alpha"
    assert alpha.is_vip is True


def test_cobra_import_dialog_browse(monkeypatch, app_root, sample_cobra_csv):
    """Verify on_browse_file triggers load_file when file is selected."""
    dialog = CobraImportDialog(
        app_root,
        existing_customers=[],
        on_import_completed=lambda c: None,
    )

    monkeypatch.setattr(filedialog, "askopenfilename", lambda **k: str(sample_cobra_csv))
    dialog.on_browse_file()

    assert dialog.file_path == str(sample_cobra_csv)
    assert len(dialog.raw_rows) == 2

    # When user cancels browse
    monkeypatch.setattr(filedialog, "askopenfilename", lambda **k: "")
    dialog.on_browse_file()
    assert dialog.file_path == str(sample_cobra_csv)

    dialog.destroy()
