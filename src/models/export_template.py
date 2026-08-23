from dataclasses import dataclass, field, asdict
from typing import Any
from enums import TargetType


@dataclass
class ExportTemplate:
    template_id: str = ""
    display_name: str = ""
    target_type: str = TargetType.CLIPBOARD_TEXT
    applicable_cases: list[str] = field(default_factory=list)
    description: str = ""
    required_schema_fields: list[str] = field(default_factory=list)
    template_string: str = ""

    def validate(self) -> list[str]:
        errors = []
        if not self.template_id.strip():
            errors.append("Template ID is required.")
        if not self.display_name.strip():
            errors.append("Display name is required.")
        if not self.template_string.strip():
            errors.append("Template string cannot be empty.")
        return errors

    def to_dict(self) -> dict[str, Any]:
        return {
            "template_id": self.template_id,
            "display_name": self.display_name,
            "target_type": self.target_type,
            "applicable_cases": self.applicable_cases,
            "description": self.description,
            "required_schema_fields": self.required_schema_fields,
            "template_string": self.template_string,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "ExportTemplate":
        return cls(
            template_id=data.get("template_id", ""),
            display_name=data.get("display_name", ""),
            target_type=data.get("target_type", TargetType.CLIPBOARD_TEXT),
            applicable_cases=list(data.get("applicable_cases", [])),
            description=data.get("description", ""),
            required_schema_fields=list(data.get("required_schema_fields", [])),
            template_string=data.get("template_string", ""),
        )
