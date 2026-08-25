"""Tests for OutlookIntegrationService bidirectional mail transfer, bridge parsing, and timeline attachment."""

import pytest
from models.case import Case, CaseCustomer, Classification
from services.outlook_integration_service import OutlookIntegrationService


def test_outlook_email_to_case_parsing():
    """Verify parsing an Outlook email creates a well-structured Case object with metadata."""
    case = OutlookIntegrationService.parse_outlook_email_to_case(
        subject="[K-10482] Abrechnungsproblem nach Update",
        sender_email="abrechnung@praxis-ulm.de",
        sender_name="Frau Sabine Weber",
        body="Guten Tag, wir können die Abrechnung nicht übermitteln. Fehlercode 404.",
        received_time="2026-08-25T15:00:00",
    )

    assert case.case_id.startswith("MAIL-")
    assert case.customer.customer_id == "K-10482"
    assert "Frau Sabine Weber" in case.customer.contact_person
    assert "Abrechnungsproblem" in case.classification.title
    assert len(case.timeline) == 1
    assert "abrechnung@praxis-ulm.de" in case.timeline[0].note


def test_outlook_append_to_case_timeline():
    """Verify attaching an incoming Outlook email adds an event to the existing case's timeline."""
    c = Case(
        case_id="T-2026-050",
        customer=CaseCustomer(customer_id="K-100", practice_name="Praxis Alpha"),
        classification=Classification(title="Serverprüfung"),
    )

    entry = OutlookIntegrationService.append_outlook_email_to_case_timeline(
        case=c,
        sender_name="Dr. Alpha",
        sender_email="alpha@praxis.de",
        subject="Re: Serverprüfung",
        body="Server wurde neu gestartet, Problem besteht weiterhin.",
        author="Outlook-Import",
    )

    assert len(c.timeline) == 1
    assert c.timeline[0].author == "Outlook-Import"
    assert c.timeline[0].channel == "E-Mail"
    assert "Problem besteht weiterhin" in c.timeline[0].note


def test_outlook_vba_macro_generation():
    """Verify VBA macro string contains the Outlook transfer subroutine."""
    macro = OutlookIntegrationService.get_outlook_vba_macro_code()
    assert "Sub TransferSelectedMailToSupportCockpit()" in macro
    assert "Outlook.MailItem" in macro
    assert "support_cockpit_import.json" in macro
