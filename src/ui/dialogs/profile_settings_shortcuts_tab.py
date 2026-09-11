from typing import TYPE_CHECKING, Any
from collections.abc import Callable
import customtkinter as ctk

from ui.dialogs.base_dialog import BaseDialog
from services.i18n_service import tr
from constants import (
    HOTKEY_RECORDER_TITLE,
    HOTKEY_RECORDER_HEADER,
    HOTKEY_RECORDER_INFO,
    HOTKEY_RECORDER_CANCEL,
    HOTKEY_RECORDER_DIMENSIONS,
    HOTKEY_RECORDER_BUTTON,
    HOTKEY_ACTION_LABELS,
    STATUS_SHORTCUT_CONFLICT,
    STATUS_SHORTCUT_CONFLICT_GENERIC,
    LABEL_APP_SHORTCUTS_HEADER,
    LABEL_SNIPPET_SHORTCUTS_HEADER,
    LABEL_NO_SNIPPETS,
)


class HotkeyRecorderDialog(BaseDialog):
    """Interactive modal dialog to capture pressed hotkeys and key combinations."""

    def __init__(self, parent, on_recorded: Callable[[str], None]):
        super().__init__(parent)
        self.on_recorded = on_recorded
        w, h = HOTKEY_RECORDER_DIMENSIONS
        self.setup_window(
            parent,
            tr("hotkey_recorder.title", HOTKEY_RECORDER_TITLE),
            (w, h),
            resizable=False,
            title_factory=lambda: tr("hotkey_recorder.title", HOTKEY_RECORDER_TITLE),
        )

        self.register_i18n(
            ctk.CTkLabel(self, text=tr("hotkey_recorder.header", HOTKEY_RECORDER_HEADER), font=ctk.CTkFont(size=14, weight="bold")),
            "hotkey_recorder.header",
            HOTKEY_RECORDER_HEADER,
        ).pack(pady=(15, 5))
        self.info_lbl = self.register_i18n(
            ctk.CTkLabel(self, text=tr("hotkey_recorder.info", HOTKEY_RECORDER_INFO), text_color=("gray30", "gray70")),
            "hotkey_recorder.info",
            HOTKEY_RECORDER_INFO,
        )
        self.info_lbl.pack(pady=5)

        cancel_btn = self.register_i18n(
            ctk.CTkButton(self, text=tr("hotkey_recorder.cancel", HOTKEY_RECORDER_CANCEL), command=self.destroy, fg_color="gray40", width=120),
            "hotkey_recorder.cancel",
            HOTKEY_RECORDER_CANCEL,
        )
        cancel_btn.pack(pady=(10, 0))

        self.bind("<KeyPress>", self.on_key_press)
        self.focus_set()

    def on_key_press(self, event):
        keysym = event.keysym
        if keysym == "Escape":
            self.destroy()
            return

        if keysym in ("Control_L", "Control_R", "Alt_L", "Alt_R", "Shift_L", "Shift_R", "Win_L", "Win_R"):
            return

        state = event.state
        mods = []
        if state & 0x0004:
            mods.append("Control")
        if state & 0x0001:
            mods.append("Shift")
        if state & 0x20000 or state & 0x0008 or keysym.startswith("Alt"):
            mods.append("Alt")

        key_name = keysym
        if len(key_name) == 1:
            key_name = key_name.lower()

        if mods:
            formatted = f"<{'--'.join(mods + [key_name])}>".replace("--", "-")
        else:
            formatted = f"<{key_name}>" if len(key_name) > 1 else key_name

        self.on_recorded(formatted)
        self.destroy()


