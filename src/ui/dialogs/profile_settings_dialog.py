import customtkinter as ctk
from typing import Callable
from models.profile import UserProfile
from services.storage_service import StorageService
from enums import LayoutMode, SyncMode, get_layout_display, get_layout_val_from_display, LAYOUT_DISPLAY


class ProfileSettingsDialog(ctk.CTkToplevel):
    def __init__(self, parent, profile: UserProfile, storage_service: StorageService, on_profile_updated: Callable[[], None] | None = None):
        super().__init__(parent)
        self.profile = profile
        self.storage_service = storage_service
        self.on_profile_updated = on_profile_updated

        self.title("⚙️ Profil & Einstellungen")
        self.geometry("960x780")
        self.minsize(880, 680)
        from utils.ui_utils import center_window
        center_window(self, 960, 780)

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
        self.tab_paths = self.tabview.add("📁 Speicherort & Pfade")
        self.tab_wiki = self.tabview.add("📚 BookStack Wiki")
        self.tab_scoring = self.tabview.add("⌨️ Tastenkürzel & Scoring")
        self.tab_backup = self.tabview.add("💾 Datensicherung")

        self.setup_user_tab()
        self.setup_ui_tab()
        self.setup_paths_tab()
        self.setup_wiki_tab()
        self.setup_scoring_tab()
        self.setup_backup_tab()

        # Bottom Action Bar
        bottom_bar = ctk.CTkFrame(self, height=50, fg_color="transparent")
        bottom_bar.pack(fill="x", side="bottom", padx=15, pady=10)

        self.save_btn = ctk.CTkButton(bottom_bar, text="💾 Einstellungen Speichern", command=self.save_settings, fg_color="forestgreen", width=180)
        self.save_btn.pack(side="right", padx=5)

        self.status_lbl = ctk.CTkLabel(bottom_bar, text="", text_color="green")
        self.status_lbl.pack(side="left", padx=5)

    def setup_user_tab(self):
        ctk.CTkLabel(self.tab_user, text="Mitarbeiter-Profil verwalten & wechseln", font=ctk.CTkFont(size=14, weight="bold")).pack(anchor="w", pady=(10, 5))

        prof_frame = ctk.CTkFrame(self.tab_user, fg_color="transparent")
        prof_frame.pack(fill="x", pady=(0, 15))

        ctk.CTkLabel(prof_frame, text="Aktives Profil:").pack(side="left", padx=(0, 10))

        profiles_list = self.storage_service.list_profiles()
        self.profile_combo = ctk.CTkOptionMenu(
            prof_frame,
            values=profiles_list,
            command=self.on_switch_profile,
            width=220,
        )
        self.profile_combo.set(self.profile.user.name if self.profile.user.name in profiles_list else profiles_list[0])
        self.profile_combo.pack(side="left", padx=(0, 10))

        btn_new_prof = ctk.CTkButton(
            prof_frame,
            text="➕ Neues Profil anlegen",
            command=self.open_create_profile_dialog,
            fg_color="forestgreen",
            width=160,
        )
        btn_new_prof.pack(side="left")

        ctk.CTkLabel(self.tab_user, text="Benutzerinformationen (Aktives Profil)", font=ctk.CTkFont(size=14, weight="bold")).pack(anchor="w", pady=(15, 5))

        ctk.CTkLabel(self.tab_user, text="Name / Anzeigename *:").pack(anchor="w", pady=(5, 2))
        self.user_name_entry = ctk.CTkEntry(self.tab_user, placeholder_text="Ihr Name")
        self.user_name_entry.insert(0, self.profile.user.name)
        self.user_name_entry.pack(fill="x", pady=(0, 10))

        ctk.CTkLabel(self.tab_user, text="Abteilung / Department *:").pack(anchor="w", pady=(5, 2))
        self.user_dept_entry = ctk.CTkEntry(self.tab_user, placeholder_text="z. B. Support, Entwicklung, Technik")
        self.user_dept_entry.insert(0, self.profile.user.department)
        self.user_dept_entry.pack(fill="x", pady=(0, 10))

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

    def open_create_profile_dialog(self):
        dialog = ctk.CTkInputDialog(
            text="Geben Sie den Namen des neuen Mitarbeiters ein:",
            title="Neues Mitarbeiter-Profil anlegen",
        )
        name_input = dialog.get_input()
        if name_input and name_input.strip():
            new_name = name_input.strip()
            from models.profile import UserInfo, UserProfile
            new_profile = UserProfile(user=UserInfo(name=new_name))
            self.storage_service.save_profile(new_profile)

            # Refresh list & switch
            self.profile = new_profile
            profiles_list = self.storage_service.list_profiles()
            self.profile_combo.configure(values=profiles_list)
            self.profile_combo.set(new_name)
            self.reload_user_fields()
            self.status_lbl.configure(text=f"Profil '{new_name}' angelegt und aktiviert!")
            if self.on_profile_updated:
                self.on_profile_updated()

    def on_switch_profile(self, selected_name: str):
        self.profile = self.storage_service.load_profile_by_name(selected_name)
        self.storage_service.save_profile(self.profile)
        self.reload_user_fields()
        self.status_lbl.configure(text=f"Profil auf '{selected_name}' gewechselt.")
        if self.on_profile_updated:
            self.on_profile_updated()

    def reload_user_fields(self):
        self.user_name_entry.delete(0, "end")
        self.user_name_entry.insert(0, self.profile.user.name)

        self.user_dept_entry.delete(0, "end")
        self.user_dept_entry.insert(0, self.profile.user.department)

        self.user_ext_entry.delete(0, "end")
        self.user_ext_entry.insert(0, self.profile.user.extension)

        self.user_email_entry.delete(0, "end")
        self.user_email_entry.insert(0, self.profile.user.email)

        self.user_mobile_entry.delete(0, "end")
        self.user_mobile_entry.insert(0, self.profile.user.mobile)

        self.theme_combo.set(self.profile.ui_settings.theme)
        self.layout_combo.set(get_layout_display(self.profile.ui_settings.default_layout))

    def setup_ui_tab(self):
        ctk.CTkLabel(self.tab_ui, text="Erscheinungsbild & Layout", font=ctk.CTkFont(size=14, weight="bold")).pack(anchor="w", pady=(10, 5))

        ctk.CTkLabel(self.tab_ui, text="Farb-Thema (Theme):").pack(anchor="w", pady=(5, 2))
        self.theme_combo = ctk.CTkOptionMenu(self.tab_ui, values=["Dark", "Light", "System"])
        self.theme_combo.set(self.profile.ui_settings.theme)
        self.theme_combo.pack(fill="x", pady=(0, 15))

        ctk.CTkLabel(self.tab_ui, text="Standard-Layout beim Start:").pack(anchor="w", pady=(5, 2))
        self.layout_combo = ctk.CTkOptionMenu(
            self.tab_ui,
            values=list(LAYOUT_DISPLAY.values())
        )
        self.layout_combo.set(get_layout_display(self.profile.ui_settings.default_layout))
        self.layout_combo.pack(fill="x", pady=(0, 15))

        self.demo_switch = ctk.CTkSwitch(  # type: ignore[attr-defined]
            self.tab_ui,
            text="🧪 Beispieldaten (Demofälle & Demokunden) in allen Ansichten einblenden"
        )
        if self.profile.ui_settings.show_demo_data is True:
            self.demo_switch.select()
        else:
            self.demo_switch.deselect()
        self.demo_switch.pack(anchor="w", pady=(0, 20))

        # Column widths reset section
        ctk.CTkLabel(self.tab_ui, text="Gespeicherte Spaltenbreiten (Profile-Level)", font=ctk.CTkFont(size=14, weight="bold")).pack(anchor="w", pady=(10, 5))

        widths = self.profile.ui_settings.column_widths
        w_str = (
            f"• Cockpit: Links {widths.get('cockpit_left', 300)}px | Mitte {widths.get('cockpit_center', 420)}px | Rechts {widths.get('cockpit_right', 320)}px\n"
            f"• Kanban-Board: Mindestspaltenbreite {widths.get('board_column', 280)}px\n"
            f"• Tabelle: ID {widths.get('table_col_id', 120)}px | Praxis {widths.get('table_col_practice', 220)}px | Titel {widths.get('table_col_title', 280)}px | Score {widths.get('table_col_score', 90)}px"
        )
        self.widths_label = ctk.CTkLabel(self.tab_ui, text=w_str, font=ctk.CTkFont(size=11), text_color=("gray40", "gray70"), justify="left", anchor="w")
        self.widths_label.pack(anchor="w", pady=(0, 12))

        btn_reset_widths = ctk.CTkButton(
            self.tab_ui,
            text="🔄 Alle Spaltenbreiten auf Standard zurücksetzen",
            command=self.on_reset_column_widths,
            fg_color="gray30",
            width=280,
        )
        btn_reset_widths.pack(anchor="w")

    def on_reset_column_widths(self):
        self.profile.ui_settings.reset_column_widths()
        self.storage_service.save_profile(self.profile)
        widths = self.profile.ui_settings.column_widths
        w_str = (
            f"• Cockpit: Links {widths.get('cockpit_left', 300)}px | Mitte {widths.get('cockpit_center', 420)}px | Rechts {widths.get('cockpit_right', 320)}px\n"
            f"• Kanban-Board: Mindestspaltenbreite {widths.get('board_column', 280)}px\n"
            f"• Tabelle: ID {widths.get('table_col_id', 120)}px | Praxis {widths.get('table_col_practice', 220)}px | Titel {widths.get('table_col_title', 280)}px | Score {widths.get('table_col_score', 90)}px"
        )
        self.widths_label.configure(text=w_str)
        self.status_lbl.configure(text="Alle Spaltenbreiten aller Ansichten auf Standard zurückgesetzt!")
        if self.on_profile_updated:
            self.on_profile_updated()

    def setup_paths_tab(self):
        from pathlib import Path
        ctk.CTkLabel(self.tab_paths, text="Speicherort & Dateipfade (EXE / Externe Daten)", font=ctk.CTkFont(size=14, weight="bold")).pack(anchor="w", pady=(10, 5))

        # Main Workspace Directory
        ctk.CTkLabel(self.tab_paths, text="Arbeitsbereich / Datenordner-Pfad:").pack(anchor="w", pady=(5, 2))
        ws_frame = ctk.CTkFrame(self.tab_paths, fg_color="transparent")
        ws_frame.pack(fill="x", pady=(0, 10))

        self.ws_entry = ctk.CTkEntry(ws_frame, placeholder_text="Pfad zum Datenordner...")
        self.ws_entry.insert(0, str(self.storage_service.config.workspace_dir))
        self.ws_entry.pack(side="left", fill="x", expand=True, padx=(0, 5))

        btn_browse_ws = ctk.CTkButton(ws_frame, text="📁 Ordner wählen", command=self.on_browse_workspace, width=120)
        btn_browse_ws.pack(side="right")

        # Custom Individual File Path Overrides
        ctk.CTkLabel(self.tab_paths, text="Benutzerdefinierte Einzeldateipfade (Optional):", font=ctk.CTkFont(size=12, weight="bold")).pack(anchor="w", pady=(10, 5))

        # Cases Path Override
        row_cases = ctk.CTkFrame(self.tab_paths, fg_color="transparent")
        row_cases.pack(fill="x", pady=2)
        ctk.CTkLabel(row_cases, text="Fälle (cases.json):", width=160, anchor="w").pack(side="left")
        self.path_cases_entry = ctk.CTkEntry(row_cases, placeholder_text="Standard im Datenordner")
        if self.storage_service.config.custom_cases_path:
            self.path_cases_entry.insert(0, str(self.storage_service.config.custom_cases_path))
        self.path_cases_entry.pack(side="left", fill="x", expand=True, padx=5)
        ctk.CTkButton(row_cases, text="Datei...", command=lambda: self.on_browse_file(self.path_cases_entry, "*.json"), width=70).pack(side="right")

        # Customers Path Override
        row_cust = ctk.CTkFrame(self.tab_paths, fg_color="transparent")
        row_cust.pack(fill="x", pady=2)
        ctk.CTkLabel(row_cust, text="Kunden (customers.json):", width=160, anchor="w").pack(side="left")
        self.path_cust_entry = ctk.CTkEntry(row_cust, placeholder_text="Standard im Datenordner")
        if self.storage_service.config.custom_customers_path:
            self.path_cust_entry.insert(0, str(self.storage_service.config.custom_customers_path))
        self.path_cust_entry.pack(side="left", fill="x", expand=True, padx=5)
        ctk.CTkButton(row_cust, text="Datei...", command=lambda: self.on_browse_file(self.path_cust_entry, "*.json"), width=70).pack(side="right")

        # Wiki DB Path Override
        row_wiki = ctk.CTkFrame(self.tab_paths, fg_color="transparent")
        row_wiki.pack(fill="x", pady=2)
        ctk.CTkLabel(row_wiki, text="Wiki DB (sqlite):", width=160, anchor="w").pack(side="left")
        self.path_wiki_entry = ctk.CTkEntry(row_wiki, placeholder_text="Standard im Datenordner")
        if self.storage_service.config.custom_wiki_db_path:
            self.path_wiki_entry.insert(0, str(self.storage_service.config.custom_wiki_db_path))
        self.path_wiki_entry.pack(side="left", fill="x", expand=True, padx=5)
        ctk.CTkButton(row_wiki, text="Datei...", command=lambda: self.on_browse_file(self.path_wiki_entry, "*.sqlite"), width=70).pack(side="right")

        # Reset button
        btn_reset_paths = ctk.CTkButton(self.tab_paths, text="🔄 Einzelpfade auf Standard zurücksetzen", command=self.on_reset_paths, fg_color="gray40", width=240)
        btn_reset_paths.pack(anchor="w", pady=(15, 5))

    def on_browse_workspace(self):
        from tkinter import filedialog
        chosen = filedialog.askdirectory(title="Datenordner auswählen", initialdir=self.ws_entry.get().strip() or None)
        if chosen:
            self.ws_entry.delete(0, "end")
            self.ws_entry.insert(0, chosen)

    def on_browse_file(self, entry_widget: ctk.CTkEntry, file_pattern: str):
        from tkinter import filedialog
        chosen = filedialog.askopenfilename(title="Datei auswählen", filetypes=[("Datendatei", file_pattern), ("Alle Dateien", "*.*")])
        if chosen:
            entry_widget.delete(0, "end")
            entry_widget.insert(0, chosen)

    def on_reset_paths(self):
        self.path_cases_entry.delete(0, "end")
        self.path_cust_entry.delete(0, "end")
        self.path_wiki_entry.delete(0, "end")

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
        from pathlib import Path
        name = self.user_name_entry.get().strip()
        if not name:
            self.status_lbl.configure(text="⚠️ Benutzername darf nicht leer sein!", text_color="red")
            return

        # Update User
        self.profile.user.name = name
        self.profile.user.department = self.user_dept_entry.get().strip() or "Support"
        self.profile.user.extension = self.user_ext_entry.get().strip()
        self.profile.user.email = self.user_email_entry.get().strip()
        self.profile.user.mobile = self.user_mobile_entry.get().strip()

        # Update UI Settings
        self.profile.ui_settings.theme = self.theme_combo.get()
        self.profile.ui_settings.default_layout = get_layout_val_from_display(self.layout_combo.get())
        if hasattr(self, "demo_switch"):
            self.profile.ui_settings.show_demo_data = bool(self.demo_switch.get())

        # Update Workspace & Custom File Paths
        ws_path_str = self.ws_entry.get().strip()
        if ws_path_str:
            self.storage_service.config.workspace_dir = Path(ws_path_str)

        cases_override = self.path_cases_entry.get().strip()
        self.storage_service.config.custom_cases_path = Path(cases_override) if cases_override else None

        cust_override = self.path_cust_entry.get().strip()
        self.storage_service.config.custom_customers_path = Path(cust_override) if cust_override else None

        wiki_override = self.path_wiki_entry.get().strip()
        self.storage_service.config.custom_wiki_db_path = Path(wiki_override) if wiki_override else None

        self.storage_service.config.ensure_directories()
        self.storage_service.config.save_user_config()

        # Update Wiki Settings
        self.profile.wiki_settings.api_url = self.wiki_url_entry.get().strip()
        self.profile.wiki_settings.token_id = self.wiki_token_id_entry.get().strip()
        self.profile.wiki_settings.token_secret = self.wiki_token_secret_entry.get().strip()
        self.profile.wiki_settings.sync_mode = self.sync_mode_combo.get()
        self.profile.wiki_settings.sync_on_startup = self.sync_startup_var.get()

        # Update Shortcuts & Scoring with conflict validation
        hk_new_val = self.hk_new.get().strip()
        hk_exp_val = self.hk_export.get().strip()
        hk_search_val = self.hk_search.get().strip()

        keys_list = [k for k in (hk_new_val, hk_exp_val, hk_search_val) if k]
        if len(keys_list) != len(set(keys_list)):
            self.status_lbl.configure(text="⚠️ Shortcut-Konflikt: Ein Hotkey darf nicht mehrfach zugewiesen werden!", text_color="red")
            return

        self.profile.shortcuts.new_case = hk_new_val
        self.profile.shortcuts.export_dialog = hk_exp_val
        self.profile.shortcuts.wiki_search = hk_search_val

        try:
            self.profile.scoring_matrix.vip_bonus_points = int(self.vip_bonus_entry.get().strip())
        except ValueError:
            pass

        self.storage_service.save_profile(self.profile)
        self.status_lbl.configure(text="✅ Einstellungen & Pfade gespeichert!", text_color="green")

        if self.on_profile_updated:
            self.on_profile_updated()

    def setup_backup_tab(self):
        from tkinter import filedialog
        from pathlib import Path
        from services.zip_backup_service import ZipBackupService
        from ui.dialogs.zip_import_dialog import ZipImportPathDialog

        ctk.CTkLabel(
            self.tab_backup,
            text="📦 Komplett-Datensicherung & ZIP-Archivierung",
            font=ctk.CTkFont(size=14, weight="bold"),
        ).pack(anchor="w", pady=(10, 5))

        desc_str = (
            "Exportieren Sie Ihren gesamten Datenbestand (alle Fälle, Kunden, Formulare, Exportvorlagen, Mitarbeiter "
            "und gespeicherten Anhang-Ordner) in eine komprimierte ZIP-Datei. Diese kann zur Sicherung oder für "
            "den Wechsel auf einen anderen Arbeitsplatz genutzt werden."
        )
        ctk.CTkLabel(
            self.tab_backup,
            text=desc_str,
            font=ctk.CTkFont(size=11),
            text_color=("gray30", "gray80"),
            justify="left",
            anchor="w",
            wraplength=800,
        ).pack(anchor="w", pady=(0, 15))

        # Section 1: Export
        exp_card = ctk.CTkFrame(self.tab_backup, corner_radius=8)
        exp_card.pack(fill="x", pady=(0, 15), padx=2)

        ctk.CTkLabel(
            exp_card,
            text="1. Komplett-Datensatz als ZIP exportieren",
            font=ctk.CTkFont(size=12, weight="bold"),
        ).pack(anchor="w", padx=12, pady=(10, 2))

        ctk.CTkLabel(
            exp_card,
            text="Erzeugt ein Backup-Archiv inklusive allen Dateien in data/ und allen Dokumenten in attachments/.",
            font=ctk.CTkFont(size=11),
            text_color=("gray40", "gray70"),
            anchor="w",
        ).pack(anchor="w", padx=12, pady=(0, 10))

        btn_export = ctk.CTkButton(
            exp_card,
            text="📦 Komplett-Backup als ZIP exportieren...",
            command=self.on_click_export_zip,
            fg_color="dodgerblue",
            width=240,
        )
        btn_export.pack(anchor="w", padx=12, pady=(0, 12))

        # Section 2: Import
        imp_card = ctk.CTkFrame(self.tab_backup, corner_radius=8)
        imp_card.pack(fill="x", pady=(0, 15), padx=2)

        ctk.CTkLabel(
            imp_card,
            text="2. Datensicherung aus ZIP-Datei importieren",
            font=ctk.CTkFont(size=12, weight="bold"),
        ).pack(anchor="w", padx=12, pady=(10, 2))

        ctk.CTkLabel(
            imp_card,
            text="Stellt Datensätze und Anhänge aus einem ZIP-Archiv an den von Ihnen gewählten Ziel-Speicherorten wieder her.",
            font=ctk.CTkFont(size=11),
            text_color=("gray40", "gray70"),
            anchor="w",
        ).pack(anchor="w", padx=12, pady=(0, 10))

        btn_import = ctk.CTkButton(
            imp_card,
            text="📥 Datensicherung aus ZIP importieren...",
            command=self.on_click_import_zip,
            fg_color="forestgreen",
            width=240,
        )
        btn_import.pack(anchor="w", padx=12, pady=(0, 12))

    def on_click_export_zip(self):
        from tkinter import filedialog
        from pathlib import Path
        from services.zip_backup_service import ZipBackupService

        dest_file = filedialog.asksaveasfilename(
            title="Datensicherung als ZIP speichern",
            defaultextension=".zip",
            filetypes=[("ZIP-Archiv", "*.zip")],
            initialfile="SupportCockpit_Backup.zip",
            parent=self,
        )
        if not dest_file:
            return

        res = ZipBackupService.export_backup_zip(self.storage_service, Path(dest_file))
        mb_size = res["total_bytes"] / (1024 * 1024)
        self.status_lbl.configure(
            text=f"✅ ZIP-Backup erfolgreich erstellt: {res['file_count']} Dateien ({mb_size:.2f} MB)",
            text_color="green",
        )

    def on_click_import_zip(self):
        from tkinter import filedialog
        from pathlib import Path
        from services.zip_backup_service import ZipBackupService
        from ui.dialogs.zip_import_dialog import ZipImportPathDialog

        zip_file = filedialog.askopenfilename(
            title="Datensicherung (ZIP-Datei) auswählen",
            filetypes=[("ZIP-Archiv", "*.zip")],
            parent=self,
        )
        if not zip_file:
            return

        zip_p = Path(zip_file)
        default_data = self.storage_service.config.data_dir
        default_att = self.storage_service.config.attachments_dir

        def on_confirmed(target_data: Path, target_att: Path):
            res = ZipBackupService.import_backup_zip(zip_p, target_data, target_att)

            # Update paths in config
            self.storage_service.config.custom_cases_path = target_data / "cases.json"
            self.storage_service.config.custom_customers_path = target_data / "customers.json"
            self.storage_service.config.ensure_directories()
            self.storage_service.config.save_user_config()

            self.status_lbl.configure(
                text=f"✅ Import abgeschlossen! {res['extracted_data_files']} Datendateien & {res['extracted_attachment_files']} Anhänge entpackt.",
                text_color="green",
            )
            if self.on_profile_updated:
                self.on_profile_updated()

        ZipImportPathDialog(
            self,
            zip_file_path=zip_p,
            default_data_dir=default_data,
            default_attachments_dir=default_att,
            on_import_confirmed=on_confirmed,
        )
