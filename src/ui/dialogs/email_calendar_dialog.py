import os
import customtkinter as ctk
from tkinter import filedialog
from typing import Any
from models.case import Case
from services.calendar_email_service import CalendarEmailService


class EmailCalendarDialog(ctk.CTkToplevel):
    """Preview dialog for E-mail drafts and iCalendar (.ics) export."""

    def __init__(
        self,
        parent,
        case: Case,
        calendar_email_service: CalendarEmailService,
        user_name: str = "",
        snippet_service: Any | None = None,
    ):
        super().__init__(parent)
        self.case = case
        self.service = calendar_email_service
        self.user_name = user_name
        self.snippet_service = snippet_service

        self.title(f"✉ E-Mail & 📅 Kalender-Entwurf - Fall {case.case_id}")
        self.geometry("760x660")
        self.minsize(720, 540)

        from utils.ui_utils import center_window, enable_auto_hiding_scrollbar
        center_window(self, 760, 660)

        self.transient(parent)
        self.grab_set()

        self.draft_data = self.service.generate_email_draft(self.case, user_name=self.user_name)
        self.create_widgets()

    def create_widgets(self):
        main_frame = ctk.CTkFrame(self, fg_color="transparent")
        main_frame.pack(fill="both", expand=True, padx=15, pady=15)

        # Header
        hdr_frame = ctk.CTkFrame(main_frame, fg_color="transparent")
        hdr_frame.pack(fill="x", pady=(0, 10))

        ctk.CTkLabel(
            hdr_frame,
            text=f"✉ E-Mail-Entwurf & 📅 Kalender-Export (Fall {self.case.case_id})",
            font=ctk.CTkFont(size=16, weight="bold"),
        ).pack(anchor="w")

        practice_name = self.case.customer.practice_name if self.case.customer else "Unbekannte Praxis"
        deadline_str = self.case.formatted_deadline or "Keine Deadline gesetzt"
        ctk.CTkLabel(
            hdr_frame,
            text=f"Praxis: {practice_name} | Rückruf-Deadline: {deadline_str}",
            font=ctk.CTkFont(size=11),
            text_color="gray",
        ).pack(anchor="w")

        # Scrollable Content Box
        from utils.ui_utils import enable_auto_hiding_scrollbar
        content_scroll = ctk.CTkScrollableFrame(main_frame, fg_color="transparent")
        content_scroll.pack(fill="both", expand=True, pady=(0, 10))
        enable_auto_hiding_scrollbar(content_scroll)

        # Recipient Email
        ctk.CTkLabel(content_scroll, text="Empfänger (E-Mail):", font=ctk.CTkFont(size=12, weight="bold")).pack(anchor="w", pady=(2, 1))
        self.to_entry = ctk.CTkEntry(content_scroll, placeholder_text="praxis@beispiel.de...")
        if self.draft_data.get("to"):
            self.to_entry.insert(0, self.draft_data["to"])
        self.to_entry.pack(fill="x", pady=(0, 8))

        # Subject
        ctk.CTkLabel(content_scroll, text="Betreff:", font=ctk.CTkFont(size=12, weight="bold")).pack(anchor="w", pady=(2, 1))
        self.subject_entry = ctk.CTkEntry(content_scroll, placeholder_text="Betreff eingeben...")
        if self.draft_data.get("subject"):
            self.subject_entry.insert(0, self.draft_data["subject"])
        self.subject_entry.pack(fill="x", pady=(0, 8))

        # Body Textbox Control Row
        body_hdr_row = ctk.CTkFrame(content_scroll, fg_color="transparent")
        body_hdr_row.pack(fill="x", pady=(2, 1))

        ctk.CTkLabel(body_hdr_row, text="E-Mail Nachrichtentext:", font=ctk.CTkFont(size=12, weight="bold")).pack(side="left")

        if self.snippet_service:
            ctk.CTkButton(
                body_hdr_row,
                text="🧩 Textbaustein",
                width=110,
                fg_color="gray30",
                hover_color="darkmagenta",
                command=self.open_snippet_picker,
            ).pack(side="right")

        self.body_textbox = ctk.CTkTextbox(content_scroll, height=200)
        if self.draft_data.get("body"):
            self.body_textbox.insert("1.0", self.draft_data["body"])
        self.body_textbox.pack(fill="x", expand=True, pady=(0, 8))

        # Status Label
        self.status_lbl = ctk.CTkLabel(main_frame, text="", font=ctk.CTkFont(size=11), text_color="dodgerblue")
        self.status_lbl.pack(anchor="w", pady=(0, 5))

        # Action Buttons Container (2 structured rows)
        btn_box = ctk.CTkFrame(main_frame, fg_color="transparent")
        btn_box.pack(fill="x", pady=(8, 0))

        # Row 1: E-Mail Actions
        row1_btns = ctk.CTkFrame(btn_box, fg_color="transparent")
        row1_btns.pack(fill="x", pady=(0, 6))

        ctk.CTkButton(
            row1_btns,
            text="✉ Im Mail-Client öffnen",
            fg_color="dodgerblue",
            hover_color="deepskyblue",
            command=self.on_open_mailto,
            height=32,
        ).pack(side="left", padx=(0, 8))

        ctk.CTkButton(
            row1_btns,
            text="📋 Text in Zwischenablage kopieren",
            fg_color="gray30",
            hover_color="gray40",
            command=self.on_copy_text,
            height=32,
        ).pack(side="left", padx=(0, 8))

        # Row 2: Calendar Actions & Close
        row2_btns = ctk.CTkFrame(btn_box, fg_color="transparent")
        row2_btns.pack(fill="x", pady=(2, 0))

        ctk.CTkButton(
            row2_btns,
            text="📅 .ics Kalenderdatei öffnen",
            fg_color="forestgreen",
            hover_color="darkgreen",
            command=self.on_open_ics,
            height=32,
        ).pack(side="left", padx=(0, 8))

        ctk.CTkButton(
            row2_btns,
            text="💾 .ics Datei speichern...",
            fg_color="gray30",
            hover_color="gray40",
            command=self.on_save_ics,
            height=32,
        ).pack(side="left", padx=(0, 8))

        ctk.CTkButton(
            row2_btns,
            text="Schließen",
            fg_color="gray50",
            hover_color="gray60",
            command=self.destroy,
            width=100,
            height=32,
        ).pack(side="right")

    def open_snippet_picker(self):
        if self.snippet_service:
            from ui.dialogs.snippet_picker_dialog import SnippetPickerDialog
            SnippetPickerDialog(
                self,
                snippet_service=self.snippet_service,
                on_snippet_selected=self.insert_snippet_text,
            )

    def insert_snippet_text(self, text: str):
        if text:
            curr = self.body_textbox.get("1.0", "end-1c")
            sep = "\n\n" if curr.strip() else ""
            self.body_textbox.insert("end", f"{sep}{text}")

    def on_open_mailto(self):
        to = self.to_entry.get().strip()
        subject = self.subject_entry.get().strip()
        body = self.body_textbox.get("1.0", "end-1c").strip()

        self.service.open_mailto_link(to, subject, body)
        self.status_lbl.configure(text="✓ Mail-Client wurde mit dem Entwurf aufgerufen.", text_color="lightgreen")

    def on_copy_text(self):
        body = self.body_textbox.get("1.0", "end-1c").strip()
        self.clipboard_clear()
        self.clipboard_append(body)
        self.status_lbl.configure(text="✓ E-Mail Text wurde in die Zwischenablage kopiert.", text_color="lightgreen")

    def on_open_ics(self):
        ics_path = self.service.generate_ics_file(self.case, user_name=self.user_name)
        self.service.open_ics_file(ics_path)
        self.status_lbl.configure(text=f"✓ Kalendereintrag (.ics) geöffnet: {ics_path.name}", text_color="lightgreen")

    def on_save_ics(self):
        file_path = filedialog.asksaveasfilename(
            title="Kalenderdatei (.ics) speichern",
            initialfile=f"Rueckruf_{self.case.case_id}.ics",
            filetypes=[("iCalendar-Dateien (*.ics)", "*.ics"), ("Alle Dateien", "*.*")],
        )
        if not file_path:
            return

        content = self.service.generate_ics_content(self.case, user_name=self.user_name)
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(content)

        self.status_lbl.configure(text=f"✓ .ics Kalenderdatei gespeichert unter: {os.path.basename(file_path)}", text_color="lightgreen")
