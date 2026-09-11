from typing import Any
from collections.abc import Callable
import customtkinter as ctk

from constants import DIALOG_DIMENSIONS, DIALOG_TITLES
from models.profile import UserProfile
from services.i18n_service import tr
from services.storage_service import StorageService
from ui.dialogs.base_dialog import BaseDialog
from ui.dialogs.profile_settings_ai_tab import AiSettingsTabMixin
from ui.dialogs.profile_settings_paths_tab import PathsSettingsTabMixin
from ui.dialogs.profile_settings_shortcuts_tab import ShortcutsSettingsTabMixin, HotkeyRecorderDialog
from ui.dialogs.profile_settings_ui_tab import (
    UiSettingsTabMixin,
    FONT_SCALE_OPTIONS,
    get_font_scale_display,
    get_font_scale_val_from_display,
)
from ui.dialogs.profile_settings_user_tab import UserSettingsTabMixin
from ui.dialogs.profile_settings_wiki_tab import WikiSettingsTabMixin


class ProfileSettingsDialog(
    UserSettingsTabMixin,
    UiSettingsTabMixin,
    ShortcutsSettingsTabMixin,
    AiSettingsTabMixin,
    WikiSettingsTabMixin,
    PathsSettingsTabMixin,
    BaseDialog,
):
    def __init__(
        self,
        parent,
        profile: UserProfile,
        storage_service: StorageService,
        on_profile_updated: Callable[[], None] | None = None,
    ):
        super().__init__(parent)
        self.profile = profile
        self.storage_service = storage_service
        self.on_profile_updated = on_profile_updated

        from services.snippet_service import SnippetService
        self.snippet_service = getattr(parent, "snippet_service", None) or SnippetService(self.storage_service.config.workspace_dir)

        w, h = DIALOG_DIMENSIONS["profile_settings"]
        self.setup_window(
            parent,
            tr("profile.title", DIALOG_TITLES["profile_settings"]),
            (w, h),
            min_size=(920, 780),
            title_factory=lambda: tr("profile.title", DIALOG_TITLES["profile_settings"]),
        )

        self._initial_font_scale = getattr(self.profile.ui_settings, "font_scale", 1.0)
        self._saved = False

        self.create_widgets()

    def create_widgets(self) -> None:
        # Top Header
        top_bar = ctk.CTkFrame(self, height=45, corner_radius=0)
        top_bar.pack(fill="x", side="top", padx=10, pady=(10, 5))

        self.top_header_lbl = self.register_i18n(
            ctk.CTkLabel(top_bar, text=tr("profile.header", "⚙ Profil & Anwendungseinstellungen"), font=ctk.CTkFont(size=16, weight="bold")),
            "profile.header",
            "⚙ Profil & Anwendungseinstellungen",
        )
        self.top_header_lbl.pack(side="left", padx=10)

        # Tabview
        self.tabview = ctk.CTkTabview(self)
        self.tabview.pack(fill="both", expand=True, padx=10, pady=(5, 10))

        self._tab_keys = [
            ("tab_user", "profile.tab_user", "👤 Benutzerprofil"),
            ("tab_paths", "profile.tab_paths", "📁 Speicherort & Datenexport"),
            ("tab_wiki", "profile.tab_wiki", "📚 BookStack Wiki"),
            ("tab_ai", "profile.tab_ai", "🤖 KI & NLP"),
            ("tab_scoring", "profile.tab_shortcuts", "⌨ Tastenkürzel & Scoring"),
        ]
        self._tab_name_map = {}
        for tab_id, key, default in self._tab_keys:
            orig_t = tr(key, default)
            self._tab_name_map[tab_id] = orig_t

        self.tab_user = self.tabview.add(self._tab_name_map["tab_user"])
        self.tab_paths = self.tabview.add(self._tab_name_map["tab_paths"])
        self.tab_wiki = self.tabview.add(self._tab_name_map["tab_wiki"])
        self.tab_ai = self.tabview.add(self._tab_name_map["tab_ai"])
        self.tab_scoring = self.tabview.add(self._tab_name_map["tab_scoring"])

        tv_fg = getattr(self.tabview, "_fg_color", ("gray86", "gray17"))
        tv_bg = getattr(self.tabview, "_bg_color", ("gray86", "gray17"))
        target_tab_color = tv_bg if tv_fg == "transparent" else tv_fg
        all_tabs: list[Any] = [self.tab_user, self.tab_paths, self.tab_wiki, self.tab_ai, self.tab_scoring]
        for tab in all_tabs:
            tab.configure(fg_color=target_tab_color, bg_color=target_tab_color)

        # Backward compatibility aliases for tab_ui and tab_backup
        self.tab_ui = self.tab_user
        self.tab_backup = self.tab_paths

        self.setup_user_tab()
        self.setup_paths_tab()
        self.setup_wiki_tab()
        self.setup_ai_tab()
        self.setup_scoring_tab()

        # Bottom Action Bar
        bottom_bar = ctk.CTkFrame(self, height=50, fg_color="transparent")
        bottom_bar.pack(fill="x", side="bottom", padx=15, pady=10)

        self.close_btn = self.register_i18n(
            ctk.CTkButton(
                bottom_bar,
                text=tr("common.close", "Schließen"),
                command=self.on_close,
                fg_color="gray40",
                hover_color="gray50",
                width=120,
            ),
            "common.close",
            "Schließen",
        )
        self.close_btn.pack(side="right", padx=5)

        self.save_btn = self.register_i18n(
            ctk.CTkButton(
                bottom_bar,
                text=tr("profile.save_btn", "💾 Einstellungen Speichern"),
                command=self.save_settings,
                fg_color="forestgreen",
                width=180,
            ),
            "profile.save_btn",
            "💾 Einstellungen Speichern",
        )
        self.save_btn.pack(side="right", padx=5)

        self.status_lbl = ctk.CTkLabel(bottom_bar, text="", text_color="green")
        self.status_lbl.pack(side="left", padx=5)

    def setup_user_tab(self) -> None:
        self.user_scroll = ctk.CTkScrollableFrame(self.tab_user, fg_color="transparent")
        self.user_scroll.pack(fill="both", expand=True, padx=5, pady=5)

        # 2-Column Side-by-Side Container
        cols_container = ctk.CTkFrame(self.user_scroll, fg_color="transparent")
        cols_container.pack(fill="both", expand=True, padx=5, pady=5)
        cols_container.columnconfigure(0, weight=1, uniform="user_cols")
        cols_container.columnconfigure(1, weight=1, uniform="user_cols")

        left_col = ctk.CTkFrame(cols_container, fg_color="transparent")
        left_col.grid(row=0, column=0, sticky="nsew", padx=(0, 15))

        right_col = ctk.CTkFrame(cols_container, fg_color="transparent")
        right_col.grid(row=0, column=1, sticky="nsew", padx=(15, 0))

        self.setup_user_section(left_col)
        self.setup_ui_section(right_col)

    def on_close(self) -> None:
        if not getattr(self, "_saved", False):
            ctk.set_widget_scaling(getattr(self, "_initial_font_scale", 1.0))
        self.destroy()

    def close_dialog(self) -> None:
        """Routes every close path (X button, Escape) through the font-scale reset."""
        self.on_close()

    def refresh_ui_labels(self) -> None:
        super().refresh_ui_labels()
        if hasattr(self, "top_header_lbl"):
            self.top_header_lbl.configure(text=tr("profile.header", "⚙ Profil & Anwendungseinstellungen"))
        if hasattr(self, "save_btn"):
            self.save_btn.configure(text=tr("profile.save_btn", "💾 Einstellungen Speichern"))
        if hasattr(self, "close_btn"):
            self.close_btn.configure(text=tr("common.close", "Schließen"))

        # Undocumented CTkTabview internal used to rename tab labels in place
        if hasattr(self, "tabview") and hasattr(self.tabview, "_segmented_button") and hasattr(self.tabview._segmented_button, "_buttons_dict"):  # pyright: ignore[reportAttributeAccessIssue]
            btns = self.tabview._segmented_button._buttons_dict  # pyright: ignore[reportAttributeAccessIssue]
            new_tab_name_map = {}
            for tab_id, key, default in getattr(self, "_tab_keys", []):
                orig_name = getattr(self, "_tab_name_map", {}).get(tab_id)
                new_txt = tr(key, default)
                new_tab_name_map[tab_id] = new_txt
                if orig_name and orig_name in btns:
                    btns[orig_name].configure(text=new_txt)
                    btns[new_txt] = btns.pop(orig_name)
            self._tab_name_map = new_tab_name_map

        self.refresh_user_tab_labels()
        self.refresh_ui_tab_labels()
        self.refresh_shortcuts_tab_labels()
        self.refresh_wiki_tab_labels()

    def save_settings(self) -> None:
        if not self.save_user_settings():
            return
        if not self.save_ui_settings():
            return
        if not self.save_paths_settings():
            return
        if not self.save_wiki_settings():
            return
        if not self.save_ai_settings():
            return
        if not self.save_shortcuts_settings():
            return

        self.storage_service.save_profile(self.profile)
        self.refresh_ui_labels()
        self.status_lbl.configure(text=tr("profile.saved_success", "✅ Einstellungen & Pfade gespeichert!"), text_color="green")

        if self.on_profile_updated:
            self.on_profile_updated()
