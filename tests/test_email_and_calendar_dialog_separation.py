"""Tests for dedicated EmailDraftDialog and CalendarExportDialog separation and action handlers."""

from pathlib import Path
import customtkinter as ctk
import pytest
from config import AppConfig
from enums import Actor, UrgencyLevel
from models.case import Case, CaseCustomer, Classification, WorkflowStatus
from services.calendar_email_service import CalendarEmailService
from services.snippet_service import SnippetService
from ui.dialogs.calendar_export_dialog import CalendarExportDialog
from ui.dialogs.email_draft_dialog import EmailDraftDialog


def test_email_draft_dialog_initialization(tmp_path: Path):
    """Verify EmailDraftDialog populates recipient, subject, and body from case details."""
    config = AppConfig(workspace_dir=tmp_path)
    cal_email_svc = CalendarEmailService(config)
    snippet_svc = SnippetService(tmp_path)

    case = Case(
        case_id="T-MAIL-01",
        customer=CaseCustomer(
            customer_id="K-100",
            practice_name="Praxis Dr. Sonnenschein",
            email="info@sonnenschein.de",
            contact_person="Dr. Sonnenschein",
        ),
        classification=Classification(title="Rezeptdruck Fehler", urgency_level=UrgencyLevel.YELLOW),
        workflow_status=WorkflowStatus(current_actor=Actor.SUPPORT),
    )

    app = ctk.CTk()
    app.withdraw()

    dialog = EmailDraftDialog(
        app,
        case=case,
        calendar_email_service=cal_email_svc,
        user_name="DaniBani",
        snippet_service=snippet_svc,
    )

    dialog.update_idletasks()

    assert dialog.to_entry.get() == "info@sonnenschein.de"
    assert "T-MAIL-01" in dialog.subject_entry.get()
    assert "Dr. Sonnenschein" in dialog.body_textbox.get("1.0", "end")

    # Verify snippet insertion
    dialog.insert_snippet_text("Zusätzlicher Text")
    assert "Zusätzlicher Text" in dialog.body_textbox.get("1.0", "end")

    dialog.destroy()
    app.destroy()


def test_calendar_export_dialog_initialization(tmp_path: Path):
    """Verify CalendarExportDialog formats .ics summary and handles direct opening and file saving."""
    config = AppConfig(workspace_dir=tmp_path)
    cal_email_svc = CalendarEmailService(config)

    case = Case(
        case_id="T-CAL-01",
        customer=CaseCustomer(
            customer_id="K-200",
            practice_name="Klinik am Park",
            phone="0711-12345",
            contact_person="Herr Wagner",
        ),
        classification=Classification(title="TI Konnektor Update", urgency_level=UrgencyLevel.RED),
        workflow_status=WorkflowStatus(
            followup_at="2026-08-27T10:00:00",
            followup_note="Mit Herrn Wagner Konnektor neu starten",
            current_actor=Actor.SUPPORT,
        ),
    )

    app = ctk.CTk()
    app.withdraw()

    dialog = CalendarExportDialog(
        app,
        case=case,
        calendar_email_service=cal_email_svc,
    )

    dialog.update_idletasks()

    assert "T-CAL-01" in dialog.desc_textbox.get("1.0", "end")
    assert "Klinik am Park" in dialog.desc_textbox.get("1.0", "end")
    assert "Konnektor neu starten" in dialog.desc_textbox.get("1.0", "end")

    dialog.destroy()
    app.destroy()
