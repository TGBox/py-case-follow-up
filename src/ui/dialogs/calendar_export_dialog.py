import os
import tempfile
import customtkinter as ctk

from ui.dialogs.base_dialog import BaseDialog
from pathlib import Path
from tkinter import filedialog
from models.case import Case
from services.calendar_email_service import CalendarEmailService
from constants import (
    BTN_HEIGHT_LG,
    BTN_WIDTH_CANCEL,
    COLOR_BTN_CANCEL,
    COLOR_BTN_CANCEL_HOVER,
    COLOR_CARD_BG_ALT,
    COLOR_MUTED_GRAY_FG,
    COLOR_MUTED_GRAY_HOVER,
    COLOR_SUCCESS,
    COLOR_SUCCESS_HOVER,
    COLOR_TEXT_GRAY,
    COLOR_TEXT_RED,
    COLOR_WARNING_TEXT,
    CORNER_RADIUS_MD,
    DIALOG_DIMENSIONS,
    DIALOG_MIN_SIZE_CALENDAR_EXPORT,
    DIALOG_TITLES,
    FILE_EXT_ICS,
    FONT_SIZE_BODY,
    FONT_SIZE_HEADER_BAR,
    FONT_SIZE_SM,
    ICS_FILENAME_TEMPLATE_APPOINTMENT,
    PAD_10,
    PAD_15,
    PAD_CONTAINER,
    PAD_MD,
    PAD_NONE,
    PAD_XS,
    TEXTBOX_HEIGHT_CALENDAR_DESC,
    get_file_types_ics,
)


