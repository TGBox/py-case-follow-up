"""Compact window to note down a task in a few seconds.

Opened by the global hotkey, usually while another program has focus, so it
is a plain window of its own (not modal, not tied to the main window, which
may be hidden in the tray).
"""

from collections.abc import Callable

import customtkinter as ctk

from constants import (
    ANCHOR_WEST,
    BTN_HEIGHT_ACTION,
    BTN_WIDTH_CANCEL_FOLLOWUP,
    BTN_WIDTH_SAVE_FOLLOWUP,
    COLOR_BTN_CANCEL,
    COLOR_DARKRED,
    COLOR_SUCCESS,
    COLOR_TRANSPARENT,
    COMBO_WIDTH_SM,
    DEFAULT_QUICK_CAPTURE_PRESET,
    FONT_SIZE_SM,
    FONT_WEIGHT_BOLD,
    PAD_LG,
    PAD_MD,
    PAD_NONE,
    PAD_SM,
    PAD_XS,
    QUICK_CAPTURE_DIALOG_SIZE,
    QUICK_CAPTURE_PRESETS,
    QUICK_CAPTURE_TEXTBOX_HEIGHT,
)
from services.i18n_service import tr
from ui.dialogs.base_dialog import BaseDialog

_PRESET_LABELS = {
    "1h": ("quick_capture.preset_1h", "In 1 Stunde"),
    "2h": ("quick_capture.preset_2h", "In 2 Stunden"),
    "today_1630": ("quick_capture.preset_today_1630", "Heute 16:30"),
    "tomorrow_0800": ("quick_capture.preset_tomorrow_0800", "Morgen 08:00"),
    "none": ("quick_capture.preset_none", "Keine Erinnerung"),
}


def _preset_choices() -> list[tuple[str, str]]:
    return [_PRESET_LABELS[preset] for preset in QUICK_CAPTURE_PRESETS]


