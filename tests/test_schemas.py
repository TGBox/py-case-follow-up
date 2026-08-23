import pytest
from enums import FieldType
from models.schema import QuestionSchema, SchemaField
from services.schema_service import SchemaService
from services.seed_service import SeedService
from services.storage_service import StorageService, AppConfig


def test_schema_field_serialization():
    field = SchemaField(
        field_id="patient_age",
        label="Patientenalter",
        field_type=FieldType.NUMBER,
        required=True,
        options=["0-18", "19-65", "65+"],
        placeholder="Alter eingeben",
        order=2,
    )

    f_dict = field.to_dict()
    assert f_dict["field_id"] == "patient_age"
    assert f_dict["field_type"] == FieldType.NUMBER
    assert f_dict["required"] is True
    assert len(f_dict["options"]) == 3

    restored = SchemaField.from_dict(f_dict)
    assert restored.field_id == "patient_age"
    assert restored.field_type == FieldType.NUMBER
    assert restored.required is True
    assert restored.order == 2


def test_question_schema_serialization():
    f1 = SchemaField(field_id="f1", label="Feld 1", field_type=FieldType.TEXT, required=True, order=1)
    f2 = SchemaField(field_id="f2", label="Feld 2", field_type=FieldType.BOOLEAN, required=False, order=2)
    schema = QuestionSchema(
        schema_id="schema_custom_01",
        display_name="Benutzerdefiniertes Formular",
        description="Ein Test-Schema",
        fields=[f1, f2],
    )

    s_dict = schema.to_dict()
    assert s_dict["schema_id"] == "schema_custom_01"
    assert len(s_dict["fields"]) == 2

    restored = QuestionSchema.from_dict(s_dict)
    assert restored.schema_id == "schema_custom_01"
    assert restored.display_name == "Benutzerdefiniertes Formular"
    assert len(restored.fields) == 2
    assert restored.fields[0].field_id == "f1"


def test_schema_service_add_remove_move_fields():
    s = QuestionSchema(schema_id="s1", display_name="Test", fields=[])

    f1 = SchemaField(field_id="f1", label="First", order=1)
    f2 = SchemaField(field_id="f2", label="Second", order=2)
    f3 = SchemaField(field_id="f3", label="Third", order=3)

    SchemaService.add_field(s, f1)
    SchemaService.add_field(s, f2)
    SchemaService.add_field(s, f3)

    assert len(s.fields) == 3
    assert [f.field_id for f in s.fields] == ["f1", "f2", "f3"]

    # Move f2 up
    SchemaService.move_field(s, "f2", "up")
    assert [f.field_id for f in s.fields] == ["f2", "f1", "f3"]

    # Move f2 down
    SchemaService.move_field(s, "f2", "down")
    assert [f.field_id for f in s.fields] == ["f1", "f2", "f3"]

    # Toggle required
    assert s.fields[0].required is False
    SchemaService.toggle_required(s, "f1")
    assert s.fields[0].required is True

    # Remove field
    SchemaService.remove_field(s, "f2")
    assert len(s.fields) == 2
    assert [f.field_id for f in s.fields] == ["f1", "f3"]


def test_schema_service_validate_missing_fields():
    f1 = SchemaField(field_id="f1", label="Name", required=True)
    f2 = SchemaField(field_id="f2", label="Alter", required=True)
    f3 = SchemaField(field_id="f3", label="Notiz", required=False)
    s = QuestionSchema(schema_id="s1", display_name="Test", fields=[f1, f2, f3])

    # Case 1: Incomplete data
    data_incomplete = {"f1": "Max Mustermann", "f3": "Einige Details"}
    is_complete, missing = SchemaService.validate_form_data(s, data_incomplete)
    assert is_complete is False
    assert missing == ["f2"]

    # Case 2: Complete data
    data_complete = {"f1": "Max Mustermann", "f2": "42"}
    is_complete2, missing_none = SchemaService.validate_form_data(s, data_complete)
    assert is_complete2 is True
    assert len(missing_none) == 0


def test_seed_service_creates_default_schemas(tmp_path: Path):
    config = AppConfig(workspace_dir=tmp_path)
    storage = StorageService(config)
    seed = SeedService(storage)

    seed_schemas = seed.create_seed_schemas()
    assert len(seed_schemas) >= 3

    schema_ids = [s.schema_id for s in seed_schemas]
    assert "schema_zuzahlungsnachforderung" in schema_ids
    assert "schema_feature_request" in schema_ids
    assert "schema_bug_report" in schema_ids
