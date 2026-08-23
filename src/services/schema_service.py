from typing import Any
from src.models.schema import QuestionSchema, SchemaField
from src.models.case import Case
from src.enums import FieldType
from src.services.storage_service import StorageService


class SchemaService:
    def __init__(self, storage_service: StorageService | None = None):
        self.storage_service = storage_service

    @staticmethod
    def validate_form_data(schema: QuestionSchema, form_data: dict[str, Any]) -> tuple[bool, list[str]]:
        """Validates form_data against a schema.
        Returns (is_data_complete, missing_required_fields).
        """
        missing_fields: list[str] = []

        for f in schema.fields:
            if not f.required:
                continue

            val = form_data.get(f.field_id)

            if f.field_type == FieldType.BOOLEAN:
                # For boolean, None or missing is incomplete. False is valid!
                if val is None or not isinstance(val, bool):
                    missing_fields.append(f.field_id)
            elif f.field_type == FieldType.NUMBER:
                if val is None or str(val).strip() == "":
                    missing_fields.append(f.field_id)
                else:
                    try:
                        float(val)
                    except ValueError:
                        missing_fields.append(f.field_id)
            else:
                # Text / Dropdown
                if val is None or str(val).strip() == "":
                    missing_fields.append(f.field_id)

        is_complete = len(missing_fields) == 0
        return is_complete, missing_fields

    @classmethod
    def update_case_completion(cls, case: Case, schema: QuestionSchema) -> None:
        """Updates is_data_complete and missing_required_fields on the case."""
        is_complete, missing = cls.validate_form_data(schema, case.form_data)
        case.workflow_status.is_data_complete = is_complete
        case.missing_required_fields = missing

    # --- Baukasten Logik ---
    @staticmethod
    def add_field(schema: QuestionSchema, new_field: SchemaField) -> None:
        new_field.order = len(schema.fields) + 1
        schema.fields.append(new_field)

    @staticmethod
    def remove_field(schema: QuestionSchema, field_id: str) -> bool:
        initial_len = len(schema.fields)
        schema.fields = [f for f in schema.fields if f.field_id != field_id]
        if len(schema.fields) < initial_len:
            SchemaService.reorder_fields(schema)
            return True
        return False

    @staticmethod
    def move_field(schema: QuestionSchema, field_id: str, direction: str) -> bool:
        idx = next((i for i, f in enumerate(schema.fields) if f.field_id == field_id), -1)
        if idx == -1:
            return False

        if direction == "up" and idx > 0:
            schema.fields[idx], schema.fields[idx - 1] = schema.fields[idx - 1], schema.fields[idx]
            SchemaService.reorder_fields(schema)
            return True
        elif direction == "down" and idx < len(schema.fields) - 1:
            schema.fields[idx], schema.fields[idx + 1] = schema.fields[idx + 1], schema.fields[idx]
            SchemaService.reorder_fields(schema)
            return True
        return False

    @staticmethod
    def toggle_required(schema: QuestionSchema, field_id: str) -> bool:
        for f in schema.fields:
            if f.field_id == field_id:
                f.required = not f.required
                return True
        return False

    @staticmethod
    def reorder_fields(schema: QuestionSchema) -> None:
        for i, f in enumerate(schema.fields, start=1):
            f.order = i

    def save_schema_changes(self, schemas: list[QuestionSchema]) -> None:
        if self.storage_service:
            self.storage_service.save_schemas(schemas)
