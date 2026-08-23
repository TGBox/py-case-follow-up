import pytest
from services.imap_import_service import ImapImportService, EmailMessageDraft
from services.webhook_integration_service import WebhookIntegrationService
from models.case import Case, CaseCustomer, Classification, WorkflowStatus


def test_imap_email_to_case_draft_conversion():
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


def test_webhook_integration_payload_builder():
    c = Case(case_id="T-DEV-100")
    c.customer = CaseCustomer(customer_id="K-999", practice_name="Gemeinschaftspraxis Nord")
    c.classification = Classification(title="DB-Locking bei Rezeptdruck")
    c.workflow_status.current_actor = "DEVELOPMENT"

    payload = WebhookIntegrationService.build_payload(c, event_name="case_handover", notes="An Entwickler übergeben")

    assert payload["event"] == "case_handover"
    assert payload["issue"]["title"] == "[T-DEV-100] DB-Locking bei Rezeptdruck"
    assert "development" in payload["issue"]["labels"]

    success = WebhookIntegrationService.send_webhook("https://gitlab.meinefirma.de/api/v4/webhooks", payload)
    assert success is True
