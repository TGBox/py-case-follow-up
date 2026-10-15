"""Calendar/e-mail drafts (ICS, mail text) and the Outlook integration: COM transfer, mailto fallback, mail-to-case parsing and matching."""
import sys
import webbrowser
from types import ModuleType
from typing import Any
from unittest.mock import MagicMock

import pytest

from models.case import Case, CaseCustomer, Classification, TimelineEntry, WorkflowStatus
from models.customer import Contact, Customer
from services.calendar_email_service import CalendarEmailService
from services.outlook_integration_service import OutlookIntegrationService as Outlook


def _callback_case() -> Case:
    """Case whose contact data comes from a master-data Customer with only a contact list (no own name/phone/mail)."""
    cust = Customer(customer_id="00121", practice_name="Gemeinschaftspraxis Musterstadt",
                    contacts=[Contact(name="Dr. Anna Weber", email="weber@musterpraxis.de", phone="030-12345678")])
    assert (cust.contact_person, cust.email, cust.phone) == ("Dr. Anna Weber", "weber@musterpraxis.de", "030-12345678")
    return Case(
        case_id="T-2026-9999",
        customer=CaseCustomer(customer_id=cust.customer_id, practice_name=cust.practice_name,
                              contact_person=cust.contact_person, phone=cust.phone, email=cust.email),
        classification=Classification(schema_id="schema_bug", title="Zuzahlungsdatei lässt sich nicht erzeugen",
                                      deadline_callback="25.08.2026 14:00"),
        timeline=[TimelineEntry(timestamp="2026-08-24T20:00:00", author="DaniBani",
                                note="Beim Export der Zuzahlungsdatei tritt Fehler AL-99 auf.")],
        workflow_status=WorkflowStatus(followup_at="2026-08-25T14:00:00"),
        created_by="DaniBani",
    )


def _fake_win32com(monkeypatch, outlook_app) -> None:
    win32com: Any = ModuleType("win32com")
    client: Any = ModuleType("client")
    client.Dispatch = MagicMock(return_value=outlook_app)
    win32com.client = client
    monkeypatch.setitem(sys.modules, "win32com", win32com)
    monkeypatch.setitem(sys.modules, "win32com.client", client)


@pytest.fixture
def no_win32com(monkeypatch):
    monkeypatch.setitem(sys.modules, "win32com", None)
    monkeypatch.setitem(sys.modules, "win32com.client", None)


# --- calendar / mail draft ---------------------------------------------------

def test_ics_file_contains_callback_event_with_alarm(tmp_path):
    service = CalendarEmailService(workspace_dir=tmp_path)
    ics_file = service.generate_ics_file(_callback_case(), target_dir=tmp_path, user_name="TestAgent")

    assert ics_file.name == "Rueckruf_T-2026-9999.ics"
    text = ics_file.read_text(encoding="utf-8")
    for line in ("BEGIN:VCALENDAR", "VERSION:2.0", "BEGIN:VEVENT", "TRIGGER:-PT15M", "END:VCALENDAR",
                 "SUMMARY:[Fall T-2026-9999] Rückruf: Gemeinschaftspraxis Musterstadt - Zuzahlungsdatei lässt sich nicht erzeugen"):
        assert line in text


def test_email_draft_addresses_contact_and_appends_signature():
    draft = CalendarEmailService().generate_email_draft(
        _callback_case(), user_name="DaniBani", signature="Tel. 0800-123456\nSupport-Team GmbH")
    assert draft["to"] == "weber@musterpraxis.de"
    assert "T-2026-9999" in draft["subject"] and "Zuzahlungsdatei" in draft["subject"]
    assert "Sehr geehrte(r) Dr. Anna Weber," in draft["body"]
    assert "DaniBani" in draft["body"]
    assert "Tel. 0800-123456\nSupport-Team GmbH" in draft["body"]


# --- Outlook transfer --------------------------------------------------------

def test_transfer_to_outlook_fills_and_shows_a_com_mail(monkeypatch):
    mail = MagicMock()
    outlook = MagicMock()
    outlook.CreateItem.return_value = mail
    _fake_win32com(monkeypatch, outlook)

    assert Outlook.transfer_to_outlook(to_email="support@example.com", subject="Test Betreff", body_text="Test Mailtext") is True
    assert (mail.To, mail.Subject, mail.Body) == ("support@example.com", "Test Betreff", "Test Mailtext")
    mail.Display.assert_called_once_with(True)


def test_transfer_to_outlook_falls_back_to_mailto(monkeypatch, no_win32com):
    opened = []
    monkeypatch.setattr(webbrowser, "open", lambda url: opened.append(url) or True)
    assert Outlook.transfer_to_outlook(to_email="kunde@praxis.de", subject="Rückruf Termin", body_text="Hallo") is True
    assert len(opened) == 1
    assert opened[0].startswith("mailto:kunde@praxis.de?")
    assert "R%C3%BCckruf" in opened[0]

    def no_browser(url):
        raise RuntimeError("No browser available")

    monkeypatch.setattr(webbrowser, "open", no_browser)
    assert Outlook.transfer_to_outlook("", "", "") is False


# --- inbox ------------------------------------------------------------------