class QuickCaptureDialog(BaseDialog):
    """Text, optional person and a reminder preset. on_save(text, person, preset) stores the task."""

    def __init__(
        self,
        parent,
        colleagues: list[str],
        initial_text: str,
        on_save: Callable[[str, str, str], None],
    ):
        super().__init__(parent)
        self.colleagues = colleagues
        self.on_save = on_save

        # No parent: a window transient to a hidden main window would be hidden too.
        self.setup_window(
            None,
            tr("quick_capture.title", "⚡ Schnellerfassung"),
            QUICK_CAPTURE_DIALOG_SIZE,
            modal=False,
            title_factory=lambda: tr("quick_capture.title", "⚡ Schnellerfassung"),
        )
        self.create_widgets()
        if initial_text:
            self.text_box.insert("1.0", initial_text)
        self.set_default_action(self.on_click_save)
        self.bind("<Control-Return>", self._on_ctrl_return)
        self.bring_forward()

    def create_widgets(self) -> None:
        main = ctk.CTkFrame(self)
        main.pack(fill="both", expand=True, padx=PAD_LG, pady=PAD_MD)

        self.register_i18n(ctk.CTkLabel(
            main, text=tr("quick_capture.text_label", "Was ist zu tun?"),
            font=ctk.CTkFont(size=FONT_SIZE_SM, weight=FONT_WEIGHT_BOLD), anchor=ANCHOR_WEST,
        ), "quick_capture.text_label", "Was ist zu tun?").pack(fill="x", padx=PAD_LG, pady=(PAD_MD, PAD_XS))
        self.text_box = ctk.CTkTextbox(main, height=QUICK_CAPTURE_TEXTBOX_HEIGHT)
        self.text_box.pack(fill="both", expand=True, padx=PAD_LG, pady=(PAD_NONE, PAD_SM))

        self.register_i18n(ctk.CTkLabel(
            main, text=tr("quick_capture.person_label", "Von / mit wem (optional):"),
            font=ctk.CTkFont(size=FONT_SIZE_SM, weight=FONT_WEIGHT_BOLD), anchor=ANCHOR_WEST,
        ), "quick_capture.person_label", "Von / mit wem (optional):").pack(fill="x", padx=PAD_LG, pady=(PAD_SM, PAD_XS))
        self.person_combo = ctk.CTkComboBox(main, values=self.colleagues or [""])
        self.person_combo.set("")
        self.person_combo.pack(fill="x", padx=PAD_LG, pady=(PAD_NONE, PAD_SM))

        self.register_i18n(ctk.CTkLabel(
            main, text=tr("quick_capture.reminder_label", "Erinnerung:"),
            font=ctk.CTkFont(size=FONT_SIZE_SM, weight=FONT_WEIGHT_BOLD), anchor=ANCHOR_WEST,
        ), "quick_capture.reminder_label", "Erinnerung:").pack(fill="x", padx=PAD_LG, pady=(PAD_SM, PAD_XS))
        self.reminder_combo = ctk.CTkOptionMenu(
            main, values=[tr(key, default) for key, default in _preset_choices()], width=COMBO_WIDTH_SM,
        )
        self.reminder_combo.set(tr(*_PRESET_LABELS[DEFAULT_QUICK_CAPTURE_PRESET]))
        self.reminder_combo.pack(anchor="w", padx=PAD_LG, pady=(PAD_NONE, PAD_SM))

        self.error_label = ctk.CTkLabel(main, text="", text_color=COLOR_DARKRED, anchor=ANCHOR_WEST)
        self.error_label.pack(fill="x", padx=PAD_LG)

        bottom = ctk.CTkFrame(main, fg_color=COLOR_TRANSPARENT)
        bottom.pack(fill="x", padx=PAD_LG, pady=(PAD_SM, PAD_MD), side="bottom")
        self.register_i18n(ctk.CTkButton(
            bottom, text=tr("timeline.edit_save_btn", "💾 Speichern"), command=self.on_click_save,
            fg_color=COLOR_SUCCESS, height=BTN_HEIGHT_ACTION, width=BTN_WIDTH_SAVE_FOLLOWUP,
        ), "timeline.edit_save_btn", "💾 Speichern").pack(side="right", padx=(PAD_SM, PAD_NONE))
        self.register_i18n(ctk.CTkButton(
            bottom, text=tr("common.cancel", "Abbrechen"), command=self.request_close,
            fg_color=COLOR_BTN_CANCEL, height=BTN_HEIGHT_ACTION, width=BTN_WIDTH_CANCEL_FOLLOWUP,
        ), "common.cancel", "Abbrechen").pack(side="left", padx=(PAD_NONE, PAD_SM))
        self.register_i18n(ctk.CTkLabel(
            bottom, text=tr("quick_capture.hint", "Strg+Enter speichert"), font=ctk.CTkFont(size=FONT_SIZE_SM),
        ), "quick_capture.hint", "Strg+Enter speichert").pack(side="left", padx=PAD_SM)

    def refresh_ui_labels(self) -> None:
        super().refresh_ui_labels()
        self.retranslate_choices(self.reminder_combo, _preset_choices())

    def bring_forward(self) -> None:
        """Shows the window above whatever has focus and puts the cursor in the text."""
        try:
            self.deiconify()
            self.lift()
            self.attributes("-topmost", True)
            self.after(300, lambda: self._release_topmost())
            self.focus_force()
            self.text_box.focus_set()
            self.text_box.mark_set("insert", "end-1c")
        except Exception:
            pass

    def _release_topmost(self) -> None:
        try:
            self.attributes("-topmost", False)
        except Exception:
            pass

    def _on_ctrl_return(self, event=None):
        self.on_click_save()
        return "break"

    def on_click_save(self) -> None:
        text = self.text_box.get("1.0", "end-1c").strip()
        if not text:
            self.error_label.configure(text=tr("quick_capture.error_empty", "Bitte einen Text eingeben."))
            return
        preset = QUICK_CAPTURE_PRESETS[self.selected_choice_index(self.reminder_combo)]
        person = self.person_combo.get().strip()
        self.close_dialog()
        self.on_save(text, person, preset)
