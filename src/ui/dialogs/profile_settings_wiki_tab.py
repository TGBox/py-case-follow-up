from typing import TYPE_CHECKING, Any
from collections.abc import Callable
import customtkinter as ctk

from enums import SyncMode
from services.i18n_service import tr


class WikiSettingsTabMixin:
    """Mixin for BookStack Wiki Server Configuration and synchronization settings."""

    if TYPE_CHECKING:
        tab_wiki: ctk.CTkFrame
        profile: Any
        register_i18n: Callable[..., Any]

    def setup_wiki_tab(self) -> None:
        self.register_i18n(
            ctk.CTkLabel(self.tab_wiki, text=tr("profile.wiki_title", "BookStack Server Konfiguration"), font=ctk.CTkFont(size=14, weight="bold")),
            "profile.wiki_title",
            "BookStack Server Konfiguration",
        ).pack(anchor="w", pady=(10, 5))

        self.register_i18n(
            ctk.CTkLabel(self.tab_wiki, text=tr("profile.wiki_url", "BookStack API URL:")),
            "profile.wiki_url",
            "BookStack API URL:",
        ).pack(anchor="w", pady=(5, 2))
        self.wiki_url_entry = self.register_i18n(
            ctk.CTkEntry(self.tab_wiki, placeholder_text=tr("profile.wiki_url_placeholder", "https://wiki.meinepraxis.de/api")),
            "profile.wiki_url_placeholder",
            "https://wiki.meinepraxis.de/api",
            attr="placeholder_text",
        )
        self.wiki_url_entry.insert(0, self.profile.wiki_settings.api_url)
        self.wiki_url_entry.pack(fill="x", pady=(0, 10))

        self.register_i18n(
            ctk.CTkLabel(self.tab_wiki, text=tr("profile.wiki_token_id", "API Token ID:")),
            "profile.wiki_token_id",
            "API Token ID:",
        ).pack(anchor="w", pady=(5, 2))
        self.wiki_token_id_entry = self.register_i18n(
            ctk.CTkEntry(self.tab_wiki, placeholder_text=tr("profile.wiki_token_id_placeholder", "Token ID")),
            "profile.wiki_token_id_placeholder",
            "Token ID",
            attr="placeholder_text",
        )
        self.wiki_token_id_entry.insert(0, self.profile.wiki_settings.token_id)
        self.wiki_token_id_entry.pack(fill="x", pady=(0, 10))

        self.register_i18n(
            ctk.CTkLabel(self.tab_wiki, text=tr("profile.wiki_token_secret", "API Token Secret:")),
            "profile.wiki_token_secret",
            "API Token Secret:",
        ).pack(anchor="w", pady=(5, 2))
        self.wiki_token_secret_entry = self.register_i18n(
            ctk.CTkEntry(self.tab_wiki, placeholder_text=tr("profile.wiki_token_secret_placeholder", "Token Secret"), show="*"),
            "profile.wiki_token_secret_placeholder",
            "Token Secret",
            attr="placeholder_text",
        )
        self.wiki_token_secret_entry.insert(0, self.profile.wiki_settings.token_secret)
        self.wiki_token_secret_entry.pack(fill="x", pady=(0, 10))

        self.register_i18n(
            ctk.CTkLabel(self.tab_wiki, text=tr("profile.wiki_sync_mode", "Synchronisations-Modus:")),
            "profile.wiki_sync_mode",
            "Synchronisations-Modus:",
        ).pack(anchor="w", pady=(5, 2))
        self.sync_mode_combo = ctk.CTkOptionMenu(self.tab_wiki, values=[SyncMode.METADATA_ONLY.value, SyncMode.FULL_OFFLINE.value])
        self.sync_mode_combo.set(self.profile.wiki_settings.sync_mode)
        self.sync_mode_combo.pack(fill="x", pady=(0, 10))

        self.sync_startup_var = ctk.BooleanVar(value=self.profile.wiki_settings.sync_on_startup)
        self.register_i18n(
            ctk.CTkCheckBox(self.tab_wiki, text=tr("profile.wiki_sync_startup", "Wiki-Inhalte beim Anwendungsstart synchronisieren"), variable=self.sync_startup_var),
            "profile.wiki_sync_startup",
            "Wiki-Inhalte beim Anwendungsstart synchronisieren",
        ).pack(anchor="w", pady=5)

    def save_wiki_settings(self) -> bool:
        self.profile.wiki_settings.api_url = self.wiki_url_entry.get().strip()
        self.profile.wiki_settings.token_id = self.wiki_token_id_entry.get().strip()
        self.profile.wiki_settings.token_secret = self.wiki_token_secret_entry.get().strip()
        self.profile.wiki_settings.sync_mode = self.sync_mode_combo.get()
        self.profile.wiki_settings.sync_on_startup = self.sync_startup_var.get()
        return True

    def refresh_wiki_tab_labels(self) -> None:
        pass
