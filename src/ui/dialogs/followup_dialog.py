from collections.abc import Callable
from datetime import timedelta
import customtkinter as ctk

from constants import (
    ANCHOR_WEST,
    BTN_HEIGHT_ACTION,
    BTN_HEIGHT_PRESET,
    BTN_WIDTH_CANCEL_FOLLOWUP,
    BTN_WIDTH_CLEAR_FOLLOWUP,
    BTN_WIDTH_SAVE_FOLLOWUP,
    COLOR_BTN_CANCEL,
    COLOR_DARKRED,
    COLOR_PRESET_BTN,
    COLOR_PRESET_BTN_HOVER,
    COLOR_SUCCESS,
    COLOR_TRANSPARENT,
    CORNER_RADIUS_NONE,
    CORNER_RADIUS_PRESET,
    DATE_PICKER_WIDTH_FOLLOWUP,
    DIALOG_MIN_SIZE_FOLLOWUP,
    DIALOG_SIZE_FOLLOWUP,
    ENTRY_START_INDEX,
    FOLLOWUP_DEFAULT_DAYS_AHEAD,
    FOLLOWUP_DEFAULT_TIME,
    FOLLOWUP_DELAY_DESTROY_MS,
    FOLLOWUP_PRESET_COLS,
    FOLLOWUP_PRESET_DAYS_1,
    FOLLOWUP_PRESET_DAYS_2,
    FOLLOWUP_PRESET_DAYS_3,
    FOLLOWUP_PRESET_DAYS_7,
    FOLLOWUP_PRESET_HOURS_1,
    FOLLOWUP_PRESET_HOURS_2,
    FOLLOWUP_PRESET_UNIFORM,
    FOLLOWUP_TIME_0800,
    FOLLOWUP_TIME_1130,
    FOLLOWUP_TIME_1330,
    FOLLOWUP_TIME_1630,
    FONT_SIZE_SM,
    FONT_SIZE_SUBTITLE,
    FONT_WEIGHT_BOLD,
    HEIGHT_TOP_BAR_FOLLOWUP,
    PAD_10,
    PAD_GAP,
    PAD_LG,
    PAD_MD,
    PAD_NONE,
    PAD_SM,
    PAD_XS,
)
from models.case import Case
from services.i18n_service import tr
from ui.dialogs.base_dialog import BaseDialog
from ui.widgets.date_picker import DatePickerWidget
from utils.datetime_utils import (
    format_german_date,
    format_german_datetime,
    get_local_now,
    parse_followup_datetime,
)


