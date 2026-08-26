"""Tests for IMAP email parsing and conversion to case drafts."""

import pytest
from services.imap_import_service import EmailMessageDraft, ImapImportService


def test_imap_email_to_case_draft_conversion():
    """Verify incoming email draft parses to a structured case object."""
    draft = EmailMessageDraft(
        sender_email="dr.mueller@praxis-sonne.de",
        sender_name="Dr. Martin Müller",
        subject="Fehler bei Quartalsabrechnung 03/2026",
        body="Sehr geehrtes Support-Team, wir erhalten den Fehlercode ERR_ACCOUNTING_500...",
    )

    case = ImapImportService.parse_email_to_case(draft, default_author="AutoMail-Bot")

    assert case.case_id.startswith("MAIL-")
    assert case.classification.title == "Fehler bei Quartalsabrechnung 03/2026"
    assert case.customer.contact_person == "Dr. Martin Müller"
    assert case.customer.practice_name == "Praxis Dr. Martin Müller"
    assert len(case.timeline) == 1
    assert case.timeline[0].author == "AutoMail-Bot"
