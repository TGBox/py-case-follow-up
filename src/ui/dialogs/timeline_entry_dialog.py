"""Dialog for changing or deleting an existing timeline entry afterwards."""

from collections.abc import Callable
from datetime import datetime

import customtkinter as ctk

from constants import (
    ANCHOR_WEST,
    BTN_HEIGHT_ACTION,
    BTN_WIDTH_CANCEL_FOLLOWUP,
    BTN_WIDTH_CLEAR_FOLLOWUP,
    BTN_WIDTH_SAVE_FOLLOWUP,
    COLOR_BTN_CANCEL,
    COLOR_DARKRED,
    COLOR_SUCCESS,
    COLOR_TRANSPARENT,
    COMBO_WIDTH_SM,
    DATE_PICKER_WIDTH_FOLLOWUP,
    DIALOG_DIMENSIONS,
    DIALOG_MIN_DIMENSIONS,
    DIALOG_TITLES,
    FONT_SIZE_SM,
    FONT_WEIGHT_BOLD,
    PAD_GAP,
    PAD_LG,
    PAD_MD,
    PAD_NONE,
    PAD_SM,
    PAD_XS,
    TEXTBOX_HEIGHT_TIMELINE_EDIT,
)
from enums import CHANNEL_DISPLAY, get_channel_display, get_channel_val_from_display
from models.case import TimelineEntry
from services.i18n_service import tr
from ui.dialogs.base_dialog import BaseDialog
from ui.widgets.date_picker import DatePickerWidget
from utils.datetime_utils import format_german_datetime


