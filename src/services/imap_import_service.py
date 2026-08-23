import logging
from dataclasses import dataclass, field
from datetime import datetime
from models.case import Case, CaseCustomer, Classification, WorkflowStatus, TimelineEntry
from enums import Channel, BoardColumn, Actor
from utils.datetime_utils import now_iso

logger = logging.getLogger(__name__)


@dataclass
class EmailMessageDraft:
    sender_email: str
    sender_name: str
    subject: str
    body: str
    received_at: str = field(default_factory=now_iso)


class ImapImportService:
    """Service for parsing email messages and creating draft cases from support inbox messages."""

    @staticmethod
    def parse_email_to_case(msg: EmailMessageDraft, default_author: str = "E-Mail Import") -> Case:
        clean_subject = msg.subject.strip() or "E-Mail Supportanfrage"
        practice_name = msg.sender_name.strip() or msg.sender_email.split("@")[0].capitalize()

        customer = CaseCustomer(
            customer_id=f"MAIL-{msg.sender_email.replace('@', '_at_')}",
            practice_name=f"Praxis {practice_name}",
            contact_person=msg.sender_name or msg.sender_email,
            phone="",
        )

        case_id = f"MAIL-{int(datetime.now().timestamp())}"

        initial_timeline = [
            TimelineEntry(
                timestamp=msg.received_at,
                author=default_author,
                channel=Channel.EMAIL,
                note=f"E-Mail Betreff: {clean_subject}\n\nInhalt:\n{msg.body[:500]}",
                status_change="NEW -> ACTION_REQUIRED (SUPPORT)",
            )
        ]

        return Case(
            case_id=case_id,
            created_at=msg.received_at,
            updated_at=msg.received_at,
            created_by=default_author,
            assigned_to=default_author,
            customer=customer,
            classification=Classification(
                schema_id="default",
                title=clean_subject,
                deadline_callback="",
                tags=["E-Mail-Import"],
            ),
            workflow_status=WorkflowStatus(
                is_completed=False,
                is_archived=False,
                board_column=BoardColumn.ACTION_REQUIRED,
                current_actor=Actor.SUPPORT,
                actor_since=msg.received_at,
            ),
            form_data={"email_sender": msg.sender_email, "email_subject": clean_subject},
            timeline=initial_timeline,
        )
