from dataclasses import dataclass, field, asdict
from typing import Any
from constants import VALIDATION_MESSAGES


@dataclass
class Contact:
    name: str = ""
    role: str = ""
    phone: str = ""
    email: str = ""
    note: str = ""

    def validate(self) -> list[str]:
        errors = []
        if not self.name.strip():
            errors.append(VALIDATION_MESSAGES["contact_name_required"])
        return errors

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "Contact":
        return cls(
            name=data.get("name", ""),
            role=data.get("role", ""),
            phone=data.get("phone", ""),
            email=data.get("email", ""),
            note=data.get("note", ""),
        )


@dataclass
class Customer:
    customer_id: str = ""
    practice_name: str = ""
    is_vip: bool = False
    system_version: str = ""
    website: str = ""
    vm_number: int | None = None
    instance_number: int | None = None
    general_notes: str = ""
    custom_ai_rules: list[str] = field(default_factory=list)
    contacts: list[Contact] = field(default_factory=list)

    @property
    def contact_person(self) -> str:
        return self.contacts[0].name if self.contacts else ""

    @property
    def email(self) -> str:
        return self.contacts[0].email if self.contacts else ""

    @property
    def phone(self) -> str:
        return self.contacts[0].phone if self.contacts else ""

    def validate(self) -> list[str]:
        errors = []
        if not self.customer_id.strip():
            errors.append(VALIDATION_MESSAGES["customer_id_required"])
        if not self.practice_name.strip():
            errors.append(VALIDATION_MESSAGES["practice_name_required"])
        for contact in self.contacts:
            errors.extend(contact.validate())
        return errors

    def to_dict(self) -> dict[str, Any]:
        res: dict[str, Any] = {
            "customer_id": self.customer_id,
            "practice_name": self.practice_name,
            "is_vip": self.is_vip,
            "system_version": self.system_version,
            "website": self.website,
            "vm_number": self.vm_number,
            "instance_number": self.instance_number,
            "general_notes": self.general_notes,
            "contacts": [c.to_dict() for c in self.contacts],
        }
        if self.custom_ai_rules:
            res["custom_ai_rules"] = self.custom_ai_rules
        return res

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "Customer":
        contacts_raw = data.get("contacts", [])
        contacts = [Contact.from_dict(c) for c in contacts_raw] if isinstance(contacts_raw, list) else []
        
        raw_vm = data.get("vm_number")
        vm_num = int(raw_vm) if raw_vm is not None and str(raw_vm).isdigit() else None
        
        raw_inst = data.get("instance_number")
        inst_num = int(raw_inst) if raw_inst is not None and str(raw_inst).isdigit() else None

        rules_raw = data.get("custom_ai_rules", [])
        rules = list(rules_raw) if isinstance(rules_raw, list) else []

        return cls(
            customer_id=data.get("customer_id", ""),
            practice_name=data.get("practice_name", ""),
            is_vip=bool(data.get("is_vip", False)),
            system_version=data.get("system_version", ""),
            website=data.get("website", ""),
            vm_number=vm_num,
            instance_number=inst_num,
            general_notes=data.get("general_notes", ""),
            custom_ai_rules=rules,
            contacts=contacts,
        )
