import customtkinter as ctk
from typing import Callable
from models.profile import UserProfile
from services.storage_service import StorageService
from enums import LayoutMode, SyncMode


class ProfileSettingsDialog(ctk.CTkToplevel):
    def __init__(self, parent, profile: UserProfile, storage_service: StorageService, on_profile_updated: Callable[[], None] | None = None):
        super().__init__(parent)
        self.profile = profile
        self.storage_service = storage_service
        self.on_profile_updated = on_profile_updated

        self.title("⚙️ Profil & Einstellungen")
        self.geometry("700x560")
        self.minsize(600, 460)

        self.transient(parent)
        self.grab_set()

        self.create_widgets()

    def create_widgets(self):
        # Top Header
        top_bar = ctk.CTkFrame(self, height=45, corner_radius=0)
        top_bar.pack(fill="x", side="top", padx=10, pady=(10, 5))

        ctk.CTkLabel(top_bar, text="⚙️ Profil & Anwendungseinstellungen", font=ctk.CTkFont(size=16, weight="bold")).pack(side="left", padx=10)

        # Tabview
        self.tabview = ctk.CTkTabview(self)
        self.tabview.pack(fill="both", expand=True, padx=10, pady=(5, 10))

        self.tab_user = self.tabview.add("👤 Benutzerprofil")
        self.tab_ui = self.tabview.add("🎨 Erscheinungsbild")
        self.tab_wiki = self.tabview.add("📚 BookStack Wiki")
        self.tab_scoring = self.tabview.add("⌨️ Tastenkürzel & Scoring")

        self.setup_user_tab()
        self.setup_ui_tab()
        self.setup_wiki_tab()
        self.setup_scoring_tab()

        # Bottom Action Bar
        bottom_bar = ctk.CTkFrame(self, height=50, fg_color="transparent")
        bottom_bar.pack(fill="x", side="bottom", padx=15, pady=10)

        self.save_btn = ctk.CTkButton(bottom_bar, text="💾 Einstellungen Speichern", command=self.save_settings, fg_color="forestgreen", width=180)
        self.save_btn.pack(side="right", padx=5)

        self.status_lbl = ctk.CTkLabel(bottom_bar, text="", text_color="green")
        self.status_lbl.pack(side="left", padx=5)

    def setup_user_tab(self):
        ctk.CTkLabel(self.tab_user, text="Benutzerinformationen", font=ctk.CTkFont(size=14, weight="bold")).pack(anchor="w", pady=(10, 5))

        ctk.CTkLabel(self.tab_user, text="Name / Anzeigename *:").pack(anchor="w", pady=(5, 2))
        self.user_name_entry = ctk.CTkEntry(self.tab_user, placeholder_text="Ihr Name")
        self.user_name_entry.insert(0, self.profile.user.name)
        self.user_name_entry.pack(fill="x", pady=(0, 10))

        ctk.CTkLabel(self.tab_user, text="Durchwahl / Extension:").pack(anchor="w", pady=(5, 2))
        self.user_ext_entry = ctk.CTkEntry(self.tab_user, placeholder_text="z.B. 4012")
        self.user_ext_entry.insert(0, self.profile.user.extension)
        self.user_ext_entry.pack(fill="x", pady=(0, 10))

        ctk.CTkLabel(self.tab_user, text="E-Mail-Adresse:").pack(anchor="w", pady=(5, 2))
        self.user_email_entry = ctk.CTkEntry(self.tab_user, placeholder_text="beispiel@support.de")
        self.user_email_entry.insert(0, self.profile.user.email)
        self.user_email_entry.pack(fill="x", pady=(0, 10))

        ctk.CTkLabel(self.tab_user, text="Mobiltelefon:").pack(anchor="w", pady=(5, 2))
        self.user_mobile_entry = ctk.CTkEntry(self.tab_user, placeholder_text="0170 / 1234567")
        self.user_mobile_entry.insert(0, self.profile.user.mobile)
        self.user_mobile_entry.pack(fill="x", pady=(0, 10))

    def setup_ui_tab(self):
        ctk.CTkLabel(self.tab_ui, text="Erscheinungsbild & Layout", font=ctk.CTkFont(size=14, weight="bold")).pack(anchor="w", pady=(10, 5))

        ctk.CTkLabel(self.tab_ui, text="Farb-Thema (Theme):").pack(anchor="w", pady=(5, 2))
        self.theme_combo = ctk.CTkOptionMenu(self.tab_ui, values=["Dark", "Light", "System"])
        self.theme_combo.set(self.profile.ui_settings.theme)
        self.theme_combo.pack(fill="x", pady=(0, 15))

        ctk.CTkLabel(self.tab_ui, text="Standard-Layout beim Start:").pack(anchor="w", pady=(5, 2))
        self.layout_combo = ctk.CTkOptionMenu(
            self.tab_ui,
            values=[LayoutMode.COCKPIT.value, LayoutMode.TAB_VIEW.value, LayoutMode.SPLIT_VIEW.value]
        )
        self.layout_combo.set(self.profile.ui_settings.default_layout)
        self.layout_combo.pack(fill="x", pady=(0, 15))

    def setup_wiki_tab(self):
        ctk.CTkLabel(self.tab_wiki, text="BookStack Server Konfiguration", font=ctk.CTkFont(size=14, weight="bold")).pack(anchor="w", pady=(10, 5))

        ctk.CTkLabel(self.tab_wiki, text="BookStack API URL:").pack(anchor="w", pady=(5, 2))
        self.wiki_url_entry = ctk.CTkEntry(self.tab_wiki, placeholder_text="https://wiki.meinepraxis.de/api")
        self.wiki_url_entry.insert(0, self.profile.wiki_settings.api_url)
        self.wiki_url_entry.pack(fill="x", pady=(0, 10))

        ctk.CTkLabel(self.tab_wiki, text="API Token ID:").pack(anchor="w", pady=(5, 2))
        self.wiki_token_id_entry = ctk.CTkEntry(self.tab_wiki, placeholder_text="Token ID")
        self.wiki_token_id_entry.insert(0, self.profile.wiki_settings.token_id)
        self.wiki_token_id_entry.pack(fill="x", pady=(0, 10))

        ctk.CTkLabel(self.tab_wiki, text="API Token Secret:").pack(anchor="w", pady=(5, 2))
        self.wiki_token_secret_entry = ctk.CTkEntry(self.tab_wiki, placeholder_text="Token Secret", show="*")
        self.wiki_token_secret_entry.insert(0, self.profile.wiki_settings.token_secret)
        self.wiki_token_secret_entry.pack(fill="x", pady=(0, 10))

        ctk.CTkLabel(self.tab_wiki, text="Synchronisations-Modus:").pack(anchor="w", pady=(5, 2))
        self.sync_mode_combo = ctk.CTkOptionMenu(self.tab_wiki, values=[SyncMode.METADATA_ONLY.value, SyncMode.FULL_OFFLINE.value])
        self.sync_mode_combo.set(self.profile.wiki_settings.sync_mode)
        self.sync_mode_combo.pack(fill="x", pady=(0, 10))

        self.sync_startup_var = ctk.BooleanVar(value=self.profile.wiki_settings.sync_on_startup)
        ctk.CTkCheckBox(self.tab_wiki, text="Wiki-Inhalte beim Anwendungsstart synchronisieren", variable=self.sync_startup_var).pack(anchor="w", pady=5)

    def setup_scoring_tab(self):
        ctk.CTkLabel(self.tab_scoring, text="Tastenkürzel (Hotkeys)", font=ctk.CTkFont(size=14, weight="bold")).pack(anchor="w", pady=(10, 5))

        row1 = ctk.CTkFrame(self.tab_scoring, fg_color="transparent")
        row1.pack(fill="x", pady=3)
        ctk.CTkLabel(row1, text="Neuer Fall:").pack(side="left")
        self.hk_new = ctk.CTkEntry(row1, width=140)
        self.hk_new.insert(0, self.profile.shortcuts.new_case)
        self.hk_new.pack(side="right")

        row2 = ctk.CTkFrame(self.tab_scoring, fg_color="transparent")
        row2.pack(fill="x", pady=3)
        ctk.CTkLabel(row2, text="Export Dialog:").pack(side="left")
        self.hk_export = ctk.CTkEntry(row2, width=140)
        self.hk_export.insert(0, self.profile.shortcuts.export_dialog)
        self.hk_export.pack(side="right")

        row3 = ctk.CTkFrame(self.tab_scoring, fg_color="transparent")
        row3.pack(fill="x", pady=3)
        ctk.CTkLabel(row3, text="Wiki-Suche fokussieren:").pack(side="left")
        self.hk_search = ctk.CTkEntry(row3, width=140)
        self.hk_search.insert(0, self.profile.shortcuts.wiki_search)
        self.hk_search.pack(side="right")

        ctk.CTkLabel(self.tab_scoring, text="Prioritäts-Scoring Punkte", font=ctk.CTkFont(size=14, weight="bold")).pack(anchor="w", pady=(15, 5))

        row4 = ctk.CTkFrame(self.tab_scoring, fg_color="transparent")
        row4.pack(fill="x", pady=3)
        ctk.CTkLabel(row4, text="VIP-Bonus (Punkte):").pack(side="left")
        self.vip_bonus_entry = ctk.CTkEntry(row4, width=80)
        self.vip_bonus_entry.insert(0, str(self.profile.scoring_matrix.vip_bonus_points))
        self.vip_bonus_entry.pack(side="right")

    def save_settings(self):
        name = self.user_name_entry.get().strip()
        if not name:
            self.status_lbl.configure(text="⚠️ Benutzername darf nicht leer sein!", text_color="red")
            return

        # Update User
        self.profile.user.name = name
        self.profile.user.extension = self.user_ext_entry.get().strip()
        self.profile.user.email = self.user_email_entry.get().strip()
        self.profile.user.mobile = self.user_mobile_entry.get().strip()

        # Update UI Settings
        self.profile.ui_settings.theme = self.theme_combo.get()
        self.profile.ui_settings.default_layout = self.layout_combo.get()

        # Update Wiki Settings
        self.profile.wiki_settings.api_url = self.wiki_url_entry.get().strip()
        self.profile.wiki_settings.token_id = self.wiki_token_id_entry.get().strip()
        self.profile.wiki_settings.token_secret = self.wiki_token_secret_entry.get().strip()
        self.profile.wiki_settings.sync_mode = self.sync_mode_combo.get()
        self.profile.wiki_settings.sync_on_startup = self.sync_startup_var.get()

        # Update Shortcuts & Scoring
        self.profile.shortcuts.new_case = self.hk_new.get().strip()
        self.profile.shortcuts.export_dialog = self.hk_export.get().strip()
        self.profile.shortcuts.wiki_search = self.hk_search.get().strip()

        try:
            self.profile.scoring_matrix.vip_bonus_points = int(self.vip_bonus_entry.get().strip())
        except ValueError:
            pass

        self.storage_service.save_profile(self.profile)
        self.status_lbl.configure(text="✅ Einstellungen erfolgreich gespeichert!", text_color="green")

        if self.on_profile_updated:
            self.on_profile_updated()
