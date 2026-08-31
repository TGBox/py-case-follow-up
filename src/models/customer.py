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
    vnum1: str = ""
    practice_name: str = ""
    practice_name_old: str = ""
    salutation: str = ""
    first_name: str = ""
    last_name: str = ""
    street: str = ""
    zip_code: str = ""
    city: str = ""
    phone_main: str = ""
    phone_direct: str = ""
    phone_private: str = ""
    phone2: str = ""
    phone3: str = ""
    mobile: str = ""
    mobile_private: str = ""
    email_address: str = ""
    email2: str = ""
    email3: str = ""
    website: str = ""
    system_version: str = ""
    dsc: str = ""
    dsc_neu: str = ""
    vm_number: int | None = None
    instance_number: int | None = None
    is_vip: bool = False
    general_notes: str = ""
    additional_contacts: list[str] = field(default_factory=list)
    custom_ai_rules: list[str] = field(default_factory=list)
    contacts: list[Contact] = field(default_factory=list)

    @property
    def contact_person(self) -> str:
        name_parts = [self.salutation, self.first_name, self.last_name]
        full_name = " ".join([p.strip() for p in name_parts if p and p.strip()])
        if full_name:
            return full_name
        if self.additional_contacts:
            return self.additional_contacts[0]
        if self.contacts:
            return self.contacts[0].name
        return ""

    @property
    def email(self) -> str:
        if self.email_address:
            return self.email_address
        if self.contacts:
            return self.contacts[0].email
        return ""

    @property
    def all_emails(self) -> list[str]:
        emails = []
        if self.email_address:
            emails.append(self.email_address)
        if self.email2:
            emails.append(self.email2)
        if self.email3:
            emails.append(self.email3)
        if not emails and self.contacts:
            for c in self.contacts:
                if c.email and c.email not in emails:
                    emails.append(c.email)
        return emails

    @property
    def phone(self) -> str:
        if self.phone_main:
            return self.phone_main
        if self.phone_direct:
            return self.phone_direct
        if self.mobile:
            return self.mobile
        if self.contacts:
            return self.contacts[0].phone
        return ""

    @property
    def full_address(self) -> str:
        city_part = f"{self.zip_code} {self.city}".strip()
        parts = [self.street.strip(), city_part]
        return ", ".join([p for p in parts if p])

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
            "vnum1": self.vnum1,
            "practice_name": self.practice_name,
            "practice_name_old": self.practice_name_old,
            "salutation": self.salutation,
            "first_name": self.first_name,
            "last_name": self.last_name,
            "street": self.street,
            "zip_code": self.zip_code,
            "city": self.city,
            "phone_main": self.phone_main,
            "phone_direct": self.phone_direct,
            "phone_private": self.phone_private,
            "phone2": self.phone2,
            "phone3": self.phone3,
            "mobile": self.mobile,
            "mobile_private": self.mobile_private,
            "email_address": self.email_address,
            "email2": self.email2,
            "email3": self.email3,
            "website": self.website,
            "system_version": self.system_version,
            "dsc": self.dsc,
            "dsc_neu": self.dsc_neu,
            "is_vip": self.is_vip,
            "vm_number": self.vm_number,
            "instance_number": self.instance_number,
            "general_notes": self.general_notes,
            "additional_contacts": list(self.additional_contacts),
            "contacts": [c.to_dict() for c in self.contacts],
        }
        if self.custom_ai_rules:
            res["custom_ai_rules"] = list(self.custom_ai_rules)
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

        add_contacts_raw = data.get("additional_contacts", [])
        add_contacts = [str(ac) for ac in add_contacts_raw] if isinstance(add_contacts_raw, list) else []

        # Legacy fallback for email/phone if only contacts exist
        email_addr = data.get("email_address", "")
        if not email_addr and contacts:
            email_addr = contacts[0].email

        phone_m = data.get("phone_main", "") or data.get("phone", "")
        if not phone_m and contacts:
            phone_m = contacts[0].phone

        contact_p = data.get("contact_person", "")
        salut = data.get("salutation", "")
        fname = data.get("first_name", "")
        lname = data.get("last_name", "")
        if not salut and not fname and not lname and contact_p:
            parts = contact_p.strip().split()
            if len(parts) == 1:
                lname = parts[0]
            elif len(parts) == 2:
                fname, lname = parts[0], parts[1]
            elif len(parts) >= 3:
                salut, fname, lname = parts[0], parts[1], " ".join(parts[2:])

        return cls(
            customer_id=data.get("customer_id", ""),
            vnum1=data.get("vnum1", ""),
            practice_name=data.get("practice_name", ""),
            practice_name_old=data.get("practice_name_old", ""),
            salutation=salut,
            first_name=fname,
            last_name=lname,
            street=data.get("street", ""),
            zip_code=data.get("zip_code", ""),
            city=data.get("city", ""),
            phone_main=phone_m,
            phone_direct=data.get("phone_direct", ""),
            phone_private=data.get("phone_private", ""),
            phone2=data.get("phone2", ""),
            phone3=data.get("phone3", ""),
            mobile=data.get("mobile", ""),
            mobile_private=data.get("mobile_private", ""),
            email_address=email_addr,
            email2=data.get("email2", ""),
            email3=data.get("email3", ""),
            website=data.get("website", ""),
            system_version=data.get("system_version", ""),
            dsc=data.get("dsc", ""),
            dsc_neu=data.get("dsc_neu", ""),
            vm_number=vm_num,
            instance_number=inst_num,
            is_vip=bool(data.get("is_vip", False)),
            general_notes=data.get("general_notes", ""),
            additional_contacts=add_contacts,
            custom_ai_rules=rules,
            contacts=contacts,
        )
