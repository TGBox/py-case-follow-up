from datetime import datetime, timedelta
from typing import Callable
import customtkinter as ctk
from models.case import Case
from utils.datetime_utils import now_iso


class FollowupDialog(ctk.CTkToplevel):
    def __init__(
        self,
        parent,
        case: Case,
        on_followup_set: Callable[[str, str], None],
    ):
        super().__init__(parent)
        self.case = case
        self.on_followup_set = on_followup_set

        self.title("🔔 Wiedervorlage & Nachfrage-Erinnerung")
        self.geometry("520x420")
        self.resizable(False, False)

        self.transient(parent)
        self.grab_set()

        self.create_widgets()

    def create_widgets(self):
        # Header
        top_bar = ctk.CTkFrame(self, height=45, corner_radius=0)
        top_bar.pack(fill="x", side="top", padx=10, pady=(10, 5))

        ctk.CTkLabel(
            top_bar,
            text=f"🔔 Wiedervorlage einplanen: {self.case.case_id}",
            font=ctk.CTkFont(size=15, weight="bold")
        ).pack(side="left", padx=10)

        main_frame = ctk.CTkFrame(self)
        main_frame.pack(fill="both", expand=True, padx=15, pady=10)

        ctk.CTkLabel(
            main_frame,
            text="Wann möchten Sie an diesen Fall erinnert werden?",
            font=ctk.CTkFont(size=12, weight="bold")
        ).pack(anchor="w", padx=10, pady=(10, 5))

        # Quick Preset Buttons
        btn_frame = ctk.CTkFrame(main_frame, fg_color="transparent")
        btn_frame.pack(fill="x", padx=10, pady=5)

        ctk.CTkButton(btn_frame, text="+ 1 Tag", width=90, command=lambda: self.set_preset_days(1)).pack(side="left", padx=3)
        ctk.CTkButton(btn_frame, text="+ 2 Tage", width=90, command=lambda: self.set_preset_days(2)).pack(side="left", padx=3)
        ctk.CTkButton(btn_frame, text="+ 3 Tage", width=90, command=lambda: self.set_preset_days(3)).pack(side="left", padx=3)
        ctk.CTkButton(btn_frame, text="+ 1 Woche", width=90, command=lambda: self.set_preset_days(7)).pack(side="left", padx=3)

        # Custom Date Entry
        ctk.CTkLabel(main_frame, text="Erinnerungs-Datum (YYYY-MM-DD):").pack(anchor="w", padx=10, pady=(15, 2))
        self.date_entry = ctk.CTkEntry(main_frame, placeholder_text="YYYY-MM-DD")

        init_date = ""
        if self.case.workflow_status.followup_at:
            init_date = self.case.workflow_status.followup_at.split("T")[0]
        else:
            init_date = (datetime.now() + timedelta(days=2)).strftime("%Y-%m-%d")

        self.date_entry.insert(0, init_date)
        self.date_entry.pack(fill="x", padx=10, pady=(0, 10))

        # Note entry
        ctk.CTkLabel(main_frame, text="Notiz / Nachfrage-Grund (Optional):").pack(anchor="w", padx=10, pady=(5, 2))
        self.note_entry = ctk.CTkEntry(main_frame, placeholder_text="z. B. Beim Entwickler nach dem Stand fragen...")
        if self.case.workflow_status.followup_note:
            self.note_entry.insert(0, self.case.workflow_status.followup_note)
        self.note_entry.pack(fill="x", padx=10, pady=(0, 15))

        # Action Buttons
        bottom_frame = ctk.CTkFrame(main_frame, fg_color="transparent")
        bottom_frame.pack(fill="x", padx=10, pady=10)

        ctk.CTkButton(
            bottom_frame,
            text="💾 Wiedervorlage Speichern",
            command=self.on_save,
            fg_color="forestgreen",
            width=180
        ).pack(side="right", padx=5)

        if self.case.workflow_status.followup_at:
            ctk.CTkButton(
                bottom_frame,
                text="❌ Entfernen",
                command=self.on_clear,
                fg_color="darkred",
                width=110
            ).pack(side="right", padx=5)

        ctk.CTkButton(
            bottom_frame,
            text="Abbrechen",
            command=self.destroy,
            fg_color="gray40",
            width=90
        ).pack(side="left", padx=5)

    def set_preset_days(self, days: int):
        target_dt = datetime.now() + timedelta(days=days)
        self.date_entry.delete(0, "end")
        self.date_entry.insert(0, target_dt.strftime("%Y-%m-%d"))

    def on_save(self):
        val = self.date_entry.get().strip()
        note = self.note_entry.get().strip()
        if val:
            if "T" not in val:
                val += "T09:00:00"
            self.on_followup_set(val, note)
        self.destroy()

    def on_clear(self):
        self.on_followup_set("", "")
        self.destroy()
