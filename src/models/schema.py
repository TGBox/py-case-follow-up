from dataclasses import dataclass, field, asdict
from typing import Any
from enums import FieldType


@dataclass
class SchemaField:
    field_id: str = ""
    label: str = ""
    field_type: str = FieldType.TEXT
    options: list[str] = field(default_factory=list)
    required: bool = False
    placeholder: str = ""
    order: int = 1

    def validate(self) -> list[str]:
        errors = []
        if not self.field_id.strip():
            errors.append("Field ID is required.")
        if not self.label.strip():
            errors.append("Label is required.")
        valid_types = [t.value for t in FieldType]
        if self.field_type not in valid_types:
            errors.append(f"Invalid field_type '{self.field_type}'. Must be one of {valid_types}.")
        return errors

    def to_dict(self) -> dict[str, Any]:
        res: dict[str, Any] = {
            "field_id": self.field_id,
            "label": self.label,
            "field_type": self.field_type,
            "required": self.required,
            "order": self.order,
        }
        if self.options:
            res["options"] = self.options
        if self.placeholder:
            res["placeholder"] = self.placeholder
        return res

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "SchemaField":
        return cls(
            field_id=data.get("field_id", ""),
            label=data.get("label", ""),
            field_type=data.get("field_type", FieldType.TEXT),
            options=list(data.get("options", [])) if data.get("options") else [],
            required=bool(data.get("required", False)),
            placeholder=data.get("placeholder", ""),
            order=int(data.get("order", 1)),
        )


@dataclass
class QuestionSchema:
    schema_id: str = ""
    display_name: str = ""
    description: str = ""
    default_suggested_exports: list[str] = field(default_factory=list)
    fields: list[SchemaField] = field(default_factory=list)

    def validate(self) -> list[str]:
        errors = []
        if not self.schema_id.strip():
            errors.append("Schema ID is required.")
        if not self.display_name.strip():
            errors.append("Display name is required.")
        for f in self.fields:
            errors.extend(f.validate())
        return errors

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema_id": self.schema_id,
            "display_name": self.display_name,
            "description": self.description,
            "default_suggested_exports": self.default_suggested_exports,
            "fields": [f.to_dict() for f in self.fields],
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "QuestionSchema":
        fields_raw = data.get("fields", [])
        fields = [SchemaField.from_dict(f) for f in fields_raw] if isinstance(fields_raw, list) else []
        return cls(
            schema_id=data.get("schema_id", ""),
            display_name=data.get("display_name", ""),
            description=data.get("description", ""),
            default_suggested_exports=list(data.get("default_suggested_exports", [])),
            fields=fields,
        )
