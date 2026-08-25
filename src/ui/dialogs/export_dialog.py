import customtkinter as ctk
from pathlib import Path
from tkinter import filedialog
from typing import Callable
from models.case import Case
from models.export_template import ExportTemplate
from models.schema import QuestionSchema
from services.export_service import ExportService


class ExportDialog(ctk.CTkToplevel):
    def __init__(
        self,
        parent,
        case: Case,
        templates: list[ExportTemplate],
        schemas: list[QuestionSchema],
        export_service: ExportService,
        on_case_updated: Callable[[Case], None],
    ):
        super().__init__(parent)
        self.title(f"Übergabe- & Export-Assistent — {case.case_id}")
        self.geometry("820x760")
        self.minsize(740, 660)
        from utils.ui_utils import center_window
        center_window(self, 820, 760)

        self.case = case
        self.templates = templates
        self.schemas = schemas
        self.export_service = export_service
        self.on_case_updated = on_case_updated

        # Find matching schema
        self.schema = next((s for s in schemas if s.schema_id == case.classification.schema_id), None)
        self.suggested_templates = self.export_service.get_suggested_templates(case, templates, self.schema)
        if not self.suggested_templates:
            self.suggested_templates = templates

        self.active_template = self.suggested_templates[0] if self.suggested_templates else None
        self.in_place_entries: dict[str, ctk.CTkEntry] = {}
        self.force_export_var = ctk.BooleanVar(value=False)

        self.grab_set()
        self.create_widgets()
        self.update_render_preview()

    def create_widgets(self):
        main_frame = ctk.CTkFrame(self, fg_color="transparent")
        main_frame.pack(fill="both", expand=True, padx=20, pady=20)

        # Header
        header = ctk.CTkLabel(main_frame, text=f"Export für Fall {self.case.case_id}", font=ctk.CTkFont(size=18, weight="bold"))
        header.pack(anchor="w", pady=(0, 10))

        # Template Selection Dropdown
        tpl_frame = ctk.CTkFrame(main_frame, fg_color="transparent")
        tpl_frame.pack(fill="x", pady=(0, 10))
        ctk.CTkLabel(tpl_frame, text="Vorlage auswählen:", font=ctk.CTkFont(weight="bold")).pack(side="left", padx=(0, 10))
        
        tpl_names = [t.display_name for t in self.templates]
        self.tpl_combo = ctk.CTkOptionMenu(
            tpl_frame,
            values=tpl_names if tpl_names else ["Keine Vorlage"],
            command=self.on_template_selected,
            width=300,
        )
        if self.active_template:
            self.tpl_combo.set(self.active_template.display_name)
        self.tpl_combo.pack(side="left")

        btn_manage = ctk.CTkButton(
            tpl_frame,
            text="🛠 Vorlagen verwalten",
            command=self.on_open_template_manager,
            width=150,
            fg_color=("gray75", "gray30"),
            hover_color=("gray65", "gray40"),
        )
        btn_manage.pack(side="right", padx=(5, 0))

        # In-Place Completion Frame
        self.inplace_frame = ctk.CTkFrame(main_frame)
        self.inplace_frame.pack(fill="x", pady=(0, 10), padx=5)

        # Force Export Checkbox
        self.force_chk = ctk.CTkCheckBox(
            main_frame,
            text="Trotz unvollständiger Daten exportieren ([FEHLT: ...] Platzhalter)",
            variable=self.force_export_var,
            command=self.update_render_preview,
        )
        self.force_chk.pack(anchor="w", pady=(5, 10))

        # Rendered Output Preview Box
        ctk.CTkLabel(main_frame, text="Vorschau des exportierten Textes:", font=ctk.CTkFont(weight="bold")).pack(anchor="w", pady=(5, 2))
        self.preview_textbox = ctk.CTkTextbox(main_frame, width=640, height=260)
        self.preview_textbox.pack(fill="both", expand=True, pady=(0, 15))

        # Status Label
        self.status_label = ctk.CTkLabel(main_frame, text="", text_color="orange")
        self.status_label.pack(anchor="w", pady=(0, 5))

        # Action Buttons
        btn_frame = ctk.CTkFrame(main_frame, fg_color="transparent")
        btn_frame.pack(fill="x")

        close_btn = ctk.CTkButton(btn_frame, text="Schließen", fg_color="gray", command=self.destroy, width=120)
        close_btn.pack(side="left")

        save_file_btn = ctk.CTkButton(btn_frame, text="In Datei speichern...", command=self.on_save_file, width=160)
        save_file_btn.pack(side="right", padx=(10, 0))

        copy_btn = ctk.CTkButton(btn_frame, text="In Zwischenablage kopieren", command=self.on_copy_clipboard, width=200)
        copy_btn.pack(side="right")

    def on_template_selected(self, selected_name: str):
        self.active_template = next((t for t in self.templates if t.display_name == selected_name), None)
        self.update_render_preview()

    def update_render_preview(self):
        if not self.active_template:
            self.preview_textbox.delete("1.0", "end")
            self.status_label.configure(text="Keine Vorlage ausgewählt.")
            return

        # Re-build inplace completion fields
        for widget in self.inplace_frame.winfo_children():
            widget.destroy()
        self.in_place_entries.clear()

        required_fields = self.active_template.required_schema_fields
        missing_fields = []

        field_labels = {f.field_id: f.label for f in self.schema.fields} if self.schema else {}

        for fid in required_fields:
            val = self.case.form_data.get(fid)
            if val is None or str(val).strip() == "":
                missing_fields.append(fid)

        if missing_fields:
            ctk.CTkLabel(
                self.inplace_frame, text="⚠ Fehlende Pflichtfelder direkt ergänzen:", font=ctk.CTkFont(weight="bold"), text_color="orange"
            ).pack(anchor="w", padx=10, pady=(5, 5))

            for fid in missing_fields:
                f_row = ctk.CTkFrame(self.inplace_frame, fg_color="transparent")
                f_row.pack(fill="x", padx=10, pady=2)
                label_text = field_labels.get(fid, fid)
                ctk.CTkLabel(f_row, text=f"{label_text}:", width=180, anchor="w").pack(side="left")
                entry = ctk.CTkEntry(f_row, width=360)
                entry.pack(side="left")
                entry.bind("<KeyRelease>", lambda e: self.render_current_state())
                self.in_place_entries[fid] = entry

        self.render_current_state()

    def render_current_state(self):
        if not self.active_template:
            return

        # Collect current in-place values
        inplace_values = {}
        for fid, entry in self.in_place_entries.items():
            txt = entry.get().strip()
            if txt:
                inplace_values[fid] = txt

        success, missing, rendered = self.export_service.render_template(
            case=self.case,
            template=self.active_template,
            schema=self.schema,
            override_form_data=inplace_values,
            force_export=self.force_export_var.get(),
        )

        self.preview_textbox.delete("1.0", "end")
        if success:
            self.preview_textbox.insert("1.0", rendered)
            self.status_label.configure(text="✅ Vorlage bereit zum Export.", text_color="green")
        else:
            missing_names = [self.schema.fields[i].label if self.schema else m for m in missing for i, f in enumerate(self.schema.fields) if f.field_id == m] if self.schema else missing
            self.preview_textbox.insert("1.0", f"[FEHLENDE PFLICHTFELDER: {', '.join(missing)}]")
            self.status_label.configure(
                text=f"⚠ Unvollständig! Bitte Felder ergänzen oder Force-Export aktivieren.", text_color="red"
            )

    def apply_inplace_values_to_case(self):
        for fid, entry in self.in_place_entries.items():
            txt = entry.get().strip()
            if txt:
                self.case.form_data[fid] = txt
        if self.schema:
            from services.schema_service import SchemaService
            SchemaService.update_case_completion(self.case, self.schema)
        self.on_case_updated(self.case)

    def on_copy_clipboard(self):
        self.apply_inplace_values_to_case()
        text = self.preview_textbox.get("1.0", "end-1c")
        if text:
            self.export_service.copy_to_clipboard(text)
            self.status_label.configure(text="📋 Erfolgreich in Zwischenablage kopiert!", text_color="green")

    def on_save_file(self):
        self.apply_inplace_values_to_case()
        text = self.preview_textbox.get("1.0", "end-1c")
        if not text:
            return

        file_path = filedialog.asksaveasfilename(
            defaultextension=".md",
            filetypes=[("Markdown", "*.md"), ("Text", "*.txt"), ("Alle Dateien", "*.*")],
            initialfile=f"export_{self.case.case_id}.md",
        )
        if file_path:
            with open(file_path, "w", encoding="utf-8") as f:
                f.write(text)
            self.status_label.configure(text=f"💾 Datei gespeichert: {Path(file_path).name}", text_color="green")

    def on_open_template_manager(self):
        from ui.dialogs.template_manager_dialog import TemplateManagerDialog
        storage_service = getattr(self.master, "storage_service", None)
        if storage_service:
            TemplateManagerDialog(
                self,
                templates=self.templates,
                schemas=self.schemas,
                storage_service=storage_service,
                export_service=self.export_service,
                on_templates_updated=self.on_templates_updated,
            )

    def on_templates_updated(self, updated_templates: list[ExportTemplate]):
        self.templates = updated_templates
        tpl_names = [t.display_name for t in self.templates]
        self.tpl_combo.configure(values=tpl_names if tpl_names else ["Keine Vorlage"])
        if self.templates:
            self.active_template = self.templates[0]
            self.tpl_combo.set(self.active_template.display_name)
        self.update_render_preview()
