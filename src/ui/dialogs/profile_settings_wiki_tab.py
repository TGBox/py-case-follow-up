from typing import TYPE_CHECKING, Any
from collections.abc import Callable
import customtkinter as ctk

from constants import FONT_SIZE_SUBTITLE, PAD_MD, PAD_NONE, PAD_SM, PAD_XS
from enums import SyncMode
from services.i18n_service import tr


class WikiSettingsTabMixin:
    """Mixin for BookStack Wiki Server Configuration and synchronization settings."""

    if TYPE_CHECKING:
        tab_wiki: ctk.CTkFrame
        profile: Any
        register_i18n: Callable[..., Any]

    def setup_wiki_section(self, parent_frame: ctk.CTkFrame) -> None:
        self.wiki_hdr_lbl = self.register_i18n(
            ctk.CTkLabel(parent_frame, text=tr("profile.wiki_title", "BookStack Server Konfiguration"), font=ctk.CTkFont(size=FONT_SIZE_SUBTITLE, weight="bold")),
            "profile.wiki_title",
            "BookStack Server Konfiguration",
        )
        self.wiki_hdr_lbl.pack(anchor="w", pady=(PAD_SM, PAD_SM))

        self.wiki_url_lbl = self.register_i18n(
            ctk.CTkLabel(parent_frame, text=tr("profile.wiki_url", "BookStack API URL:")),
            "profile.wiki_url",
            "BookStack API URL:",
        )
        self.wiki_url_lbl.pack(anchor="w", pady=(PAD_SM, PAD_XS))
        self.wiki_url_entry = self.register_i18n(
            ctk.CTkEntry(parent_frame, placeholder_text=tr("profile.wiki_url_placeholder", "https://wiki.meinepraxis.de/api")),
            "profile.wiki_url_placeholder",
            "https://wiki.meinepraxis.de/api",
            attr="placeholder_text",
        )
        self.wiki_url_entry.insert(0, self.profile.wiki_settings.api_url)
        self.wiki_url_entry.pack(fill="x", pady=(PAD_NONE, PAD_MD))

        self.wiki_token_id_lbl = self.register_i18n(
            ctk.CTkLabel(parent_frame, text=tr("profile.wiki_token_id", "API Token ID:")),
            "profile.wiki_token_id",
            "API Token ID:",
        )
        self.wiki_token_id_lbl.pack(anchor="w", pady=(PAD_SM, PAD_XS))
        self.wiki_token_id_entry = self.register_i18n(
            ctk.CTkEntry(parent_frame, placeholder_text=tr("profile.wiki_token_id_placeholder", "Token ID")),
            "profile.wiki_token_id_placeholder",
            "Token ID",
            attr="placeholder_text",
        )
        self.wiki_token_id_entry.insert(0, self.profile.wiki_settings.token_id)
        self.wiki_token_id_entry.pack(fill="x", pady=(PAD_NONE, PAD_MD))

        self.wiki_token_secret_lbl = self.register_i18n(
            ctk.CTkLabel(parent_frame, text=tr("profile.wiki_token_secret", "API Token Secret:")),
            "profile.wiki_token_secret",
            "API Token Secret:",
        )
        self.wiki_token_secret_lbl.pack(anchor="w", pady=(PAD_SM, PAD_XS))
        self.wiki_token_secret_entry = self.register_i18n(
            ctk.CTkEntry(parent_frame, placeholder_text=tr("profile.wiki_token_secret_placeholder", "Token Secret"), show="*"),
            "profile.wiki_token_secret_placeholder",
            "Token Secret",
            attr="placeholder_text",
        )
        self.wiki_token_secret_entry.insert(0, self.profile.wiki_settings.token_secret)
        self.wiki_token_secret_entry.pack(fill="x", pady=(PAD_NONE, PAD_MD))

        self.wiki_sync_mode_lbl = self.register_i18n(
            ctk.CTkLabel(parent_frame, text=tr("profile.wiki_sync_mode", "Synchronisations-Modus:")),
            "profile.wiki_sync_mode",
            "Synchronisations-Modus:",
        )
        self.wiki_sync_mode_lbl.pack(anchor="w", pady=(PAD_SM, PAD_XS))
        self.sync_mode_combo = ctk.CTkOptionMenu(parent_frame, values=[SyncMode.METADATA_ONLY.value, SyncMode.FULL_OFFLINE.value])
        self.sync_mode_combo.set(self.profile.wiki_settings.sync_mode)
        self.sync_mode_combo.pack(fill="x", pady=(PAD_NONE, PAD_MD))

        self.sync_startup_var = ctk.BooleanVar(value=self.profile.wiki_settings.sync_on_startup)
        self.sync_startup_chk = self.register_i18n(
            ctk.CTkCheckBox(parent_frame, text=tr("profile.wiki_sync_startup", "Wiki-Inhalte beim Anwendungsstart synchronisieren"), variable=self.sync_startup_var),
            "profile.wiki_sync_startup",
            "Wiki-Inhalte beim Anwendungsstart synchronisieren",
        )
        self.sync_startup_chk.pack(anchor="w", pady=(PAD_SM, PAD_MD))

    def setup_wiki_tab(self) -> None:
        if hasattr(self, "wiki_url_entry"):
            return
        target = getattr(self, "tab_wiki", None)
        if target:
            self.setup_wiki_section(target)

    def save_wiki_settings(self) -> bool:
        if hasattr(self, "wiki_url_entry"):
            self.profile.wiki_settings.api_url = self.wiki_url_entry.get().strip()
        if hasattr(self, "wiki_token_id_entry"):
            self.profile.wiki_settings.token_id = self.wiki_token_id_entry.get().strip()
        if hasattr(self, "wiki_token_secret_entry"):
            self.profile.wiki_settings.token_secret = self.wiki_token_secret_entry.get().strip()
        if hasattr(self, "sync_mode_combo"):
            self.profile.wiki_settings.sync_mode = self.sync_mode_combo.get()
        if hasattr(self, "sync_startup_var"):
            self.profile.wiki_settings.sync_on_startup = self.sync_startup_var.get()
        return True

    def reload_wiki_fields(self) -> None:
        ws = getattr(self.profile, "wiki_settings", None)
        if ws is None:
            return

        if hasattr(self, "wiki_url_entry"):
            self.wiki_url_entry.delete(0, "end")
            self.wiki_url_entry.insert(0, ws.api_url or "")

        if hasattr(self, "wiki_token_id_entry"):
            self.wiki_token_id_entry.delete(0, "end")
            self.wiki_token_id_entry.insert(0, ws.token_id or "")

        if hasattr(self, "wiki_token_secret_entry"):
            self.wiki_token_secret_entry.delete(0, "end")
            self.wiki_token_secret_entry.insert(0, ws.token_secret or "")

        if hasattr(self, "sync_mode_combo"):
            self.sync_mode_combo.set(ws.sync_mode or SyncMode.METADATA_ONLY.value)

        if hasattr(self, "sync_startup_var"):
            self.sync_startup_var.set(bool(ws.sync_on_startup))

    def refresh_wiki_tab_labels(self) -> None:
        if hasattr(self, "wiki_hdr_lbl"):
            self.wiki_hdr_lbl.configure(text=tr("profile.wiki_title", "BookStack Server Konfiguration"))
        if hasattr(self, "wiki_url_lbl"):
            self.wiki_url_lbl.configure(text=tr("profile.wiki_url", "BookStack API URL:"))
        if hasattr(self, "wiki_token_id_lbl"):
            self.wiki_token_id_lbl.configure(text=tr("profile.wiki_token_id", "API Token ID:"))
        if hasattr(self, "wiki_token_secret_lbl"):
            self.wiki_token_secret_lbl.configure(text=tr("profile.wiki_token_secret", "API Token Secret:"))
        if hasattr(self, "wiki_sync_mode_lbl"):
            self.wiki_sync_mode_lbl.configure(text=tr("profile.wiki_sync_mode", "Synchronisations-Modus:"))
        if hasattr(self, "sync_startup_chk"):
            self.sync_startup_chk.configure(text=tr("profile.wiki_sync_startup", "Wiki-Inhalte beim Anwendungsstart synchronisieren"))
