import customtkinter as ctk
from tkinter import filedialog
from pathlib import Path
from typing import Callable, Any
from services.zip_backup_service import ZipBackupService
from utils.ui_utils import center_window


class ZipImportPathDialog(ctk.CTkToplevel):
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

        self.title("📥 Datensicherung Importieren — Zielpfade festlegen")
        self.geometry("840x620")
        self.minsize(760, 540)
        center_window(self, 840, 620)

        self.transient(parent)
        self.grab_set()

        # Inspect Zip Info
        self.zip_info = ZipBackupService.inspect_backup_zip(self.zip_file_path)

        self.mode = "root"  # "root" or "custom"
        self.target_data_dir = self.default_data_dir
        self.target_attachments_dir = self.default_attachments_dir

        self.create_widgets()

    def create_widgets(self):
        main_frame = ctk.CTkFrame(self, fg_color="transparent")
        main_frame.pack(fill="both", expand=True, padx=20, pady=20)

        # Header Info Card
        header_card = ctk.CTkFrame(main_frame, fg_color=("gray85", "gray20"), corner_radius=8)
        header_card.pack(fill="x", pady=(0, 15))

        title_lbl = ctk.CTkLabel(
            header_card,
            text=f"📦 Backup-Datei: {self.zip_file_path.name}",
            font=ctk.CTkFont(size=14, weight="bold"),
            anchor="w",
        )
        title_lbl.pack(fill="x", padx=12, pady=(10, 2))

        mb_size = self.zip_info["total_bytes"] / (1024 * 1024)
        info_str = (
            f"Enthält: {self.zip_info['total_files']} Dateien  "
            f"({self.zip_info['data_files']} Datendateien, {self.zip_info['attachment_files']} Anhänge)  "
            f"•  Größe: {mb_size:.2f} MB"
        )
        sub_lbl = ctk.CTkLabel(
            header_card,
            text=info_str,
            font=ctk.CTkFont(size=11),
            text_color=("gray30", "gray70"),
            anchor="w",
        )
        sub_lbl.pack(fill="x", padx=12, pady=(0, 10))

        # Selection Mode Selector
        ctk.CTkLabel(
            main_frame,
            text="Wählen Sie aus, wie die Zielspeicherorte festgelegt werden sollen:",
            font=ctk.CTkFont(weight="bold", size=12),
        ).pack(anchor="w", pady=(5, 8))

        mode_frame = ctk.CTkFrame(main_frame, fg_color="transparent")
        mode_frame.pack(fill="x", pady=(0, 15))

        self.btn_mode_root = ctk.CTkButton(
            mode_frame,
            text="📁 Gesamt-Zielordner wählen",
            command=self.set_mode_root,
            fg_color="dodgerblue",
            width=230,
        )
        self.btn_mode_root.pack(side="left", padx=(0, 10))

        self.btn_mode_custom = ctk.CTkButton(
            mode_frame,
            text="⚙️ Einzelne Pfade anpassen",
            command=self.set_mode_custom,
            fg_color="gray40",
            width=230,
        )
        self.btn_mode_custom.pack(side="left")

        # Destination Paths Inputs Frame
        self.paths_frame = ctk.CTkFrame(main_frame, corner_radius=8)
        self.paths_frame.pack(fill="x", pady=(0, 15), padx=2)

        self.render_path_inputs()

        # Status / Warning Info
        warn_lbl = ctk.CTkLabel(
            main_frame,
            text="⚠️ Hinweis: Beim Importieren werden vorhandene Dateien mit gleichem Namen am Zielspeicherort überschrieben.",
            font=ctk.CTkFont(size=11),
            text_color=("darkgoldenrod", "gold"),
            anchor="w",
            wraplength=680,
        )
        warn_lbl.pack(fill="x", pady=(0, 15))

        # Bottom Action Bar
        bottom_bar = ctk.CTkFrame(main_frame, fg_color="transparent")
        bottom_bar.pack(fill="x", side="bottom")

        ctk.CTkButton(
            bottom_bar,
            text="Abbrechen",
            command=self.destroy,
            fg_color="gray40",
            width=120,
        ).pack(side="left")

        ctk.CTkButton(
            bottom_bar,
            text="📥 Daten entpacken & importieren",
            command=self.on_confirm,
            fg_color="forestgreen",
            width=240,
            font=ctk.CTkFont(weight="bold"),
        ).pack(side="right")

    def set_mode_root(self):
        self.mode = "root"
        self.btn_mode_root.configure(fg_color="dodgerblue")
        self.btn_mode_custom.configure(fg_color="gray40")
        self.render_path_inputs()

    def set_mode_custom(self):
        self.mode = "custom"
        self.btn_mode_root.configure(fg_color="gray40")
        self.btn_mode_custom.configure(fg_color="dodgerblue")
        self.render_path_inputs()

    def render_path_inputs(self):
        for w in self.paths_frame.winfo_children():
            w.destroy()

        if self.mode == "root":
            ctk.CTkLabel(
                self.paths_frame,
                text="Haupt-Zielverzeichnis (Erzeugt automatisch data/ und attachments/ Unterordner):",
                font=ctk.CTkFont(size=11, weight="bold"),
            ).pack(anchor="w", padx=12, pady=(10, 2))

            row = ctk.CTkFrame(self.paths_frame, fg_color="transparent")
            row.pack(fill="x", padx=12, pady=(0, 12))

            root_parent = self.target_data_dir.parent if self.target_data_dir else Path.cwd()
            self.root_entry = ctk.CTkEntry(row, width=480)
            self.root_entry.insert(0, str(root_parent))
            self.root_entry.pack(side="left", padx=(0, 8))

            ctk.CTkButton(
                row,
                text="Durchsuchen...",
                width=120,
                command=self.browse_root_dir,
            ).pack(side="left")

        else:
            # Custom Data Dir
            ctk.CTkLabel(
                self.paths_frame,
                text="1. Speicherort für Datendateien & Profile (data/):",
                font=ctk.CTkFont(size=11, weight="bold"),
            ).pack(anchor="w", padx=12, pady=(10, 2))

            row1 = ctk.CTkFrame(self.paths_frame, fg_color="transparent")
            row1.pack(fill="x", padx=12, pady=(0, 8))

            self.data_entry = ctk.CTkEntry(row1, width=480)
            self.data_entry.insert(0, str(self.target_data_dir))
            self.data_entry.pack(side="left", padx=(0, 8))

            ctk.CTkButton(
                row1,
                text="Durchsuchen...",
                width=120,
                command=self.browse_data_dir,
            ).pack(side="left")

            # Custom Attachments Dir
            ctk.CTkLabel(
                self.paths_frame,
                text="2. Speicherort für Fall-Anhänge (attachments/):",
                font=ctk.CTkFont(size=11, weight="bold"),
            ).pack(anchor="w", padx=12, pady=(4, 2))

            row2 = ctk.CTkFrame(self.paths_frame, fg_color="transparent")
            row2.pack(fill="x", padx=12, pady=(0, 12))

            self.att_entry = ctk.CTkEntry(row2, width=480)
            self.att_entry.insert(0, str(self.target_attachments_dir))
            self.att_entry.pack(side="left", padx=(0, 8))

            ctk.CTkButton(
                row2,
                text="Durchsuchen...",
                width=120,
                command=self.browse_att_dir,
            ).pack(side="left")

    def browse_root_dir(self):
        chosen = filedialog.askdirectory(title="Gesamt-Zielverzeichnis wählen", parent=self)
        if chosen:
            self.root_entry.delete(0, "end")
            self.root_entry.insert(0, chosen)

    def browse_data_dir(self):
        chosen = filedialog.askdirectory(title="Zielverzeichnis für Datendateien (data/) wählen", parent=self)
        if chosen:
            self.data_entry.delete(0, "end")
            self.data_entry.insert(0, chosen)

    def browse_att_dir(self):
        chosen = filedialog.askdirectory(title="Zielverzeichnis für Fall-Anhänge (attachments/) wählen", parent=self)
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
