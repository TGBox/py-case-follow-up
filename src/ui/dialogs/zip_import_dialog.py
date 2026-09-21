import customtkinter as ctk

from ui.dialogs.base_dialog import BaseDialog
from tkinter import filedialog
from pathlib import Path
from collections.abc import Callable
from services.zip_backup_service import ZipBackupService
from constants import (
    BTN_WIDTH_CLOSE,
    BTN_WIDTH_WIDE,
    BTN_WIDTH_ZIP_MODE,
    BYTES_PER_KB,
    COLOR_BTN_CANCEL,
    COLOR_BTN_CANCEL_HOVER,
    COLOR_CARD_BG_ALT,
    COLOR_NOTE_TEXT,
    COLOR_PRIMARY_BLUE,
    COLOR_SUCCESS,
    COLOR_WARNING_NOTE,
    CORNER_RADIUS_CARD,
    CORNER_RADIUS_LG,
    DIALOG_DIMENSIONS,
    DIALOG_MIN_SIZE_ZIP_IMPORT,
    DIALOG_TITLES,
    ENTRY_WIDTH_IMPORT_PATH,
    FONT_SIZE_BODY,
    FONT_SIZE_SM,
    FONT_SIZE_SUBTITLE,
    FONT_WEIGHT_BOLD,
    PAD_10,
    PAD_15,
    PAD_2XL,
    PAD_CONTAINER,
    PAD_LG,
    PAD_MD,
    PAD_NONE,
    PAD_SM,
    PAD_XS,
    ZIP_IMPORT_WARN_WRAPLENGTH,
)


