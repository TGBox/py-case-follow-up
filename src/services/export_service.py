import logging
from typing import Any
from jinja2 import Template, Environment
from src.models.case import Case
from src.models.export_template import ExportTemplate
from src.models.schema import QuestionSchema
from src.services.schema_service import SchemaService
from src.services.storage_service import StorageService

logger = logging.getLogger("SupportCockpit")


class ExportService:
    def __init__(self, storage_service: StorageService | None = None):
        self.storage_service = storage_service
        self.jinja_env = Environment(autoescape=False)

    def get_suggested_templates(
        self, case: Case, all_templates: list[ExportTemplate], schema: QuestionSchema | None = None
    ) -> list[ExportTemplate]:
        """Returns list of applicable ExportTemplates for the case/schema."""
        applicable = []
        schema_id = case.classification.schema_id

        # Check suggested templates in schema
        suggested_ids = schema.default_suggested_exports if schema else []

        for t in all_templates:
            if not t.applicable_cases or schema_id in t.applicable_cases or t.template_id in suggested_ids:
                applicable.append(t)
        return applicable

    def render_template(
        self,
        case: Case,
        template: ExportTemplate,
        schema: QuestionSchema | None = None,
        override_form_data: dict[str, Any] | None = None,
        force_export: bool = False,
    ) -> tuple[bool, list[str], str]:
        """Renders Jinja2 export template for a case.
        Returns tuple: (success, missing_required_fields, rendered_text).
        """
        # Apply in-place form_data overrides if provided
        if override_form_data:
            case.form_data.update(override_form_data)

        # Check missing fields
        missing_fields: list[str] = []
        required_fields = template.required_schema_fields

        if schema:
            field_label_map = {f.field_id: f.label for f in schema.fields}
        else:
            field_label_map = {}

        for fid in required_fields:
            val = case.form_data.get(fid)
            if val is None or str(val).strip() == "":
                missing_fields.append(fid)

        if missing_fields and not force_export:
            return False, missing_fields, ""

        # Prepare Jinja2 render context
        render_form_data = dict(case.form_data)
        if force_export and missing_fields:
            for fid in missing_fields:
                label = field_label_map.get(fid, fid)
                render_form_data[fid] = f"[FEHLT: {label}]"

        context = {
            "case": case,
            "customer": case.customer,
            "classification": case.classification,
            "workflow_status": case.workflow_status,
            "form_data": render_form_data,
            "timeline": case.timeline,
            "created_by": case.created_by,
            "assigned_to": case.assigned_to,
            "attachment_directory": case.attachment_directory,
        }

        try:
            tpl = self.jinja_env.from_string(template.template_string)
            rendered = tpl.render(**context)
            return True, missing_fields, rendered
        except Exception as e:
            logger.error(f"Error rendering Jinja2 template '{template.template_id}': {e}")
            return False, missing_fields, f"Rendering Error: {e}"

    @staticmethod
    def copy_to_clipboard(text: str) -> bool:
        """Copies text to OS clipboard using tkinter or fallback."""
        try:
            import tkinter as tk
            root = tk.Tk()
            root.withdraw()
            root.clipboard_clear()
            root.clipboard_append(text)
            root.update()
            root.destroy()
            return True
        except Exception as e:
            logger.warning(f"Could not copy to clipboard via tkinter: {e}")
            return False
