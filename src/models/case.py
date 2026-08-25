from dataclasses import dataclass, field, asdict
from typing import Any
from enums import UrgencyLevel, BoardColumn, Actor, Channel
from utils.datetime_utils import parse_iso, format_german_datetime
from constants import VALIDATION_MESSAGES


@dataclass
class TimelineEntry:
    timestamp: str = ""
    author: str = ""
    channel: str = Channel.INTERNAL_NOTE
    note: str = ""
    status_change: str = ""

    def validate(self) -> list[str]:
        errors = []
        if not self.timestamp:
            errors.append(VALIDATION_MESSAGES["timeline_timestamp_required"])
        else:
            try:
                parse_iso(self.timestamp)
            except Exception:
                errors.append(f"Invalid timestamp format: '{self.timestamp}'.")
        if not self.author.strip():
            errors.append(VALIDATION_MESSAGES["timeline_author_required"])
        return errors

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "TimelineEntry":
        return cls(
            timestamp=data.get("timestamp", ""),
            author=data.get("author", ""),
            channel=data.get("channel", Channel.INTERNAL_NOTE),
            note=data.get("note", ""),
            status_change=data.get("status_change", ""),
        )


@dataclass
class CaseCustomer:
    customer_id: str = ""
    practice_name: str = ""
    is_vip: bool = False
    contact_person: str = ""
    phone: str = ""
    email: str = ""

    def validate(self) -> list[str]:
        errors = []
        if self.customer_id == "INTERNAL":
            return []
        if not self.customer_id.strip():
            errors.append(VALIDATION_MESSAGES["case_customer_id_required"])
        if not self.practice_name.strip():
            errors.append(VALIDATION_MESSAGES["case_practice_name_required"])
        return errors

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "CaseCustomer":
        return cls(
            customer_id=data.get("customer_id", ""),
            practice_name=data.get("practice_name", ""),
            is_vip=bool(data.get("is_vip", False)),
            contact_person=data.get("contact_person", ""),
            phone=data.get("phone", ""),
            email=data.get("email", ""),
        )


@dataclass
class Classification:
    schema_id: str = ""
    title: str = ""
    urgency_level: str = UrgencyLevel.GREEN
    calculated_score: float = 0.0
    deadline_callback: str = ""
    tags: list[str] = field(default_factory=list)

    def validate(self) -> list[str]:
        errors = []
        if not self.schema_id.strip():
            errors.append(VALIDATION_MESSAGES["schema_id_required"])
        if not self.title.strip():
            errors.append(VALIDATION_MESSAGES["title_required"])
        valid_urgencies = [u.value for u in UrgencyLevel]
        if self.urgency_level not in valid_urgencies:
            errors.append(f"Invalid urgency_level '{self.urgency_level}'. Must be one of {valid_urgencies}.")
        if self.deadline_callback:
            try:
                parse_iso(self.deadline_callback)
            except Exception:
                errors.append(f"Invalid deadline_callback format: '{self.deadline_callback}'.")
        return errors

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "Classification":
        return cls(
            schema_id=data.get("schema_id", ""),
            title=data.get("title", ""),
            urgency_level=data.get("urgency_level", UrgencyLevel.GREEN),
            calculated_score=float(data.get("calculated_score", 0.0)),
            deadline_callback=data.get("deadline_callback", ""),
            tags=list(data.get("tags", [])),
        )


@dataclass
class WorkflowStatus:
    is_completed: bool = False
    is_archived: bool = False
    board_column: str = BoardColumn.NEW
    current_actor: str = Actor.SUPPORT
    actor_since: str = ""
    idle_warning_days: int = 1
    is_data_complete: bool = False
    followup_at: str = ""
    followup_note: str = ""

    def validate(self) -> list[str]:
        errors = []
        valid_columns = [c.value for c in BoardColumn]
        if self.board_column not in valid_columns:
            errors.append(f"Invalid board_column '{self.board_column}'. Must be one of {valid_columns}.")
        valid_actors = [a.value for a in Actor]
        if self.current_actor not in valid_actors:
            errors.append(f"Invalid current_actor '{self.current_actor}'. Must be one of {valid_actors}.")
        if self.actor_since:
            try:
                parse_iso(self.actor_since)
            except Exception:
                errors.append(f"Invalid actor_since format: '{self.actor_since}'.")
        return errors

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "WorkflowStatus":
        return cls(
            is_completed=bool(data.get("is_completed", False)),
            is_archived=bool(data.get("is_archived", False)),
            board_column=data.get("board_column", BoardColumn.NEW),
            current_actor=data.get("current_actor", Actor.SUPPORT),
            actor_since=data.get("actor_since", ""),
            idle_warning_days=int(data.get("idle_warning_days", 1)),
            is_data_complete=bool(data.get("is_data_complete", False)),
            followup_at=data.get("followup_at", ""),
            followup_note=data.get("followup_note", ""),
        )