class ShortcutsSettingsTabMixin:
    """Mixin for keyboard shortcuts, snippet macros, and VIP scoring points."""

    if TYPE_CHECKING:
        tab_scoring: ctk.CTkFrame
        profile: Any
        storage_service: Any
        snippet_service: Any
        status_lbl: ctk.CTkLabel
        on_profile_updated: Callable[[], None] | None
        register_i18n: Callable[..., Any]

    def setup_scoring_tab(self) -> None:
        scroll = ctk.CTkScrollableFrame(self.tab_scoring, fg_color="transparent")
        scroll.pack(fill="both", expand=True, padx=5, pady=5)

        self.app_shortcuts_hdr_lbl = self.register_i18n(
            ctk.CTkLabel(scroll, text=tr("profile.shortcuts_app_header", LABEL_APP_SHORTCUTS_HEADER), font=ctk.CTkFont(size=14, weight="bold")),
            "profile.shortcuts_app_header",
            LABEL_APP_SHORTCUTS_HEADER,
        )
        self.app_shortcuts_hdr_lbl.pack(anchor="w", pady=(5, 5))

        self.shortcut_entries: dict[str, ctk.CTkEntry] = {}
        self.rec_buttons: list[ctk.CTkButton] = []

        for attr_name, label_text in HOTKEY_ACTION_LABELS:
            row = ctk.CTkFrame(scroll, fg_color="transparent")
            row.pack(fill="x", pady=2)
            ctk.CTkLabel(row, text=label_text, width=180, anchor="w").pack(side="left")

            val = getattr(self.profile.shortcuts, attr_name, "")
            entry = ctk.CTkEntry(row, width=140)
            entry.insert(0, val)
            entry.pack(side="left", padx=(5, 5))
            self.shortcut_entries[attr_name] = entry

            rec_btn = self.register_i18n(
                ctk.CTkButton(
                    row,
                    text=tr("hotkey_recorder.button", HOTKEY_RECORDER_BUTTON),
                    width=120,
                    fg_color=("gray75", "gray30"),
                    hover_color=("gray65", "gray40"),
                    command=lambda e=entry: self.open_hotkey_recorder(e),
                ),
                "hotkey_recorder.button",
                HOTKEY_RECORDER_BUTTON,
            )
            rec_btn.pack(side="left")
            self.rec_buttons.append(rec_btn)

            entry.bind("<KeyRelease>", lambda evt: self.validate_shortcut_conflicts())

        # --- Text-Makros (Snippets) Section ---
        self.snippet_shortcuts_hdr_lbl = self.register_i18n(
            ctk.CTkLabel(scroll, text=tr("profile.shortcuts_snippet_header", LABEL_SNIPPET_SHORTCUTS_HEADER), font=ctk.CTkFont(size=14, weight="bold")),
            "profile.shortcuts_snippet_header",
            LABEL_SNIPPET_SHORTCUTS_HEADER,
        )
        self.snippet_shortcuts_hdr_lbl.pack(anchor="w", pady=(20, 5))

        self.snippet_shortcut_entries: list[tuple[Any, ctk.CTkEntry]] = []
        all_snippets = self.snippet_service.get_all_snippets()

        if not all_snippets:
            self.no_snippets_lbl = self.register_i18n(
                ctk.CTkLabel(scroll, text=tr("profile.no_snippets", LABEL_NO_SNIPPETS), text_color="gray60"),
                "profile.no_snippets",
                LABEL_NO_SNIPPETS,
            )
            self.no_snippets_lbl.pack(anchor="w", pady=2)
        else:
            for snip in all_snippets:
                s_row = ctk.CTkFrame(scroll, fg_color="transparent")
                s_row.pack(fill="x", pady=2)

                title_lbl = ctk.CTkLabel(s_row, text=f"{snip.title[:30]} ({snip.snippet_id}):", width=220, anchor="w")
                title_lbl.pack(side="left")

                s_entry = ctk.CTkEntry(s_row, width=140)
                s_entry.insert(0, snip.shortcut or "")
                s_entry.pack(side="left", padx=(5, 5))
                self.snippet_shortcut_entries.append((snip, s_entry))

                s_rec_btn = self.register_i18n(
                    ctk.CTkButton(
                        s_row,
                        text=tr("hotkey_recorder.button", HOTKEY_RECORDER_BUTTON),
                        width=120,
                        fg_color=("gray75", "gray30"),
                        hover_color=("gray65", "gray40"),
                        command=lambda e=s_entry: self.open_hotkey_recorder(e),
                    ),
                    "hotkey_recorder.button",
                    HOTKEY_RECORDER_BUTTON,
                )
                s_rec_btn.pack(side="left")
                self.rec_buttons.append(s_rec_btn)

                s_entry.bind("<KeyRelease>", lambda evt: self.validate_shortcut_conflicts())

        # Conflict Warning Label
        self.conflict_warn_lbl = ctk.CTkLabel(scroll, text="", text_color="red", font=ctk.CTkFont(weight="bold"))
        self.conflict_warn_lbl.pack(fill="x", pady=(5, 5))

        # --- Prioritäts-Scoring Section ---
        self.register_i18n(
            ctk.CTkLabel(scroll, text=tr("profile.scoring_points_title", "Prioritäts-Scoring Punkte"), font=ctk.CTkFont(size=14, weight="bold")),
            "profile.scoring_points_title",
            "Prioritäts-Scoring Punkte",
        ).pack(anchor="w", pady=(15, 5))

        row4 = ctk.CTkFrame(scroll, fg_color="transparent")
        row4.pack(fill="x", pady=3)
        self.register_i18n(
            ctk.CTkLabel(row4, text=tr("profile.vip_bonus_lbl", "VIP-Bonus (Punkte):")),
            "profile.vip_bonus_lbl",
            "VIP-Bonus (Punkte):",
        ).pack(side="left")
        self.vip_bonus_entry = ctk.CTkEntry(row4, width=80)
        self.vip_bonus_entry.insert(0, str(self.profile.scoring_matrix.vip_bonus_points))
        self.vip_bonus_entry.pack(side="right")

    def setup_shortcuts_tab(self) -> None:
        """Alias for setup_scoring_tab."""
        self.setup_scoring_tab()

    def open_hotkey_recorder(self, target_entry: ctk.CTkEntry) -> None:
        def on_recorded(key_str: str):
            target_entry.delete(0, "end")
            target_entry.insert(0, key_str)
            self.validate_shortcut_conflicts()

        HotkeyRecorderDialog(self, on_recorded)

    def validate_shortcut_conflicts(self) -> bool:
        keys = []
        for entry in self.shortcut_entries.values():
            val = entry.get().strip()
            if val:
                keys.append(val)
        for _, entry in self.snippet_shortcut_entries:
            val = entry.get().strip()
            if val:
                keys.append(val)

        duplicates = set([k for k in keys if keys.count(k) > 1])
        if duplicates:
            dup_str = ", ".join(duplicates)
            self.conflict_warn_lbl.configure(text=STATUS_SHORTCUT_CONFLICT.format(dup_str=dup_str))
            return False
        else:
            self.conflict_warn_lbl.configure(text="")
            return True

    def save_shortcuts_settings(self) -> bool:
        if not self.validate_shortcut_conflicts():
            self.status_lbl.configure(text=STATUS_SHORTCUT_CONFLICT_GENERIC, text_color="red")
            return False

        for attr_name, entry in self.shortcut_entries.items():
            setattr(self.profile.shortcuts, attr_name, entry.get().strip())

        for snip, entry in self.snippet_shortcut_entries:
            snip.shortcut = entry.get().strip()
            self.snippet_service.add_or_update_snippet(snip)

        try:
            self.profile.scoring_matrix.vip_bonus_points = int(self.vip_bonus_entry.get().strip())
        except ValueError:
            pass
        return True

    def refresh_shortcuts_tab_labels(self) -> None:
        if hasattr(self, "app_shortcuts_hdr_lbl"):
            self.app_shortcuts_hdr_lbl.configure(text=tr("profile.shortcuts_app_header", LABEL_APP_SHORTCUTS_HEADER))
        if hasattr(self, "snippet_shortcuts_hdr_lbl"):
            self.snippet_shortcuts_hdr_lbl.configure(text=tr("profile.shortcuts_snippet_header", LABEL_SNIPPET_SHORTCUTS_HEADER))
        if hasattr(self, "no_snippets_lbl"):
            self.no_snippets_lbl.configure(text=tr("profile.no_snippets", LABEL_NO_SNIPPETS))
        if hasattr(self, "rec_buttons"):
            for btn in self.rec_buttons:
                btn.configure(text=tr("hotkey_recorder.button", HOTKEY_RECORDER_BUTTON))
