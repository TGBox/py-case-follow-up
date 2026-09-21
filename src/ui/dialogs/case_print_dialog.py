import tempfile
import webbrowser
import customtkinter as ctk

from ui.dialogs.base_dialog import BaseDialog
from pathlib import Path
from tkinter import filedialog
from typing import Any
from models.case import Case
from utils.datetime_utils import format_german_datetime
from constants import (
    BTN_WIDTH_ACTION_SM,
    BTN_WIDTH_HTML,
    BTN_WIDTH_PRINT,
    CASE_PRINT_NOTE_PREVIEW_LEN,
    COLOR_CANCEL_FG,
    COLOR_CANCEL_HOVER,
    COLOR_MUTED_GRAY_FG,
    COLOR_MUTED_GRAY_HOVER,
    COLOR_PRIMARY,
    COLOR_PRIMARY_HOVER,
    COLOR_SUCCESS,
    COLOR_SUCCESS_HOVER,
    DIALOG_DIMENSIONS,
    DIALOG_MIN_DIMENSIONS,
    ENTRY_WIDTH_SHORTCUT,
    FILE_EXT_HTML,
    FONT_SIZE_TITLE,
    PAD_LG,
    PAD_MD,
    PAD_NONE,
    PAD_SM,
    PAD_XL,
    PAD_XS,
    REPORT_FILENAME_TEMPLATE,
    REPORT_PRINT_FILENAME_TEMPLATE,
    SCROLL_HEIGHT_PRINT_TIMELINE,
    get_file_types_html_report,
)


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
            min_size=DIALOG_MIN_DIMENSIONS["print_report"],
            title_factory=lambda: tr("case_print.dialog_title", "🖨 Fall-Akte Druck- & HTML Export: {case_id}", case_id=case.case_id),
        )

        self.timeline_vars: list[tuple[ctk.BooleanVar, int]] = []
        self.include_customer_var = ctk.BooleanVar(value=True)
        self.include_fields_var = ctk.BooleanVar(value=True)
        self.include_attachments_var = ctk.BooleanVar(value=True)

        self.create_widgets()

    def create_widgets(self):
        main_frame = ctk.CTkFrame(self, fg_color="transparent")
        main_frame.pack(fill="both", expand=True, padx=PAD_XL, pady=PAD_XL)

        from services.i18n_service import tr

        self.register_i18n(ctk.CTkLabel(main_frame, text=tr("case_print.header", "🖨 Druckansicht für Fall {case_id} anpassen", case_id=self.case.case_id), font=ctk.CTkFont(size=FONT_SIZE_TITLE, weight="bold")), "case_print.header", "🖨 Druckansicht für Fall {case_id} anpassen", case_id=self.case.case_id).pack(anchor="w", pady=(PAD_NONE, PAD_MD + PAD_XS))

        self.register_i18n(ctk.CTkLabel(main_frame, text=tr("case_print.sub_header", "Wählen Sie aus, welche Elemente im Druckbericht erscheinen sollen:")), "case_print.sub_header", "Wählen Sie aus, welche Elemente im Druckbericht erscheinen sollen:").pack(anchor="w", pady=(PAD_NONE, PAD_MD))

        # Main options
        opts_frame = ctk.CTkFrame(main_frame, fg_color="transparent")
        opts_frame.pack(fill="x", pady=(PAD_NONE, PAD_MD))

        self.register_i18n(ctk.CTkCheckBox(opts_frame, text=tr("case_print.customer_data", "Praxis & Kundendaten"), variable=self.include_customer_var), "case_print.customer_data", "Praxis & Kundendaten").pack(side="left", padx=(PAD_NONE, PAD_LG))
        self.register_i18n(ctk.CTkCheckBox(opts_frame, text=tr("case_print.form_fields", "Formularfelder"), variable=self.include_fields_var), "case_print.form_fields", "Formularfelder").pack(side="left", padx=(PAD_NONE, PAD_LG))
        self.register_i18n(ctk.CTkCheckBox(opts_frame, text=tr("case_print.attachments_end", "Bilder & Anhänge am Ende"), variable=self.include_attachments_var), "case_print.attachments_end", "Bilder & Anhänge am Ende").pack(side="left")

        self.register_i18n(ctk.CTkLabel(main_frame, text=tr("case_print.timeline_lbl", "Zeitleiste / Notizen-Verlauf (einzelne Einträge abwählen):"), font=ctk.CTkFont(weight="bold")), "case_print.timeline_lbl", "Zeitleiste / Notizen-Verlauf (einzelne Einträge abwählen):").pack(anchor="w", pady=(PAD_MD, PAD_SM))

        scroll = ctk.CTkScrollableFrame(main_frame, height=SCROLL_HEIGHT_PRINT_TIMELINE)
        scroll.pack(fill="both", expand=True, pady=(PAD_NONE, PAD_MD + PAD_XS))

        if not self.case.timeline:
            self.register_i18n(ctk.CTkLabel(scroll, text=tr("case_print.no_timeline_notes", "Keine Notizen in der Zeitleiste.")), "case_print.no_timeline_notes", "Keine Notizen in der Zeitleiste.").pack(pady=PAD_MD + PAD_XS)
        else:
            for idx, entry in enumerate(self.case.timeline):
                var = ctk.BooleanVar(value=True)
                self.timeline_vars.append((var, idx))

                formatted_ts = format_german_datetime(entry.timestamp)
                lbl_text = f"[{formatted_ts}] {entry.author}: {entry.note[:CASE_PRINT_NOTE_PREVIEW_LEN]}..."
                ctk.CTkCheckBox(scroll, text=lbl_text, variable=var).pack(anchor="w", pady=PAD_SM - 1, padx=PAD_SM + 1)

        # Action bar
        btn_frame = ctk.CTkFrame(main_frame, fg_color="transparent")
        btn_frame.pack(fill="x", side="bottom", pady=(PAD_MD, PAD_NONE))

        self.register_i18n(ctk.CTkButton(
            btn_frame,
            text=tr("common.cancel", "Abbrechen"),
            fg_color=COLOR_CANCEL_FG,
            hover_color=COLOR_CANCEL_HOVER,
            command=self.safe_destroy,
            width=BTN_WIDTH_ACTION_SM,
        ), "common.cancel", "Abbrechen").pack(side="left")

        self.register_i18n(ctk.CTkButton(
            btn_frame,
            text=tr("ui_buttons.print_pdf", "🖨 PDF-Bericht drucken"),
            fg_color=COLOR_SUCCESS,
            hover_color=COLOR_SUCCESS_HOVER,
            command=self.generate_and_print_pdf,
            width=BTN_WIDTH_PRINT,
        ), "ui_buttons.print_pdf", "🖨 PDF-Bericht drucken").pack(side="right", padx=(PAD_MD, PAD_NONE))

        self.register_i18n(ctk.CTkButton(
            btn_frame,
            text=tr("case_print.html_report_btn", "🌐 HTML-Bericht"),
            fg_color=COLOR_PRIMARY,
            hover_color=COLOR_PRIMARY_HOVER,
            command=self.generate_and_open_html,
            width=BTN_WIDTH_HTML,
        ), "case_print.html_report_btn", "🌐 HTML-Bericht").pack(side="right", padx=(PAD_MD, PAD_NONE))

        self.register_i18n(ctk.CTkButton(
            btn_frame,
            text=tr("case_print.save_btn", "💾 Speichern..."),
            fg_color=COLOR_MUTED_GRAY_FG,
            hover_color=COLOR_MUTED_GRAY_HOVER,
            command=self.generate_and_save_file,
            width=ENTRY_WIDTH_SHORTCUT,
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
        html_file = temp_dir / REPORT_FILENAME_TEMPLATE.format(case_id=self.case.case_id)
        html_file.write_text(html_content, encoding="utf-8")

        webbrowser.open(html_file.as_uri())
        self.safe_destroy()

    def generate_and_print_pdf(self):
        """Generates printable report and automatically triggers the print/Save-to-PDF dialog."""
        html_content = self.build_html_content(auto_print=True)
        temp_dir = Path(tempfile.gettempdir())
        html_file = temp_dir / REPORT_PRINT_FILENAME_TEMPLATE.format(case_id=self.case.case_id)
        html_file.write_text(html_content, encoding="utf-8")

        webbrowser.open(html_file.as_uri())
        self.safe_destroy()

    def generate_and_save_file(self):
        """Prompts user to save the static HTML report file."""
        from services.i18n_service import tr
        file_path = filedialog.asksaveasfilename(
            parent=self,
            title=tr("case_print.save_dialog_title", "Fallbericht speichern"),
            defaultextension=FILE_EXT_HTML,
            initialfile=REPORT_FILENAME_TEMPLATE.format(case_id=self.case.case_id),
            filetypes=get_file_types_html_report(),
        )
        if not file_path:
            return

        html_content = self.build_html_content(auto_print=False)
        Path(file_path).write_text(html_content, encoding="utf-8")
        self.safe_destroy()