@dataclass
class Case:
    case_id: str = ""
    created_at: str = ""
    updated_at: str = ""
    created_by: str = ""
    assigned_to: str = ""
    customer: CaseCustomer = field(default_factory=CaseCustomer)
    classification: Classification = field(default_factory=Classification)
    workflow_status: WorkflowStatus = field(default_factory=WorkflowStatus)
    form_data: dict[str, Any] = field(default_factory=dict)
    missing_required_fields: list[str] = field(default_factory=list)
    attachment_directory: str = ""
    timeline: list[TimelineEntry] = field(default_factory=list)
    is_demo_data: bool = False

    @property
    def is_internal(self) -> bool:
        return self.customer.customer_id == "INTERNAL"

    @property
    def title(self) -> str:
        return self.classification.title if self.classification else ""

    @property
    def followup_due_at(self) -> str:
        return self.classification.deadline_callback if self.classification else ""

    @property
    def formatted_deadline(self) -> str:
        return format_german_datetime(self.followup_due_at, with_uhr=True) if self.followup_due_at else ""

    @property
    def formatted_followup(self) -> str:
        return format_german_datetime(self.workflow_status.followup_at, with_uhr=True) if self.workflow_status.followup_at else ""

    @property
    def formatted_created_at(self) -> str:
        return format_german_datetime(self.created_at, with_uhr=True) if self.created_at else ""

    @property
    def formatted_updated_at(self) -> str:
        return format_german_datetime(self.updated_at, with_uhr=True) if self.updated_at else ""

    @property
    def initial_note(self) -> str:
        if self.timeline:
            return self.timeline[0].note
        return ""

    def validate(self) -> list[str]:
        errors = []
        if not self.case_id:
            errors.append("Case ID cannot be empty.")
        if self.created_at:
            try:
                parse_iso(self.created_at)
            except Exception:
                errors.append(f"Invalid created_at format: '{self.created_at}'.")
        if self.updated_at:
            try:
                parse_iso(self.updated_at)
            except Exception:
                errors.append(f"Invalid updated_at format: '{self.updated_at}'.")

        errors.extend(self.customer.validate())
        errors.extend(self.classification.validate())
        errors.extend(self.workflow_status.validate())
        for entry in self.timeline:
            errors.extend(entry.validate())
        return errors

    def to_dict(self) -> dict[str, Any]:
        return {
            "case_id": self.case_id,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "created_by": self.created_by,
            "assigned_to": self.assigned_to,
            "customer": self.customer.to_dict(),
            "classification": self.classification.to_dict(),
            "workflow_status": self.workflow_status.to_dict(),
            "form_data": self.form_data,
            "missing_required_fields": self.missing_required_fields,
            "attachment_directory": self.attachment_directory,
            "timeline": [t.to_dict() for t in self.timeline],
            "is_demo_data": self.is_demo_data,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "Case":
        timeline_raw = data.get("timeline", [])
        timeline = [TimelineEntry.from_dict(t) for t in timeline_raw] if isinstance(timeline_raw, list) else []
        return cls(
            case_id=data.get("case_id", ""),
            created_at=data.get("created_at", ""),
            updated_at=data.get("updated_at", ""),
            created_by=data.get("created_by", ""),
            assigned_to=data.get("assigned_to", ""),
            customer=CaseCustomer.from_dict(data.get("customer", {})),
            classification=Classification.from_dict(data.get("classification", {})),
            workflow_status=WorkflowStatus.from_dict(data.get("workflow_status", {})),
            form_data=dict(data.get("form_data", {})),
            missing_required_fields=list(data.get("missing_required_fields", [])),
            attachment_directory=data.get("attachment_directory", ""),
            timeline=timeline,
            is_demo_data=bool(data.get("is_demo_data", False)),
        )
