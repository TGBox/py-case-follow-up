from typing import TYPE_CHECKING, Any, cast
from collections.abc import Callable
from pathlib import Path
import tkinter as tk
from tkinter import filedialog
import customtkinter as ctk

from constants import COLOR_PANEL_BG, COLOR_PANEL_BORDER
from models.profile import BackupSettings
from services.i18n_service import tr
from services.zip_backup_service import ZipBackupService
from ui.dialogs.zip_import_dialog import ZipImportPathDialog


class PathsSettingsTabMixin:
    """Mixin for Storage Locations, Custom Overrides, ZIP Export/Import, and Backup Retention."""

    if TYPE_CHECKING:
        tab_paths: ctk.CTkFrame
        profile: Any
        storage_service: Any
        status_lbl: ctk.CTkLabel
        on_profile_updated: Callable[[], None] | None
        register_i18n: Callable[..., Any]

    def setup_paths_tab(self) -> None:
        self.paths_scroll = ctk.CTkScrollableFrame(self.tab_paths, fg_color="transparent")
        self.paths_scroll.pack(fill="both", expand=True, padx=5, pady=5)

        # --- Sektion 1: Speicherorte & Dateipfade ---
        self.register_i18n(
            ctk.CTkLabel(self.paths_scroll, text=tr("profile.paths_title", "Speicherort & Dateipfade (EXE / Externe Daten)"), font=ctk.CTkFont(size=14, weight="bold")),
            "profile.paths_title",
            "Speicherort & Dateipfade (EXE / Externe Daten)",
        ).pack(anchor="w", pady=(5, 5))

        # Main Workspace Directory
        self.register_i18n(
            ctk.CTkLabel(self.paths_scroll, text=tr("profile.workspace_label", "Arbeitsbereich / Datenordner-Pfad:")),
            "profile.workspace_label",
            "Arbeitsbereich / Datenordner-Pfad:",
        ).pack(anchor="w", pady=(5, 2))
        ws_frame = ctk.CTkFrame(self.paths_scroll, fg_color="transparent")
        ws_frame.pack(fill="x", pady=(0, 10))

        self.ws_entry = self.register_i18n(
            ctk.CTkEntry(ws_frame, placeholder_text=tr("profile.workspace_placeholder", "Pfad zum Datenordner...")),
            "profile.workspace_placeholder",
            "Pfad zum Datenordner...",
            attr="placeholder_text",
        )
        self.ws_entry.insert(0, str(self.storage_service.config.workspace_dir))
        self.ws_entry.pack(side="left", fill="x", expand=True, padx=(0, 5))

        btn_browse_ws = self.register_i18n(
            ctk.CTkButton(ws_frame, text=tr("profile.browse_folder", "📁 Ordner wählen"), command=self.on_browse_workspace, width=120),
            "profile.browse_folder",
            "📁 Ordner wählen",
        )
        btn_browse_ws.pack(side="right")

        # Custom Individual File Path Overrides
        self.register_i18n(
            ctk.CTkLabel(self.paths_scroll, text=tr("profile.custom_overrides", "Benutzerdefinierte Einzeldateipfade (Optional):"), font=ctk.CTkFont(size=12, weight="bold")),
            "profile.custom_overrides",
            "Benutzerdefinierte Einzeldateipfade (Optional):",
        ).pack(anchor="w", pady=(10, 5))

        # Cases Path Override
        row_cases = ctk.CTkFrame(self.paths_scroll, fg_color="transparent")
        row_cases.pack(fill="x", pady=2)
        self.register_i18n(
            ctk.CTkLabel(row_cases, text=tr("profile.cases_file", "Fälle (cases.json):"), width=160, anchor="w"),
            "profile.cases_file",
            "Fälle (cases.json):",
        ).pack(side="left")
        self.path_cases_entry = self.register_i18n(
            ctk.CTkEntry(row_cases, placeholder_text=tr("profile.default_in_data", "Standard im Datenordner")),
            "profile.default_in_data",
            "Standard im Datenordner",
            attr="placeholder_text",
        )
        if self.storage_service.config.custom_cases_path:
            self.path_cases_entry.insert(0, str(self.storage_service.config.custom_cases_path))
        self.path_cases_entry.pack(side="left", fill="x", expand=True, padx=5)
        self.register_i18n(
            ctk.CTkButton(row_cases, text=tr("profile.file_browse", "Datei..."), command=lambda: self.on_browse_file(self.path_cases_entry, "*.json"), width=70),
            "profile.file_browse",
            "Datei...",
        ).pack(side="right")

        # Customers Path Override
        row_cust = ctk.CTkFrame(self.paths_scroll, fg_color="transparent")
        row_cust.pack(fill="x", pady=2)
        self.register_i18n(
            ctk.CTkLabel(row_cust, text=tr("profile.cust_file", "Kunden (customers.json):"), width=160, anchor="w"),
            "profile.cust_file",
            "Kunden (customers.json):",
        ).pack(side="left")
        self.path_cust_entry = self.register_i18n(
            ctk.CTkEntry(row_cust, placeholder_text=tr("profile.default_in_data", "Standard im Datenordner")),
            "profile.default_in_data",
            "Standard im Datenordner",
            attr="placeholder_text",
        )
        if self.storage_service.config.custom_customers_path:
            self.path_cust_entry.insert(0, str(self.storage_service.config.custom_customers_path))
        self.path_cust_entry.pack(side="left", fill="x", expand=True, padx=5)
        self.register_i18n(
            ctk.CTkButton(row_cust, text=tr("profile.file_browse", "Datei..."), command=lambda: self.on_browse_file(self.path_cust_entry, "*.json"), width=70),
            "profile.file_browse",
            "Datei...",
        ).pack(side="right")

        # Wiki DB Path Override
        row_wiki = ctk.CTkFrame(self.paths_scroll, fg_color="transparent")
        row_wiki.pack(fill="x", pady=2)
        self.register_i18n(
            ctk.CTkLabel(row_wiki, text=tr("profile.wiki_file", "Wiki DB (sqlite):"), width=160, anchor="w"),
            "profile.wiki_file",
            "Wiki DB (sqlite):",
        ).pack(side="left")
        self.path_wiki_entry = self.register_i18n(
            ctk.CTkEntry(row_wiki, placeholder_text=tr("profile.default_in_data", "Standard im Datenordner")),
            "profile.default_in_data",
            "Standard im Datenordner",
            attr="placeholder_text",
        )
        if self.storage_service.config.custom_wiki_db_path:
            self.path_wiki_entry.insert(0, str(self.storage_service.config.custom_wiki_db_path))
        self.path_wiki_entry.pack(side="left", fill="x", expand=True, padx=5)
        self.register_i18n(
            ctk.CTkButton(row_wiki, text=tr("profile.file_browse", "Datei..."), command=lambda: self.on_browse_file(self.path_wiki_entry, "*.sqlite"), width=70),
            "profile.file_browse",
            "Datei...",
        ).pack(side="right")

        # Reset button
        btn_reset_paths = self.register_i18n(
            ctk.CTkButton(self.paths_scroll, text=tr("profile.reset_paths_btn", "🔄 Einzelpfade auf Standard zurücksetzen"), command=self.on_reset_paths, fg_color="gray40", width=240),
            "profile.reset_paths_btn",
            "🔄 Einzelpfade auf Standard zurücksetzen",
        )
        btn_reset_paths.pack(anchor="w", pady=(15, 20))

        # --- Sektion 2: Komplett-Datensicherung & ZIP-Archivierung (Datenexport / Import) ---
        self.register_i18n(
            ctk.CTkLabel(
                self.paths_scroll,
                text=tr("profile.backup_title", "📦 Komplett-Datensicherung & ZIP-Archivierung"),
                font=ctk.CTkFont(size=14, weight="bold"),
            ),
            "profile.backup_title",
            "📦 Komplett-Datensicherung & ZIP-Archivierung",
        ).pack(anchor="w", pady=(10, 5))

        desc_str = tr(
            "profile.backup_desc",
            "Exportieren Sie Ihren gesamten Datenbestand (alle Fälle, Kunden, Formulare, Exportvorlagen, Mitarbeiter "
            "und gespeicherten Anhang-Ordner) in eine komprimierte ZIP-Datei. Diese kann zur Sicherung oder für "
            "den Wechsel auf einen anderen Arbeitsplatz genutzt werden.",
        )
        ctk.CTkLabel(
            self.paths_scroll,
            text=desc_str,
            font=ctk.CTkFont(size=11),
            text_color=("gray30", "gray80"),
            justify="left",
            anchor="w",
            wraplength=800,
        ).pack(anchor="w", pady=(0, 15))

        # Section 2.1: Export
        exp_card = ctk.CTkFrame(self.paths_scroll, corner_radius=8, fg_color=COLOR_PANEL_BG, border_width=1, border_color=COLOR_PANEL_BORDER)
        exp_card.pack(fill="x", pady=(0, 15), padx=2)

        self.register_i18n(
            ctk.CTkLabel(
                exp_card,
                text=tr("profile.backup_exp_title", "1. Komplett-Datensatz als ZIP exportieren"),
                font=ctk.CTkFont(size=12, weight="bold"),
            ),
            "profile.backup_exp_title",
            "1. Komplett-Datensatz als ZIP exportieren",
        ).pack(anchor="w", padx=12, pady=(10, 2))

        self.register_i18n(
            ctk.CTkLabel(
                exp_card,
                text=tr("profile.backup_exp_desc", "Erzeugt ein Backup-Archiv inklusive allen Dateien in data/ und allen Dokumenten in attachments/."),
                font=ctk.CTkFont(size=11),
                text_color=("gray40", "gray70"),
                anchor="w",
            ),
            "profile.backup_exp_desc",
            "Erzeugt ein Backup-Archiv inklusive allen Dateien in data/ und allen Dokumenten in attachments/.",
        ).pack(anchor="w", padx=12, pady=(0, 10))

        btn_export = self.register_i18n(
            ctk.CTkButton(
                exp_card,
                text=tr("profile.backup_exp_btn", "📦 Komplett-Backup als ZIP exportieren..."),
                command=self.on_click_export_zip,
                fg_color="dodgerblue",
                width=240,
            ),
            "profile.backup_exp_btn",
            "📦 Komplett-Backup als ZIP exportieren...",
        )
        btn_export.pack(anchor="w", padx=12, pady=(0, 12))

        # Section 2.2: Import
        imp_card = ctk.CTkFrame(self.paths_scroll, corner_radius=8, fg_color=COLOR_PANEL_BG, border_width=1, border_color=COLOR_PANEL_BORDER)
        imp_card.pack(fill="x", pady=(0, 15), padx=2)

        self.register_i18n(
            ctk.CTkLabel(
                imp_card,
                text=tr("profile.backup_imp_title", "2. Datensicherung aus ZIP-Datei importieren"),
                font=ctk.CTkFont(size=12, weight="bold"),
            ),
            "profile.backup_imp_title",
            "2. Datensicherung aus ZIP-Datei importieren",
        ).pack(anchor="w", padx=12, pady=(10, 2))

        self.register_i18n(
            ctk.CTkLabel(
                imp_card,
                text=tr("profile.backup_imp_desc", "Stellt Datensätze und Anhänge aus einem ZIP-Archiv an den von Ihnen gewählten Ziel-Speicherorten wieder her."),
                font=ctk.CTkFont(size=11),
                text_color=("gray40", "gray70"),
                anchor="w",
            ),
            "profile.backup_imp_desc",
            "Stellt Datensätze und Anhänge aus einem ZIP-Archiv an den von Ihnen gewählten Ziel-Speicherorten wieder her.",
        ).pack(anchor="w", padx=12, pady=(0, 10))

        btn_import = self.register_i18n(
            ctk.CTkButton(
                imp_card,
                text=tr("profile.backup_imp_btn", "📥 Datensicherung aus ZIP importieren..."),
                command=self.on_click_import_zip,
                fg_color="forestgreen",
                width=240,
            ),
            "profile.backup_imp_btn",
            "📥 Datensicherung aus ZIP importieren...",
        )
        btn_import.pack(anchor="w", padx=12, pady=(0, 12))

        # --- Sektion 3: Automatische Backup-Aufbewahrung (Retention) ---
        self.register_i18n(
            ctk.CTkLabel(
                self.paths_scroll,
                text=tr("profile.retention_title", "🔄 Automatische Backup-Aufbewahrung (Retention)"),
                font=ctk.CTkFont(size=14, weight="bold"),
            ),
            "profile.retention_title",
            "🔄 Automatische Backup-Aufbewahrung (Retention)",
        ).pack(anchor="w", pady=(15, 5))

        self.register_i18n(
            ctk.CTkLabel(
                self.paths_scroll,
                text=tr(
                    "profile.retention_desc",
                    "Tägliche Sicherungen (cases_YYYY-MM-DD.json) werden beim Programmstart nach dem Großvater-Vater-Sohn-Prinzip bereinigt: Die letzten Tage vollständig behalten, danach wöchentlich und monatlich verdichten. Ältere Backups werden automatisch gelöscht.",
                ),
                font=ctk.CTkFont(size=11),
                text_color=("gray40", "gray70"),
                justify="left",
                anchor="w",
                wraplength=800,
            ),
            "profile.retention_desc",
            "Tägliche Sicherungen (cases_YYYY-MM-DD.json) werden beim Programmstart nach dem Großvater-Vater-Sohn-Prinzip bereinigt: Die letzten Tage vollständig behalten, danach wöchentlich und monatlich verdichten. Ältere Backups werden automatisch gelöscht.",
        ).pack(anchor="w", pady=(0, 10))

        retention_card = ctk.CTkFrame(self.paths_scroll, corner_radius=8, fg_color=COLOR_PANEL_BG, border_width=1, border_color=COLOR_PANEL_BORDER)
        retention_card.pack(fill="x", pady=(0, 15), padx=2)

        # Row 1: Daily days
        row_daily = ctk.CTkFrame(retention_card, fg_color="transparent")
        row_daily.pack(fill="x", padx=12, pady=(10, 4))
        self.register_i18n(
            ctk.CTkLabel(row_daily, text=tr("profile.retention_daily", "Tägliche Backups (Tage vollständig behalten):"), width=340, anchor="w"),
            "profile.retention_daily",
            "Tägliche Backups (Tage vollständig behalten):",
        ).pack(side="left")
        self.retention_daily_entry = ctk.CTkEntry(row_daily, width=80)
        self.retention_daily_entry.insert(0, str(getattr(getattr(self.profile, "backup_settings", None), "daily_days", 7)))
        self.retention_daily_entry.pack(side="left", padx=5)

        # Row 2: Weekly weeks
        row_weekly = ctk.CTkFrame(retention_card, fg_color="transparent")
        row_weekly.pack(fill="x", padx=12, pady=4)
        self.register_i18n(
            ctk.CTkLabel(row_weekly, text=tr("profile.retention_weekly", "Wöchentliche Backups (Wochen je 1 Backup):"), width=340, anchor="w"),
            "profile.retention_weekly",
            "Wöchentliche Backups (Wochen je 1 Backup):",
        ).pack(side="left")
        self.retention_weekly_entry = ctk.CTkEntry(row_weekly, width=80)
        self.retention_weekly_entry.insert(0, str(getattr(getattr(self.profile, "backup_settings", None), "weekly_weeks", 4)))
        self.retention_weekly_entry.pack(side="left", padx=5)

        # Row 3: Monthly months
        row_monthly = ctk.CTkFrame(retention_card, fg_color="transparent")
        row_monthly.pack(fill="x", padx=12, pady=(4, 10))
        self.register_i18n(
            ctk.CTkLabel(row_monthly, text=tr("profile.retention_monthly", "Monatliche Backups (Monate je 1 Backup):"), width=340, anchor="w"),
            "profile.retention_monthly",
            "Monatliche Backups (Monate je 1 Backup):",
        ).pack(side="left")
        self.retention_monthly_entry = ctk.CTkEntry(row_monthly, width=80)
        self.retention_monthly_entry.insert(0, str(getattr(getattr(self.profile, "backup_settings", None), "monthly_months", 6)))
        self.retention_monthly_entry.pack(side="left", padx=5)

        # Row 4: Manual prune button
        btn_prune = self.register_i18n(
            ctk.CTkButton(
                retention_card,
                text=tr("profile.retention_prune_now_btn", "🧹 Jetzt alte Backups bereinigen"),
                command=self.on_click_prune_backups,
                fg_color="gray40",
                hover_color="gray50",
                width=240,
            ),
            "profile.retention_prune_now_btn",
            "🧹 Jetzt alte Backups bereinigen",
        )
        btn_prune.pack(anchor="w", padx=12, pady=(0, 12))

    def on_browse_workspace(self) -> None:
        chosen = filedialog.askdirectory(title=tr("profile.browse_folder_title", "Datenordner auswählen"), initialdir=self.ws_entry.get().strip() or None)
        if chosen:
            self.ws_entry.delete(0, "end")
            self.ws_entry.insert(0, chosen)

    def on_browse_file(self, entry_widget: ctk.CTkEntry, file_pattern: str) -> None:
        chosen = filedialog.askopenfilename(title=tr("profile.browse_file_title", "Datei auswählen"), filetypes=[("Datendatei", file_pattern), ("Alle Dateien", "*.*")])
        if chosen:
            entry_widget.delete(0, "end")
            entry_widget.insert(0, chosen)

    def on_reset_paths(self) -> None:
        self.path_cases_entry.delete(0, "end")
        self.path_cust_entry.delete(0, "end")
        self.path_wiki_entry.delete(0, "end")

    def on_click_export_zip(self) -> None:
        dest_file = filedialog.asksaveasfilename(
            title=tr("profile.save_zip_title", "Datensicherung als ZIP speichern"),
            defaultextension=".zip",
            filetypes=[("ZIP-Archiv", "*.zip")],
            initialfile="SupportCockpit_Backup.zip",
            parent=cast(tk.Misc, self),
        )
        if not dest_file:
            return

        res = ZipBackupService.export_backup_zip(self.storage_service, Path(dest_file))
        mb_size = res["total_bytes"] / (1024 * 1024)
        self.status_lbl.configure(
            text=tr(
                "profile.zip_backup_success",
                "✅ ZIP-Backup erfolgreich erstellt: {file_count} Dateien ({mb_size:.2f} MB)",
                file_count=res["file_count"],
                mb_size=mb_size,
            ),
            text_color="green",
        )

    def on_click_import_zip(self) -> None:
        zip_file = filedialog.askopenfilename(
            title=tr("profile.select_zip_title", "Datensicherung (ZIP-Datei) auswählen"),
            filetypes=[("ZIP-Archiv", "*.zip")],
            parent=cast(tk.Misc, self),
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
                text=tr(
                    "profile.zip_import_success",
                    "✅ Import abgeschlossen! {data_files} Datendateien & {attachment_files} Anhänge entpackt.",
                    data_files=res["extracted_data_files"],
                    attachment_files=res["extracted_attachment_files"],
                ),
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

    def on_click_prune_backups(self) -> None:
        try:
            d = max(1, int(self.retention_daily_entry.get().strip())) if hasattr(self, "retention_daily_entry") else 7
            w = max(0, int(self.retention_weekly_entry.get().strip())) if hasattr(self, "retention_weekly_entry") else 4
            m = max(0, int(self.retention_monthly_entry.get().strip())) if hasattr(self, "retention_monthly_entry") else 6
            active_settings = BackupSettings(daily_days=d, weekly_weeks=w, monthly_months=m)
        except Exception:
            active_settings = getattr(self.profile, "backup_settings", BackupSettings())

        deleted = self.storage_service.prune_old_backups(settings=active_settings)
        if deleted:
            self.status_lbl.configure(
                text=tr("profile.retention_pruned_count", "🧹 {count} veraltete Backup(s) bereinigt.", count=len(deleted)),
                text_color="green",
            )
        else:
            self.status_lbl.configure(
                text=tr("profile.retention_pruned_none", "ℹ Keine veralteten Backups zum Bereinigen gefunden."),
                text_color="gray70",
            )

    def save_paths_settings(self) -> bool:
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

        # Update Backup Retention Settings
        if hasattr(self, "retention_daily_entry"):
            try:
                self.profile.backup_settings.daily_days = max(1, int(self.retention_daily_entry.get().strip()))
            except ValueError:
                pass
        if hasattr(self, "retention_weekly_entry"):
            try:
                self.profile.backup_settings.weekly_weeks = max(0, int(self.retention_weekly_entry.get().strip()))
            except ValueError:
                pass
        if hasattr(self, "retention_monthly_entry"):
            try:
                self.profile.backup_settings.monthly_months = max(0, int(self.retention_monthly_entry.get().strip()))
            except ValueError:
                pass
        return True

    def setup_backup_tab(self) -> None:
        """Integrated into setup_paths_tab; retained for backward compatibility."""
        pass
