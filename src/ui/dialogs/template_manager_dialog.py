from typing import Callable, Any
import customtkinter as ctk
from models.export_template import ExportTemplate
from models.schema import QuestionSchema
from models.case import Case
from enums import TargetType
from services.export_service import ExportService
from services.storage_service import StorageService


class EditTemplateDialog(ctk.CTkToplevel):
    def __init__(
        self,
        parent,
        template: ExportTemplate | None,
        schemas: list[QuestionSchema],
        export_service: ExportService,
        on_save: Callable[[ExportTemplate], None],
    ):
        super().__init__(parent)
        self.template = template
        self.schemas = schemas
        self.export_service = export_service
        self.on_save = on_save

        is_new = template is None
        self.title("✏ Vorlage bearbeiten" if not is_new else "➕ Neue Export-Vorlage")
        self.geometry("880x740")
        self.minsize(800, 640)
        from utils.ui_utils import center_window
        center_window(self, 880, 740)

        self.transient(parent)
        self.grab_set()

        self.schema_vars: dict[str, ctk.BooleanVar] = {}
        self.field_vars: dict[str, ctk.BooleanVar] = {}

        self.create_widgets(is_new)

    def create_widgets(self, is_new: bool):
        top_bar = ctk.CTkFrame(self, height=45, corner_radius=0)
        top_bar.pack(fill="x", side="top", padx=10, pady=(10, 5))

        title_txt = "➕ Neue Export-Vorlage erstellen" if is_new else f"✏ Vorlage bearbeiten: {self.template.display_name if self.template else ''}"
        ctk.CTkLabel(top_bar, text=title_txt, font=ctk.CTkFont(size=15, weight="bold")).pack(side="left", padx=10)

        scroll_frame = ctk.CTkScrollableFrame(self)
        scroll_frame.pack(fill="both", expand=True, padx=15, pady=5)

        # Template ID & Display Name
        row1 = ctk.CTkFrame(scroll_frame, fg_color="transparent")
        row1.pack(fill="x", pady=4)

        ctk.CTkLabel(row1, text="Vorlage-ID *:", width=130, anchor="w").pack(side="left")
        self.id_entry = ctk.CTkEntry(row1, placeholder_text="z. B. gitlab_dev_ticket")
        if self.template:
            self.id_entry.insert(0, self.template.template_id)
            if not is_new:
                self.id_entry.configure(state="disabled")
        self.id_entry.pack(side="left", fill="x", expand=True)

        row2 = ctk.CTkFrame(scroll_frame, fg_color="transparent")
        row2.pack(fill="x", pady=4)

        ctk.CTkLabel(row2, text="Anzeigename *:", width=130, anchor="w").pack(side="left")
        self.name_entry = ctk.CTkEntry(row2, placeholder_text="z. B. GitLab / Dev-Ticket")
        if self.template:
            self.name_entry.insert(0, self.template.display_name)
        self.name_entry.pack(side="left", fill="x", expand=True)

        # Description & Target Type
        row3 = ctk.CTkFrame(scroll_frame, fg_color="transparent")
        row3.pack(fill="x", pady=4)

        ctk.CTkLabel(row3, text="Beschreibung:", width=130, anchor="w").pack(side="left")
        self.desc_entry = ctk.CTkEntry(row3, placeholder_text="Kurze Beschreibung des Formats...")
        if self.template:
            self.desc_entry.insert(0, self.template.description)
        self.desc_entry.pack(side="left", fill="x", expand=True)

        row4 = ctk.CTkFrame(scroll_frame, fg_color="transparent")
        row4.pack(fill="x", pady=4)

        ctk.CTkLabel(row4, text="Ziel-Aktion / Typ:", width=130, anchor="w").pack(side="left")
        self.type_combo = ctk.CTkOptionMenu(row4, values=[TargetType.CLIPBOARD_TEXT.value, TargetType.FILE_EXPORT.value])
        if self.template:
            self.type_combo.set(self.template.target_type)
        self.type_combo.pack(side="left")

        # Applicable Schemas Checkboxes
        ctk.CTkLabel(scroll_frame, text="Zugeordnete Formular-Schemas:", font=ctk.CTkFont(weight="bold", size=12)).pack(anchor="w", pady=(10, 2))
        schemas_frame = ctk.CTkFrame(scroll_frame, fg_color=("gray90", "gray20"))
        schemas_frame.pack(fill="x", pady=(0, 10), padx=2)

        for s in self.schemas:
            var = ctk.BooleanVar(value=bool(self.template and s.schema_id in self.template.applicable_cases))
            self.schema_vars[s.schema_id] = var
            cb = ctk.CTkCheckBox(schemas_frame, text=f"{s.display_name} ({s.schema_id})", variable=var)
            cb.pack(anchor="w", padx=8, pady=4)

        # Required Fields Checkboxes
        ctk.CTkLabel(scroll_frame, text="Erforderliche Pflichtfelder vor Export:", font=ctk.CTkFont(weight="bold", size=12)).pack(anchor="w", pady=(5, 2))
        fields_frame = ctk.CTkFrame(scroll_frame, fg_color=("gray90", "gray20"))
        fields_frame.pack(fill="x", pady=(0, 10), padx=2)

        all_fields: dict[str, str] = {}
        for s in self.schemas:
            for f in s.fields:
                all_fields[f.field_id] = f.label

        if not all_fields and self.template:
            for f_id in self.template.required_schema_fields:
                all_fields[f_id] = f_id

        for f_id, f_label in all_fields.items():
            var = ctk.BooleanVar(value=bool(self.template and f_id in self.template.required_schema_fields))
            self.field_vars[f_id] = var
            cb = ctk.CTkCheckBox(fields_frame, text=f"{f_label} [{f_id}]", variable=var)
            cb.pack(anchor="w", padx=8, pady=4)

        # Jinja2 Template Markup Editor
        ctk.CTkLabel(scroll_frame, text="Jinja2 Template Text (Markdown / Text):", font=ctk.CTkFont(weight="bold", size=12)).pack(anchor="w", pady=(5, 2))
        self.template_textbox = ctk.CTkTextbox(scroll_frame, height=160, font=ctk.CTkFont(family="Consolas", size=12))
        self.template_textbox.pack(fill="x", pady=(0, 10))
        if self.template:
            self.template_textbox.insert("1.0", self.template.template_string)

        # Live Preview Panel
        preview_btn = ctk.CTkButton(scroll_frame, text="👁 Live-Vorschau rendern", command=self.render_preview, fg_color="dodgerblue")
        preview_btn.pack(anchor="w", pady=4)

        self.preview_textbox = ctk.CTkTextbox(scroll_frame, height=120, font=ctk.CTkFont(family="Consolas", size=11))
        self.preview_textbox.pack(fill="x", pady=(0, 10))
        self.preview_textbox.configure(state="disabled")

        # Bottom Action Bar
        bottom_bar = ctk.CTkFrame(self, height=50, fg_color="transparent")
        bottom_bar.pack(fill="x", side="bottom", padx=15, pady=10)

        ctk.CTkButton(bottom_bar, text="💾 Vorlage Speichern", command=self.save, fg_color="forestgreen", width=160).pack(side="right", padx=5)
        ctk.CTkButton(bottom_bar, text="Abbrechen", command=self.destroy, fg_color=("gray70", "gray40"), hover_color=("gray60", "gray50"), width=90).pack(side="left", padx=5)

    def render_preview(self):
        tmpl_str = self.template_textbox.get("1.0", "end-1c")
        sample_case = Case(
            case_id="T-2026-DEMO",
            created_by="Support-Agent",
            form_data={"billing_quarter": "2026-Q2", "error_code": "ERR_DEMO_101", "database_dump_provided": True},
            attachment_directory="attachments/T-2026-DEMO_Praxis",
        )
        sample_case.customer.practice_name = "Musterpraxis Dr. Test"
        sample_case.customer.customer_id = "K-99999"
        sample_case.customer.is_vip = True
        sample_case.classification.title = "Beispiel-Fall für Vorschau"

        test_template = ExportTemplate(
            template_id="preview",
            display_name="Preview",
            target_type=self.type_combo.get(),
            template_string=tmpl_str,
        )

        success, missing, res = self.export_service.render_template(sample_case, test_template)
        self.preview_textbox.configure(state="normal")
        self.preview_textbox.delete("1.0", "end")
        self.preview_textbox.insert("1.0", res)
        self.preview_textbox.configure(state="disabled")

    def save(self):
        t_id = self.id_entry.get().strip()
        t_name = self.name_entry.get().strip()
        if not t_id or not t_name:
            return

        applicable = [s_id for s_id, v in self.schema_vars.items() if v.get()]
        required = [f_id for f_id, v in self.field_vars.items() if v.get()]
        tmpl_str = self.template_textbox.get("1.0", "end-1c")

        new_template = ExportTemplate(
            template_id=t_id,
            display_name=t_name,
            target_type=self.type_combo.get(),
            applicable_cases=applicable,
            description=self.desc_entry.get().strip(),
            required_schema_fields=required,
            template_string=tmpl_str,
        )

        self.on_save(new_template)
        self.destroy()


