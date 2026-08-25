"""Tests for schema and template field width layouts and compact structuring."""

from pathlib import Path
import customtkinter as ctk
import pytest
from enums import FieldType
from models.schema import QuestionSchema, SchemaField
from services.export_service import ExportService
from services.storage_service import StorageService
from config import AppConfig
from ui.dialogs.template_manager_dialog import EditTemplateDialog


def test_edit_template_dialog_layout(tmp_path: Path):
    """Verify EditTemplateDialog organizes template configuration with structured layout."""
    config = AppConfig(workspace_dir=tmp_path)
    storage = StorageService(config)
    export_svc = ExportService(storage)

    schemas = [
        QuestionSchema(
            schema_id="schema_test",
            display_name="Test Schema",
            fields=[
                SchemaField(field_id="short_f", label="Kurzes Feld", field_type=FieldType.TEXT),
            ],
        )
    ]

    app = ctk.CTk()
    app.withdraw()

    saved_templates = []
    dialog = EditTemplateDialog(
        app,
        template=None,
        schemas=schemas,
        export_service=export_svc,
        on_save=lambda t: saved_templates.append(t),
    )

    dialog.update_idletasks()

    assert dialog.id_entry.winfo_exists()
    assert dialog.name_entry.winfo_exists()
    assert dialog.desc_entry.winfo_exists()
    assert len(dialog.schema_vars) == 1

    dialog.destroy()
    app.destroy()
