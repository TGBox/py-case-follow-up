import pytest # type: ignore
import customtkinter as ctk
from models.schema import QuestionSchema, SchemaField
from enums import FieldType
from ui.widgets.dynamic_form_widget import DynamicFormWidget


def test_schema_field_v2_serialization():
    f1 = SchemaField(
        field_id="error_category",
        label="Fehlerkategorie",
        field_type=FieldType.DROPDOWN,
        options=["Hardware", "Software", "Sonstiges"],
    )
    f2 = SchemaField(
        field_id="other_details",
        label="Sonstige Details",
        field_type=FieldType.TEXT,
        depends_on_field_id="error_category",
        depends_on_value="Sonstiges",
    )
    f3 = SchemaField(
        field_id="log_file",
        label="Log-Datei Anhang",
        field_type=FieldType.FILE,
        allowed_extensions=[".log", ".txt"],
    )

    schema = QuestionSchema(
        schema_id="v2_test_schema",
        display_name="V2 Test Schema",
        fields=[f1, f2, f3],
    )

    d = schema.to_dict()
    assert d["schema_id"] == "v2_test_schema"
    assert d["fields"][1]["depends_on_field_id"] == "error_category"
    assert d["fields"][1]["depends_on_value"] == "Sonstiges"
    assert d["fields"][2]["field_type"] == "file"
    assert d["fields"][2]["allowed_extensions"] == [".log", ".txt"]

    deserialized = QuestionSchema.from_dict(d)
    assert len(deserialized.fields) == 3
    assert deserialized.fields[1].depends_on_field_id == "error_category"
    assert deserialized.fields[2].field_type == FieldType.FILE
    assert deserialized.fields[2].allowed_extensions == [".log", ".txt"]


def test_dynamic_form_widget_v2_rendering_and_conditional_visibility():
    root = ctk.CTk()
    root.withdraw()

    f_parent = SchemaField(
        field_id="is_reproducible",
        label="Reproduzierbar?",
        field_type=FieldType.BOOLEAN,
    )
    f_child = SchemaField(
        field_id="reproduction_steps",
        label="Schritte zur Reproduktion",
        field_type=FieldType.TEXT,
        depends_on_field_id="is_reproducible",
        depends_on_value="true",
    )
    f_file = SchemaField(
        field_id="screenshot",
        label="Screenshot hochladen",
        field_type=FieldType.FILE,
        allowed_extensions=[".png", ".jpg"],
    )

    schema = QuestionSchema(
        schema_id="conditional_test",
        display_name="Conditional Test",
        fields=[f_parent, f_child, f_file],
    )

    widget = DynamicFormWidget(root)
    # Load schema with parent set to False initially
    widget.load_schema(schema, form_data={"is_reproducible": False, "screenshot": "test.png"})

    assert f_child.field_id in widget.field_row_frames
    assert f_file.field_id in widget.field_row_frames

    # Verify conditional visibility logic
    child_frame = widget.field_row_frames[f_child.field_id]
    # Initially hidden because parent is False
    assert not child_frame.winfo_viewable() or not child_frame.winfo_ismapped()

    # Now set parent value to True
    widget.field_widgets["is_reproducible"][1].set(True)
    widget.update_conditional_visibility()

    form_data = widget.get_form_data()
    assert form_data["is_reproducible"] is True
    assert form_data["screenshot"] == "test.png"

    widget.destroy()
    root.destroy()
