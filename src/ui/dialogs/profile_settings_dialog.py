from typing import Any
from collections.abc import Callable
import customtkinter as ctk

from constants import (
    BTN_WIDTH_MD,
    BTN_WIDTH_XL,
    COLOR_MUTED_GRAY_FG,
    COLOR_MUTED_GRAY_HOVER,
    COLOR_NOTE_TEXT,
    COLOR_SETTINGS_NAV_ACCENT,
    COLOR_SETTINGS_NAV_BG,
    COLOR_SETTINGS_NAV_HOVER,
    COLOR_SETTINGS_NAV_SELECTED,
    COLOR_SETTINGS_NAV_TEXT,
    COLOR_SUCCESS,
    COLOR_TIP_TEXT,
    CORNER_RADIUS_CARD,
    CORNER_RADIUS_MD,
    CORNER_RADIUS_XS,
    DIALOG_DIMENSIONS,
    DIALOG_MIN_DIMENSIONS,
    DIALOG_TITLES,
    FONT_SIZE_BODY,
    FONT_SIZE_H2,
    FONT_SIZE_SM,
    FONT_SIZE_TITLE,
    HEIGHT_BOTTOM_BAR,
    PAD_LG,
    PAD_MD,
    PAD_NONE,
    PAD_SM,
    PAD_TINY,
    PAD_XS,
    SETTINGS_NAV_ACCENT_WIDTH,
    SETTINGS_NAV_ITEM_HEIGHT,
    SETTINGS_NAV_WIDTH,
    SETTINGS_PAGE_DESC_WRAP,
)
from models.profile import UserProfile
from services.i18n_service import tr
from services.storage_service import StorageService
from ui.dialogs.base_dialog import BaseDialog
from ui.dialogs.profile_settings_ai_tab import AiSettingsTabMixin
from ui.dialogs.profile_settings_paths_tab import PathsSettingsTabMixin
from ui.dialogs.profile_settings_shortcuts_tab import ShortcutsSettingsTabMixin
from ui.dialogs.profile_settings_ui_tab import UiSettingsTabMixin
from ui.dialogs.profile_settings_user_tab import UserSettingsTabMixin
from ui.dialogs.profile_settings_wiki_tab import WikiSettingsTabMixin

