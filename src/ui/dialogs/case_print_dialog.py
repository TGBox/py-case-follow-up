import tempfile
import webbrowser
import customtkinter as ctk

from ui.dialogs.base_dialog import BaseDialog
from pathlib import Path
from tkinter import filedialog
from typing import Any
from models.case import Case
from utils.datetime_utils import format_german_datetime
from constants import DIALOG_DIMENSIONS


class CasePrintDialog(BaseDialog):
    """Print preview and HTML report generator dialog allowing selective unchecking of timeline entries and fields."""

    def __init__(self, parent, case: Case, attachment_service: Any | None = None):
        super().__init__(parent)
        self.case = case
        self.attachment_service = attachment_service

        from services.i18n_service import tr
        w, h = DIALOG_DIMENSIONS["print_report"]
        self.setup_window(
            parent,
            tr("case_print.dialog_title", "🖨 Fall-Akte Druck- & HTML Export: {case_id}", case_id=case.case_id),
            (w, h),
            min_size=(620, 500),

            title_factory=lambda: tr("case_print.dialog_title", "🖨 Fall-Akte Druck- & HTML Export: {case_id}", case_id=case.case_id),
        )

        self.timeline_vars: list[tuple[ctk.BooleanVar, int]] = []
        self.include_customer_var = ctk.BooleanVar(value=True)
        self.include_fields_var = ctk.BooleanVar(value=True)
        self.include_attachments_var = ctk.BooleanVar(value=True)

        self.create_widgets()

    def create_widgets(self):
        main_frame = ctk.CTkFrame(self, fg_color="transparent")
        main_frame.pack(fill="both", expand=True, padx=15, pady=15)

        from services.i18n_service import tr

        self.register_i18n(ctk.CTkLabel(main_frame, text=tr("case_print.header", "🖨 Druckansicht für Fall {case_id} anpassen", case_id=self.case.case_id), font=ctk.CTkFont(size=16, weight="bold")), "case_print.header", "🖨 Druckansicht für Fall {case_id} anpassen", case_id=self.case.case_id).pack(anchor="w", pady=(0, 10))

        self.register_i18n(ctk.CTkLabel(main_frame, text=tr("case_print.sub_header", "Wählen Sie aus, welche Elemente im Druckbericht erscheinen sollen:")), "case_print.sub_header", "Wählen Sie aus, welche Elemente im Druckbericht erscheinen sollen:").pack(anchor="w", pady=(0, 8))

        # Main options
        opts_frame = ctk.CTkFrame(main_frame, fg_color="transparent")
        opts_frame.pack(fill="x", pady=(0, 8))

        self.register_i18n(ctk.CTkCheckBox(opts_frame, text=tr("case_print.customer_data", "Praxis & Kundendaten"), variable=self.include_customer_var), "case_print.customer_data", "Praxis & Kundendaten").pack(side="left", padx=(0, 12))
        self.register_i18n(ctk.CTkCheckBox(opts_frame, text=tr("case_print.form_fields", "Formularfelder"), variable=self.include_fields_var), "case_print.form_fields", "Formularfelder").pack(side="left", padx=(0, 12))
        self.register_i18n(ctk.CTkCheckBox(opts_frame, text=tr("case_print.attachments_end", "Bilder & Anhänge am Ende"), variable=self.include_attachments_var), "case_print.attachments_end", "Bilder & Anhänge am Ende").pack(side="left")

        self.register_i18n(ctk.CTkLabel(main_frame, text=tr("case_print.timeline_lbl", "Zeitleiste / Notizen-Verlauf (einzelne Einträge abwählen):"), font=ctk.CTkFont(weight="bold")), "case_print.timeline_lbl", "Zeitleiste / Notizen-Verlauf (einzelne Einträge abwählen):").pack(anchor="w", pady=(8, 4))

        scroll = ctk.CTkScrollableFrame(main_frame, height=220)
        scroll.pack(fill="both", expand=True, pady=(0, 10))

        if not self.case.timeline:
            self.register_i18n(ctk.CTkLabel(scroll, text=tr("case_print.no_timeline_notes", "Keine Notizen in der Zeitleiste.")), "case_print.no_timeline_notes", "Keine Notizen in der Zeitleiste.").pack(pady=10)
        else:
            for idx, entry in enumerate(self.case.timeline):
                var = ctk.BooleanVar(value=True)
                self.timeline_vars.append((var, idx))

                formatted_ts = format_german_datetime(entry.timestamp)
                lbl_text = f"[{formatted_ts}] {entry.author}: {entry.note[:60]}..."
                ctk.CTkCheckBox(scroll, text=lbl_text, variable=var).pack(anchor="w", pady=3, padx=5)

        # Action bar
        btn_frame = ctk.CTkFrame(main_frame, fg_color="transparent")
        btn_frame.pack(fill="x", side="bottom", pady=(5, 0))

        self.register_i18n(ctk.CTkButton(
            btn_frame,
            text=tr("common.cancel", "Abbrechen"),
            fg_color=("gray70", "gray40"),
            hover_color=("gray60", "gray50"),
            command=self.safe_destroy,
            width=90,
        ), "common.cancel", "Abbrechen").pack(side="left")

        self.register_i18n(ctk.CTkButton(
            btn_frame,
            text=tr("ui_buttons.print_pdf", "🖨 PDF-Bericht drucken"),
            fg_color="forestgreen",
            hover_color="darkgreen",
            command=self.generate_and_print_pdf,
            width=175,
        ), "ui_buttons.print_pdf", "🖨 PDF-Bericht drucken").pack(side="right", padx=(6, 0))

        self.register_i18n(ctk.CTkButton(
            btn_frame,
            text=tr("case_print.html_report_btn", "🌐 HTML-Bericht"),
            fg_color="#2563eb",
            hover_color="#1d4ed8",
            command=self.generate_and_open_html,
            width=135,
        ), "case_print.html_report_btn", "🌐 HTML-Bericht").pack(side="right", padx=(6, 0))

        self.register_i18n(ctk.CTkButton(
            btn_frame,
            text=tr("case_print.save_btn", "💾 Speichern..."),
            fg_color=("gray75", "gray30"),
            hover_color=("gray65", "gray40"),
            command=self.generate_and_save_file,
            width=110,
        ), "case_print.save_btn", "💾 Speichern...").pack(side="right")

    def safe_destroy(self):
        try:
            self.grab_release()
        except Exception:
            pass
        if hasattr(self, "tk"):
            self.after(1, self._do_destroy)
        else:
            self._do_destroy()

    def _do_destroy(self):
        try:
            self.destroy()
        except Exception:
            pass

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
        )


    def generate_and_open_html(self):
        """Generates clean HTML report and opens it in the default browser without triggering print."""
        html_content = self.build_html_content(auto_print=False)
        temp_dir = Path(tempfile.gettempdir())
        html_file = temp_dir / f"Fallbericht_{self.case.case_id}.html"
        html_file.write_text(html_content, encoding="utf-8")

        webbrowser.open(html_file.as_uri())
        self.safe_destroy()

    def generate_and_print_pdf(self):
        """Generates printable report and automatically triggers the print/Save-to-PDF dialog."""
        html_content = self.build_html_content(auto_print=True)
        temp_dir = Path(tempfile.gettempdir())
        html_file = temp_dir / f"Fallbericht_{self.case.case_id}_Print.html"
        html_file.write_text(html_content, encoding="utf-8")

        webbrowser.open(html_file.as_uri())
        self.safe_destroy()

    def generate_and_save_file(self):
        """Prompts user to save the static HTML report file."""
        from services.i18n_service import tr
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
        self.safe_destroy()


