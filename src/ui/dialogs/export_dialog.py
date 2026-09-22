import tempfile
import webbrowser
from collections.abc import Callable
from pathlib import Path
from tkinter import filedialog
from typing import Any

import customtkinter as ctk

from constants import (
    BTN_WIDTH_MD,
    BTN_WIDTH_LG,
    BTN_WIDTH_XL,
    COLOR_DANGER,
    COLOR_MUTED_GRAY_FG,
    COLOR_MUTED_GRAY_HOVER,
    COLOR_PRIMARY,
    COLOR_PRIMARY_HOVER,
    COLOR_SUCCESS,
    COLOR_SUCCESS_HOVER,
    COLOR_WARNING,
    COMBO_WIDTH_MD,
    DIALOG_DIMENSIONS,
    DIALOG_MIN_DIMENSIONS,
    ENTRY_WIDTH_XL,
    get_file_types_html_report,
    get_file_types_markdown_export,
    FONT_SIZE_TITLE,
    LABEL_WIDTH_LG,
    PAD_NONE,
    PAD_XS,
    PAD_SM,
    PAD_MD,
    PAD_LG,
    PAD_XL,
    SCROLL_FRAME_HEIGHT_SM,
    TEXTBOX_HEIGHT_EXPORT_PREVIEW,
    TEXTBOX_WIDTH_EXPORT_PREVIEW,
)
from models.case import Case
from models.export_template import ExportTemplate
from models.schema import QuestionSchema
from services.export_service import ExportService
from services.i18n_service import tr
from ui.dialogs.base_dialog import BaseDialog
from utils.datetime_utils import format_german_datetime


