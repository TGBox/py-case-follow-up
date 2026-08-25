"""Tests for CasePrintDialog build_html_content, auto_print toggle, and report saving."""

from pathlib import Path
import customtkinter as ctk
import pytest
from config import AppConfig
from enums import Actor, BoardColumn
from models.case import Case, CaseCustomer, Classification, TimelineEntry, WorkflowStatus
from services.attachment_service import AttachmentService
from ui.dialogs.case_print_dialog import CasePrintDialog


def test_case_print_build_html_content(tmp_path: Path):
    """Verify build_html_content supports both auto_print mode and clean static file saving mode."""
    config = AppConfig(workspace_dir=tmp_path)
    att_service = AttachmentService(config)

    case = Case(
        case_id="T-2026-PRINT-OPT",
        customer=CaseCustomer(customer_id="K-55", practice_name="Praxis Dr. Med. Test", is_vip=True),
        classification=Classification(title="Druckoptionen Testfall", calculated_score=92.0),
        workflow_status=WorkflowStatus(board_column=BoardColumn.ACTION_REQUIRED, current_actor=Actor.SUPPORT),
        created_by="DaniBani",
        form_data={"Modul": "Abrechnung", "Betrag": "120,50 €"},
        timeline=[
            TimelineEntry(timestamp="2026-08-25T11:00:00", author="DaniBani", note="Kunde hat Korrekturdatei geschickt."),
        ],
    )

    app = ctk.CTk()
    app.withdraw()

    dialog = CasePrintDialog(app, case, attachment_service=att_service)

    # HTML with auto_print for direct browser printing
    html_print = dialog.build_html_content(auto_print=True)
    assert "window.print()" in html_print
    assert "T-2026-PRINT-OPT" in html_print
    assert "Praxis Dr. Med. Test" in html_print
    assert "VIP-Kunde" in html_print

    # HTML without auto_print for static archiving
    html_static = dialog.build_html_content(auto_print=False)
    assert "window.addEventListener('DOMContentLoaded'" not in html_static
    assert "T-2026-PRINT-OPT" in html_static

    dialog.destroy()
    app.destroy()
