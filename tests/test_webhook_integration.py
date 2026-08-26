"""Tests for GitLab and Jira webhook payload formatting and transmission."""

import pytest
from models.case import Case, CaseCustomer, Classification
from services.webhook_integration_service import WebhookIntegrationService


def test_webhook_integration_payload_builder():
    """Verify webhook payload structure contains case ID, labels, title, and formatted description."""
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