class ZipImportPathDialog(BaseDialog):
    """Modal dialog to select target extraction destination paths before unpacking ZIP backup."""

    def __init__(
        self,
        parent,
        zip_file_path: Path,
        default_data_dir: Path,
        default_attachments_dir: Path,
        on_import_confirmed: Callable[[Path, Path], None],
    ):
        super().__init__(parent)
        self.zip_file_path = zip_file_path
        self.default_data_dir = default_data_dir
        self.default_attachments_dir = default_attachments_dir
        self.on_import_confirmed = on_import_confirmed

        w, h = DIALOG_DIMENSIONS["zip_import"]
        self.setup_window(
            parent,
            DIALOG_TITLES["zip_import"],
            (w, h),
            min_size=DIALOG_MIN_SIZE_ZIP_IMPORT,

            title_factory=lambda: DIALOG_TITLES["zip_import"],
        )


        # Inspect Zip Info
        self.zip_info = ZipBackupService.inspect_backup_zip(self.zip_file_path)

        self.mode = "root"  # "root" or "custom"
        self.target_data_dir = self.default_data_dir
        self.target_attachments_dir = self.default_attachments_dir

        self.create_widgets()

    def create_widgets(self):
        main_frame = ctk.CTkFrame(self, fg_color="transparent")
        main_frame.pack(fill="both", expand=True, padx=PAD_2XL, pady=PAD_2XL)

        # Header Info Card
        header_card = ctk.CTkFrame(main_frame, fg_color=COLOR_CARD_BG_ALT, corner_radius=CORNER_RADIUS_CARD)
        header_card.pack(fill="x", pady=(PAD_NONE, PAD_15))

        from services.i18n_service import tr

        title_lbl = self.register_i18n(ctk.CTkLabel(
            header_card,
            text=tr("zip_import.backup_file", "📦 Backup-Datei: {name}", name=self.zip_file_path.name),
            font=ctk.CTkFont(size=FONT_SIZE_SUBTITLE, weight=FONT_WEIGHT_BOLD),
            anchor="w",
        ), "zip_import.backup_file", "📦 Backup-Datei: {name}", name=self.zip_file_path.name)
        title_lbl.pack(fill="x", padx=PAD_LG, pady=(PAD_10, PAD_XS))

        mb_size = self.zip_info["total_bytes"] / (BYTES_PER_KB * BYTES_PER_KB)
        info_summary_default = "Enthält: {total} Dateien  ({data} Datendateien, {att} Anhänge)  •  Größe: {size:.2f} MB"
        info_kwargs = {
            "total": self.zip_info["total_files"],
            "data": self.zip_info["data_files"],
            "att": self.zip_info["attachment_files"],
            "size": mb_size,
        }
        sub_lbl = self.register_i18n(ctk.CTkLabel(
            header_card,
            text=tr("zip_import.info_summary", info_summary_default, **info_kwargs),
            font=ctk.CTkFont(size=FONT_SIZE_SM),
            text_color=COLOR_NOTE_TEXT,
            anchor="w",
        ), "zip_import.info_summary", info_summary_default, **info_kwargs)
        sub_lbl.pack(fill="x", padx=PAD_LG, pady=(PAD_NONE, PAD_10))

        # Selection Mode Selector
        self.register_i18n(ctk.CTkLabel(
            main_frame,
            text=tr("zip_import.select_mode", "Wählen Sie aus, wie die Zielspeicherorte festgelegt werden sollen:"),
            font=ctk.CTkFont(weight=FONT_WEIGHT_BOLD, size=FONT_SIZE_BODY),
        ), "zip_import.select_mode", "Wählen Sie aus, wie die Zielspeicherorte festgelegt werden sollen:").pack(anchor="w", pady=(PAD_CONTAINER, PAD_MD))

        mode_frame = ctk.CTkFrame(main_frame, fg_color="transparent")
        mode_frame.pack(fill="x", pady=(PAD_NONE, PAD_15))

        self.btn_mode_root = self.register_i18n(ctk.CTkButton(
            mode_frame,
            text=tr("zip_import.root_folder_btn", "Gesamt-Zielordner wählen"),
            command=self.set_mode_root,
            fg_color=COLOR_PRIMARY_BLUE,
            width=BTN_WIDTH_ZIP_MODE,
        ), "zip_import.root_folder_btn", "Gesamt-Zielordner wählen")
        self.btn_mode_root.pack(side="left", padx=(PAD_NONE, PAD_10))

        self.btn_mode_custom = self.register_i18n(ctk.CTkButton(
            mode_frame,
            text=tr("zip_import.custom_paths_btn", "Einzelne Pfade anpassen"),
            command=self.set_mode_custom,
            fg_color=COLOR_BTN_CANCEL,
            hover_color=COLOR_BTN_CANCEL_HOVER,
            width=BTN_WIDTH_ZIP_MODE,
        ), "zip_import.custom_paths_btn", "Einzelne Pfade anpassen")
        self.btn_mode_custom.pack(side="left")

        # Destination Paths Inputs Frame
        self.paths_frame = ctk.CTkFrame(main_frame, corner_radius=CORNER_RADIUS_LG)
        self.paths_frame.pack(fill="x", pady=(PAD_NONE, PAD_15), padx=PAD_XS)

        self.render_path_inputs()

        # Status / Warning Info
        warn_lbl = self.register_i18n(ctk.CTkLabel(
            main_frame,
            text=tr("zip_import.warning_overwrite", "Hinweis: Beim Importieren werden vorhandene Dateien mit gleichem Namen am Zielspeicherort überschrieben."),
            font=ctk.CTkFont(size=FONT_SIZE_SM),
            text_color=COLOR_WARNING_NOTE,
            anchor="w",
            wraplength=ZIP_IMPORT_WARN_WRAPLENGTH,
        ), "zip_import.warning_overwrite", "Hinweis: Beim Importieren werden vorhandene Dateien mit gleichem Namen am Zielspeicherort überschrieben.")
        warn_lbl.pack(fill="x", pady=(PAD_NONE, PAD_15))

        # Bottom Action Bar
        bottom_bar = ctk.CTkFrame(main_frame, fg_color="transparent")
        bottom_bar.pack(fill="x", side="bottom")

        self.register_i18n(ctk.CTkButton(
            bottom_bar,
            text=tr("common.cancel", "Abbrechen"),
            command=self.destroy,
            fg_color=COLOR_BTN_CANCEL,
            hover_color=COLOR_BTN_CANCEL_HOVER,
            width=BTN_WIDTH_CLOSE,
        ), "common.cancel", "Abbrechen").pack(side="left")

        self.register_i18n(ctk.CTkButton(
            bottom_bar,
            text=tr("zip_import.unpack_btn", "Daten entpacken & importieren"),
            command=self.on_confirm,
            fg_color=COLOR_SUCCESS,
            width=BTN_WIDTH_WIDE,
            font=ctk.CTkFont(weight=FONT_WEIGHT_BOLD),
        ), "zip_import.unpack_btn", "Daten entpacken & importieren").pack(side="right")

    def set_mode_root(self):
        self.mode = "root"
        self.btn_mode_root.configure(fg_color=COLOR_PRIMARY_BLUE)
        self.btn_mode_custom.configure(fg_color=COLOR_BTN_CANCEL)
        self.render_path_inputs()

    def set_mode_custom(self):
        self.mode = "custom"
        self.btn_mode_root.configure(fg_color=COLOR_BTN_CANCEL)
        self.btn_mode_custom.configure(fg_color=COLOR_PRIMARY_BLUE)
        self.render_path_inputs()

    def render_path_inputs(self):
        for w in self.paths_frame.winfo_children():
            w.destroy()

        from services.i18n_service import tr

        if self.mode == "root":
            self.register_i18n(ctk.CTkLabel(
                self.paths_frame,
                text=tr("zip_import.main_target_dir", "Haupt-Zielverzeichnis (Erzeugt automatisch data/ und attachments/ Unterordner):"),
                font=ctk.CTkFont(size=FONT_SIZE_SM, weight=FONT_WEIGHT_BOLD),
            ), "zip_import.main_target_dir", "Haupt-Zielverzeichnis (Erzeugt automatisch data/ und attachments/ Unterordner):").pack(anchor="w", padx=PAD_LG, pady=(PAD_10, PAD_XS))

            row = ctk.CTkFrame(self.paths_frame, fg_color="transparent")
            row.pack(fill="x", padx=PAD_LG, pady=(PAD_NONE, PAD_LG))

            root_parent = self.target_data_dir.parent if self.target_data_dir else Path.cwd()
            self.root_entry = ctk.CTkEntry(row, width=ENTRY_WIDTH_IMPORT_PATH)
            self.root_entry.insert(0, str(root_parent))
            self.root_entry.pack(side="left", padx=(PAD_NONE, PAD_MD))

            self.register_i18n(ctk.CTkButton(
                row,
                text=tr("common.browse", "Durchsuchen..."),
                width=BTN_WIDTH_CLOSE,
                command=self.browse_root_dir,
            ), "common.browse", "Durchsuchen...").pack(side="left")

        else:
            # Custom Data Dir
            self.register_i18n(ctk.CTkLabel(
                self.paths_frame,
                text=tr("zip_import.data_loc", "1. Speicherort für Datendateien & Profile (data/):"),
                font=ctk.CTkFont(size=FONT_SIZE_SM, weight=FONT_WEIGHT_BOLD),
            ), "zip_import.data_loc", "1. Speicherort für Datendateien & Profile (data/):").pack(anchor="w", padx=PAD_LG, pady=(PAD_10, PAD_XS))

            row1 = ctk.CTkFrame(self.paths_frame, fg_color="transparent")
            row1.pack(fill="x", padx=PAD_LG, pady=(PAD_NONE, PAD_MD))

            self.data_entry = ctk.CTkEntry(row1, width=ENTRY_WIDTH_IMPORT_PATH)
            self.data_entry.insert(0, str(self.target_data_dir))
            self.data_entry.pack(side="left", padx=(PAD_NONE, PAD_MD))

            self.register_i18n(ctk.CTkButton(
                row1,
                text=tr("common.browse", "Durchsuchen..."),
                width=BTN_WIDTH_CLOSE,
                command=self.browse_data_dir,
            ), "common.browse", "Durchsuchen...").pack(side="left")

            # Custom Attachments Dir
            self.register_i18n(ctk.CTkLabel(
                self.paths_frame,
                text=tr("zip_import.att_loc", "2. Speicherort für Fall-Anhänge (attachments/):"),
                font=ctk.CTkFont(size=FONT_SIZE_SM, weight=FONT_WEIGHT_BOLD),
            ), "zip_import.att_loc", "2. Speicherort für Fall-Anhänge (attachments/):").pack(anchor="w", padx=PAD_LG, pady=(PAD_SM, PAD_XS))

            row2 = ctk.CTkFrame(self.paths_frame, fg_color="transparent")
            row2.pack(fill="x", padx=PAD_LG, pady=(PAD_NONE, PAD_LG))

            self.att_entry = ctk.CTkEntry(row2, width=ENTRY_WIDTH_IMPORT_PATH)
            self.att_entry.insert(0, str(self.target_attachments_dir))
            self.att_entry.pack(side="left", padx=(PAD_NONE, PAD_MD))

            self.register_i18n(ctk.CTkButton(
                row2,
                text=tr("common.browse", "Durchsuchen..."),
                width=BTN_WIDTH_CLOSE,
                command=self.browse_att_dir,
            ), "common.browse", "Durchsuchen...").pack(side="left")

    def browse_root_dir(self):
        from services.i18n_service import tr
        chosen = filedialog.askdirectory(title=tr("zip_import.browse_root_title", "Gesamt-Zielverzeichnis wählen"), parent=self)
        if chosen:
            self.root_entry.delete(0, "end")
            self.root_entry.insert(0, chosen)

    def browse_data_dir(self):
        from services.i18n_service import tr
        chosen = filedialog.askdirectory(title=tr("zip_import.browse_data_title", "Zielverzeichnis für Datendateien (data/) wählen"), parent=self)
        if chosen:
            self.data_entry.delete(0, "end")
            self.data_entry.insert(0, chosen)

    def browse_att_dir(self):
        from services.i18n_service import tr
        chosen = filedialog.askdirectory(title=tr("zip_import.browse_att_title", "Zielverzeichnis für Fall-Anhänge (attachments/) wählen"), parent=self)
        if chosen:
            self.att_entry.delete(0, "end")
            self.att_entry.insert(0, chosen)

    def on_confirm(self):
        if self.mode == "root":
            r_str = self.root_entry.get().strip()
            if not r_str:
                return
            root_p = Path(r_str)
            target_data = root_p / "data"
            target_att = root_p / "attachments"
        else:
            d_str = self.data_entry.get().strip()
            a_str = self.att_entry.get().strip()
            if not d_str or not a_str:
                return
            target_data = Path(d_str)
            target_att = Path(a_str)

        self.on_import_confirmed(target_data, target_att)
        self.destroy()
