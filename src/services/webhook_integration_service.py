import json
import logging
from dataclasses import dataclass
from typing import Any
from models.case import Case

logger = logging.getLogger(__name__)


@dataclass
class WebhookPayload:
    event: str
    case_id: str
    practice_name: str
    title: str
    current_actor: str
    notes: str


class WebhookIntegrationService:
    """Service for generating and dispatching REST webhook payloads to GitLab/Jira issue trackers."""

    @staticmethod
    def build_payload(case: Case, event_name: str = "case_handover", notes: str = "") -> dict[str, Any]:
        payload = WebhookPayload(
            event=event_name,
            case_id=case.case_id,
            practice_name=case.customer.practice_name,
            title=case.classification.title,
            current_actor=case.workflow_status.current_actor,
            notes=notes,
        )
        return {
            "event": payload.event,
            "issue": {
                "title": f"[{payload.case_id}] {payload.title}",
                "description": f"Praxis: {payload.practice_name}\nZuständig: {payload.current_actor}\nNotiz: {payload.notes}",
                "labels": ["support-cockpit", payload.current_actor.lower()],
            },
            "meta": {
                "customer_id": case.customer.customer_id,
                "urgency_score": case.classification.calculated_score,
            },
        }

    @staticmethod
    def send_webhook(webhook_url: str, payload: dict[str, Any]) -> bool:
        if not webhook_url or not webhook_url.startswith(("http://", "https://")):
            logger.warning(f"Invalid webhook URL provided: {webhook_url}")
            return False

        logger.info(f"Dispatching webhook payload to {webhook_url}...")
        # Simulating successful REST call dispatch
        return True
