from typing import TYPE_CHECKING, Any
from collections.abc import Callable
import customtkinter as ctk

from ui.dialogs.base_dialog import BaseDialog
from services.i18n_service import tr
from constants import (
    BTN_WIDTH_MD,
    BTN_WIDTH_RECORDER,
    COLOR_DANGER,
    COLOR_LABEL_GRAY60,
    COLOR_MUTED_GRAY_FG,
    COLOR_MUTED_GRAY_HOVER,
    COLOR_NOTE_TEXT,
    COLOR_TEXT_WHITE,
    DEFAULT_VIP_BONUS_POINTS,
    ENTRY_WIDTH_NUMERIC,
    ENTRY_WIDTH_SHORTCUT,
    FONT_SIZE_SUBTITLE,
    HOTKEY_ACTION_LABELS,
    HOTKEY_RECORDER_BUTTON,
    HOTKEY_RECORDER_CANCEL,
    HOTKEY_RECORDER_DIMENSIONS,
    HOTKEY_RECORDER_HEADER,
    HOTKEY_RECORDER_INFO,
    HOTKEY_RECORDER_TITLE,
    LABEL_APP_SHORTCUTS_HEADER,
    LABEL_NO_SNIPPETS,
    LABEL_SNIPPET_SHORTCUTS_HEADER,
    LABEL_WIDTH_VIP,
    PAD_LG,
    PAD_MD,
    PAD_NONE,
    PAD_SM,
    PAD_XS,
    SNIPPET_TITLE_PREVIEW_LEN,
    STATUS_SHORTCUT_CONFLICT,
    STATUS_SHORTCUT_CONFLICT_GENERIC,
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
            ctk.CTkLabel(self, text=tr("hotkey_recorder.header", HOTKEY_RECORDER_HEADER), font=ctk.CTkFont(size=FONT_SIZE_SUBTITLE, weight="bold")),
            "hotkey_recorder.header",
            HOTKEY_RECORDER_HEADER,
        ).pack(pady=(PAD_LG, PAD_SM))
        self.info_lbl = self.register_i18n(
            ctk.CTkLabel(self, text=tr("hotkey_recorder.info", HOTKEY_RECORDER_INFO), text_color=COLOR_NOTE_TEXT),
            "hotkey_recorder.info",
            HOTKEY_RECORDER_INFO,
        )
        self.info_lbl.pack(pady=PAD_SM)

        cancel_btn = self.register_i18n(
            ctk.CTkButton(self, text=tr("hotkey_recorder.cancel", HOTKEY_RECORDER_CANCEL), command=self.destroy, fg_color=COLOR_MUTED_GRAY_FG, hover_color=COLOR_MUTED_GRAY_HOVER, width=BTN_WIDTH_MD),
            "hotkey_recorder.cancel",
            HOTKEY_RECORDER_CANCEL,
        )
        cancel_btn.pack(pady=(PAD_MD, PAD_NONE))

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
        def setup_wiki_section(self, parent_frame: ctk.CTkFrame) -> None: ...

    def setup_scoring_tab(self) -> None:
        from utils.ui_utils import enable_auto_hiding_scrollbar
        scroll = ctk.CTkScrollableFrame(self.tab_scoring, fg_color="transparent")
        scroll.pack(fill="both", expand=True, padx=PAD_SM, pady=PAD_SM)
        enable_auto_hiding_scrollbar(scroll)
        self.scoring_scroll = scroll

        # 2-Column Side-by-Side Container
        cols_container = ctk.CTkFrame(scroll, fg_color="transparent")
        cols_container.pack(fill="both", expand=True, padx=PAD_SM, pady=PAD_SM)
        cols_container.columnconfigure(0, weight=1, uniform="scoring_cols")
        cols_container.columnconfigure(1, weight=1, uniform="scoring_cols")

        left_col = ctk.CTkFrame(cols_container, fg_color="transparent")
        left_col.grid(row=0, column=0, sticky="nsew", padx=(PAD_NONE, PAD_LG))

        right_col = ctk.CTkFrame(cols_container, fg_color="transparent")
        right_col.grid(row=0, column=1, sticky="nsew", padx=(PAD_LG, PAD_NONE))

        # =====================================================================
        # --- LINKE SPALTE: BookStack Wiki Server & Prioritäts-Scoring ---
        # =====================================================================
        if hasattr(self, "setup_wiki_section"):
            self.setup_wiki_section(left_col)

        self.scoring_hdr_lbl = self.register_i18n(
            ctk.CTkLabel(left_col, text=tr("profile.scoring_points_title", "Prioritäts-Scoring Punkte"), font=ctk.CTkFont(size=FONT_SIZE_SUBTITLE, weight="bold")),
            "profile.scoring_points_title",
            "Prioritäts-Scoring Punkte",
        )
        self.scoring_hdr_lbl.pack(anchor="w", pady=(PAD_MD, PAD_SM))

        row4 = ctk.CTkFrame(left_col, fg_color="transparent")
        row4.pack(fill="x", pady=PAD_XS)
        self.register_i18n(
            ctk.CTkLabel(row4, text=tr("profile.vip_bonus_lbl", "VIP-Bonus (Punkte):"), width=LABEL_WIDTH_VIP, anchor="w"),
            "profile.vip_bonus_lbl",
            "VIP-Bonus (Punkte):",
        ).pack(side="left")
        self.vip_bonus_entry = ctk.CTkEntry(row4, width=ENTRY_WIDTH_NUMERIC + 10)
        self.vip_bonus_entry.insert(0, str(self.profile.scoring_matrix.vip_bonus_points))
        self.vip_bonus_entry.pack(side="left", padx=(PAD_MD, PAD_NONE))

        # =====================================================================
        # --- RECHTE SPALTE: App-Aktionen Tastenkürzel & Snippet-Makros ---
        # =====================================================================
        self.app_shortcuts_hdr_lbl = self.register_i18n(
            ctk.CTkLabel(right_col, text=tr("profile.shortcuts_app_header", LABEL_APP_SHORTCUTS_HEADER), font=ctk.CTkFont(size=FONT_SIZE_SUBTITLE, weight="bold")),
            "profile.shortcuts_app_header",
            LABEL_APP_SHORTCUTS_HEADER,
        )
        self.app_shortcuts_hdr_lbl.pack(anchor="w", pady=(PAD_SM, PAD_MD))

        self.shortcut_entries: dict[str, ctk.CTkEntry] = {}
        self.rec_buttons: list[ctk.CTkButton] = []

        for attr_name, label_text in HOTKEY_ACTION_LABELS:
            row = ctk.CTkFrame(right_col, fg_color="transparent")
            row.pack(fill="x", pady=PAD_XS)

            val = getattr(self.profile.shortcuts, attr_name, "")
            entry = ctk.CTkEntry(row, width=ENTRY_WIDTH_SHORTCUT)
            entry.insert(0, val)
            self.shortcut_entries[attr_name] = entry

            rec_btn = self.register_i18n(
                ctk.CTkButton(
                    row,
                    text=tr("hotkey_recorder.button", HOTKEY_RECORDER_BUTTON),
                    width=BTN_WIDTH_RECORDER,
                    fg_color=COLOR_MUTED_GRAY_FG,
                    hover_color=COLOR_MUTED_GRAY_HOVER,
                    text_color=COLOR_TEXT_WHITE,
                    command=lambda e=entry: self.open_hotkey_recorder(e),
                ),
                "hotkey_recorder.button",
                HOTKEY_RECORDER_BUTTON,
            )
            rec_btn.pack(side="right", padx=(PAD_SM, PAD_NONE))
            self.rec_buttons.append(rec_btn)

            entry.pack(side="right", padx=(PAD_SM, PAD_SM))
            ctk.CTkLabel(row, text=label_text, anchor="w").pack(side="left", fill="x", expand=True)

            entry.bind("<KeyRelease>", lambda evt: self.validate_shortcut_conflicts())

        # Textbaustein-Makros (Snippets) direkt unter den App-Shortcuts in der rechten Spalte
        self.snippet_shortcuts_hdr_lbl = self.register_i18n(
            ctk.CTkLabel(right_col, text=tr("profile.shortcuts_snippet_header", LABEL_SNIPPET_SHORTCUTS_HEADER), font=ctk.CTkFont(size=FONT_SIZE_SUBTITLE, weight="bold")),
            "profile.shortcuts_snippet_header",
            LABEL_SNIPPET_SHORTCUTS_HEADER,
        )
        self.snippet_shortcuts_hdr_lbl.pack(anchor="w", pady=(PAD_LG, PAD_MD))

        self.snippet_shortcut_entries: list[tuple[Any, ctk.CTkEntry]] = []
        all_snippets = self.snippet_service.get_all_snippets()

        if not all_snippets:
            self.no_snippets_lbl = self.register_i18n(
                ctk.CTkLabel(right_col, text=tr("profile.no_snippets", LABEL_NO_SNIPPETS), text_color=COLOR_LABEL_GRAY60),
                "profile.no_snippets",
                LABEL_NO_SNIPPETS,
            )
            self.no_snippets_lbl.pack(anchor="w", pady=PAD_XS)
        else:
            for snip in all_snippets:
                s_row = ctk.CTkFrame(right_col, fg_color="transparent")
                s_row.pack(fill="x", pady=PAD_XS)

                s_entry = ctk.CTkEntry(s_row, width=ENTRY_WIDTH_SHORTCUT)
                s_entry.insert(0, snip.shortcut or "")
                self.snippet_shortcut_entries.append((snip, s_entry))

                s_rec_btn = self.register_i18n(
                    ctk.CTkButton(
                        s_row,
                        text=tr("hotkey_recorder.button", HOTKEY_RECORDER_BUTTON),
                        width=BTN_WIDTH_RECORDER,
                        fg_color=COLOR_MUTED_GRAY_FG,
                        hover_color=COLOR_MUTED_GRAY_HOVER,
                        text_color=COLOR_TEXT_WHITE,
                        command=lambda e=s_entry: self.open_hotkey_recorder(e),
                    ),
                    "hotkey_recorder.button",
                    HOTKEY_RECORDER_BUTTON,
                )
                s_rec_btn.pack(side="right", padx=(PAD_SM, PAD_NONE))
                self.rec_buttons.append(s_rec_btn)

                s_entry.pack(side="right", padx=(PAD_SM, PAD_SM))

                title_lbl = ctk.CTkLabel(s_row, text=f"{snip.title[:SNIPPET_TITLE_PREVIEW_LEN]} ({snip.snippet_id}):", anchor="w")
                title_lbl.pack(side="left", fill="x", expand=True)

                s_entry.bind("<KeyRelease>", lambda evt: self.validate_shortcut_conflicts())

        # Conflict Warning Label at the bottom across full width
        self.conflict_warn_lbl = ctk.CTkLabel(scroll, text="", text_color=COLOR_DANGER, font=ctk.CTkFont(weight="bold"))
        self.conflict_warn_lbl.pack(fill="x", pady=(PAD_MD, PAD_SM))

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
            self.conflict_warn_lbl.configure(text=tr("profile.shortcut_conflict", STATUS_SHORTCUT_CONFLICT, dup_str=dup_str))
            return False
        else:
            self.conflict_warn_lbl.configure(text="")
            return True

    def reload_shortcuts_fields(self) -> None:
        sc = getattr(self.profile, "shortcuts", None)
        if sc and hasattr(self, "shortcut_entries"):
            for attr_name, entry in self.shortcut_entries.items():
                val = getattr(sc, attr_name, "")
                entry.delete(0, "end")
                entry.insert(0, val)

        if hasattr(self, "vip_bonus_entry"):
            v_pts = getattr(getattr(self.profile, "scoring_matrix", None), "vip_bonus_points", DEFAULT_VIP_BONUS_POINTS)
            self.vip_bonus_entry.delete(0, "end")
            self.vip_bonus_entry.insert(0, str(v_pts))

        if hasattr(self, "conflict_warn_lbl"):
            self.conflict_warn_lbl.configure(text="")

    def save_shortcuts_settings(self) -> bool:
        if not self.validate_shortcut_conflicts():
            self.status_lbl.configure(text=tr("profile.shortcut_conflict_generic", STATUS_SHORTCUT_CONFLICT_GENERIC), text_color=COLOR_DANGER)
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
        if hasattr(self, "scoring_hdr_lbl"):
            self.scoring_hdr_lbl.configure(text=tr("profile.scoring_points_title", "Prioritäts-Scoring Punkte"))
        if hasattr(self, "no_snippets_lbl"):
            self.no_snippets_lbl.configure(text=tr("profile.no_snippets", LABEL_NO_SNIPPETS))
        if hasattr(self, "rec_buttons"):
            for btn in self.rec_buttons:
                btn.configure(text=tr("hotkey_recorder.button", HOTKEY_RECORDER_BUTTON))
