import os
import tempfile
import customtkinter as ctk
from pathlib import Path
from tkinter import filedialog
from models.case import Case
from services.calendar_email_service import CalendarEmailService
from utils.datetime_utils import format_german_datetime
from constants import DIALOG_DIMENSIONS, DIALOG_TITLES


class CalendarExportDialog(ctk.CTkToplevel):
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

        w, h = DIALOG_DIMENSIONS["calendar_export"]
        self.title(f"{DIALOG_TITLES['calendar_export']} - Fall {case.case_id}")
        self.geometry(f"{w}x{h}")
        self.minsize(580, 440)

        from utils.ui_utils import center_window
        center_window(self, w, h)

        try:
            self.transient(parent)
            self.grab_set()
        except Exception:
            pass

        self.create_widgets()

    def create_widgets(self):
        main_frame = ctk.CTkFrame(self, fg_color="transparent")
        main_frame.pack(fill="both", expand=True, padx=15, pady=15)

        # Header
        hdr_frame = ctk.CTkFrame(main_frame, fg_color="transparent")
        hdr_frame.pack(fill="x", pady=(0, 10))

        ctk.CTkLabel(
            hdr_frame,
            text=f"📅 Kalendereintrag erstellen (.ics) - Fall {self.case.case_id}",
            font=ctk.CTkFont(size=16, weight="bold"),
        ).pack(anchor="w")

        practice_name = self.case.customer.practice_name if self.case.customer else "Unbekannte Praxis"
        deadline_str = self.case.formatted_deadline or "Keine Frist gesetzt"
        followup_str = self.case.formatted_followup or "Keine Wiedervorlage gesetzt"

        ctk.CTkLabel(
            hdr_frame,
            text=f"Praxis: {practice_name} | Rückruf-Deadline: {deadline_str}",
            font=ctk.CTkFont(size=11),
            text_color="gray",
        ).pack(anchor="w")

        # Info Box with details
        info_box = ctk.CTkFrame(main_frame, fg_color=("gray85", "gray20"), corner_radius=6)
        info_box.pack(fill="x", pady=(0, 10), padx=2)

        ctk.CTkLabel(info_box, text=f"📋 Betreff: [{self.case.case_id}] {self.case.classification.title}", font=ctk.CTkFont(size=12, weight="bold"), anchor="w").pack(fill="x", padx=10, pady=(8, 2))
        ctk.CTkLabel(info_box, text=f"🔔 Wiedervorlage / Fälligkeit: {followup_str}", font=ctk.CTkFont(size=11), text_color="darkorange", anchor="w").pack(fill="x", padx=10, pady=(0, 2))
        ctk.CTkLabel(info_box, text=f"⏱ Frist / Rückruf bis: {deadline_str}", font=ctk.CTkFont(size=11), anchor="w").pack(fill="x", padx=10, pady=(0, 8))

        # Description preview
        ctk.CTkLabel(main_frame, text="Kalender-Beschreibung / Notiz:", font=ctk.CTkFont(size=12, weight="bold")).pack(anchor="w", pady=(2, 2))
        self.desc_textbox = ctk.CTkTextbox(main_frame, height=140)
        desc_text = (
            f"Support-Fall {self.case.case_id}: {self.case.classification.title}\n"
            f"Kunde: {practice_name}\n"
            f"Ansprechpartner: {self.case.customer.contact_person or '-'}\n"
            f"Telefon: {self.case.customer.phone or '-'}\n"
        )
        if self.case.workflow_status.followup_note:
            desc_text += f"\nWiedervorlage-Notiz: {self.case.workflow_status.followup_note}\n"
        self.desc_textbox.insert("1.0", desc_text)
        self.desc_textbox.pack(fill="both", expand=True, pady=(0, 10))

        # Status Label
        self.status_lbl = ctk.CTkLabel(main_frame, text="", font=ctk.CTkFont(size=11), text_color="forestgreen")
        self.status_lbl.pack(anchor="w", pady=(0, 5))

        from services.i18n_service import tr

        # Action Buttons
        btn_box = ctk.CTkFrame(main_frame, fg_color="transparent")
        btn_box.pack(fill="x", pady=(5, 0))

        ctk.CTkButton(
            btn_box,
            text=tr("calendar_export.open_ics", "📅 Direkt im Kalender öffnen"),
            fg_color="forestgreen",
            hover_color="darkgreen",
            command=self.on_open_ics,
            height=32,
        ).pack(side="left", padx=(0, 8))

        ctk.CTkButton(
            btn_box,
            text=tr("calendar_export.save_ics", "💾 Als .ics Datei speichern..."),
            fg_color=("gray75", "gray30"),
            hover_color=("gray65", "gray40"),
            command=self.on_save_ics,
            height=32,
        ).pack(side="left")

        ctk.CTkButton(
            btn_box,
            text=tr("common.cancel", "Abbrechen"),
            fg_color=("gray70", "gray40"),
            hover_color=("gray60", "gray50"),
            command=self.destroy,
            width=90,
            height=32,
        ).pack(side="right")

    def on_open_ics(self):
        try:
            ics_content = self.service.generate_ics_content(self.case)
            temp_dir = Path(tempfile.gettempdir())
            temp_file = temp_dir / f"Termin_Fall_{self.case.case_id}.ics"
            temp_file.write_text(ics_content, encoding="utf-8")
            os.startfile(str(temp_file))
            self.status_lbl.configure(text=f"✓ Kalenderdatei geöffnet: {temp_file.name}")
        except Exception as e:
            self.status_lbl.configure(text=f"Fehler: {e}", text_color="red")

    def on_save_ics(self):
        file_path = filedialog.asksaveasfilename(
            parent=self,
            title="iCalendar-Datei speichern",
            defaultextension=".ics",
            initialfile=f"Termin_Fall_{self.case.case_id}.ics",
            filetypes=[("iCalendar Datei", "*.ics"), ("Alle Dateien", "*.*")],
        )
        if not file_path:
            return

        try:
            ics_content = self.service.generate_ics_content(self.case)
            Path(file_path).write_text(ics_content, encoding="utf-8")
            self.status_lbl.configure(text=f"✓ Kalenderdatei gespeichert: {Path(file_path).name}")
        except Exception as e:
            self.status_lbl.configure(text=f"Fehler beim Speichern: {e}", text_color="red")