class TimelineEntryDialog(BaseDialog):
    """Edits channel, date/time and text of one timeline entry, or deletes it.

    on_save receives (timestamp_dt, channel_value, note_text); the caller owns
    the entry and decides how to store the change. on_delete is only called
    after the user confirmed the deletion.
    """

    def __init__(
        self,
        parent,
        entry: TimelineEntry,
        on_save: Callable[[datetime, str, str], None],
        on_delete: Callable[[], None] | None = None,
    ):
        super().__init__(parent)
        self.entry = entry
        self.on_save = on_save
        self.on_delete = on_delete

        self.setup_window(
            parent,
            DIALOG_TITLES["timeline_edit"],
            DIALOG_DIMENSIONS["timeline_edit"],
            min_size=DIALOG_MIN_DIMENSIONS["timeline_edit"],
            title_factory=lambda: DIALOG_TITLES["timeline_edit"],
        )
        self.create_widgets()
        self.enable_unsaved_guard()

    def create_widgets(self) -> None:
        main_frame = ctk.CTkFrame(self)
        main_frame.pack(fill="both", expand=True, padx=PAD_LG, pady=PAD_MD)

        info_text = tr("timeline.edit_author_info", "Verfasst von: {author}", author=self.entry.author or "-")
        self.register_i18n(
            ctk.CTkLabel(main_frame, text=info_text, font=ctk.CTkFont(size=FONT_SIZE_SM), anchor=ANCHOR_WEST),
            "timeline.edit_author_info", "Verfasst von: {author}", author=self.entry.author or "-",
        ).pack(fill="x", padx=PAD_LG, pady=(PAD_MD, PAD_SM))

        # Channel
        self.register_i18n(ctk.CTkLabel(
            main_frame,
            text=tr("timeline.edit_channel_lbl", "Kanal:"),
            font=ctk.CTkFont(size=FONT_SIZE_SM, weight=FONT_WEIGHT_BOLD),
            anchor=ANCHOR_WEST,
        ), "timeline.edit_channel_lbl", "Kanal:").pack(fill="x", padx=PAD_LG, pady=(PAD_SM, PAD_XS))
        self.channel_combo = ctk.CTkOptionMenu(
            main_frame, values=[get_channel_display(c) for c in CHANNEL_DISPLAY], width=COMBO_WIDTH_SM
        )
        self.channel_combo.set(get_channel_display(self.entry.channel))
        self.channel_combo.pack(anchor="w", padx=PAD_LG, pady=(PAD_NONE, PAD_SM))

        # Date & time - never in the future, a timeline documents what happened.
        self.register_i18n(ctk.CTkLabel(
            main_frame,
            text=tr("timeline.edit_time_lbl", "🕒 Datum & Uhrzeit (TT.MM.JJJJ HH:MM):"),
            font=ctk.CTkFont(size=FONT_SIZE_SM, weight=FONT_WEIGHT_BOLD),
            anchor=ANCHOR_WEST,
        ), "timeline.edit_time_lbl", "🕒 Datum & Uhrzeit (TT.MM.JJJJ HH:MM):").pack(fill="x", padx=PAD_LG, pady=(PAD_SM, PAD_XS))
        self.date_picker = DatePickerWidget(
            main_frame,
            include_time=True,
            initial_value=format_german_datetime(self.entry.timestamp) if self.entry.timestamp else "",
            width=DATE_PICKER_WIDTH_FOLLOWUP,
            time_bound="past",
        )
        self.date_picker.pack(fill="x", padx=PAD_LG, pady=(PAD_NONE, PAD_SM))

        # Note text
        self.register_i18n(ctk.CTkLabel(
            main_frame,
            text=tr("timeline.edit_note_lbl", "📝 Notiz:"),
            font=ctk.CTkFont(size=FONT_SIZE_SM, weight=FONT_WEIGHT_BOLD),
            anchor=ANCHOR_WEST,
        ), "timeline.edit_note_lbl", "📝 Notiz:").pack(fill="x", padx=PAD_LG, pady=(PAD_SM, PAD_XS))
        self.note_textbox = ctk.CTkTextbox(main_frame, height=TEXTBOX_HEIGHT_TIMELINE_EDIT)
        self.note_textbox.insert("1.0", self.entry.note or "")
        self.note_textbox.pack(fill="both", expand=True, padx=PAD_LG, pady=(PAD_NONE, PAD_SM))

        self.error_label = ctk.CTkLabel(main_frame, text="", text_color=COLOR_DARKRED, anchor=ANCHOR_WEST)
        self.error_label.pack(fill="x", padx=PAD_LG)

        # Buttons
        bottom = ctk.CTkFrame(main_frame, fg_color=COLOR_TRANSPARENT)
        bottom.pack(fill="x", padx=PAD_LG, pady=(PAD_GAP, PAD_MD), side="bottom")

        self.register_i18n(ctk.CTkButton(
            bottom,
            text=tr("timeline.edit_save_btn", "💾 Speichern"),
            command=self.on_click_save,
            fg_color=COLOR_SUCCESS,
            height=BTN_HEIGHT_ACTION,
            width=BTN_WIDTH_SAVE_FOLLOWUP,
        ), "timeline.edit_save_btn", "💾 Speichern").pack(side="right", padx=(PAD_SM, PAD_NONE))

        if self.on_delete is not None:
            self.register_i18n(ctk.CTkButton(
                bottom,
                text=tr("timeline.edit_delete_btn", "🗑 Löschen"),
                command=self.on_click_delete,
                fg_color=COLOR_DARKRED,
                height=BTN_HEIGHT_ACTION,
                width=BTN_WIDTH_CLEAR_FOLLOWUP,
            ), "timeline.edit_delete_btn", "🗑 Löschen").pack(side="right", padx=PAD_SM)

        self.register_i18n(ctk.CTkButton(
            bottom,
            text=tr("common.cancel", "Abbrechen"),
            command=self.request_close,
            fg_color=COLOR_BTN_CANCEL,
            height=BTN_HEIGHT_ACTION,
            width=BTN_WIDTH_CANCEL_FOLLOWUP,
        ), "common.cancel", "Abbrechen").pack(side="left", padx=(PAD_NONE, PAD_SM))

    def _show_error(self, text: str) -> None:
        try:
            self.error_label.configure(text=text)
        except Exception:
            pass

    def on_click_save(self) -> None:
        note = self.note_textbox.get("1.0", "end-1c").strip()
        if not note:
            self._show_error(tr("timeline.edit_error_empty", "Die Notiz darf nicht leer sein."))
            return
        dt = self.date_picker.get_datetime()
        if dt is None:
            self._show_error(tr("timeline.edit_error_time", "Bitte ein gültiges Datum mit Uhrzeit eingeben (TT.MM.JJJJ HH:MM)."))
            return
        channel_val = get_channel_val_from_display(self.channel_combo.get())
        self.close_dialog()
        self.on_save(dt, channel_val, note)

    def on_click_delete(self) -> None:
        from ui.dialogs.confirm_dialog import ask_confirmation

        if not ask_confirmation(
            self,
            tr("timeline.delete_confirm", "Diesen Timeline-Eintrag wirklich löschen? Das kann nicht rückgängig gemacht werden."),
            title=tr("timeline.delete_confirm_title", "Eintrag löschen"),
            confirm_text=tr("timeline.edit_delete_btn", "🗑 Löschen"),
        ):
            return
        self.close_dialog()
        if self.on_delete:
            self.on_delete()