def test_fetch_recent_emails_reads_the_com_inbox(monkeypatch):
    msg = MagicMock(Subject="Test COM Mail", SenderName="Frau Schmidt", SenderEmailAddress="schmidt@labor.de",
                    Body="Laborergebnisse", ReceivedTime="2026-09-17 10:00:00")
    items = MagicMock()
    items.__iter__.return_value = [msg]
    outlook = MagicMock()
    outlook.GetNamespace.return_value.GetDefaultFolder.return_value.Items = items
    _fake_win32com(monkeypatch, outlook)

    emails = Outlook.fetch_recent_emails(max_count=5)
    assert len(emails) == 1
    assert (emails[0]["subject"], emails[0]["sender_email"]) == ("Test COM Mail", "schmidt@labor.de")


def test_fetch_recent_emails_without_outlook_returns_demo_mails(no_win32com):
    emails = Outlook.fetch_recent_emails()
    assert len(emails) >= 2
    assert "FALL-2026-0001" in emails[0]["subject"]
    assert "@" in emails[0]["sender_email"]


# --- mail <-> case -----------------------------------------------------------

@pytest.mark.parametrize("subject, body, expected", [
    ("Re: [FALL-2026-0042] Status update", "", "FALL-2026-0042"),
    ("Statusanfrage", "Bezug auf mail-109 danke", "MAIL-109"),
    ("Ticket-777 Rückmeldung", "", "TICKET-777"),
    ("Kein Treffer", "Unbekannter Fall", None),
])
def test_find_matching_case(subject, body, expected):
    cases = [Case(case_id=cid, customer=CaseCustomer(practice_name=f"Praxis {cid}"))
             for cid in ("FALL-2026-0042", "MAIL-109", "TICKET-777")]
    match = Outlook.find_matching_case(subject, body, cases)
    assert (match.case_id if match else None) == expected


def test_parse_outlook_email_to_case():
    case = Outlook.parse_outlook_email_to_case(
        subject="[K-10482] Abrechnungsproblem nach Update", sender_email="abrechnung@praxis-ulm.de",
        sender_name="Frau Sabine Weber", body="Wir können die Abrechnung nicht übermitteln.",
        received_time="2026-08-25T15:00:00",
    )
    assert case.case_id.startswith("MAIL-")
    assert case.customer.customer_id == "K-10482"
    assert "Frau Sabine Weber" in case.customer.contact_person
    assert case.classification.title == "[K-10482] Abrechnungsproblem nach Update"
    assert len(case.timeline) == 1
    assert "abrechnung@praxis-ulm.de" in case.timeline[0].note
    assert "Abrechnung nicht übermitteln" in case.timeline[0].note

    doctor = Outlook.parse_outlook_email_to_case(subject="TI-Fehler bei K-44921", sender_email="rossi@arztpraxis.de",
                                                 sender_name="Dr. Elena Rossi", body="Konnektor nicht erreichbar.")
    assert (doctor.customer.customer_id, doctor.customer.practice_name, doctor.customer.email) == (
        "K-44921", "Dr. Elena Rossi", "rossi@arztpraxis.de")

    anonymous = Outlook.parse_outlook_email_to_case(subject="", sender_email="sonnenberg@med.de",
                                                    sender_name="Sonnenberg Gemeinschaft", body="Kurze Info")
    assert anonymous.customer.customer_id == "K-OUTLOOK"
    assert anonymous.customer.practice_name == "Praxis Sonnenberg Gemeinschaft"
    assert anonymous.classification.title == "E-Mail ohne Betreff"


def test_append_outlook_email_to_case_timeline():
    case = Case(case_id="T-2026-050", customer=CaseCustomer(customer_id="K-100", practice_name="Praxis Alpha"))
    entry = Outlook.append_outlook_email_to_case_timeline(
        case=case, sender_name="Dr. Alpha", sender_email="alpha@praxis.de", subject="Re: Serverprüfung",
        body="Server wurde neu gestartet, Problem besteht weiterhin.", author="Outlook-Import",
    )
    assert case.timeline == [entry]
    assert (entry.author, entry.channel) == ("Outlook-Import", "E-Mail")
    for text in ("Re: Serverprüfung", "alpha@praxis.de", "Problem besteht weiterhin"):
        assert text in entry.note


# --- import dialog -----------------------------------------------------------

def test_email_import_dialog_appends_to_case_and_creates_new_case(root):
    from ui.dialogs.email_import_dialog import EmailImportDialog

    case = Case(case_id="FALL-2026-0001", customer=CaseCustomer(practice_name="Praxis Weber"))
    created, updated = [], []
    dialog = EmailImportDialog(parent=root, cases=[case], on_case_created=created.append,
                               on_case_updated=updated.append, author_name="Tester")
    assert dialog.emails, "inbox (demo mails off Windows) is listed"

    dialog.append_to_case({"subject": "Ref: FALL-2026-0001 Notiz", "sender_name": "Dr. Weber",
                           "sender_email": "weber@test.de", "body": "Hallo", "received_time": "2026-08-26T12:00:00"}, case, 0)
    assert updated == [case] and case.timeline

    dialog.create_new_case_from_mail({"subject": "Neue Supportanfrage", "sender_name": "Fr. Schmidt",
                                      "sender_email": "schmidt@test.de", "body": "Fehler beim Export",
                                      "received_time": "2026-08-26T12:05:00"}, 0)
    assert len(created) == 1
    assert created[0].customer.contact_person == "Fr. Schmidt"
    dialog.destroy()
