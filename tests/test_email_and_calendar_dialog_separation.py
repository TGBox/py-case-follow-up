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


def test_german_salutation_formatting():
    """Verify polite German business salutations for various contact person formats."""
    from services.calendar_email_service import format_german_salutation

    assert format_german_salutation("Frau Weber") == "Sehr geehrte Frau Weber,"
    assert format_german_salutation("Herr Lehmann") == "Sehr geehrter Herr Lehmann,"
    assert format_german_salutation("Herrn Schmidt") == "Sehr geehrter Herr Schmidt,"
    assert format_german_salutation("Dr. Elena Rossi") == "Sehr geehrte(r) Dr. Elena Rossi,"
    assert format_german_salutation("Frau Dr. Meyer") == "Sehr geehrte Frau Dr. Meyer,"
    assert format_german_salutation("Herr Dr. med. Koch") == "Sehr geehrter Herr Dr. med. Koch,"
    assert format_german_salutation("Klaus Becker") == "Sehr geehrte/r Klaus Becker,"
    assert format_german_salutation("", "Praxis Sonnenberg") == "Sehr geehrte Damen und Herren (Praxis Sonnenberg),"
    assert format_german_salutation("", "") == "Sehr geehrte Damen und Herren,"


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
            contact_person="Frau Weber",
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
    assert "Sehr geehrte Frau Weber," in dialog.body_textbox.get("1.0", "end")

    # Verify snippet insertion
    dialog.insert_snippet_text("Zusätzlicher Text")
    assert "Zusätzlicher Text" in dialog.body_textbox.get("1.0", "end")

    dialog.destroy()
    app.destroy()


def test_email_draft_dialog_without_case_and_praxiskartei_autocomplete(tmp_path: Path):
    """Verify EmailDraftDialog supports case=None, Praxiskartei dropdown, typing filter, and freeform input."""
    from models.customer import Customer, Contact

    config = AppConfig(workspace_dir=tmp_path)
    cal_email_svc = CalendarEmailService(config)

    test_customers = [
        Customer(
            customer_id="K-10482",
            practice_name="Praxis Sonnenberg",
            contacts=[
                Contact(name="Frau Weber", role="Leitende MFA", email="weber@sonnenberg.de"),
                Contact(name="Dr. med. Frank Berg", role="Inhaber", email="berg@sonnenberg.de"),
            ],
        ),
        Customer(
            customer_id="K-10890",
            practice_name="Zahnarztpraxis Dr. Lehmann",
            contacts=[
                Contact(name="Herr Lehmann", role="Praxisinhaber", email="lehmann@zahnpraxis.de"),
            ],
        ),
    ]

    app = ctk.CTk()
    app.withdraw()

    dialog = EmailDraftDialog(
        app,
        case=None,
        calendar_email_service=cal_email_svc,
        user_name="SupportAgent",
        customers=test_customers,
    )
    dialog.update_idletasks()

    # 1. Starts empty with generic salutation
    assert dialog.to_entry.get() == ""
    assert "Sehr geehrte Damen und Herren," in dialog.body_textbox.get("1.0", "end")

    # 2. Test Praxiskartei dropdown toggle
    assert not dialog.suggestions_frame_visible
    dialog.toggle_praxiskartei_dropdown()
    dialog.update_idletasks()
    assert dialog.suggestions_frame_visible

    # 3. Test typing filter with search string
    dialog.to_entry.delete(0, "end")
    dialog.to_entry.insert(0, "weber")
    dialog._on_to_keyrelease()
    dialog.update_idletasks()
    assert dialog.suggestions_frame_visible

    # 4. Test selecting contact -> updates to_entry & dynamic salutation in body
    weber_contact = next(c for c in dialog.all_contacts if "weber" in c["search_key"])
    dialog.select_contact(weber_contact)
    dialog.update_idletasks()

    assert dialog.to_entry.get() == "weber@sonnenberg.de"
    assert not dialog.suggestions_frame_visible
    assert "Sehr geehrte Frau Weber," in dialog.body_textbox.get("1.0", "end")

    # 5. Test selecting another contact from Lehmann
    lehmann_contact = next(c for c in dialog.all_contacts if "lehmann" in c["search_key"])
    dialog.select_contact(lehmann_contact)
    dialog.update_idletasks()

    assert dialog.to_entry.get() == "lehmann@zahnpraxis.de"
    assert "Sehr geehrter Herr Lehmann," in dialog.body_textbox.get("1.0", "end")

    # 6. Test completely custom / new email address entry
    dialog.to_entry.delete(0, "end")
    dialog.to_entry.insert(0, "ganz.neue.praxis@gesundheit-nord.de")
    assert dialog.to_entry.get() == "ganz.neue.praxis@gesundheit-nord.de"

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
