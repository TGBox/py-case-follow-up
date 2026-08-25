import customtkinter as ctk
from datetime import timedelta
from typing import Callable
from models.case import Case
from ui.widgets.date_picker import DatePickerWidget
from utils.datetime_utils import format_german_date, parse_german_date, get_local_now


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
        self.geometry("580x500")
        self.minsize(520, 440)
        from utils.ui_utils import center_window
        center_window(self, 580, 500)

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

        # Quick Preset Buttons Rows
        btn_frame1 = ctk.CTkFrame(main_frame, fg_color="transparent")
        btn_frame1.pack(fill="x", padx=10, pady=2)

        ctk.CTkButton(btn_frame1, text="Heute 11:30 (vor Mittag)", width=155, command=self.set_preset_today_before_lunch, fg_color=("gray75", "gray30"), hover_color=("gray65", "gray40")).pack(side="left", padx=2)
        ctk.CTkButton(btn_frame1, text="Heute 13:30 (nach Mittag)", width=155, command=self.set_preset_today_after_lunch, fg_color=("gray75", "gray30"), hover_color=("gray65", "gray40")).pack(side="left", padx=2)
        ctk.CTkButton(btn_frame1, text="Morgen 08:00 Uhr", width=140, command=self.set_preset_tomorrow_8am, fg_color=("gray75", "gray30"), hover_color=("gray65", "gray40")).pack(side="left", padx=2)

        btn_frame2 = ctk.CTkFrame(main_frame, fg_color="transparent")
        btn_frame2.pack(fill="x", padx=10, pady=(2, 5))

        ctk.CTkButton(btn_frame2, text="+ 1 Tag", width=95, command=lambda: self.set_preset_days(1), fg_color=("gray75", "gray30"), hover_color=("gray65", "gray40")).pack(side="left", padx=2)
        ctk.CTkButton(btn_frame2, text="+ 2 Tage", width=95, command=lambda: self.set_preset_days(2), fg_color=("gray75", "gray30"), hover_color=("gray65", "gray40")).pack(side="left", padx=2)
        ctk.CTkButton(btn_frame2, text="+ 3 Tage", width=95, command=lambda: self.set_preset_days(3), fg_color=("gray75", "gray30"), hover_color=("gray65", "gray40")).pack(side="left", padx=2)
        ctk.CTkButton(btn_frame2, text="+ 1 Woche", width=105, command=lambda: self.set_preset_days(7), fg_color=("gray75", "gray30"), hover_color=("gray65", "gray40")).pack(side="left", padx=2)

        # Custom Date Entry using DatePickerWidget
        ctk.CTkLabel(main_frame, text="Erinnerungs-Datum & Uhrzeit (TT.MM.JJJJ HH:MM):").pack(anchor="w", padx=10, pady=(15, 2))
        
        init_date = ""
        if self.case.workflow_status.followup_at:
            init_date = self.case.workflow_status.followup_at
        else:
            target_dt = get_local_now() + timedelta(days=2)
            init_date = format_german_date(target_dt) + " 09:00"

        self.date_picker = DatePickerWidget(
            main_frame,
            placeholder_text="TT.MM.JJJJ 09:00",
            include_time=True,
            initial_value=init_date,
            width=260,
        )
        self.date_picker.pack(fill="x", padx=10, pady=(0, 10))

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
            command=self.safe_destroy,
            fg_color=("gray70", "gray40"),
            width=90
        ).pack(side="left", padx=5)

    def set_preset_today_before_lunch(self):
        now = get_local_now()
        german_str = f"{format_german_date(now)} 11:30"
        self.date_picker.set_date(german_str)

    def set_preset_today_after_lunch(self):
        now = get_local_now()
        german_str = f"{format_german_date(now)} 13:30"
        self.date_picker.set_date(german_str)

    def set_preset_tomorrow_8am(self):
        tmw = get_local_now() + timedelta(days=1)
        german_str = f"{format_german_date(tmw)} 08:00"
        self.date_picker.set_date(german_str)

    def set_preset_days(self, days: int):
        target_dt = get_local_now() + timedelta(days=days)
        german_str = format_german_date(target_dt) + " 09:00"
        self.date_picker.set_date(german_str)

    def safe_destroy(self):
        try:
            self.grab_release()
        except Exception:
            pass
        self.after(1, self._do_destroy)

    def _do_destroy(self):
        try:
            self.destroy()
        except Exception:
            pass

    def on_save(self):
        iso_val = self.date_picker.get_iso()
        note = self.note_entry.get().strip()
        if iso_val:
            self.on_followup_set(iso_val, note)
        self.safe_destroy()

    def on_clear(self):
        self.on_followup_set("", "")
        self.safe_destroy()