class ExportDialog(BaseDialog):
    """Consolidated 2-tab dialog for 'Export & Übergabe' combining Template Export and Printable Case File."""

    def __init__(
        self,
        parent,
        case: Case,
        templates: list[ExportTemplate],
        schemas: list[QuestionSchema],
        export_service: ExportService,
        on_case_updated: Callable[[Case], None],
        attachment_service: Any | None = None,
        default_tab: str | None = None,
    ):
        super().__init__(parent)
        size = DIALOG_DIMENSIONS["export"]
        min_size = DIALOG_MIN_DIMENSIONS.get("export", (760, 720))

        self.setup_window(
            parent,
            tr("export_dialog.dialog_title", "Export & Übergabe — {case_id}", case_id=case.case_id),
            size,
            min_size=min_size,
            title_factory=lambda: tr("export_dialog.dialog_title", "Export & Übergabe — {case_id}", case_id=case.case_id),
        )

        self.case = case
        self.templates = templates
        self.schemas = schemas
        self.export_service = export_service
        self.on_case_updated = on_case_updated
        self.attachment_service = attachment_service or getattr(parent, "attachment_service", None)
        self.default_tab = default_tab

        # Find matching schema
        self.schema = next((s for s in schemas if s.schema_id == case.classification.schema_id), None)
        self.suggested_templates = self.export_service.get_suggested_templates(case, templates, self.schema)
        if not self.suggested_templates:
            self.suggested_templates = templates

        self.active_template = self.suggested_templates[0] if self.suggested_templates else None
        self.in_place_entries: dict[str, ctk.CTkEntry] = {}
        self.force_export_var = ctk.BooleanVar(value=False)

        # Print / HTML report vars
        self.timeline_vars: list[tuple[ctk.BooleanVar, int]] = []
        self.include_customer_var = ctk.BooleanVar(value=True)
        self.include_fields_var = ctk.BooleanVar(value=True)
        self.include_attachments_var = ctk.BooleanVar(value=True)

        self.create_widgets()
        self.update_render_preview()

    def create_widgets(self):
        main_frame = ctk.CTkFrame(self, fg_color="transparent")
        main_frame.pack(fill="both", expand=True, padx=PAD_XL, pady=PAD_XL)

        # Header
        header = self.register_i18n(
            ctk.CTkLabel(
                main_frame,
                text=tr("export_dialog.dialog_title", "Export & Übergabe — {case_id}", case_id=self.case.case_id),
                font=ctk.CTkFont(size=FONT_SIZE_TITLE, weight="bold"),
            ),
            "export_dialog.dialog_title",
            "Export & Übergabe — {case_id}",
            case_id=self.case.case_id,
        )
        header.pack(anchor="w", pady=(PAD_NONE, PAD_MD))

        # 2-Tab View
        self.tabview = ctk.CTkTabview(main_frame)
        self.tabview.pack(fill="both", expand=True, pady=(PAD_NONE, PAD_MD))

        tab_export_title = tr("export_dialog.tab_export", "Export & Vorlagen")
        tab_print_title = tr("export_dialog.tab_print", "Drucken & Akte")

        self.tab_export = self.tabview.add(tab_export_title)
        self.tab_print = self.tabview.add(tab_print_title)

        if self.default_tab == "print":
            self.tabview.set(tab_print_title)
        else:
            self.tabview.set(tab_export_title)

        self._build_export_tab(self.tab_export)
        self._build_print_tab(self.tab_print)

        # Bottom Close Button
        btn_frame = ctk.CTkFrame(main_frame, fg_color="transparent")
        btn_frame.pack(fill="x", side="bottom")

        close_btn = self.register_i18n(
            ctk.CTkButton(
                btn_frame,
                text=tr("common.close", "Schließen"),
                fg_color=COLOR_MUTED_GRAY_FG,
                hover_color=COLOR_MUTED_GRAY_HOVER,
                command=self.destroy,
                width=BTN_WIDTH_MD,
            ),
            "common.close",
            "Schließen",
        )
        close_btn.pack(side="left")

    # ------------------------------------------------------------------ #
    # TAB 1: Template Export                                             #
    # ------------------------------------------------------------------ #

    def _build_export_tab(self, parent: ctk.CTkFrame):
        # Template Selection Dropdown
        tpl_frame = ctk.CTkFrame(parent, fg_color="transparent")
        tpl_frame.pack(fill="x", pady=(PAD_SM, PAD_MD), padx=PAD_SM)

        self.register_i18n(
            ctk.CTkLabel(tpl_frame, text=tr("export_dialog.select_template", "Vorlage auswählen:"), font=ctk.CTkFont(weight="bold")),
            "export_dialog.select_template",
            "Vorlage auswählen:",
        ).pack(side="left", padx=(PAD_NONE, PAD_MD))

        tpl_names = [t.display_name for t in self.templates]
        self.tpl_combo = ctk.CTkOptionMenu(
            tpl_frame,
            values=tpl_names if tpl_names else [tr("export_dialog.no_template", "Keine Vorlage")],
            command=self.on_template_selected,
            width=COMBO_WIDTH_MD,
        )
        if self.active_template:
            self.tpl_combo.set(self.active_template.display_name)
        self.tpl_combo.pack(side="left")

        btn_manage = self.register_i18n(
            ctk.CTkButton(
                tpl_frame,
                text=tr("export_dialog.manage_templates_btn", "🛠 Vorlagen verwalten"),
                command=self.on_open_template_manager,
                width=BTN_WIDTH_LG,
                fg_color=COLOR_MUTED_GRAY_FG,
                hover_color=COLOR_MUTED_GRAY_HOVER,
            ),
            "export_dialog.manage_templates_btn",
            "🛠 Vorlagen verwalten",
        )
        btn_manage.pack(side="right", padx=(PAD_SM, PAD_NONE))

        # In-Place Completion Frame
        self.inplace_frame = ctk.CTkFrame(parent)
        self.inplace_frame.pack(fill="x", pady=(PAD_NONE, PAD_MD), padx=PAD_SM)

        # Force Export Checkbox
        self.force_chk = self.register_i18n(
            ctk.CTkCheckBox(
                parent,
                text=tr("export_dialog.force_export_chk", "Trotz unvollständiger Daten exportieren ([FEHLT: ...] Platzhalter)"),
                variable=self.force_export_var,
                command=self.update_render_preview,
            ),
            "export_dialog.force_export_chk",
            "Trotz unvollständiger Daten exportieren ([FEHLT: ...] Platzhalter)",
        )
        self.force_chk.pack(anchor="w", pady=(PAD_XS, PAD_MD), padx=PAD_SM)

        # Rendered Output Preview Box
        self.register_i18n(
            ctk.CTkLabel(parent, text=tr("export_dialog.preview_header", "Vorschau des exportierten Textes:"), font=ctk.CTkFont(weight="bold")),
            "export_dialog.preview_header",
            "Vorschau des exportierten Textes:",
        ).pack(anchor="w", pady=(PAD_XS, PAD_XS), padx=PAD_SM)

        self.preview_textbox = ctk.CTkTextbox(parent, width=TEXTBOX_WIDTH_EXPORT_PREVIEW, height=TEXTBOX_HEIGHT_EXPORT_PREVIEW)
        self.preview_textbox.pack(fill="both", expand=True, pady=(PAD_NONE, PAD_MD), padx=PAD_SM)

        # Status Label
        self.status_label = ctk.CTkLabel(parent, text="", text_color=COLOR_WARNING)
        self.status_label.pack(anchor="w", pady=(PAD_NONE, PAD_SM), padx=PAD_SM)

        # Action Buttons in Export Tab
        exp_btn_frame = ctk.CTkFrame(parent, fg_color="transparent")
        exp_btn_frame.pack(fill="x", padx=PAD_SM, pady=(PAD_NONE, PAD_SM))

        save_file_btn = self.register_i18n(
            ctk.CTkButton(exp_btn_frame, text=tr("export_dialog.save_file_btn", "In Datei speichern..."), command=self.on_save_file, width=BTN_WIDTH_XL),
            "export_dialog.save_file_btn",
            "In Datei speichern...",
        )
        save_file_btn.pack(side="right", padx=(PAD_MD, PAD_NONE))

        copy_btn = self.register_i18n(
            ctk.CTkButton(exp_btn_frame, text=tr("export_dialog.copy_btn", "In Zwischenablage kopieren"), command=self.on_copy_clipboard, width=BTN_WIDTH_XL),
            "export_dialog.copy_btn",
            "In Zwischenablage kopieren",
        )
        copy_btn.pack(side="right")

    # ------------------------------------------------------------------ #
    # TAB 2: Case Print & HTML Report                                    #
    # ------------------------------------------------------------------ #

    def _build_print_tab(self, parent: ctk.CTkFrame):
        opts_frame = ctk.CTkFrame(parent, fg_color="transparent")
        opts_frame.pack(fill="x", pady=(PAD_MD, PAD_MD), padx=PAD_SM)

        self.register_i18n(
            ctk.CTkCheckBox(opts_frame, text=tr("case_print.customer_data", "Praxis & Kundendaten"), variable=self.include_customer_var),
            "case_print.customer_data",
            "Praxis & Kundendaten",
        ).pack(side="left", padx=(PAD_NONE, PAD_LG))

        self.register_i18n(
            ctk.CTkCheckBox(opts_frame, text=tr("case_print.form_fields", "Formularfelder"), variable=self.include_fields_var),
            "case_print.form_fields",
            "Formularfelder",
        ).pack(side="left", padx=(PAD_NONE, PAD_LG))

        self.register_i18n(
            ctk.CTkCheckBox(opts_frame, text=tr("case_print.attachments_end", "Bilder & Anhänge am Ende"), variable=self.include_attachments_var),
            "case_print.attachments_end",
            "Bilder & Anhänge am Ende",
        ).pack(side="left")

        self.register_i18n(
            ctk.CTkLabel(parent, text=tr("case_print.timeline_lbl", "Zeitleiste / Notizen-Verlauf (einzelne Einträge abwählen):"), font=ctk.CTkFont(weight="bold")),
            "case_print.timeline_lbl",
            "Zeitleiste / Notizen-Verlauf (einzelne Einträge abwählen):",
        ).pack(anchor="w", pady=(PAD_MD, PAD_SM), padx=PAD_SM)

        scroll = ctk.CTkScrollableFrame(parent, height=SCROLL_FRAME_HEIGHT_SM)
        scroll.pack(fill="both", expand=True, pady=(PAD_NONE, PAD_MD), padx=PAD_SM)

        if not self.case.timeline:
            self.register_i18n(
                ctk.CTkLabel(scroll, text=tr("case_print.no_timeline_notes", "Keine Notizen in der Zeitleiste.")),
                "case_print.no_timeline_notes",
                "Keine Notizen in der Zeitleiste.",
            ).pack(pady=PAD_MD)
        else:
            for idx, entry in enumerate(self.case.timeline):
                var = ctk.BooleanVar(value=True)
                self.timeline_vars.append((var, idx))
                formatted_ts = format_german_datetime(entry.timestamp)
                lbl_text = f"[{formatted_ts}] {entry.author}: {entry.note[:60]}..."
                ctk.CTkCheckBox(scroll, text=lbl_text, variable=var).pack(anchor="w", pady=PAD_XS, padx=PAD_SM)

        # Print Action Buttons
        print_btn_frame = ctk.CTkFrame(parent, fg_color="transparent")
        print_btn_frame.pack(fill="x", padx=PAD_SM, pady=(PAD_NONE, PAD_SM))

        self.register_i18n(
            ctk.CTkButton(
                print_btn_frame,
                text=tr("ui_buttons.print_pdf", "🖨 PDF-Bericht drucken"),
                fg_color=COLOR_SUCCESS,
                hover_color=COLOR_SUCCESS_HOVER,
                command=self.generate_and_print_pdf,
                width=BTN_WIDTH_XL,
            ),
            "ui_buttons.print_pdf",
            "🖨 PDF-Bericht drucken",
        ).pack(side="right", padx=(PAD_SM, PAD_NONE))

        self.register_i18n(
            ctk.CTkButton(
                print_btn_frame,
                text=tr("case_print.html_report_btn", "🌐 HTML-Bericht"),
                fg_color=COLOR_PRIMARY,
                hover_color=COLOR_PRIMARY_HOVER,
                command=self.generate_and_open_html,
                width=BTN_WIDTH_LG,
            ),
            "case_print.html_report_btn",
            "🌐 HTML-Bericht",
        ).pack(side="right", padx=(PAD_SM, PAD_NONE))

        self.register_i18n(
            ctk.CTkButton(
                print_btn_frame,
                text=tr("case_print.save_btn", "💾 Speichern..."),
                fg_color=COLOR_MUTED_GRAY_FG,
                hover_color=COLOR_MUTED_GRAY_HOVER,
                command=self.generate_and_save_file,
                width=BTN_WIDTH_MD,
            ),
            "case_print.save_btn",
            "💾 Speichern...",
        ).pack(side="right")

    # ------------------------------------------------------------------ #
    # Export Handlers                                                    #
    # ------------------------------------------------------------------ #

    def on_template_selected(self, selected_name: str):
        self.active_template = next((t for t in self.templates if t.display_name == selected_name), None)
        self.update_render_preview()

    def update_render_preview(self):
        if not self.active_template:
            self.preview_textbox.delete("1.0", "end")
            self.status_label.configure(text=tr("export.no_template", "Keine Vorlage ausgewählt."))
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
            self.register_i18n(
                ctk.CTkLabel(
                    self.inplace_frame,
                    text=tr("export.missing_fields_hdr", "⚠ Fehlende Pflichtfelder direkt ergänzen:"),
                    font=ctk.CTkFont(weight="bold"),
                    text_color=COLOR_WARNING,
                ),
                "export.missing_fields_hdr",
                "⚠ Fehlende Pflichtfelder direkt ergänzen:",
            ).pack(anchor="w", padx=PAD_MD, pady=(PAD_SM, PAD_SM))

            for fid in missing_fields:
                f_row = ctk.CTkFrame(self.inplace_frame, fg_color="transparent")
                f_row.pack(fill="x", padx=PAD_MD, pady=PAD_XS)
                label_text = field_labels.get(fid, fid)
                ctk.CTkLabel(f_row, text=f"{label_text}:", width=LABEL_WIDTH_LG, anchor="w").pack(side="left")
                entry = ctk.CTkEntry(f_row, width=ENTRY_WIDTH_XL)
                entry.pack(side="left")
                entry.bind("<KeyRelease>", lambda e: self.render_current_state())
                self.in_place_entries[fid] = entry

        self.render_current_state()

    def render_current_state(self):
        if not self.active_template:
            return

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
            self.status_label.configure(text=tr("export.ready", "✅ Vorlage bereit zum Export."), text_color=COLOR_SUCCESS)
        else:
            missing_names = (
                [self.schema.fields[i].label if self.schema else m for m in missing for i, f in enumerate(self.schema.fields) if f.field_id == m]
                if self.schema
                else missing
            )
            self.preview_textbox.insert("1.0", tr("export.missing_required_fields", "[FEHLENDE PFLICHTFELDER: {fields}]", fields=", ".join(missing_names)))
            self.status_label.configure(
                text=tr("export.incomplete", "⚠ Unvollständig! Bitte Felder ergänzen oder Force-Export aktivieren."), text_color=COLOR_DANGER
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
            self.status_label.configure(text=tr("export.copied", "📋 Erfolgreich in Zwischenablage kopiert!"), text_color=COLOR_SUCCESS)

    def on_save_file(self):
        self.apply_inplace_values_to_case()
        text = self.preview_textbox.get("1.0", "end-1c")
        if not text:
            return

        file_path = filedialog.asksaveasfilename(
            defaultextension=".md",
            filetypes=get_file_types_markdown_export(),
            initialfile=f"export_{self.case.case_id}.md",
        )
        if file_path:
            with open(file_path, "w", encoding="utf-8") as f:
                f.write(text)
            self.status_label.configure(text=tr("export_dialog.file_saved", "💾 Datei gespeichert: {name}", name=Path(file_path).name), text_color=COLOR_SUCCESS)

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
        self.tpl_combo.configure(values=tpl_names if tpl_names else [tr("export_dialog.no_template", "Keine Vorlage")])
        if self.templates:
            self.active_template = self.templates[0]
            self.tpl_combo.set(self.active_template.display_name)
        self.update_render_preview()

    # ------------------------------------------------------------------ #
    # Print / HTML Handlers                                              #
    # ------------------------------------------------------------------ #

    def build_html_content(self, auto_print: bool = False) -> str:
        from services.case_report_builder import generate_case_report_html

        selected_entries = [self.case.timeline[idx] for var, idx in self.timeline_vars if var.get()]
        return generate_case_report_html(
            case=self.case,
            include_customer=self.include_customer_var.get(),
            include_fields=self.include_fields_var.get(),
            include_attachments=self.include_attachments_var.get(),
            selected_entries=selected_entries,
            attachment_service=self.attachment_service,
            auto_print=auto_print,
            schemas=self.schemas,
        )


    def generate_and_open_html(self):
        """Generates clean HTML report and opens it in the default browser without triggering print."""
        html_content = self.build_html_content(auto_print=False)
        temp_dir = Path(tempfile.gettempdir())
        html_file = temp_dir / f"Fallbericht_{self.case.case_id}.html"
        html_file.write_text(html_content, encoding="utf-8")

        webbrowser.open(html_file.as_uri())
        self.destroy()

    def generate_and_print_pdf(self):
        """Generates printable report and automatically triggers the print/Save-to-PDF dialog."""
        html_content = self.build_html_content(auto_print=True)
        temp_dir = Path(tempfile.gettempdir())
        html_file = temp_dir / f"Fallbericht_{self.case.case_id}_Print.html"
        html_file.write_text(html_content, encoding="utf-8")

        webbrowser.open(html_file.as_uri())
        self.destroy()

    def generate_and_save_file(self):
        """Prompts user to save the static HTML report file."""
        file_path = filedialog.asksaveasfilename(
            parent=self,
            title=tr("case_print.save_dialog_title", "Fallbericht speichern"),
            defaultextension=".html",
            initialfile=f"Fallbericht_{self.case.case_id}.html",
            filetypes=get_file_types_html_report(),
        )
        if not file_path:
            return

        html_content = self.build_html_content(auto_print=False)
        Path(file_path).write_text(html_content, encoding="utf-8")
        self.destroy()
