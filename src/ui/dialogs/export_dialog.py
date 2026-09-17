import base64
import tempfile
import webbrowser
from collections.abc import Callable
from pathlib import Path
from tkinter import filedialog
from typing import Any

import customtkinter as ctk

from constants import DIALOG_DIMENSIONS
from enums import get_actor_display, get_board_column_display
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
        w, h = DIALOG_DIMENSIONS.get("export", (820, 720))
        # Ensure window is large enough for both tabs
        w = max(w, 820)
        h = max(h, 720)

        self.setup_window(
            parent,
            tr("export_dialog.dialog_title", "Export & Übergabe — {case_id}", case_id=case.case_id),
            (w, h),
            min_size=(760, 640),
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
        main_frame.pack(fill="both", expand=True, padx=15, pady=15)

        # Header
        header = self.register_i18n(
            ctk.CTkLabel(
                main_frame,
                text=tr("export_dialog.dialog_title", "Export & Übergabe — {case_id}", case_id=self.case.case_id),
                font=ctk.CTkFont(size=17, weight="bold"),
            ),
            "export_dialog.dialog_title",
            "Export & Übergabe — {case_id}",
            case_id=self.case.case_id,
        )
        header.pack(anchor="w", pady=(0, 8))

        # 2-Tab View
        self.tabview = ctk.CTkTabview(main_frame)
        self.tabview.pack(fill="both", expand=True, pady=(0, 10))

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
            ctk.CTkButton(btn_frame, text=tr("common.close", "Schließen"), fg_color="gray", command=self.destroy, width=110),
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
        tpl_frame.pack(fill="x", pady=(5, 8), padx=5)

        self.register_i18n(
            ctk.CTkLabel(tpl_frame, text=tr("export_dialog.select_template", "Vorlage auswählen:"), font=ctk.CTkFont(weight="bold")),
            "export_dialog.select_template",
            "Vorlage auswählen:",
        ).pack(side="left", padx=(0, 10))

        tpl_names = [t.display_name for t in self.templates]
        self.tpl_combo = ctk.CTkOptionMenu(
            tpl_frame,
            values=tpl_names if tpl_names else [tr("export_dialog.no_template", "Keine Vorlage")],
            command=self.on_template_selected,
            width=280,
        )
        if self.active_template:
            self.tpl_combo.set(self.active_template.display_name)
        self.tpl_combo.pack(side="left")

        btn_manage = self.register_i18n(
            ctk.CTkButton(
                tpl_frame,
                text=tr("export_dialog.manage_templates_btn", "🛠 Vorlagen verwalten"),
                command=self.on_open_template_manager,
                width=150,
                fg_color=("gray75", "gray30"),
                hover_color=("gray65", "gray40"),
            ),
            "export_dialog.manage_templates_btn",
            "🛠 Vorlagen verwalten",
        )
        btn_manage.pack(side="right", padx=(5, 0))

        # In-Place Completion Frame
        self.inplace_frame = ctk.CTkFrame(parent)
        self.inplace_frame.pack(fill="x", pady=(0, 6), padx=5)

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
        self.force_chk.pack(anchor="w", pady=(3, 6), padx=5)

        # Rendered Output Preview Box
        self.register_i18n(
            ctk.CTkLabel(parent, text=tr("export_dialog.preview_header", "Vorschau des exportierten Textes:"), font=ctk.CTkFont(weight="bold")),
            "export_dialog.preview_header",
            "Vorschau des exportierten Textes:",
        ).pack(anchor="w", pady=(3, 2), padx=5)

        self.preview_textbox = ctk.CTkTextbox(parent, width=640, height=200)
        self.preview_textbox.pack(fill="both", expand=True, pady=(0, 8), padx=5)

        # Status Label
        self.status_label = ctk.CTkLabel(parent, text="", text_color="orange")
        self.status_label.pack(anchor="w", pady=(0, 5), padx=5)

        # Action Buttons in Export Tab
        exp_btn_frame = ctk.CTkFrame(parent, fg_color="transparent")
        exp_btn_frame.pack(fill="x", padx=5, pady=(0, 5))

        save_file_btn = self.register_i18n(
            ctk.CTkButton(exp_btn_frame, text=tr("export_dialog.save_file_btn", "In Datei speichern..."), command=self.on_save_file, width=160),
            "export_dialog.save_file_btn",
            "In Datei speichern...",
        )
        save_file_btn.pack(side="right", padx=(10, 0))

        copy_btn = self.register_i18n(
            ctk.CTkButton(exp_btn_frame, text=tr("export_dialog.copy_btn", "In Zwischenablage kopieren"), command=self.on_copy_clipboard, width=190),
            "export_dialog.copy_btn",
            "In Zwischenablage kopieren",
        )
        copy_btn.pack(side="right")

    # ------------------------------------------------------------------ #
    # TAB 2: Case Print & HTML Report                                    #
    # ------------------------------------------------------------------ #

    def _build_print_tab(self, parent: ctk.CTkFrame):
        opts_frame = ctk.CTkFrame(parent, fg_color="transparent")
        opts_frame.pack(fill="x", pady=(8, 6), padx=5)

        self.register_i18n(
            ctk.CTkCheckBox(opts_frame, text=tr("case_print.customer_data", "Praxis & Kundendaten"), variable=self.include_customer_var),
            "case_print.customer_data",
            "Praxis & Kundendaten",
        ).pack(side="left", padx=(0, 12))

        self.register_i18n(
            ctk.CTkCheckBox(opts_frame, text=tr("case_print.form_fields", "Formularfelder"), variable=self.include_fields_var),
            "case_print.form_fields",
            "Formularfelder",
        ).pack(side="left", padx=(0, 12))

        self.register_i18n(
            ctk.CTkCheckBox(opts_frame, text=tr("case_print.attachments_end", "Bilder & Anhänge am Ende"), variable=self.include_attachments_var),
            "case_print.attachments_end",
            "Bilder & Anhänge am Ende",
        ).pack(side="left")

        self.register_i18n(
            ctk.CTkLabel(parent, text=tr("case_print.timeline_lbl", "Zeitleiste / Notizen-Verlauf (einzelne Einträge abwählen):"), font=ctk.CTkFont(weight="bold")),
            "case_print.timeline_lbl",
            "Zeitleiste / Notizen-Verlauf (einzelne Einträge abwählen):",
        ).pack(anchor="w", pady=(8, 4), padx=5)

        scroll = ctk.CTkScrollableFrame(parent, height=190)
        scroll.pack(fill="both", expand=True, pady=(0, 8), padx=5)

        if not self.case.timeline:
            self.register_i18n(
                ctk.CTkLabel(scroll, text=tr("case_print.no_timeline_notes", "Keine Notizen in der Zeitleiste.")),
                "case_print.no_timeline_notes",
                "Keine Notizen in der Zeitleiste.",
            ).pack(pady=10)
        else:
            for idx, entry in enumerate(self.case.timeline):
                var = ctk.BooleanVar(value=True)
                self.timeline_vars.append((var, idx))
                formatted_ts = format_german_datetime(entry.timestamp)
                lbl_text = f"[{formatted_ts}] {entry.author}: {entry.note[:60]}..."
                ctk.CTkCheckBox(scroll, text=lbl_text, variable=var).pack(anchor="w", pady=3, padx=5)

        # Print Action Buttons
        print_btn_frame = ctk.CTkFrame(parent, fg_color="transparent")
        print_btn_frame.pack(fill="x", padx=5, pady=(0, 5))

        self.register_i18n(
            ctk.CTkButton(
                print_btn_frame,
                text=tr("ui_buttons.print_pdf", "🖨 PDF-Bericht drucken"),
                fg_color="forestgreen",
                hover_color="darkgreen",
                command=self.generate_and_print_pdf,
                width=175,
            ),
            "ui_buttons.print_pdf",
            "🖨 PDF-Bericht drucken",
        ).pack(side="right", padx=(6, 0))

        self.register_i18n(
            ctk.CTkButton(
                print_btn_frame,
                text=tr("case_print.html_report_btn", "🌐 HTML-Bericht"),
                fg_color="#2563eb",
                hover_color="#1d4ed8",
                command=self.generate_and_open_html,
                width=135,
            ),
            "case_print.html_report_btn",
            "🌐 HTML-Bericht",
        ).pack(side="right", padx=(6, 0))

        self.register_i18n(
            ctk.CTkButton(
                print_btn_frame,
                text=tr("case_print.save_btn", "💾 Speichern..."),
                fg_color=("gray75", "gray30"),
                hover_color=("gray65", "gray40"),
                command=self.generate_and_save_file,
                width=110,
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
                    text_color="orange",
                ),
                "export.missing_fields_hdr",
                "⚠ Fehlende Pflichtfelder direkt ergänzen:",
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
            self.status_label.configure(text=tr("export.ready", "✅ Vorlage bereit zum Export."), text_color="green")
        else:
            missing_names = (
                [self.schema.fields[i].label if self.schema else m for m in missing for i, f in enumerate(self.schema.fields) if f.field_id == m]
                if self.schema
                else missing
            )
            self.preview_textbox.insert("1.0", f"[FEHLENDE PFLICHTFELDER: {', '.join(missing_names)}]")
            self.status_label.configure(
                text=tr("export.incomplete", "⚠ Unvollständig! Bitte Felder ergänzen oder Force-Export aktivieren."), text_color="red"
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
            self.status_label.configure(text=tr("export.copied", "📋 Erfolgreich in Zwischenablage kopiert!"), text_color="green")

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
            self.status_label.configure(text=tr("export_dialog.file_saved", "💾 Datei gespeichert: {name}", name=Path(file_path).name), text_color="green")

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

    # ------------------------------------------------------------------ #
    # Print / HTML Handlers                                              #
    # ------------------------------------------------------------------ #

    def build_html_content(self, auto_print: bool = False) -> str:
        selected_entries = [self.case.timeline[idx] for var, idx in self.timeline_vars if var.get()]

        status_disp = get_board_column_display(self.case.workflow_status.board_column)
        actor_disp = get_actor_display(self.case.workflow_status.current_actor)
        created_str = self.case.formatted_created_at or format_german_datetime(self.case.created_at)
        deadline_str = self.case.formatted_deadline or tr("case_print.no_deadline", "Keine Frist gesetzt")
        followup_str = self.case.formatted_followup or tr("case_print.no_followup", "Keine Wiedervorlage gesetzt")

        print_script = """<script>
window.addEventListener('DOMContentLoaded', function() {
    setTimeout(function() { window.print(); }, 400);
});
</script>""" if auto_print else ""

        banner_text = (
            tr("case_print.banner_print", "<strong>Druckansicht Fall-Akte</strong> — Druckdialog wird geöffnet. Wählen Sie Ihren Drucker oder „Als PDF speichern“.")
            if auto_print
            else tr("case_print.banner_view", "<strong>Fall-Akte Ansicht</strong> — Übersicht für Fall {case_id}.", case_id=self.case.case_id)
        )

        btn_print_pdf_txt = tr("case_print.btn_print_pdf", "🖨 Drucken / Als PDF speichern")
        hdr_customer = tr("case_print.header_customer_data", "Kunden- & Praxisdaten")
        hdr_fields = tr("case_print.header_form_fields", "Formularfelder & Details")
        hdr_timeline = tr("case_print.header_timeline", "Verlauf & Zeitleiste")
        hdr_attachments = tr("case_print.header_attachments", "Anhänge & Bilder")

        lbl_case_id = tr("case_print.col_case_id", "Fall-ID")
        lbl_score = tr("case_print.col_score", "Priorität / Score")
        lbl_status = tr("case_print.col_status", "Aktueller Status")
        lbl_actor = tr("case_print.col_actor", "Zuständigkeit")
        lbl_created = tr("case_print.col_created", "Erstellt am")
        lbl_deadline = tr("case_print.col_deadline", "Rückruf-Deadline")
        lbl_followup = tr("case_print.col_followup", "Wiedervorlage")

        lbl_practice = tr("case_print.col_practice", "Praxisname")
        lbl_cust_id = tr("case_print.col_cust_id", "Kunden-ID")
        lbl_contact = tr("case_print.col_contact", "Ansprechpartner")
        lbl_phone = tr("case_print.col_phone", "Telefon")
        lbl_email = tr("case_print.col_email", "E-Mail")

        lbl_field = tr("case_print.col_field", "Feld")
        lbl_value = tr("case_print.col_value", "Wert")
        lbl_filename = tr("case_print.col_filename", "Dateiname")
        lbl_filesize = tr("case_print.col_filesize", "Dateigröße")

        html_lines = [
            "<!DOCTYPE html>",
            "<html><head><meta charset='utf-8'>",
            f"<title>Fall-Akte {self.case.case_id} — {self.case.classification.title}</title>",
            "<style>",
            "body { font-family: 'Segoe UI', Arial, sans-serif; margin: 35px; color: #222; background: #fff; line-height: 1.5; }",
            "h1 { color: #1a5276; border-bottom: 2px solid #1a5276; padding-bottom: 8px; margin-bottom: 12px; }",
            "h2 { color: #2e4053; margin-top: 25px; border-bottom: 1px solid #ddd; padding-bottom: 4px; }",
            "table { width: 100%; border-collapse: collapse; margin-top: 10px; margin-bottom: 15px; }",
            "th, td { border: 1px solid #ddd; padding: 8px 12px; text-align: left; font-size: 13px; }",
            "th { background-color: #f4f6f7; width: 25%; font-weight: bold; color: #333; }",
            ".entry { background: #f8f9f9; border-left: 4px solid #3498db; margin: 10px 0; padding: 10px 14px; border-radius: 0 4px 4px 0; }",
            ".no-print { margin-bottom: 20px; background: #ebf5fb; padding: 15px; border-radius: 6px; border: 1px solid #aed6f1; font-size: 14px; display: flex; align-items: center; justify-content: space-between; }",
            ".print-btn { background: #27ae60; color: white; border: none; padding: 10px 20px; font-size: 14px; font-weight: bold; border-radius: 4px; cursor: pointer; }",
            ".print-btn:hover { background: #219150; }",
            ".img-container { margin: 18px 0; page-break-inside: avoid; text-align: center; }",
            ".img-container img { max-width: 95%; max-height: 800px; border: 1px solid #ccc; border-radius: 6px; box-shadow: 0 2px 8px rgba(0,0,0,0.12); }",
            ".img-caption { font-size: 12px; color: #666; margin-top: 6px; font-weight: bold; }",
            "@media print { .no-print { display: none !important; } body { margin: 0; } }",
            "</style>",
            print_script,
            "</head><body>",
            "<div class='no-print'>",
            f"  <div>{banner_text}</div>",
            f"  <button class='print-btn' onclick='window.print()'>{btn_print_pdf_txt}</button>",
            "</div>",
            f"<h1>Fall-Akte: {self.case.case_id} — {self.case.classification.title}</h1>",
            "<table>",
            f"<tr><th>{lbl_case_id}</th><td><strong>{self.case.case_id}</strong></td><th>{lbl_score}</th><td>{self.case.classification.calculated_score:.0f} Pkt. ({self.case.classification.urgency_level})</td></tr>",
            f"<tr><th>{lbl_status}</th><td>{status_disp}</td><th>{lbl_actor}</th><td>{actor_disp}</td></tr>",
            f"<tr><th>{lbl_created}</th><td>{created_str} ({self.case.created_by})</td><th>{lbl_deadline}</th><td>{deadline_str}</td></tr>",
            f"<tr><th>{lbl_followup}</th><td colspan='3'>{followup_str}</td></tr>",
            "</table>",
        ]

        if self.include_customer_var.get() and self.case.customer:
            cust = self.case.customer
            vip_str = tr("case_print.vip_suffix", " (VIP-Kunde)") if cust.is_vip else ""
            html_lines.extend([
                f"<h2>{hdr_customer}</h2>",
                "<table>",
                f"<tr><th>{lbl_practice}</th><td>{cust.practice_name}{vip_str}</td></tr>",
                f"<tr><th>{lbl_cust_id}</th><td>{cust.customer_id}</td></tr>",
                f"<tr><th>{lbl_contact}</th><td>{cust.contact_person or '-'}</td></tr>",
                f"<tr><th>{lbl_phone}</th><td>{cust.phone or '-'}</td></tr>",
                f"<tr><th>{lbl_email}</th><td>{cust.email or '-'}</td></tr>",
                "</table>",
            ])

        if self.include_fields_var.get() and self.case.form_data:
            html_lines.extend([f"<h2>{hdr_fields}</h2><table>", f"<tr><th>{lbl_field}</th><th>{lbl_value}</th></tr>"])
            for k, v in self.case.form_data.items():
                val_disp = "<br>".join(str(v).splitlines()) if "\n" in str(v) else str(v)
                html_lines.append(f"<tr><th>{k}</th><td>{val_disp}</td></tr>")
            html_lines.append("</table>")

        if selected_entries:
            html_lines.append(f"<h2>{hdr_timeline}</h2>")
            for entry in selected_entries:
                ts_str = format_german_datetime(entry.timestamp)
                note_html = "<br>".join(entry.note.splitlines())
                html_lines.append(
                    f"<div class='entry'><strong>[{ts_str}] {entry.author} ({entry.channel}):</strong><br>{note_html}</div>"
                )

        if self.include_attachments_var.get() and self.attachment_service:
            try:
                att_files = self.attachment_service.list_attachments(self.case)
                if att_files:
                    html_lines.append(f"<h2>{hdr_attachments}</h2>")
                    img_exts = {".png", ".jpg", ".jpeg", ".gif", ".webp", ".bmp"}
                    img_files = [f for f in att_files if f.suffix.lower() in img_exts]
                    other_files = [f for f in att_files if f.suffix.lower() not in img_exts]

                    if other_files:
                        html_lines.append(f"<table><tr><th>{lbl_filename}</th><th>{lbl_filesize}</th></tr>")
                        for f in other_files:
                            size_kb = f.stat().st_size / 1024.0 if f.exists() else 0
                            html_lines.append(f"<tr><td>📄 {f.name}</td><td>{size_kb:.1f} KB</td></tr>")
                        html_lines.append("</table>")

                    for img_path in img_files:
                        try:
                            data = img_path.read_bytes()
                            ext = img_path.suffix.lower().replace(".", "")
                            if ext == "jpg":
                                ext = "jpeg"
                            b64 = base64.b64encode(data).decode("utf-8")
                            html_lines.append(
                                f"<div class='img-container'><img src='data:image/{ext};base64,{b64}' alt='{img_path.name}' /><div class='img-caption'>📷 {img_path.name}</div></div>"
                            )
                        except Exception:
                            pass
            except Exception:
                pass

        html_lines.append("</body></html>")
        return "\n".join(html_lines)

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
            filetypes=[("HTML-Bericht (für PDF-Druck)", "*.html"), ("Alle Dateien", "*.*")],
        )
        if not file_path:
            return

        html_content = self.build_html_content(auto_print=False)
        Path(file_path).write_text(html_content, encoding="utf-8")
        self.destroy()