class CalendarExportDialog(BaseDialog):
    """Standalone dialog for generating, previewing, and exporting iCalendar (.ics) entries."""

    def __init__(
        self,
        parent,
        case: Case,
        calendar_email_service: CalendarEmailService,
    ):
        super().__init__(parent)
        self.case = case
        self.service = calendar_email_service

        from services.i18n_service import tr
        w, h = DIALOG_DIMENSIONS["calendar_export"]
        self.setup_window(
            parent,
            f"{DIALOG_TITLES['calendar_export']} - {tr('common.case', 'Fall')} {case.case_id}",
            (w, h),
            min_size=DIALOG_MIN_SIZE_CALENDAR_EXPORT,

            title_factory=lambda: f"{DIALOG_TITLES['calendar_export']} - {tr('common.case', 'Fall')} {case.case_id}",
        )

        self.create_widgets()

    def create_widgets(self):
        from services.i18n_service import tr
        main_frame = ctk.CTkFrame(self, fg_color="transparent")
        main_frame.pack(fill="both", expand=True, padx=PAD_15, pady=PAD_15)

        # Header
        hdr_frame = ctk.CTkFrame(main_frame, fg_color="transparent")
        hdr_frame.pack(fill="x", pady=(PAD_NONE, PAD_10))

        self.register_i18n(ctk.CTkLabel(
            hdr_frame,
            text=tr("calendar_export.header", "📅 Kalendereintrag erstellen (.ics) - Fall {case_id}", case_id=self.case.case_id),
            font=ctk.CTkFont(size=FONT_SIZE_HEADER_BAR, weight="bold"),
        ), "calendar_export.header", "📅 Kalendereintrag erstellen (.ics) - Fall {case_id}", case_id=self.case.case_id).pack(anchor="w")

        practice_name = self.case.customer.practice_name if self.case.customer else tr("common.unknown_practice", "Unbekannte Praxis")
        deadline_str = self.case.formatted_deadline or tr("common.no_deadline_set", "Keine Frist gesetzt")
        followup_str = self.case.formatted_followup or tr("common.no_followup_set", "Keine Wiedervorlage gesetzt")

        self.register_i18n(ctk.CTkLabel(
            hdr_frame,
            text=tr("calendar_export.sub_header", "Praxis: {practice} | Rückruf-Deadline: {deadline}", practice=practice_name, deadline=deadline_str),
            font=ctk.CTkFont(size=FONT_SIZE_SM),
            text_color=COLOR_TEXT_GRAY,
        ), "calendar_export.sub_header", "Praxis: {practice} | Rückruf-Deadline: {deadline}", practice=practice_name, deadline=deadline_str).pack(anchor="w")

        # Info Box with details
        info_box = ctk.CTkFrame(main_frame, fg_color=COLOR_CARD_BG_ALT, corner_radius=CORNER_RADIUS_MD)
        info_box.pack(fill="x", pady=(PAD_NONE, PAD_10), padx=PAD_XS)

        self.register_i18n(ctk.CTkLabel(
            info_box,
            text=tr("calendar_export.subject_line", "📋 Betreff: [{case_id}] {title}", case_id=self.case.case_id, title=self.case.classification.title),
            font=ctk.CTkFont(size=FONT_SIZE_BODY, weight="bold"),
            anchor="w"
        ), "calendar_export.subject_line", "📋 Betreff: [{case_id}] {title}", case_id=self.case.case_id, title=self.case.classification.title).pack(fill="x", padx=PAD_10, pady=(PAD_MD, PAD_XS))
        self.register_i18n(ctk.CTkLabel(
            info_box,
            text=tr("calendar_export.followup_line", "🔔 Wiedervorlage / Fälligkeit: {followup}", followup=followup_str),
            font=ctk.CTkFont(size=FONT_SIZE_SM),
            text_color=COLOR_WARNING_TEXT,
            anchor="w"
        ), "calendar_export.followup_line", "🔔 Wiedervorlage / Fälligkeit: {followup}", followup=followup_str).pack(fill="x", padx=PAD_10, pady=(PAD_NONE, PAD_XS))
        self.register_i18n(ctk.CTkLabel(
            info_box,
            text=tr("calendar_export.deadline_line", "⏱ Frist / Rückruf bis: {deadline}", deadline=deadline_str),
            font=ctk.CTkFont(size=FONT_SIZE_SM),
            anchor="w"
        ), "calendar_export.deadline_line", "⏱ Frist / Rückruf bis: {deadline}", deadline=deadline_str).pack(fill="x", padx=PAD_10, pady=(PAD_NONE, PAD_MD))

        # Description preview
        self.register_i18n(ctk.CTkLabel(main_frame, text=tr("calendar_export.desc_label", "Kalender-Beschreibung / Notiz:"), font=ctk.CTkFont(size=FONT_SIZE_BODY, weight="bold")), "calendar_export.desc_label", "Kalender-Beschreibung / Notiz:").pack(anchor="w", pady=(PAD_XS, PAD_XS))
        self.desc_textbox = ctk.CTkTextbox(main_frame, height=TEXTBOX_HEIGHT_CALENDAR_DESC)
        desc_text = (
            f"Support-Fall {self.case.case_id}: {self.case.classification.title}\n"
            f"Kunde: {practice_name}\n"
            f"Ansprechpartner: {self.case.customer.contact_person or '-'}\n"
            f"Telefon: {self.case.customer.phone or '-'}\n"
        )
        if self.case.workflow_status.followup_note:
            desc_text += f"\nWiedervorlage-Notiz: {self.case.workflow_status.followup_note}\n"
        self.desc_textbox.insert("1.0", desc_text)
        self.desc_textbox.pack(fill="both", expand=True, pady=(PAD_NONE, PAD_10))

        # Status Label
        self.status_lbl = ctk.CTkLabel(main_frame, text="", font=ctk.CTkFont(size=FONT_SIZE_SM), text_color=COLOR_SUCCESS)
        self.status_lbl.pack(anchor="w", pady=(PAD_NONE, PAD_CONTAINER))

        from services.i18n_service import tr

        # Action Buttons
        btn_box = ctk.CTkFrame(main_frame, fg_color="transparent")
        btn_box.pack(fill="x", pady=(PAD_CONTAINER, PAD_NONE))

        self.register_i18n(ctk.CTkButton(
            btn_box,
            text=tr("calendar_export.open_ics", "📅 Direkt im Kalender öffnen"),
            fg_color=COLOR_SUCCESS,
            hover_color=COLOR_SUCCESS_HOVER,
            command=self.on_open_ics,
            height=BTN_HEIGHT_LG,
        ), "calendar_export.open_ics", "📅 Direkt im Kalender öffnen").pack(side="left", padx=(PAD_NONE, PAD_MD))

        self.register_i18n(ctk.CTkButton(
            btn_box,
            text=tr("calendar_export.save_ics", "💾 Als .ics Datei speichern..."),
            fg_color=COLOR_MUTED_GRAY_FG,
            hover_color=COLOR_MUTED_GRAY_HOVER,
            command=self.on_save_ics,
            height=BTN_HEIGHT_LG,
        ), "calendar_export.save_ics", "💾 Als .ics Datei speichern...").pack(side="left")

        self.register_i18n(ctk.CTkButton(
            btn_box,
            text=tr("common.cancel", "Abbrechen"),
            fg_color=COLOR_BTN_CANCEL,
            hover_color=COLOR_BTN_CANCEL_HOVER,
            command=self.destroy,
            width=BTN_WIDTH_CANCEL,
            height=BTN_HEIGHT_LG,
        ), "common.cancel", "Abbrechen").pack(side="right")

    def on_open_ics(self):
        from services.i18n_service import tr
        try:
            ics_content = self.service.generate_ics_content(self.case)
            temp_dir = Path(tempfile.gettempdir())
            temp_file = temp_dir / f"Termin_Fall_{self.case.case_id}.ics"
            temp_file.write_text(ics_content, encoding="utf-8")
            os.startfile(str(temp_file))
            self.status_lbl.configure(text=tr("calendar_export.ics_opened", "✓ Kalenderdatei geöffnet: {filename}", filename=temp_file.name))
        except Exception as e:
            self.status_lbl.configure(text=tr("calendar_export.error_generic", "Fehler: {error}", error=e), text_color=COLOR_TEXT_RED)

    def on_save_ics(self):
        from services.i18n_service import tr
        file_path = filedialog.asksaveasfilename(
            parent=self,
            title=tr("calendar_export.save_dialog_title", "iCalendar-Datei speichern"),
            defaultextension=FILE_EXT_ICS,
            initialfile=ICS_FILENAME_TEMPLATE_APPOINTMENT.format(case_id=self.case.case_id),
            filetypes=get_file_types_ics(),
        )
        if not file_path:
            return

        try:
            ics_content = self.service.generate_ics_content(self.case)
            Path(file_path).write_text(ics_content, encoding="utf-8")
            self.status_lbl.configure(text=tr("calendar_export.ics_saved", "✓ Kalenderdatei gespeichert: {filename}", filename=Path(file_path).name))
        except Exception as e:
            self.status_lbl.configure(text=tr("calendar_export.error_save", "Fehler beim Speichern: {error}", error=e), text_color=COLOR_TEXT_RED)
