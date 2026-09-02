from utils.datetime_utils import format_german_datetime
import customtkinter as ctk
from datetime import timedelta
from typing import Callable
from models.case import Case
from ui.widgets.date_picker import DatePickerWidget
from utils.datetime_utils import format_german_date, parse_german_date, get_local_now
from utils.ui_utils import center_window


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
        self.geometry("500x385")
        self.minsize(460, 350)
        center_window(self, 500, 385)

        self.transient(parent)
        self.grab_set()

        self.create_widgets()

    def create_widgets(self):
        # Header
        top_bar = ctk.CTkFrame(self, height=40, corner_radius=0)
        top_bar.pack(fill="x", side="top", padx=10, pady=(8, 4))

        ctk.CTkLabel(
            top_bar,
            text=f"🔔 Wiedervorlage einplanen: {self.case.case_id}",
            font=ctk.CTkFont(size=14, weight="bold")
        ).pack(side="left", padx=10)

        main_frame = ctk.CTkFrame(self)
        main_frame.pack(fill="both", expand=True, padx=12, pady=(0, 10))

        from services.i18n_service import tr

        ctk.CTkLabel(
            main_frame,
            text=tr("followup.presets_lbl", "⚡ Schnellauswahl / Presets:"),
            font=ctk.CTkFont(size=11, weight="bold"),
            anchor="w"
        ).pack(fill="x", padx=12, pady=(8, 3))

        # Quick Preset Buttons Grid (Uniform sizes for all pill buttons)
        preset_grid = ctk.CTkFrame(main_frame, fg_color="transparent")
        preset_grid.pack(fill="x", padx=10, pady=(0, 6))

        for col in range(4):
            preset_grid.grid_columnconfigure(col, weight=1, uniform="fw_presets")

        presets_row1 = [
            ("+ 1 Std.", lambda: self.set_preset_hours(1)),
            ("+ 2 Std.", lambda: self.set_preset_hours(2)),
            ("Heute 16:30", self.set_preset_today_1630),
            ("Morgen 08:00", self.set_preset_tomorrow_8am),
        ]
        for col_idx, (text, cmd) in enumerate(presets_row1):
            btn = ctk.CTkButton(
                preset_grid,
                text=text,
                height=28,
                corner_radius=12,
                font=ctk.CTkFont(size=11),
                fg_color=("gray75", "gray30"),
                hover_color=("gray65", "gray40"),
                command=cmd,
            )
            btn.grid(row=0, column=col_idx, padx=2, pady=2, sticky="ew")

        presets_row2 = [
            ("+ 1 Tag", lambda: self.set_preset_days(1)),
            ("+ 2 Tage", lambda: self.set_preset_days(2)),
            ("+ 3 Tage", lambda: self.set_preset_days(3)),
            ("+ 1 Woche", lambda: self.set_preset_days(7)),
        ]
        for col_idx, (text, cmd) in enumerate(presets_row2):
            btn = ctk.CTkButton(
                preset_grid,
                text=text,
                height=28,
                corner_radius=12,
                font=ctk.CTkFont(size=11),
                fg_color=("gray75", "gray30"),
                hover_color=("gray65", "gray40"),
                command=cmd,
            )
            btn.grid(row=1, column=col_idx, padx=2, pady=2, sticky="ew")

        # Custom Date Entry using DatePickerWidget
        ctk.CTkLabel(
            main_frame,
            text=tr("followup.date_lbl", "📅 Erinnerungs-Datum & Uhrzeit (TT.MM.JJJJ HH:MM):"),
            font=ctk.CTkFont(size=11, weight="bold"),
            anchor="w"
        ).pack(fill="x", padx=12, pady=(6, 2))
        
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
        self.date_picker.pack(fill="x", padx=12, pady=(0, 6))

        # Note entry
        ctk.CTkLabel(
            main_frame,
            text=tr("followup.note_lbl", "📝 Notiz / Nachfrage-Grund (Optional):"),
            font=ctk.CTkFont(size=11, weight="bold"),
            anchor="w"
        ).pack(fill="x", padx=12, pady=(4, 2))
        self.note_entry = ctk.CTkEntry(main_frame, placeholder_text="z. B. Beim Entwickler nach dem Stand fragen...")
        if self.case.workflow_status.followup_note:
            self.note_entry.insert(0, self.case.workflow_status.followup_note)
        self.note_entry.pack(fill="x", padx=12, pady=(0, 8))

        # Action Buttons
        bottom_frame = ctk.CTkFrame(main_frame, fg_color="transparent")
        bottom_frame.pack(fill="x", padx=12, pady=(4, 8), side="bottom")

        ctk.CTkButton(
            bottom_frame,
            text=tr("followup.save_btn", "💾 Wiedervorlage Speichern"),
            command=self.on_save,
            fg_color="forestgreen",
            height=30,
            width=180
        ).pack(side="right", padx=(4, 0))

        from services.i18n_service import tr

        if self.case.workflow_status.followup_at:
            ctk.CTkButton(
                bottom_frame,
                text=tr("ui_buttons.clear", "❌ Entfernen"),
                command=self.on_clear,
                fg_color="darkred",
                height=30,
                width=100
            ).pack(side="right", padx=4)

        ctk.CTkButton(
            bottom_frame,
            text=tr("common.cancel", "Abbrechen"),
            command=self.safe_destroy,
            fg_color=("gray70", "gray40"),
            height=30,
            width=85
        ).pack(side="left", padx=(0, 4))

    def set_preset_hours(self, hours: int):
        target_dt = get_local_now() + timedelta(hours=hours)
        german_str = format_german_datetime(target_dt)
        self.date_picker.set_date(german_str)

    def set_preset_today_1630(self):
        now = get_local_now()
        german_str = f"{format_german_date(now)} 16:30"
        self.date_picker.set_date(german_str)

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
        self.safe_destroy()
        if iso_val:
            self.on_followup_set(iso_val, note)

    def on_clear(self):
        self.safe_destroy()
        self.on_followup_set("", "")
