"""Extended tests for OutlookIntegrationService: mail transfer, COM automation, parsing, matching, and fallback."""

import sys
import webbrowser
from types import ModuleType
from typing import Any
from unittest.mock import MagicMock
from models.case import Case, CaseCustomer
from services.outlook_integration_service import OutlookIntegrationService


def test_transfer_to_outlook_com_success(monkeypatch):
    """Verify transfer_to_outlook successfully drives win32com Outlook.Application."""
    mock_mail = MagicMock()
    mock_outlook = MagicMock()
    mock_outlook.CreateItem.return_value = mock_mail
    mock_win32com: Any = ModuleType("win32com")
    mock_client: Any = ModuleType("client")
    mock_client.Dispatch = MagicMock(return_value=mock_outlook)
    mock_win32com.client = mock_client

    monkeypatch.setitem(sys.modules, "win32com", mock_win32com)
    monkeypatch.setitem(sys.modules, "win32com.client", mock_client)

    success = OutlookIntegrationService.transfer_to_outlook(
        to_email="support@example.com",
        subject="Test Betreff",
        body_text="Test Mailtext",
    )
    assert success is True
    assert mock_mail.To == "support@example.com"
    assert mock_mail.Subject == "Test Betreff"
    assert mock_mail.Body == "Test Mailtext"
    mock_mail.Display.assert_called_once_with(True)


def test_transfer_to_outlook_mailto_fallback(monkeypatch):
    """Verify transfer_to_outlook falls back to mailto when COM raises exception."""
    # Ensure win32com is absent or raises
    monkeypatch.setitem(sys.modules, "win32com", None)
    monkeypatch.setitem(sys.modules, "win32com.client", None)

    opened_urls = []
    monkeypatch.setattr(webbrowser, "open", lambda url: opened_urls.append(url) or True)

    success = OutlookIntegrationService.transfer_to_outlook(
        to_email="kunde@praxis.de",
        subject="Rückruf Termin",
        body_text="Hallo Herr Dr. Meier",
    )
    assert success is True
    assert len(opened_urls) == 1
    assert "mailto:kunde@praxis.de?" in opened_urls[0]
    assert "R%C3%BCckruf" in opened_urls[0] or "Rückruf" in opened_urls[0]

    # Test failure when webbrowser.open raises
    def failing_browser(url):
        raise RuntimeError("No browser available")

    monkeypatch.setattr(webbrowser, "open", failing_browser)
    assert OutlookIntegrationService.transfer_to_outlook("", "", "") is False


def test_parse_outlook_email_to_case():
    """Verify parse_outlook_email_to_case extracts customer ID, practice name, and creates timeline."""
    # 1. Subject with Customer ID and Doctor title
    case1 = OutlookIntegrationService.parse_outlook_email_to_case(
        subject="TI-Fehler bei K-44921",
        sender_email="rossi@arztpraxis.de",
        sender_name="Dr. Elena Rossi",
        body="Konnektor nicht erreichbar.",
    )
    assert case1.customer.customer_id == "K-44921"
    assert case1.customer.practice_name == "Dr. Elena Rossi"
    assert case1.customer.email == "rossi@arztpraxis.de"
    assert case1.classification.title == "TI-Fehler bei K-44921"
    assert len(case1.timeline) == 1
    assert "Konnektor nicht erreichbar" in case1.timeline[0].note

    # 2. Email without customer ID, without Dr. or Praxis prefix, empty subject
    case2 = OutlookIntegrationService.parse_outlook_email_to_case(
        subject="",
        sender_email="sonnenberg@med.de",
        sender_name="Sonnenberg Gemeinschaft",
        body="Kurze Info",
    )
    assert case2.customer.customer_id == "K-OUTLOOK"
    assert case2.customer.practice_name == "Praxis Sonnenberg Gemeinschaft"
    assert case2.classification.title == "E-Mail ohne Betreff"


