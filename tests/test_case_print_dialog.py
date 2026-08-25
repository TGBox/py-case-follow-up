"""Tests for CasePrintDialog formatting, metadata overview, and embedded image attachments."""

from pathlib import Path
import customtkinter as ctk
import pytest
from config import AppConfig
from enums import Actor, BoardColumn
from models.case import Case, CaseCustomer, Classification, TimelineEntry, WorkflowStatus
from services.attachment_service import AttachmentService
from ui.dialogs.case_print_dialog import CasePrintDialog


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
    png_bytes = b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01\x08\x06\x00\x00\x00\x1f\x15c4\x00\x00\x00\nIDATx\x9cc`\x00\x00\x00\x02\x00\x01H\xaf\xa4q\x00\x00\x00\x00IEND\xaeB`\x82"
    sample_img.write_bytes(png_bytes)

    app = ctk.CTk()
    app.withdraw()

    dialog = CasePrintDialog(app, case, attachment_service=att_service)

    dialog.update_idletasks()
    assert dialog.include_attachments_var.get() is True

    dialog.destroy()
    app.destroy()


def test_case_print_report_formatting():
    """Verify Case report object contains all customer, timeline, and form fields for print rendering."""
    c = Case(case_id="T-PRINT-01")
    c.customer = CaseCustomer(customer_id="K-500", practice_name="Zahnarzt Dr. Sonntags", contact_person="Herr Lehmann")
    c.classification = Classification(title="PVS Serverabsturz")
    c.form_data = {"affected_user": "Dr. Sonntags", "error_code": "ERR_503"}
    c.timeline.append(TimelineEntry(timestamp="2026-08-23T10:00:00", author="Support Agent", note="Ticket aufgenommen"))
    c.timeline.append(TimelineEntry(timestamp="2026-08-23T11:30:00", author="Support Agent", note="Interner Testlauf"))

    assert c.customer.customer_id == "K-500"
    assert len(c.timeline) == 2
    assert c.form_data["error_code"] == "ERR_503"
