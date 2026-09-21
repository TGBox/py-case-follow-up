from typing import TYPE_CHECKING, Any, cast
from collections.abc import Callable
from pathlib import Path
import tkinter as tk
from tkinter import filedialog
import customtkinter as ctk

from constants import (
    BTN_WIDTH_XS,
    BTN_WIDTH_MD,
    BTN_WIDTH_WIDE,
    COLOR_INFO,
    COLOR_LABEL_GRAY70,
    COLOR_MUTED_BODY,
    COLOR_MUTED_GRAY_FG,
    COLOR_MUTED_GRAY_HOVER,
    COLOR_PANEL_BG,
    COLOR_PANEL_BORDER,
    COLOR_SUCCESS,
    COLOR_TIP_TEXT,
    CORNER_RADIUS_CARD,
    DEFAULT_BACKUP_DAILY_DAYS,
    DEFAULT_BACKUP_MONTHLY_MONTHS,
    DEFAULT_BACKUP_WEEKLY_WEEKS,
    DEFAULT_BACKUP_ZIP_FILENAME,
    ENTRY_WIDTH_NUMERIC,
    get_file_types_data_file,
    get_file_types_zip,
    FILENAME_APP_PROFILE,
    FILENAME_ARCHIVE,
    FILENAME_CASES,
    FILENAME_COLLEAGUES,
    FILENAME_CUSTOMERS,
    FILENAME_EXPORT_TEMPLATES,
    FILENAME_QUESTION_SCHEMAS,
    FILENAME_WIKI_INDEX,
    FONT_SIZE_BODY,
    FONT_SIZE_SM,
    FONT_SIZE_SUBTITLE,
    LABEL_WIDTH_LG,
    LABEL_WIDTH_XL,
    PAD_NONE,
    PAD_XS,
    PAD_SM,
    PAD_GAP,
    PAD_MD,
    PAD_LG,
    PAD_XL,
    PROFILE_CARD_DESC_WRAPLENGTH,
    PROFILE_DESC_WRAPLENGTH,
)
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
        ws_entry: ctk.CTkEntry
        path_cases_entry: ctk.CTkEntry
        path_archive_entry: ctk.CTkEntry
        path_cust_entry: ctk.CTkEntry
        path_profile_entry: ctk.CTkEntry
        path_colleagues_entry: ctk.CTkEntry
        path_schemas_entry: ctk.CTkEntry
        path_templates_entry: ctk.CTkEntry
        path_wiki_entry: ctk.CTkEntry

    def setup_paths_tab(self) -> None:
        from utils.ui_utils import enable_auto_hiding_scrollbar
        self.paths_scroll = ctk.CTkScrollableFrame(self.tab_paths, fg_color="transparent")
        self.paths_scroll.pack(fill="both", expand=True, padx=PAD_SM, pady=PAD_SM)
        enable_auto_hiding_scrollbar(self.paths_scroll)

        # 2-Column Side-by-Side Container
        cols_container = ctk.CTkFrame(self.paths_scroll, fg_color="transparent")
        cols_container.pack(fill="both", expand=True, padx=PAD_SM, pady=PAD_SM)
        cols_container.columnconfigure(0, weight=1, uniform="paths_cols")
        cols_container.columnconfigure(1, weight=1, uniform="paths_cols")

        left_col = ctk.CTkFrame(cols_container, fg_color="transparent")
        left_col.grid(row=0, column=0, sticky="nsew", padx=(PAD_NONE, PAD_XL))

        right_col = ctk.CTkFrame(cols_container, fg_color="transparent")
        right_col.grid(row=0, column=1, sticky="nsew", padx=(PAD_XL, PAD_NONE))

        # =========================================================================
        # --- LINKE SPALTE: Speicherorte & Retention ---
        # =========================================================================
        self.register_i18n(
            ctk.CTkLabel(left_col, text=tr("profile.paths_title", "Speicherort & Dateipfade (EXE / Externe Daten)"), font=ctk.CTkFont(size=FONT_SIZE_SUBTITLE, weight="bold")),
            "profile.paths_title",
            "Speicherort & Dateipfade (EXE / Externe Daten)",
        ).pack(anchor="w", pady=(PAD_SM, PAD_SM))

        # Main Workspace Directory
        self.register_i18n(
            ctk.CTkLabel(left_col, text=tr("profile.workspace_label", "Arbeitsbereich / Datenordner-Pfad:")),
            "profile.workspace_label",
            "Arbeitsbereich / Datenordner-Pfad:",
        ).pack(anchor="w", pady=(PAD_SM, PAD_XS))
        ws_frame = ctk.CTkFrame(left_col, fg_color="transparent")
        ws_frame.pack(fill="x", pady=(PAD_NONE, PAD_MD))

        self.ws_entry = self.register_i18n(
            ctk.CTkEntry(ws_frame, placeholder_text=tr("profile.workspace_placeholder", "Pfad zum Datenordner...")),
            "profile.workspace_placeholder",
            "Pfad zum Datenordner...",
            attr="placeholder_text",
        )
        ws_init = getattr(getattr(self.profile, "path_settings", None), "workspace_dir", "") or str(self.storage_service.config.workspace_dir)
        self.ws_entry.insert(0, ws_init)
        self.ws_entry.pack(side="left", fill="x", expand=True, padx=(PAD_NONE, PAD_SM))
        self.ws_entry.bind("<FocusOut>", lambda e: self.on_workspace_entry_changed())
        self.ws_entry.bind("<Return>", lambda e: self.on_workspace_entry_changed())

        btn_browse_ws = self.register_i18n(
            ctk.CTkButton(ws_frame, text=tr("profile.browse_folder", "📁 Ordner wählen"), command=self.on_browse_workspace, width=BTN_WIDTH_MD),
            "profile.browse_folder",
            "📁 Ordner wählen",
        )
        btn_browse_ws.pack(side="right")

        # Custom Individual File Path Overrides
        self.register_i18n(
            ctk.CTkLabel(left_col, text=tr("profile.custom_overrides", "Benutzerdefinierte Einzeldateipfade (Optional):"), font=ctk.CTkFont(size=FONT_SIZE_BODY, weight="bold")),
            "profile.custom_overrides",
            "Benutzerdefinierte Einzeldateipfade (Optional):",
        ).pack(anchor="w", pady=(PAD_MD, PAD_SM))

        path_specs = [
            ("path_cases_entry", "custom_cases_path", "profile.cases_file", "Fälle (cases.json):", "*.json"),
            ("path_archive_entry", "custom_archive_path", "profile.archive_file", "Archiv (archive.json):", "*.json"),
            ("path_cust_entry", "custom_customers_path", "profile.cust_file", "Kunden (customers.json):", "*.json"),
            ("path_profile_entry", "custom_app_profile_path", "profile.app_profile_file", "App-Profil (app_profile.json):", "*.json"),
            ("path_colleagues_entry", "custom_colleagues_path", "profile.colleagues_file", "Kollegen (colleagues.json):", "*.json"),
            ("path_schemas_entry", "custom_question_schemas_path", "profile.schemas_file", "Formulare (question_schemas.json):", "*.json"),
            ("path_templates_entry", "custom_export_templates_path", "profile.templates_file", "Export-Vorlagen (export_templates.json):", "*.json"),
            ("path_wiki_entry", "custom_wiki_db_path", "profile.wiki_file", "Wiki DB (sqlite):", "*.sqlite"),
        ]

        for attr_name, config_attr, label_key, label_default, file_pat in path_specs:
            row = ctk.CTkFrame(left_col, fg_color="transparent")
            row.pack(fill="x", pady=1)

            entry = self.register_i18n(
                ctk.CTkEntry(row, placeholder_text=tr("profile.default_in_data", "Standard im Datenordner")),
                "profile.default_in_data",
                "Standard im Datenordner",
                attr="placeholder_text",
            )
            val_init = getattr(getattr(self.profile, "path_settings", None), config_attr, "") or (
                str(getattr(self.storage_service.config, config_attr))
                if getattr(self.storage_service.config, config_attr)
                else ""
            )
            if val_init:
                entry.insert(0, val_init)
            setattr(self, attr_name, entry)

            btn = self.register_i18n(
                ctk.CTkButton(
                    row,
                    text=tr("profile.file_browse", "Datei..."),
                    command=lambda e=entry, pat=file_pat: self.on_browse_file(e, pat),
                    width=BTN_WIDTH_XS,
                ),
                "profile.file_browse",
                "Datei...",
            )
            btn.pack(side="right")
            entry.pack(side="right", fill="x", expand=True, padx=PAD_SM)

            self.register_i18n(
                ctk.CTkLabel(row, text=tr(label_key, label_default), width=LABEL_WIDTH_LG, anchor="w"),
                label_key,
                label_default,
            ).pack(side="left")

        # Reset button
        btn_reset_paths = self.register_i18n(
            ctk.CTkButton(left_col, text=tr("profile.reset_paths_btn", "🔄 Einzelpfade auf Standard zurücksetzen"), command=self.on_reset_paths, fg_color=COLOR_MUTED_GRAY_FG, hover_color=COLOR_MUTED_GRAY_HOVER, width=BTN_WIDTH_WIDE),
            "profile.reset_paths_btn",
            "🔄 Einzelpfade auf Standard zurücksetzen",
        )
        btn_reset_paths.pack(anchor="w", pady=(PAD_MD, PAD_LG))

        # --- Sektion 2: Automatische Backup-Aufbewahrung (Retention) ---
        self.register_i18n(
            ctk.CTkLabel(
                left_col,
                text=tr("profile.retention_title", "🔄 Automatische Backup-Aufbewahrung (Retention)"),
                font=ctk.CTkFont(size=FONT_SIZE_SUBTITLE, weight="bold"),
            ),
            "profile.retention_title",
            "🔄 Automatische Backup-Aufbewahrung (Retention)",
        ).pack(anchor="w", pady=(PAD_MD, PAD_SM))

        self.register_i18n(
            ctk.CTkLabel(
                left_col,
                text=tr(
                    "profile.retention_desc",
                    "Tägliche Sicherungen (cases_YYYY-MM-DD.json) werden beim Programmstart nach dem Großvater-Vater-Sohn-Prinzip bereinigt: Die letzten Tage vollständig behalten, danach wöchentlich und monatlich verdichten. Ältere Backups werden automatisch gelöscht.",
                ),
                font=ctk.CTkFont(size=FONT_SIZE_SM),
                text_color=COLOR_TIP_TEXT,
                justify="left",
                anchor="w",
                wraplength=PROFILE_DESC_WRAPLENGTH,
            ),
            "profile.retention_desc",
            "Tägliche Sicherungen (cases_YYYY-MM-DD.json) werden beim Programmstart nach dem Großvater-Vater-Sohn-Prinzip bereinigt: Die letzten Tage vollständig behalten, danach wöchentlich und monatlich verdichten. Ältere Backups werden automatisch gelöscht.",
        ).pack(anchor="w", pady=(PAD_NONE, PAD_GAP))

        retention_card = ctk.CTkFrame(left_col, corner_radius=CORNER_RADIUS_CARD, fg_color=COLOR_PANEL_BG, border_width=1, border_color=COLOR_PANEL_BORDER)
        retention_card.pack(fill="x", pady=(PAD_NONE, PAD_MD), padx=PAD_XS)

        # Row 1: Daily days
        row_daily = ctk.CTkFrame(retention_card, fg_color="transparent")
        row_daily.pack(fill="x", padx=PAD_MD, pady=(PAD_MD, PAD_XS))
        self.register_i18n(
            ctk.CTkLabel(row_daily, text=tr("profile.retention_daily", "Tägliche Backups (Tage vollständig behalten):"), width=LABEL_WIDTH_XL, anchor="w"),
            "profile.retention_daily",
            "Tägliche Backups (Tage vollständig behalten):",
        ).pack(side="left")
        self.retention_daily_entry = ctk.CTkEntry(row_daily, width=ENTRY_WIDTH_NUMERIC)
        self.retention_daily_entry.insert(0, str(getattr(getattr(self.profile, "backup_settings", None), "daily_days", DEFAULT_BACKUP_DAILY_DAYS)))
        self.retention_daily_entry.pack(side="left", padx=PAD_SM)

        # Row 2: Weekly weeks
        row_weekly = ctk.CTkFrame(retention_card, fg_color="transparent")
        row_weekly.pack(fill="x", padx=PAD_MD, pady=PAD_XS)
        self.register_i18n(
            ctk.CTkLabel(row_weekly, text=tr("profile.retention_weekly", "Wöchentliche Backups (Wochen je 1 Backup):"), width=LABEL_WIDTH_XL, anchor="w"),
            "profile.retention_weekly",
            "Wöchentliche Backups (Wochen je 1 Backup):",
        ).pack(side="left")
        self.retention_weekly_entry = ctk.CTkEntry(row_weekly, width=ENTRY_WIDTH_NUMERIC)
        self.retention_weekly_entry.insert(0, str(getattr(getattr(self.profile, "backup_settings", None), "weekly_weeks", DEFAULT_BACKUP_WEEKLY_WEEKS)))
        self.retention_weekly_entry.pack(side="left", padx=PAD_SM)

        # Row 3: Monthly months
        row_monthly = ctk.CTkFrame(retention_card, fg_color="transparent")
        row_monthly.pack(fill="x", padx=PAD_MD, pady=(PAD_XS, PAD_MD))
        self.register_i18n(
            ctk.CTkLabel(row_monthly, text=tr("profile.retention_monthly", "Monatliche Backups (Monate je 1 Backup):"), width=LABEL_WIDTH_XL, anchor="w"),
            "profile.retention_monthly",
            "Monatliche Backups (Monate je 1 Backup):",
        ).pack(side="left")
        self.retention_monthly_entry = ctk.CTkEntry(row_monthly, width=ENTRY_WIDTH_NUMERIC)
        self.retention_monthly_entry.insert(0, str(getattr(getattr(self.profile, "backup_settings", None), "monthly_months", DEFAULT_BACKUP_MONTHLY_MONTHS)))
        self.retention_monthly_entry.pack(side="left", padx=PAD_SM)

        # Row 4: Manual prune button
        btn_prune = self.register_i18n(
            ctk.CTkButton(
                retention_card,
                text=tr("profile.retention_prune_now_btn", "🧹 Jetzt alte Backups bereinigen"),
                command=self.on_click_prune_backups,
                fg_color=COLOR_MUTED_GRAY_FG,
                hover_color=COLOR_MUTED_GRAY_HOVER,
                width=BTN_WIDTH_WIDE,
            ),
            "profile.retention_prune_now_btn",
            "🧹 Jetzt alte Backups bereinigen",
        )
        btn_prune.pack(anchor="w", padx=PAD_MD, pady=(PAD_NONE, PAD_MD))

        # =========================================================================
        # --- RECHTE SPALTE: Komplett-Datensicherung & ZIP-Archivierung ---
        # =========================================================================
        self.register_i18n(
            ctk.CTkLabel(
                right_col,
                text=tr("profile.backup_title", "📦 Komplett-Datensicherung & ZIP-Archivierung"),
                font=ctk.CTkFont(size=FONT_SIZE_SUBTITLE, weight="bold"),
            ),
            "profile.backup_title",
            "📦 Komplett-Datensicherung & ZIP-Archivierung",
        ).pack(anchor="w", pady=(PAD_SM, PAD_SM))

        desc_str = tr(
            "profile.backup_desc",
            "Exportieren Sie Ihren gesamten Datenbestand (alle Fälle, Kunden, Formulare, Exportvorlagen, Mitarbeiter "
            "und gespeicherten Anhang-Ordner) in eine komprimierte ZIP-Datei. Diese kann zur Sicherung oder für "
            "den Wechsel auf einen anderen Arbeitsplatz genutzt werden.",
        )
        ctk.CTkLabel(
            right_col,
            text=desc_str,
            font=ctk.CTkFont(size=FONT_SIZE_SM),
            text_color=COLOR_MUTED_BODY,
            justify="left",
            anchor="w",
            wraplength=PROFILE_DESC_WRAPLENGTH,
        ).pack(anchor="w", pady=(PAD_NONE, PAD_LG))

        # Section 2.1: Export
        exp_card = ctk.CTkFrame(right_col, corner_radius=CORNER_RADIUS_CARD, fg_color=COLOR_PANEL_BG, border_width=1, border_color=COLOR_PANEL_BORDER)
        exp_card.pack(fill="x", pady=(PAD_NONE, PAD_LG), padx=PAD_XS)

        self.register_i18n(
            ctk.CTkLabel(
                exp_card,
                text=tr("profile.backup_exp_title", "1. Komplett-Datensatz als ZIP exportieren"),
                font=ctk.CTkFont(size=FONT_SIZE_BODY, weight="bold"),
            ),
            "profile.backup_exp_title",
            "1. Komplett-Datensatz als ZIP exportieren",
        ).pack(anchor="w", padx=PAD_LG, pady=(PAD_MD, PAD_XS))

        self.register_i18n(
            ctk.CTkLabel(
                exp_card,
                text=tr("profile.backup_exp_desc", "Erzeugt ein Backup-Archiv inklusive allen Dateien in data/ und allen Dokumenten in attachments/."),
                font=ctk.CTkFont(size=FONT_SIZE_SM),
                text_color=COLOR_TIP_TEXT,
                anchor="w",
                wraplength=PROFILE_CARD_DESC_WRAPLENGTH,
                justify="left",
            ),
            "profile.backup_exp_desc",
            "Erzeugt ein Backup-Archiv inklusive allen Dateien in data/ und allen Dokumenten in attachments/.",
        ).pack(anchor="w", padx=PAD_LG, pady=(PAD_NONE, PAD_MD))

        btn_export = self.register_i18n(
            ctk.CTkButton(
                exp_card,
                text=tr("profile.backup_exp_btn", "📦 Komplett-Backup als ZIP exportieren..."),
                command=self.on_click_export_zip,
                fg_color=COLOR_INFO,
                width=BTN_WIDTH_WIDE,
            ),
            "profile.backup_exp_btn",
            "📦 Komplett-Backup als ZIP exportieren...",
        )
        btn_export.pack(anchor="w", padx=PAD_LG, pady=(PAD_NONE, PAD_LG))

        # Section 2.2: Import
        imp_card = ctk.CTkFrame(right_col, corner_radius=CORNER_RADIUS_CARD, fg_color=COLOR_PANEL_BG, border_width=1, border_color=COLOR_PANEL_BORDER)
        imp_card.pack(fill="x", pady=(PAD_NONE, PAD_LG), padx=PAD_XS)

        self.register_i18n(
            ctk.CTkLabel(
                imp_card,
                text=tr("profile.backup_imp_title", "2. Datensicherung aus ZIP-Datei importieren"),
                font=ctk.CTkFont(size=FONT_SIZE_BODY, weight="bold"),
            ),
            "profile.backup_imp_title",
            "2. Datensicherung aus ZIP-Datei importieren",
        ).pack(anchor="w", padx=PAD_LG, pady=(PAD_MD, PAD_XS))

        self.register_i18n(
            ctk.CTkLabel(
                imp_card,
                text=tr("profile.backup_imp_desc", "Stellt Datensätze und Anhänge aus einem ZIP-Archiv an den von Ihnen gewählten Ziel-Speicherorten wieder her."),
                font=ctk.CTkFont(size=FONT_SIZE_SM),
                text_color=COLOR_TIP_TEXT,
                anchor="w",
                wraplength=PROFILE_CARD_DESC_WRAPLENGTH,
                justify="left",
            ),
            "profile.backup_imp_desc",
            "Stellt Datensätze und Anhänge aus einem ZIP-Archiv an den von Ihnen gewählten Ziel-Speicherorten wieder her.",
        ).pack(anchor="w", padx=PAD_LG, pady=(PAD_NONE, PAD_MD))

        btn_import = self.register_i18n(
            ctk.CTkButton(
                imp_card,
                text=tr("profile.backup_imp_btn", "📥 Datensicherung aus ZIP importieren..."),
                command=self.on_click_import_zip,
                fg_color=COLOR_SUCCESS,
                width=BTN_WIDTH_WIDE,
            ),
            "profile.backup_imp_btn",
            "📥 Datensicherung aus ZIP importieren...",
        )
        btn_import.pack(anchor="w", padx=PAD_LG, pady=(PAD_NONE, PAD_LG))

    def on_browse_workspace(self) -> None:
        chosen = filedialog.askdirectory(title=tr("profile.browse_folder_title", "Datenordner auswählen"), initialdir=self.ws_entry.get().strip() or None)
        if chosen:
            self.ws_entry.delete(0, "end")
            self.ws_entry.insert(0, chosen)
            self.update_paths_from_workspace(chosen)

    def on_workspace_entry_changed(self) -> None:
        ws = self.ws_entry.get().strip() if hasattr(self, "ws_entry") else ""
        if ws:
            self.update_paths_from_workspace(ws)

    def update_paths_from_workspace(self, ws: str) -> None:
        if not ws:
            return
        ws_path = Path(ws)
        if ws_path.name.lower() == "data":
            data_dir = ws_path
        else:
            data_dir = ws_path / "data"

        mapping = [
            (getattr(self, "path_cases_entry", None), data_dir / FILENAME_CASES),
            (getattr(self, "path_archive_entry", None), data_dir / FILENAME_ARCHIVE),
            (getattr(self, "path_cust_entry", None), data_dir / FILENAME_CUSTOMERS),
            (getattr(self, "path_profile_entry", None), data_dir / FILENAME_APP_PROFILE),
            (getattr(self, "path_colleagues_entry", None), data_dir / FILENAME_COLLEAGUES),
            (getattr(self, "path_schemas_entry", None), data_dir / FILENAME_QUESTION_SCHEMAS),
            (getattr(self, "path_templates_entry", None), data_dir / FILENAME_EXPORT_TEMPLATES),
            (getattr(self, "path_wiki_entry", None), data_dir / FILENAME_WIKI_INDEX),
        ]

        for entry, path in mapping:
            if entry is not None:
                entry.delete(0, "end")
                entry.insert(0, str(path))

    def on_browse_file(self, entry_widget: ctk.CTkEntry, file_pattern: str) -> None:
        chosen = filedialog.askopenfilename(title=tr("profile.browse_file_title", "Datei auswählen"), filetypes=get_file_types_data_file(file_pattern))
        if chosen:
            entry_widget.delete(0, "end")
            entry_widget.insert(0, chosen)

    def on_reset_paths(self) -> None:
        for attr in [
            "path_cases_entry", "path_archive_entry", "path_cust_entry",
            "path_profile_entry", "path_colleagues_entry", "path_schemas_entry",
            "path_templates_entry", "path_wiki_entry"
        ]:
            entry = getattr(self, attr, None)
            if entry is not None:
                entry.delete(0, "end")

    def on_click_export_zip(self) -> None:
        dest_file = filedialog.asksaveasfilename(
            title=tr("profile.save_zip_title", "Datensicherung als ZIP speichern"),
            defaultextension=".zip",
            filetypes=get_file_types_zip(),
            initialfile=DEFAULT_BACKUP_ZIP_FILENAME,
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
            text_color=COLOR_SUCCESS,
        )

    def on_click_import_zip(self) -> None:
        zip_file = filedialog.askopenfilename(
            title=tr("profile.select_zip_title", "Datensicherung (ZIP-Datei) auswählen"),
            filetypes=get_file_types_zip(),
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
            self.storage_service.config.custom_cases_path = target_data / FILENAME_CASES
            self.storage_service.config.custom_customers_path = target_data / FILENAME_CUSTOMERS
            self.storage_service.config.ensure_directories()
            self.storage_service.config.save_user_config()

            self.status_lbl.configure(
                text=tr(
                    "profile.zip_import_success",
                    "✅ Import abgeschlossen! {data_files} Datendateien & {attachment_files} Anhänge entpackt.",
                    data_files=res["extracted_data_files"],
                    attachment_files=res["extracted_attachment_files"],
                ),
                text_color=COLOR_SUCCESS,
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
            d = max(1, int(self.retention_daily_entry.get().strip())) if hasattr(self, "retention_daily_entry") else DEFAULT_BACKUP_DAILY_DAYS
            w = max(0, int(self.retention_weekly_entry.get().strip())) if hasattr(self, "retention_weekly_entry") else DEFAULT_BACKUP_WEEKLY_WEEKS
            m = max(0, int(self.retention_monthly_entry.get().strip())) if hasattr(self, "retention_monthly_entry") else DEFAULT_BACKUP_MONTHLY_MONTHS
            active_settings = BackupSettings(daily_days=d, weekly_weeks=w, monthly_months=m)
        except Exception:
            active_settings = getattr(self.profile, "backup_settings", BackupSettings())

        deleted = self.storage_service.prune_old_backups(settings=active_settings)
        if deleted:
            self.status_lbl.configure(
                text=tr("profile.retention_pruned_count", "🧹 {count} veraltete Backup(s) bereinigt.", count=len(deleted)),
                text_color=COLOR_SUCCESS,
            )
        else:
            self.status_lbl.configure(
                text=tr("profile.retention_pruned_none", "ℹ Keine veralteten Backups zum Bereinigen gefunden."),
                text_color=COLOR_LABEL_GRAY70,
            )

    def reload_paths_fields(self) -> None:
        from config import get_default_workspace_dir
        ps = getattr(self.profile, "path_settings", None)
        ws = getattr(ps, "workspace_dir", "") or str(get_default_workspace_dir())

        if hasattr(self, "ws_entry"):
            self.ws_entry.delete(0, "end")
            self.ws_entry.insert(0, ws)

        attr_mapping = [
            ("path_cases_entry", getattr(ps, "custom_cases_path", "")),
            ("path_archive_entry", getattr(ps, "custom_archive_path", "")),
            ("path_cust_entry", getattr(ps, "custom_customers_path", "")),
            ("path_profile_entry", getattr(ps, "custom_app_profile_path", "")),
            ("path_colleagues_entry", getattr(ps, "custom_colleagues_path", "")),
            ("path_schemas_entry", getattr(ps, "custom_question_schemas_path", "")),
            ("path_templates_entry", getattr(ps, "custom_export_templates_path", "")),
            ("path_wiki_entry", getattr(ps, "custom_wiki_db_path", "")),
        ]

        for attr, val in attr_mapping:
            entry = getattr(self, attr, None)
            if entry is not None:
                entry.delete(0, "end")
                if val:
                    entry.insert(0, val)

        b_set = getattr(self.profile, "backup_settings", None)
        d_val = getattr(b_set, "daily_days", DEFAULT_BACKUP_DAILY_DAYS)
        w_val = getattr(b_set, "weekly_weeks", DEFAULT_BACKUP_WEEKLY_WEEKS)
        m_val = getattr(b_set, "monthly_months", DEFAULT_BACKUP_MONTHLY_MONTHS)

        if hasattr(self, "retention_daily_entry"):
            self.retention_daily_entry.delete(0, "end")
            self.retention_daily_entry.insert(0, str(d_val))

        if hasattr(self, "retention_weekly_entry"):
            self.retention_weekly_entry.delete(0, "end")
            self.retention_weekly_entry.insert(0, str(w_val))

        if hasattr(self, "retention_monthly_entry"):
            self.retention_monthly_entry.delete(0, "end")
            self.retention_monthly_entry.insert(0, str(m_val))

    def save_paths_settings(self) -> bool:
        ws_path_str = self.ws_entry.get().strip() if hasattr(self, "ws_entry") else ""

        def get_val(attr: str) -> str:
            entry = getattr(self, attr, None)
            return entry.get().strip() if entry else ""

        cases_override = get_val("path_cases_entry")
        archive_override = get_val("path_archive_entry")
        cust_override = get_val("path_cust_entry")
        profile_override = get_val("path_profile_entry")
        colleagues_override = get_val("path_colleagues_entry")
        schemas_override = get_val("path_schemas_entry")
        templates_override = get_val("path_templates_entry")
        wiki_override = get_val("path_wiki_entry")

        if not hasattr(self.profile, "path_settings") or self.profile.path_settings is None:
            from models.profile import PathSettings
            self.profile.path_settings = PathSettings()

        self.profile.path_settings.workspace_dir = ws_path_str
        self.profile.path_settings.custom_cases_path = cases_override
        self.profile.path_settings.custom_archive_path = archive_override
        self.profile.path_settings.custom_customers_path = cust_override
        self.profile.path_settings.custom_app_profile_path = profile_override
        self.profile.path_settings.custom_colleagues_path = colleagues_override
        self.profile.path_settings.custom_question_schemas_path = schemas_override
        self.profile.path_settings.custom_export_templates_path = templates_override
        self.profile.path_settings.custom_wiki_db_path = wiki_override

        if ws_path_str:
            self.storage_service.config.workspace_dir = Path(ws_path_str)

        self.storage_service.config.custom_cases_path = Path(cases_override) if cases_override else None
        self.storage_service.config.custom_archive_path = Path(archive_override) if archive_override else None
        self.storage_service.config.custom_customers_path = Path(cust_override) if cust_override else None
        self.storage_service.config.custom_app_profile_path = Path(profile_override) if profile_override else None
        self.storage_service.config.custom_colleagues_path = Path(colleagues_override) if colleagues_override else None
        self.storage_service.config.custom_question_schemas_path = Path(schemas_override) if schemas_override else None
        self.storage_service.config.custom_export_templates_path = Path(templates_override) if templates_override else None
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