def test_append_outlook_email_to_case_timeline():
    """Verify append_outlook_email_to_case_timeline appends note with author and content."""
    case = Case(case_id="FALL-99")
    entry = OutlookIntegrationService.append_outlook_email_to_case_timeline(
        case=case,
        sender_name="Sabine Meyer",
        sender_email="meyer@labor.de",
        subject="Laborbefunde Verzögerung",
        body="Die Übertragung verzögert sich um 2 Tage.",
        author="Outlook-Bot",
    )
    assert entry in case.timeline
    assert entry.author == "Outlook-Bot"
    assert entry.channel == "E-Mail"
    assert "Laborbefunde Verzögerung" in entry.note
    assert "meyer@labor.de" in entry.note


def test_find_matching_case():
    """Verify find_matching_case locates cases by explicit case_id or regex patterns."""
    cases = [
        Case(case_id="FALL-2026-0042", customer=CaseCustomer(practice_name="Praxis A")),
        Case(case_id="MAIL-109", customer=CaseCustomer(practice_name="Praxis B")),
        Case(case_id="TICKET-777", customer=CaseCustomer(practice_name="Praxis C")),
    ]

    # Explicit match in subject
    match1 = OutlookIntegrationService.find_matching_case("Re: FALL-2026-0042 Update", "Details hier", cases)
    assert match1 is not None
    assert match1.case_id == "FALL-2026-0042"

    # Match in body
    match2 = OutlookIntegrationService.find_matching_case("Statusanfrage", "Bezug auf mail-109 danke", cases)
    assert match2 is not None
    assert match2.case_id == "MAIL-109"

    # Regex fallback match
    match3 = OutlookIntegrationService.find_matching_case("Ticket-777 Rückmeldung", "", cases)
    assert match3 is not None
    assert match3.case_id == "TICKET-777"

    # No match
    assert OutlookIntegrationService.find_matching_case("Kein Treffer", "Unbekannter Fall", cases) is None


def test_fetch_recent_emails_com_success(monkeypatch):
    """Verify fetch_recent_emails extracts message attributes when COM is active."""
    mock_msg = MagicMock()
    mock_msg.Subject = "Test COM Mail"
    mock_msg.SenderName = "Frau Schmidt"
    mock_msg.SenderEmailAddress = "schmidt@labor.de"
    mock_msg.Body = "Laborergebnisse"
    mock_msg.ReceivedTime = "2026-09-17 10:00:00"

    mock_items = MagicMock()
    mock_items.__iter__.return_value = [mock_msg]

    mock_inbox = MagicMock()
    mock_inbox.Items = mock_items

    mock_namespace = MagicMock()
    mock_namespace.GetDefaultFolder.return_value = mock_inbox

    mock_outlook = MagicMock()
    mock_outlook.GetNamespace.return_value = mock_namespace

    mock_win32com: Any = ModuleType("win32com")
    mock_client: Any = ModuleType("client")
    mock_client.Dispatch = MagicMock(return_value=mock_outlook)
    mock_win32com.client = mock_client

    monkeypatch.setitem(sys.modules, "win32com", mock_win32com)
    monkeypatch.setitem(sys.modules, "win32com.client", mock_client)

    emails = OutlookIntegrationService.fetch_recent_emails(max_count=5)
    assert len(emails) == 1
    assert emails[0]["subject"] == "Test COM Mail"
    assert emails[0]["sender_email"] == "schmidt@labor.de"


def test_fetch_recent_emails_fallback(monkeypatch):
    """Verify fetch_recent_emails returns fallback demo emails when COM is unavailable."""
    monkeypatch.setitem(sys.modules, "win32com", None)
    monkeypatch.setitem(sys.modules, "win32com.client", None)

    emails = OutlookIntegrationService.fetch_recent_emails()
    assert len(emails) >= 2
    assert "FALL-2026-0001" in emails[0]["subject"]
    assert "@" in emails[0]["sender_email"]


def test_get_outlook_vba_macro_code():
    """Verify get_outlook_vba_macro_code returns valid macro with subroutine."""
    code = OutlookIntegrationService.get_outlook_vba_macro_code()
    assert "Sub TransferSelectedMailToSupportCockpit()" in code
    assert "support_cockpit_import.json" in code
    assert "End Sub" in code
