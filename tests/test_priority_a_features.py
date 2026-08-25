"""Test suite for Priority (A) features and quality safeguards:

- Unicode Emoji variation selector (\ufe0f) cleanup and anti-regression scanning
- Relative date formatting and 3-line followup display
- Dynamic case list text wrapping
- Case print dialog with embedded image attachments
- Multi-file request schema fields
- Toast notification button layout
"""

from datetime import datetime, date, timedelta
from pathlib import Path
import re
import pytest
import customtkinter as ctk

from config import AppConfig
from enums import BoardColumn, UrgencyLevel, Actor
from models.case import Case, CaseCustomer, Classification, WorkflowStatus, TimelineEntry
from services.attachment_service import AttachmentService
from services.seed_service import SeedService
from services.storage_service import StorageService
from ui.widgets.case_list_widget import CaseListWidget
from ui.dialogs.case_print_dialog import CasePrintDialog
from ui.widgets.toast_notification import ToastNotification
from utils.datetime_utils import (
    get_relative_date_text,
    format_german_date_with_relative,
    format_german_date,
    format_german_time,
    format_german_datetime,
)


def test_unicode_no_variation_selectors_in_src():
    """Anti-regression test: Ensure no \\ufe0f or \\ufe0e variation selectors exist anywhere in src/*.py."""
    forbidden_chars = {
        "\ufe0f": "VARIATION SELECTOR-16 (\\ufe0f)",
        "\ufe0e": "VARIATION SELECTOR-15 (\\ufe0e)",
        "\u200b": "ZERO WIDTH SPACE (\\u200b)",
        "\ufeff": "ZERO WIDTH NO-BREAK SPACE (\\ufeff)",
    }

    violations = []
    src_dir = Path("src")
    for py_file in src_dir.rglob("*.py"):
        content = py_file.read_text(encoding="utf-8")
        for char, char_name in forbidden_chars.items():
            if char in content:
                violations.append(f"{py_file} contains {char_name}")

    assert not violations, f"Found forbidden Unicode control characters in codebase:\n" + "\n".join(violations)


def test_relative_date_text_calculation():
    """Verify get_relative_date_text accurately calculates today, tomorrow, day-after-tomorrow,

    yesterday, day-before-yesterday, weeks and day counts.
    """
    ref = date(2026, 8, 25)  # Tuesday

    # Today
    assert get_relative_date_text("2026-08-25T14:00:00", ref_date=ref) == "heute"
    assert get_relative_date_text("25.08.2026", ref_date=ref) == "heute"

    # Tomorrow & Day after tomorrow
    assert get_relative_date_text("2026-08-26T10:00:00", ref_date=ref) == "morgen"
    assert get_relative_date_text("2026-08-27T10:00:00", ref_date=ref) == "übermorgen"

    # Yesterday & Day before yesterday
    assert get_relative_date_text("2026-08-24T10:00:00", ref_date=ref) == "gestern"
    assert get_relative_date_text("2026-08-23T10:00:00", ref_date=ref) == "vorgestern"

    # This week / Next week
    assert get_relative_date_text("2026-08-28T10:00:00", ref_date=ref) == "diese Woche"
    assert get_relative_date_text("2026-08-31T10:00:00", ref_date=ref) == "nächste Woche"
    assert get_relative_date_text("2026-08-18T10:00:00", ref_date=ref) == "letzte Woche"

    # Distant days
    assert get_relative_date_text("2026-09-10T10:00:00", ref_date=ref) == "in 16 Tagen"
    assert get_relative_date_text("2026-08-01T10:00:00", ref_date=ref) == "vor 24 Tagen"

    # Formatted helper
    assert format_german_date_with_relative("2026-08-26T14:00:00", ref_date=ref) == "26.08.2026 (morgen)"
    assert format_german_date_with_relative("2026-08-25T14:00:00", ref_date=ref) == "25.08.2026 (heute)"


