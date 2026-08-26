import pytest # type: ignore
from pathlib import Path
from unittest.mock import MagicMock
import customtkinter as ctk

from models.case import Case, CaseCustomer, Classification
from models.profile import UserProfile, UserInfo
from services.outlook_integration_service import OutlookIntegrationService
from services.calendar_email_service import CalendarEmailService
from ui.dialogs.email_import_dialog import EmailImportDialog
from ui.dialogs.email_draft_dialog import EmailDraftDialog


def test_outlook_find_matching_case():
    c1 = Case(case_id="FALL-2026-0042", customer=CaseCustomer(practice_name="Praxis A"))
    c2 = Case(case_id="MAIL-1002", customer=CaseCustomer(practice_name="Praxis B"))

    # Subject with explicit ID
    m1 = OutlookIntegrationService.find_matching_case("Re: [FALL-2026-0042] Status update", "", [c1, c2])
    assert m1 is c1

    # Body with regex match
    m2 = OutlookIntegrationService.find_matching_case("Frage zu Ticket", "Bitte prüfen Sie MAIL-1002.", [c1, c2])
    assert m2 is c2

    # No match
    m3 = OutlookIntegrationService.find_matching_case("Freier Betreff", "Ohne Fall-ID", [c1, c2])
    assert m3 is None


def test_outlook_fetch_recent_emails():
    emails = OutlookIntegrationService.fetch_recent_emails(max_count=5)
    assert isinstance(emails, list)
    assert len(emails) > 0
    assert "subject" in emails[0]
    assert "sender_email" in emails[0]


def test_calendar_email_service_signature():
    svc = CalendarEmailService()
    c = Case(case_id="FALL-001", customer=CaseCustomer(practice_name="Praxis Test", contact_person="Dr. Müller"))

    draft = svc.generate_email_draft(
        case=c,
        user_name="Max Mustermann",
        signature="Tel. 0800-123456\nSupport-Team GmbH",
    )

    assert "FALL-001" in draft["subject"]
    assert "Sehr geehrte(r) Dr. Müller," in draft["body"]
    assert "Max Mustermann" in draft["body"]
    assert "Tel. 0800-123456" in draft["body"]
    assert "Support-Team GmbH" in draft["body"]


def test_email_import_dialog_actions():
    root = ctk.CTk()
    root.withdraw()

    c1 = Case(case_id="FALL-2026-0001", customer=CaseCustomer(practice_name="Praxis Weber"))
    cases = [c1]

    created_cases = []
    updated_cases = []

    def on_created(new_c):
        created_cases.append(new_c)

    def on_updated(upd_c):
        updated_cases.append(upd_c)

    dialog = EmailImportDialog(
        parent=root,
        cases=cases,
        on_case_created=on_created,
        on_case_updated=on_updated,
        author_name="Tester",
    )

    assert len(dialog.emails) > 0
    
    # Test append to case
    test_mail = {
        "subject": "Ref: FALL-2026-0001 Notiz",
        "sender_name": "Dr. Weber",
        "sender_email": "weber@test.de",
        "body": "Hallo",
        "received_time": "2026-08-26T12:00:00",
    }
    dialog.append_to_case(test_mail, c1, 0)
    assert len(updated_cases) == 1
    assert len(c1.timeline) > 0

    # Test create new case from mail
    test_mail2 = {
        "subject": "Neue Supportanfrage",
        "sender_name": "Fr. Schmidt",
        "sender_email": "schmidt@test.de",
        "body": "Fehler beim Export",
        "received_time": "2026-08-26T12:05:00",
    }
    dialog.create_new_case_from_mail(test_mail2, 0)
    assert len(created_cases) == 1
    assert created_cases[0].customer.contact_person == "Fr. Schmidt"

    dialog.destroy()
    root.destroy()
