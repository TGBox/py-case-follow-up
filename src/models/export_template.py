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
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> ExportTemplate:
        fields = cls.__dataclass_fields__
        return cls(**{k: v for k, v in data.items() if k in fields})