class TemplateManagerDialog(ctk.CTkToplevel):
    def __init__(
        self,
        parent,
        templates: list[ExportTemplate],
        schemas: list[QuestionSchema],
        storage_service: StorageService,
        export_service: ExportService,
        on_templates_updated: Callable[[list[ExportTemplate]], None] | None = None,
    ):
        super().__init__(parent)
        self.templates = list(templates)
        self.schemas = schemas
        self.storage_service = storage_service
        self.export_service = export_service
        self.on_templates_updated = on_templates_updated

        self.title("📄 Export-Vorlagen verwalten")
        self.geometry("980x720")
        self.minsize(880, 640)
        from utils.ui_utils import center_window
        center_window(self, 980, 720)

        self.transient(parent)
        self.grab_set()

        self.create_widgets()

    def create_widgets(self):
        top_bar = ctk.CTkFrame(self, height=50, corner_radius=0)
        top_bar.pack(fill="x", side="top", padx=10, pady=(10, 5))

        ctk.CTkLabel(top_bar, text="📄 Export-Vorlagen-Verwaltung", font=ctk.CTkFont(size=16, weight="bold")).pack(side="left", padx=10)

        btn_new = ctk.CTkButton(top_bar, text="+ Neue Vorlage", command=self.on_add_template, fg_color="forestgreen", width=140)
        btn_new.pack(side="right", padx=5)

        btn_reset = ctk.CTkButton(top_bar, text="🔄 Standard-Vorlagen laden", command=self.on_reset_templates, fg_color=("gray75", "gray30"), hover_color=("gray65", "gray40"), width=180)
        btn_reset.pack(side="right", padx=5)

        self.scroll_frame = ctk.CTkScrollableFrame(self)
        self.scroll_frame.pack(fill="both", expand=True, padx=10, pady=5)

        self.render_list()

    def on_reset_templates(self):
        self.templates = self.storage_service.reset_templates_to_defaults()
        self.render_list()
        if self.on_templates_updated:
            self.on_templates_updated(self.templates)

    def render_list(self):
        for w in self.scroll_frame.winfo_children():
            w.destroy()

        from services.seed_service import SeedService
        seed_templates = SeedService(self.storage_service).create_seed_templates()
        saved_templates = self.storage_service.load_templates()

        display_templates = list(self.templates)
        for st in seed_templates:
            if not any(t.template_id == st.template_id for t in display_templates):
                display_templates.append(st)

        if not display_templates:
            ctk.CTkLabel(self.scroll_frame, text="Keine Vorlagen vorhanden.", text_color="gray").pack(pady=20)
            return

        for tmpl in display_templates:
            card = ctk.CTkFrame(self.scroll_frame, fg_color=("gray85", "gray20"), corner_radius=6)
            card.pack(fill="x", pady=5, padx=5)

            top_row = ctk.CTkFrame(card, fg_color="transparent")
            top_row.pack(fill="x", padx=10, pady=(6, 2))

            name_lbl = ctk.CTkLabel(top_row, text=f"📄 {tmpl.display_name}", font=ctk.CTkFont(weight="bold", size=13))
            name_lbl.pack(side="left")

            id_lbl = ctk.CTkLabel(top_row, text=f"[{tmpl.template_id}]", font=ctk.CTkFont(size=11), text_color=("gray40", "gray70"))
            id_lbl.pack(side="left", padx=8)

            btn_del = ctk.CTkButton(top_row, text="🗑 Löschen", width=80, fg_color="darkred", command=lambda t=tmpl: self.on_delete_template(t))
            btn_del.pack(side="right", padx=4)

            btn_edit = ctk.CTkButton(top_row, text="✏ Bearbeiten", width=100, command=lambda t=tmpl: self.on_edit_template(t))
            btn_edit.pack(side="right", padx=4)

            is_already_saved = any(
                s.template_id == tmpl.template_id and s.template_string == tmpl.template_string and s.display_name == tmpl.display_name
                for s in saved_templates
            )

            if is_already_saved:
                btn_adopt = ctk.CTkButton(top_row, text="✓ In Realdaten enthalten", width=170, state="disabled", fg_color="gray40")
            else:
                btn_adopt = ctk.CTkButton(top_row, text="📥 Zu Realdaten übernehmen", width=180, fg_color="dodgerblue", command=lambda t=tmpl: self.on_adopt_template(t))
            btn_adopt.pack(side="right", padx=4)

            desc_txt = tmpl.description or "Keine Beschreibung"
            req_txt = f"Pflichtfelder: {', '.join(tmpl.required_schema_fields)}" if tmpl.required_schema_fields else "Keine Pflichtfelder"
            sub_lbl = ctk.CTkLabel(card, text=f"{desc_txt}  •  {req_txt}", anchor="w", font=ctk.CTkFont(size=11), text_color=("gray30", "gray80"))
            sub_lbl.pack(fill="x", padx=10, pady=(0, 6))

    def on_adopt_template(self, tmpl: ExportTemplate):
        saved_templates = self.storage_service.load_templates()
        idx = next((i for i, t in enumerate(saved_templates) if t.template_id == tmpl.template_id), -1)
        if idx >= 0:
            saved_templates[idx] = tmpl
        else:
            saved_templates.append(tmpl)

        self.storage_service.save_templates(saved_templates)
        self.templates = saved_templates
        self.render_list()
        if self.on_templates_updated:
            self.on_templates_updated(self.templates)

    def on_add_template(self):
        EditTemplateDialog(self, None, self.schemas, self.export_service, self.save_template)

    def on_edit_template(self, tmpl: ExportTemplate):
        EditTemplateDialog(self, tmpl, self.schemas, self.export_service, self.save_template)

    def on_delete_template(self, tmpl: ExportTemplate):
        self.templates = [t for t in self.templates if t.template_id != tmpl.template_id]
        self.storage_service.save_templates(self.templates)
        self.render_list()
        if self.on_templates_updated:
            self.on_templates_updated(self.templates)

    def save_template(self, updated_tmpl: ExportTemplate):
        idx = next((i for i, t in enumerate(self.templates) if t.template_id == updated_tmpl.template_id), -1)
        if idx >= 0:
            self.templates[idx] = updated_tmpl
        else:
            self.templates.append(updated_tmpl)

        self.storage_service.save_templates(self.templates)
        self.render_list()
        if self.on_templates_updated:
            self.on_templates_updated(self.templates)