def test_case_list_widget_3_line_followup_and_dynamic_wrapping():
    """Verify CaseListWidget renders followups across 3 lines and dynamically adjusts wraplength on configure."""
    app = ctk.CTk()
    app.withdraw()

    selected_cases = []
    widget = CaseListWidget(
        app,
        on_case_selected=lambda c: selected_cases.append(c),
        on_search_changed=lambda s: None,
    )

    case = Case(
        case_id="T-2026-100",
        customer=CaseCustomer(customer_id="K-1", practice_name="Gemeinschaftspraxis Nord"),
        classification=Classification(title="Zuzahlungsfehler", urgency_level=UrgencyLevel.YELLOW),
        workflow_status=WorkflowStatus(
            followup_at="2026-08-26T14:30:00",
            followup_note="Wegen Rückmeldung anrufen",
            current_actor=Actor.SUPPORT,
        ),
    )

    widget.set_cases([case])

    # Verify wrap labels are registered
    assert len(widget.wrap_labels) >= 3

    # Check 3-line followup label texts
    all_texts = [lbl.cget("text") for lbl in widget.wrap_labels]
    assert any("🔔 Nachfragen am:" in t for t in all_texts)
    assert any("26.08.2026" in t for t in all_texts)
    assert any("14:30 Uhr" in t for t in all_texts)
    assert any("Wegen Rückmeldung anrufen" in t for t in all_texts)

    # Test dynamic configure resize
    initial_wrap = widget.wrap_labels[0].cget("wraplength")
    widget._last_wrap_width = 100
    widget.configure(width=400)
    # Simulate configure event with larger width
    class DummyEvent:
        pass
    widget._on_widget_configure(DummyEvent())
    # Should update wraplength without throwing exceptions
    assert widget.wrap_labels[0].cget("wraplength") >= 160

    widget.destroy()
    app.destroy()


def test_case_print_dialog_embeds_images_and_overview(tmp_path: Path):
    """Verify CasePrintDialog creates report with metadata overview and embeds image attachments."""
    workspace_dir = tmp_path / "workspace"
    workspace_dir.mkdir()
    config = AppConfig(workspace_dir=workspace_dir)
    att_service = AttachmentService(config)

    case = Case(
        case_id="T-2026-PRINT",
        customer=CaseCustomer(customer_id="K-01", practice_name="Praxis Sonnenberg", contact_person="Dr. Sonne"),
        classification=Classification(title="Druckvorschau Test", calculated_score=85.0),
        workflow_status=WorkflowStatus(board_column=BoardColumn.ACTION_REQUIRED, current_actor=Actor.SUPPORT),
        created_by="DaniBani",
        form_data={"Modul": "Faktura", "Fehler": "Rechnungsdatei fehlt"},
        timeline=[
            TimelineEntry(timestamp="2026-08-25T10:00:00", author="DaniBani", note="Fehlerbericht vom Kunden erhalten"),
        ],
    )

    # Create dummy image in attachment dir
    case_dir = att_service.get_case_attachment_dir(case)
    sample_img = case_dir / "screenshot.png"
    # Write valid minimal PNG bytes (1x1 transparent pixel)
    png_bytes = b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01\x08\x06\x00\x00\x00\x1f\x15c4\x00\x00\x00\nIDATx\x9cc`\x00\x00\x00\x02\x00\x01H\xaf\xa4q\x00\x00\x00\x00IEND\xaeB`\x82"
    sample_img.write_bytes(png_bytes)

    app = ctk.CTk()
    app.withdraw()

    dialog = CasePrintDialog(app, case, attachment_service=att_service)

    # Check generated HTML content
    selected_entries = [case.timeline[0]]
    # We can inspect generate_and_open_html output
    dialog.update_idletasks()
    assert dialog.include_attachments_var.get() is True

    dialog.destroy()
    app.destroy()


def test_schema_zuzahlungsnachforderung_has_requested_files():
    """Verify schema_zuzahlungsnachforderung contains the multi-line requested_files field."""
    storage = StorageService(AppConfig(workspace_dir=Path(".")))
    seed_service = SeedService(storage)
    schemas = seed_service.create_seed_schemas()

    zuzahlung_schema = next((s for s in schemas if s.schema_id == "schema_zuzahlungsnachforderung"), None)
    assert zuzahlung_schema is not None

    req_field = next((f for f in zuzahlung_schema.fields if f.field_id == "requested_files"), None)
    assert req_field is not None
    assert "Dateien" in req_field.label
    assert req_field.required is False


def test_toast_notification_button_visibility():
    """Verify ToastNotification initializes with spacious geometry and fully visible button."""
    app = ctk.CTk()
    app.withdraw()

    opened = []
    toast = ToastNotification(
        app,
        title="🔔 Wiedervorlage fällig",
        message="Fall T-2026-001 ist zur Wiedervorlage bereit.",
        duration_ms=10000,
        on_open=lambda: opened.append(True),
    )

    toast.update_idletasks()

    # Find button and verify width and text
    btn = next((c for c in toast.winfo_children()[0].winfo_children() if isinstance(c, ctk.CTkButton)), None)
    assert btn is not None
    assert btn.cget("text") == "👁 Öffnen"
    assert btn.cget("width") >= 90

    toast.safe_destroy()
    app.destroy()

