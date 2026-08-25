import os
import urllib.parse
import webbrowser
import customtkinter as ctk
from typing import Any
from models.case import Case
from services.calendar_email_service import CalendarEmailService


class EmailDraftDialog(ctk.CTkToplevel):
    """Standalone dialog for preparing and dispatching support emails."""

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

        self.title(f"✉ E-Mail verfassen - Fall {case.case_id}")
        self.geometry("740x620")
        self.minsize(680, 500)

        from utils.ui_utils import center_window, enable_auto_hiding_scrollbar
        center_window(self, 740, 620)

        try:
            self.transient(parent)
            self.grab_set()
        except Exception:
            pass

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
            text=f"✉ E-Mail verfassen (Fall {self.case.case_id})",
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

        self.body_textbox = ctk.CTkTextbox(content_scroll, height=220)
        if self.draft_data.get("body"):
            self.body_textbox.insert("1.0", self.draft_data["body"])
        self.body_textbox.pack(fill="x", expand=True, pady=(0, 8))

        # Status Label
        self.status_lbl = ctk.CTkLabel(main_frame, text="", font=ctk.CTkFont(size=11), text_color="dodgerblue")
        self.status_lbl.pack(anchor="w", pady=(0, 5))

        # Action Buttons
        btn_box = ctk.CTkFrame(main_frame, fg_color="transparent")
        btn_box.pack(fill="x", pady=(5, 0))

        ctk.CTkButton(
            btn_box,
            text="✉ In Standard-Mail-App öffnen",
            fg_color="dodgerblue",
            hover_color="deepskyblue",
            command=self.on_open_mailto,
            height=32,
        ).pack(side="left", padx=(0, 8))

        ctk.CTkButton(
            btn_box,
            text="📬 In Outlook übertragen",
            fg_color="royalblue",
            hover_color="blue",
            command=self.on_transfer_to_outlook,
            height=32,
        ).pack(side="left", padx=(0, 8))

        ctk.CTkButton(
            btn_box,
            text="📋 In Zwischenablage kopieren",
            fg_color=("gray75", "gray30"),
            hover_color=("gray65", "gray40"),
            command=self.on_copy_text,
            height=32,
        ).pack(side="left", padx=(0, 8))

        ctk.CTkButton(
            btn_box,
            text="Schließen",
            fg_color=("gray70", "gray40"),
            hover_color=("gray60", "gray50"),
            command=self.destroy,
            width=90,
            height=32,
        ).pack(side="right")

    def open_snippet_picker(self):
        if not self.snippet_service:
            return
        from ui.dialogs.snippet_picker_dialog import SnippetPickerDialog
        SnippetPickerDialog(
            self,
            self.snippet_service,
            on_snippet_selected=self.insert_snippet_text,
        )

    def insert_snippet_text(self, text: str):
        self.body_textbox.insert("insert", text)
        self.status_lbl.configure(text="✓ Textbaustein eingefügt.")

    def on_open_mailto(self):
        to = self.to_entry.get().strip()
        subject = self.subject_entry.get().strip()
        body = self.body_textbox.get("1.0", "end-1c")

        params = {}
        if subject:
            params["subject"] = subject
        if body:
            params["body"] = body

        query_str = urllib.parse.urlencode(params, quote_via=urllib.parse.quote)
        mailto_url = f"mailto:{to}?{query_str}" if to else f"mailto:?{query_str}"

        try:
            webbrowser.open(mailto_url)
            self.status_lbl.configure(text="✓ Standard-Mail-Programm aufgerufen.")
        except Exception as e:
            self.status_lbl.configure(text=f"Fehler beim Öffnen: {e}")

    def on_transfer_to_outlook(self):
        """Transfers the drafted email directly into Microsoft Outlook."""
        to = self.to_entry.get().strip()
        subject = self.subject_entry.get().strip()
        body = self.body_textbox.get("1.0", "end-1c")

        # First attempt: Windows COM automation for Outlook if available
        success = False
        try:
            import win32com.client  # type: ignore
            outlook = win32com.client.Dispatch("Outlook.Application")
            mail = outlook.CreateItem(0)  # 0 = olMailItem
            if to:
                mail.To = to
            if subject:
                mail.Subject = subject
            if body:
                mail.Body = body
            mail.Display(True)
            success = True
            self.status_lbl.configure(text="✓ E-Mail direkt in Microsoft Outlook geöffnet.")
        except Exception:
            pass

        if not success:
            # Fallback: URL Mailto open or protocol
            self.on_open_mailto()
            self.status_lbl.configure(text="✓ E-Mail über Mail-Client aufgerufen.")

    def on_copy_text(self):
        body = self.body_textbox.get("1.0", "end-1c")
        self.clipboard_clear()
        self.clipboard_append(body)
        self.status_lbl.configure(text="✓ Text in die Zwischenablage kopiert.")