#: Sidebar structure: (group key, group default, pages). Each page is
#: (page id, title key, title default, description key, description default,
#: whether the dialog wraps the page body in a scrollable frame). The data page
#: brings its own scrolling two-column layout.
SETTINGS_PAGES: list[tuple[str, str, list[tuple[str, str, str, str, str, bool]]]] = [
    ("profile.nav_group_you", "Du", [
        ("profile", "profile.page_profile", "Profil",
         "profile.page_profile_desc", "Wer du bist und wie du in Fällen und E-Mails auftrittst.", True),
        ("appearance", "profile.page_appearance", "Darstellung",
         "profile.page_appearance_desc", "Sprache, Farben, Schriftgröße und Anordnung der App.", True),
    ]),
    ("profile.nav_group_notify", "Erinnern und benachrichtigen", [
        ("notifications", "profile.page_notifications", "Benachrichtigungen",
         "profile.page_notifications_desc", "Hinweise auf diesem PC, wenn Wiedervorlagen fällig werden.", True),
        ("push", "profile.page_push", "Smartphone-Push",
         "profile.page_push_desc", "Meldungen aufs Handy, wenn du nicht am Platz bist. Läuft über ntfy.sh.", True),
        ("checkout", "profile.page_checkout", "Feierabend",
         "profile.page_checkout_desc", "Checkliste, Abfahrten und Geh-Wecker zum Dienstende.", True),
    ]),
    ("profile.nav_group_work", "Arbeit", [
        ("scoring", "profile.page_scoring", "Priorisierung",
         "profile.page_scoring_desc", "Wie stark Fälle in der Liste nach oben rücken.", True),
        ("shortcuts", "profile.page_shortcuts", "Tastenkürzel",
         "profile.page_shortcuts_desc", "Tastenkombinationen für Aktionen und Textbausteine.", True),
        ("team", "profile.page_team", "Team-Sync",
         "profile.page_team_desc", "Fälle mit Kolleginnen und Kollegen im Netzwerk abgleichen.", True),
        ("wiki", "profile.page_wiki", "Wiki",
         "profile.page_wiki_desc", "Verbindung zum BookStack-Wiki.", True),
        ("ai", "profile.page_ai", "KI und Textanalyse",
         "profile.page_ai_desc", "KI-Anbieter, lokale Modelle und Grundregeln für Antworten.", True),
    ]),
    ("profile.nav_group_system", "System", [
        ("data", "profile.page_data", "Daten und Backup",
         "profile.page_data_desc", "Speicherort, automatische Sicherungen und Export.", False),
    ]),
]


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
        initial_page: str | None = None,
    ):
        super().__init__(parent)
        self.profile = profile
        self.storage_service = storage_service
        self.on_profile_updated = on_profile_updated
        self._initial_page = initial_page

        from services.snippet_service import SnippetService
        self.snippet_service = getattr(parent, "snippet_service", None) or SnippetService(self.storage_service.config.workspace_dir)

        w, h = DIALOG_DIMENSIONS["profile_settings"]
        self.setup_window(
            parent,
            tr("profile.title", DIALOG_TITLES["profile_settings"]),
            (w, h),
            min_size=DIALOG_MIN_DIMENSIONS["profile_settings"],
            title_factory=lambda: tr("profile.title", DIALOG_TITLES["profile_settings"]),
        )

        self._initial_font_scale = getattr(self.profile.ui_settings, "font_scale", 1.0)
        self._saved = False

        self.create_widgets()

    def create_widgets(self) -> None:
        # Bottom action bar first, so the page area never pushes it out of view
        bottom_bar = ctk.CTkFrame(self, height=HEIGHT_BOTTOM_BAR, fg_color="transparent")
        bottom_bar.pack(fill="x", side="bottom", padx=PAD_LG, pady=PAD_MD)

        self.close_btn = self.register_i18n(
            ctk.CTkButton(
                bottom_bar,
                text=tr("common.close", "Schließen"),
                command=self.on_close,
                fg_color=COLOR_MUTED_GRAY_FG,
                hover_color=COLOR_MUTED_GRAY_HOVER,
                width=BTN_WIDTH_MD,
            ),
            "common.close",
            "Schließen",
        )
        self.close_btn.pack(side="right", padx=PAD_SM)

        self.save_btn = self.register_i18n(
            ctk.CTkButton(
                bottom_bar,
                text=tr("profile.save_btn", "💾 Einstellungen Speichern"),
                command=self.save_settings,
                fg_color=COLOR_SUCCESS,
                hover_color=COLOR_SUCCESS,
                width=BTN_WIDTH_XL,
            ),
            "profile.save_btn",
            "💾 Einstellungen Speichern",
        )
        self.save_btn.pack(side="right", padx=PAD_SM)

        self.status_lbl = ctk.CTkLabel(bottom_bar, text="", text_color=COLOR_SUCCESS)
        self.status_lbl.pack(side="left", padx=PAD_SM)

        # Sidebar + page area
        body = ctk.CTkFrame(self, fg_color="transparent")
        body.pack(fill="both", expand=True, padx=PAD_MD, pady=(PAD_MD, PAD_NONE))

        self.nav_frame = ctk.CTkFrame(body, width=SETTINGS_NAV_WIDTH, fg_color=COLOR_SETTINGS_NAV_BG, corner_radius=CORNER_RADIUS_CARD)
        self.nav_frame.pack(side="left", fill="y", padx=(PAD_NONE, PAD_LG))
        self.nav_frame.pack_propagate(False)

        self.top_header_lbl = self.register_i18n(
            ctk.CTkLabel(
                self.nav_frame,
                text=tr("profile.nav_title", "Einstellungen"),
                font=ctk.CTkFont(size=FONT_SIZE_TITLE, weight="bold"),
                anchor="w",
            ),
            "profile.nav_title",
            "Einstellungen",
        )
        self.top_header_lbl.pack(fill="x", padx=PAD_LG, pady=(PAD_LG, PAD_XS))

        self.page_area = ctk.CTkFrame(body, fg_color="transparent")
        self.page_area.pack(side="left", fill="both", expand=True)

        self._pages: dict[str, ctk.CTkFrame] = {}
        self._page_bodies: dict[str, Any] = {}
        self._nav_items: dict[str, tuple[ctk.CTkFrame, ctk.CTkButton]] = {}
        self._page_order: list[str] = []
        self.current_page: str | None = None

        for group_key, group_default, pages in SETTINGS_PAGES:
            self.register_i18n(
                ctk.CTkLabel(
                    self.nav_frame,
                    text=tr(group_key, group_default),
                    font=ctk.CTkFont(size=FONT_SIZE_SM),
                    text_color=COLOR_TIP_TEXT,
                    anchor="w",
                ),
                group_key,
                group_default,
            ).pack(fill="x", padx=PAD_LG, pady=(PAD_MD, PAD_TINY))
            for page_id, title_key, title_default, desc_key, desc_default, scrolls in pages:
                self._add_nav_item(page_id, title_key, title_default)
                self._build_page(page_id, title_key, title_default, desc_key, desc_default, scrolls)

        # Backward compatibility: the mixins (and older callers) still address
        # their former tab frames by these names.
        self.tab_user = self._page_bodies["profile"]
        self.tab_ui = self._page_bodies["appearance"]
        self.tab_paths = self._page_bodies["data"]
        self.tab_backup = self.tab_paths
        self.tab_ai = self._page_bodies["ai"]
        self.tab_scoring = self._page_bodies["scoring"]
        self.tab_wiki = self._page_bodies["wiki"]

        pb = self._page_bodies
        self.setup_user_section(pb["profile"])
        self.setup_appearance_section(pb["appearance"])
        self.setup_column_widths_section(pb["appearance"])
        self.setup_notifications_section(pb["notifications"])
        self.setup_ntfy_section(pb["push"])
        self.setup_checkout_section(pb["checkout"])
        self.setup_scoring_section(pb["scoring"])
        self.setup_shortcuts_section(pb["shortcuts"])
        self.setup_p2p_section(pb["team"])
        self.setup_wiki_section(pb["wiki"])
        self.setup_ai_tab()
        self.setup_paths_tab()

        self.bind("<Control-Next>", lambda _e: self._step_page(1), add="+")
        self.bind("<Control-Prior>", lambda _e: self._step_page(-1), add="+")
        first = self._initial_page if self._initial_page in self._pages else self._page_order[0]
        self.show_page(first)

    # ------------------------------------------------------------------
    # Sidebar navigation
    # ------------------------------------------------------------------
    def _add_nav_item(self, page_id: str, title_key: str, title_default: str) -> None:
        row = ctk.CTkFrame(self.nav_frame, fg_color="transparent", height=SETTINGS_NAV_ITEM_HEIGHT)
        row.pack(fill="x", padx=(PAD_SM, PAD_MD), pady=PAD_TINY)
        row.pack_propagate(False)

        accent = ctk.CTkFrame(row, width=SETTINGS_NAV_ACCENT_WIDTH, fg_color="transparent", corner_radius=CORNER_RADIUS_XS)
        accent.pack(side="left", fill="y", pady=PAD_SM)

        btn = self.register_i18n(
            ctk.CTkButton(
                row,
                text=tr(title_key, title_default),
                anchor="w",
                height=SETTINGS_NAV_ITEM_HEIGHT,
                fg_color="transparent",
                hover_color=COLOR_SETTINGS_NAV_HOVER,
                text_color=COLOR_SETTINGS_NAV_TEXT,
                corner_radius=CORNER_RADIUS_MD,
                command=lambda p=page_id: self.show_page(p),
            ),
            title_key,
            title_default,
        )
        btn.pack(side="left", fill="both", expand=True, padx=(PAD_XS, PAD_NONE))
        self._nav_items[page_id] = (accent, btn)
        self._page_order.append(page_id)

    def _build_page(self, page_id: str, title_key: str, title_default: str, desc_key: str, desc_default: str, scrolls: bool) -> None:
        from utils.ui_utils import enable_auto_hiding_scrollbar

        page = ctk.CTkFrame(self.page_area, fg_color="transparent")

        self.register_i18n(
            ctk.CTkLabel(page, text=tr(title_key, title_default), font=ctk.CTkFont(size=FONT_SIZE_H2, weight="bold"), anchor="w"),
            title_key,
            title_default,
        ).pack(fill="x", padx=PAD_SM, pady=(PAD_SM, PAD_NONE))
        self.register_i18n(
            ctk.CTkLabel(
                page,
                text=tr(desc_key, desc_default),
                font=ctk.CTkFont(size=FONT_SIZE_BODY),
                text_color=COLOR_NOTE_TEXT,
                anchor="w",
                justify="left",
                wraplength=SETTINGS_PAGE_DESC_WRAP,
            ),
            desc_key,
            desc_default,
        ).pack(fill="x", padx=PAD_SM, pady=(PAD_XS, PAD_LG))

        body: Any
        if scrolls:
            body = ctk.CTkScrollableFrame(page, fg_color="transparent")
            body.pack(fill="both", expand=True)
            enable_auto_hiding_scrollbar(body)
        else:
            body = ctk.CTkFrame(page, fg_color="transparent")
            body.pack(fill="both", expand=True)

        self._pages[page_id] = page
        self._page_bodies[page_id] = body

    def show_page(self, page_id: str) -> None:
        """Brings one settings page to the front and marks it in the sidebar."""
        if page_id not in self._pages:
            return
        if self.current_page in self._pages:
            self._pages[self.current_page].pack_forget()
        self._pages[page_id].pack(fill="both", expand=True)
        for pid, (accent, btn) in self._nav_items.items():
            selected = pid == page_id
            btn.configure(fg_color=COLOR_SETTINGS_NAV_SELECTED if selected else "transparent")
            accent.configure(fg_color=COLOR_SETTINGS_NAV_ACCENT if selected else "transparent")
        self.current_page = page_id

    def _step_page(self, delta: int) -> str:
        if self.current_page in self._page_order:
            idx = (self._page_order.index(self.current_page) + delta) % len(self._page_order)
            self.show_page(self._page_order[idx])
        return "break"

    def on_close(self) -> None:
        if not getattr(self, "_saved", False):
            ctk.set_widget_scaling(getattr(self, "_initial_font_scale", 1.0))
        self.destroy()

    def close_dialog(self) -> None:
        """Routes every close path (X button, Escape) through the font-scale reset."""
        self.on_close()

    def refresh_ui_labels(self) -> None:
        super().refresh_ui_labels()
        if hasattr(self, "save_btn"):
            self.save_btn.configure(text=tr("profile.save_btn", "💾 Einstellungen Speichern"))
        if hasattr(self, "close_btn"):
            self.close_btn.configure(text=tr("common.close", "Schließen"))

        self.refresh_user_tab_labels()
        self.refresh_ui_tab_labels()
        self.refresh_shortcuts_tab_labels()
        self.refresh_wiki_tab_labels()
        self.refresh_ai_tab_labels()

    def reload_all_tabs(self) -> None:
        """Reloads all input widgets across all dialog tabs to reflect self.profile."""
        self.reload_user_fields()
        if hasattr(self, "reload_ui_fields"):
            self.reload_ui_fields()
        if hasattr(self, "reload_paths_fields"):
            self.reload_paths_fields()
        if hasattr(self, "reload_wiki_fields"):
            self.reload_wiki_fields()
        if hasattr(self, "reload_ai_fields"):
            self.reload_ai_fields()
        if hasattr(self, "reload_shortcuts_fields"):
            self.reload_shortcuts_fields()

    def save_settings_quietly(self) -> bool:
        """Saves all tabs to self.profile without status message or label re-renders."""
        if not self.save_user_settings():
            return False
        if not self.save_ui_settings():
            return False
        if not self.save_paths_settings():
            return False
        if not self.save_wiki_settings():
            return False
        if not self.save_ai_settings():
            return False
        if not self.save_shortcuts_settings():
            return False

        self.storage_service.save_profile(self.profile, sync=True)
        return True

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

        self.storage_service.save_profile(self.profile, sync=True)
        self.storage_service.apply_profile_paths(self.profile)
        self.refresh_ui_labels()
        self.status_lbl.configure(text=tr("profile.saved_success", "✅ Einstellungen & Pfade gespeichert!"), text_color=COLOR_SUCCESS)

        if self.on_profile_updated:
            self.on_profile_updated()