class FollowupDialog(BaseDialog):
    def __init__(
        self,
        parent,
        case: Case,
        on_followup_set: Callable[[str, str], None],
    ):
        super().__init__(parent)
        self.case = case
        self.on_followup_set = on_followup_set

        self.setup_window(
            parent,
            tr("dialog_titles.followup", "🔔 Wiedervorlage & Nachfrage-Erinnerung"),
            DIALOG_SIZE_FOLLOWUP,
            min_size=DIALOG_MIN_SIZE_FOLLOWUP,
            title_factory=lambda: tr("dialog_titles.followup", "🔔 Wiedervorlage & Nachfrage-Erinnerung"),
        )

        self.create_widgets()
        # Closing now asks before throwing away a typed follow-up note.
        self.enable_unsaved_guard()

    def create_widgets(self):
        # Header
        top_bar = ctk.CTkFrame(self, height=HEIGHT_TOP_BAR_FOLLOWUP, corner_radius=CORNER_RADIUS_NONE)
        top_bar.pack(fill="x", side="top", padx=PAD_10, pady=(PAD_MD, PAD_SM))

        self.register_i18n(ctk.CTkLabel(
            top_bar,
            text=tr("followup.header", "🔔 Wiedervorlage einplanen: {case_id}", case_id=self.case.case_id),
            font=ctk.CTkFont(size=FONT_SIZE_SUBTITLE, weight=FONT_WEIGHT_BOLD),
        ), "followup.header", "🔔 Wiedervorlage einplanen: {case_id}", case_id=self.case.case_id).pack(side="left", padx=PAD_10)

        main_frame = ctk.CTkFrame(self)
        main_frame.pack(fill="both", expand=True, padx=PAD_LG, pady=(PAD_NONE, PAD_10))

        self.register_i18n(ctk.CTkLabel(
            main_frame,
            text=tr("followup.presets_lbl", "⚡ Schnellauswahl / Presets:"),
            font=ctk.CTkFont(size=FONT_SIZE_SM, weight=FONT_WEIGHT_BOLD),
            anchor=ANCHOR_WEST,
        ), "followup.presets_lbl", "⚡ Schnellauswahl / Presets:").pack(fill="x", padx=PAD_LG, pady=(PAD_MD, PAD_SM - 1))

        # Quick Preset Buttons Grid (Uniform sizes for all pill buttons)
        preset_grid = ctk.CTkFrame(main_frame, fg_color=COLOR_TRANSPARENT)
        preset_grid.pack(fill="x", padx=PAD_10, pady=(PAD_NONE, PAD_GAP))

        for col in range(FOLLOWUP_PRESET_COLS):
            preset_grid.grid_columnconfigure(col, weight=1, uniform=FOLLOWUP_PRESET_UNIFORM)

        presets_row1 = [
            (tr("followup.preset_1h", "+ 1 Std."), lambda: self.set_preset_hours(FOLLOWUP_PRESET_HOURS_1)),
            (tr("followup.preset_2h", "+ 2 Std."), lambda: self.set_preset_hours(FOLLOWUP_PRESET_HOURS_2)),
            (tr("followup.preset_today_1630", "Heute 16:30"), self.set_preset_today_1630),
            (tr("followup.preset_tomorrow_8am", "Morgen 08:00"), self.set_preset_tomorrow_8am),
        ]
        for col_idx, (text, cmd) in enumerate(presets_row1):
            btn = ctk.CTkButton(
                preset_grid,
                text=text,
                height=BTN_HEIGHT_PRESET,
                corner_radius=CORNER_RADIUS_PRESET,
                font=ctk.CTkFont(size=FONT_SIZE_SM),
                fg_color=COLOR_PRESET_BTN,
                hover_color=COLOR_PRESET_BTN_HOVER,
                command=cmd,
            )
            btn.grid(row=0, column=col_idx, padx=PAD_XS, pady=PAD_XS, sticky="ew")

        presets_row2 = [
            (tr("followup.preset_1d", "+ 1 Tag"), lambda: self.set_preset_days(FOLLOWUP_PRESET_DAYS_1)),
            (tr("followup.preset_2d", "+ 2 Tage"), lambda: self.set_preset_days(FOLLOWUP_PRESET_DAYS_2)),
            (tr("followup.preset_3d", "+ 3 Tage"), lambda: self.set_preset_days(FOLLOWUP_PRESET_DAYS_3)),
            (tr("followup.preset_1w", "+ 1 Woche"), lambda: self.set_preset_days(FOLLOWUP_PRESET_DAYS_7)),
        ]
        for col_idx, (text, cmd) in enumerate(presets_row2):
            btn = ctk.CTkButton(
                preset_grid,
                text=text,
                height=BTN_HEIGHT_PRESET,
                corner_radius=CORNER_RADIUS_PRESET,
                font=ctk.CTkFont(size=FONT_SIZE_SM),
                fg_color=COLOR_PRESET_BTN,
                hover_color=COLOR_PRESET_BTN_HOVER,
                command=cmd,
            )
            btn.grid(row=1, column=col_idx, padx=PAD_XS, pady=PAD_XS, sticky="ew")

        # Custom Date Entry using DatePickerWidget
        self.register_i18n(ctk.CTkLabel(
            main_frame,
            text=tr("followup.date_lbl", "📅 Erinnerungs-Datum & Uhrzeit (TT.MM.JJJJ HH:MM):"),
            font=ctk.CTkFont(size=FONT_SIZE_SM, weight=FONT_WEIGHT_BOLD),
            anchor=ANCHOR_WEST,
        ), "followup.date_lbl", "📅 Erinnerungs-Datum & Uhrzeit (TT.MM.JJJJ HH:MM):").pack(fill="x", padx=PAD_LG, pady=(PAD_GAP, PAD_XS))

        init_date = ""
        if self.case.workflow_status.followup_at:
            init_date = self.case.workflow_status.followup_at
        else:
            target_dt = get_local_now() + timedelta(days=FOLLOWUP_DEFAULT_DAYS_AHEAD)
            init_date = f"{format_german_date(target_dt)} {FOLLOWUP_DEFAULT_TIME}"

        self.date_picker = self.register_i18n(DatePickerWidget(
            main_frame,
            placeholder_text=tr("date_picker.placeholder_datetime", "TT.MM.JJJJ 09:00"),
            include_time=True,
            initial_value=init_date,
            width=DATE_PICKER_WIDTH_FOLLOWUP,
        ), "date_picker.placeholder_datetime", "TT.MM.JJJJ 09:00", attr="placeholder_text")
        self.date_picker.pack(fill="x", padx=PAD_LG, pady=(PAD_NONE, PAD_GAP))

        # Note entry
        self.register_i18n(ctk.CTkLabel(
            main_frame,
            text=tr("followup.note_lbl", "📝 Notiz / Nachfrage-Grund (Optional):"),
            font=ctk.CTkFont(size=FONT_SIZE_SM, weight=FONT_WEIGHT_BOLD),
            anchor=ANCHOR_WEST,
        ), "followup.note_lbl", "📝 Notiz / Nachfrage-Grund (Optional):").pack(fill="x", padx=PAD_LG, pady=(PAD_SM, PAD_XS))
        self.note_entry = self.register_i18n(
            ctk.CTkEntry(
                main_frame,
                placeholder_text=tr("followup.note_placeholder", "z. B. Beim Entwickler nach dem Stand fragen..."),
            ),
            "followup.note_placeholder",
            "z. B. Beim Entwickler nach dem Stand fragen...",
            attr="placeholder_text",
        )
        if self.case.workflow_status.followup_note:
            self.note_entry.insert(ENTRY_START_INDEX, self.case.workflow_status.followup_note)
        self.note_entry.pack(fill="x", padx=PAD_LG, pady=(PAD_NONE, PAD_MD))

        # Action Buttons
        bottom_frame = ctk.CTkFrame(main_frame, fg_color=COLOR_TRANSPARENT)
        bottom_frame.pack(fill="x", padx=PAD_LG, pady=(PAD_SM, PAD_MD), side="bottom")

        self.register_i18n(ctk.CTkButton(
            bottom_frame,
            text=tr("followup.save_btn", "Wiedervorlage Speichern"),
            command=self.on_save,
            fg_color=COLOR_SUCCESS,
            height=BTN_HEIGHT_ACTION,
            width=BTN_WIDTH_SAVE_FOLLOWUP,
        ), "followup.save_btn", "Wiedervorlage Speichern").pack(side="right", padx=(PAD_SM, PAD_NONE))

        if self.case.workflow_status.followup_at:
            self.register_i18n(ctk.CTkButton(
                bottom_frame,
                text=tr("ui_buttons.clear", "Entfernen"),
                command=self.on_clear,
                fg_color=COLOR_DARKRED,
                height=BTN_HEIGHT_ACTION,
                width=BTN_WIDTH_CLEAR_FOLLOWUP,
            ), "ui_buttons.clear", "Entfernen").pack(side="right", padx=PAD_SM)

        self.register_i18n(ctk.CTkButton(
            bottom_frame,
            text=tr("common.cancel", "Abbrechen"),
            command=self.safe_destroy,
            fg_color=COLOR_BTN_CANCEL,
            height=BTN_HEIGHT_ACTION,
            width=BTN_WIDTH_CANCEL_FOLLOWUP,
        ), "common.cancel", "Abbrechen").pack(side="left", padx=(PAD_NONE, PAD_SM))

    def set_preset_hours(self, hours: int):
        # If the field below already shows a date/time, add the increment on top of it
        # (so repeated clicks stack up); only fall back to "now" when the field is empty
        # or its content can't be parsed.
        base_dt = parse_followup_datetime(self.date_picker.get()) or get_local_now()
        target_dt = base_dt + timedelta(hours=hours)
        german_str = format_german_datetime(target_dt)
        self.date_picker.set_date(german_str)

    def set_preset_today_1630(self):
        now = get_local_now()
        german_str = f"{format_german_date(now)} {FOLLOWUP_TIME_1630}"
        self.date_picker.set_date(german_str)

    def set_preset_today_before_lunch(self):
        now = get_local_now()
        german_str = f"{format_german_date(now)} {FOLLOWUP_TIME_1130}"
        self.date_picker.set_date(german_str)

    def set_preset_today_after_lunch(self):
        now = get_local_now()
        german_str = f"{format_german_date(now)} {FOLLOWUP_TIME_1330}"
        self.date_picker.set_date(german_str)

    def set_preset_tomorrow_8am(self):
        tmw = get_local_now() + timedelta(days=FOLLOWUP_PRESET_DAYS_1)
        german_str = f"{format_german_date(tmw)} {FOLLOWUP_TIME_0800}"
        self.date_picker.set_date(german_str)

    def set_preset_days(self, days: int):
        target_dt = get_local_now() + timedelta(days=days)
        german_str = f"{format_german_date(target_dt)} {FOLLOWUP_DEFAULT_TIME}"
        self.date_picker.set_date(german_str)

    def safe_destroy(self):
        try:
            self.grab_release()
        except Exception:
            pass
        self.after(FOLLOWUP_DELAY_DESTROY_MS, self._do_destroy)

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

