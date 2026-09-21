import os
from pathlib import Path
import subprocess
import tkinter as tk
from tkinter import filedialog
import customtkinter as ctk
from PIL import Image  # type: ignore

from constants import (
    BORDER_WIDTH_PANEL,
    BTN_WIDTH_ADD_FILE,
    BTN_WIDTH_ICON_DELETE,
    BTN_WIDTH_OPEN_EXPLORER,
    BTN_WIDTH_XS,
    BYTES_PER_KB,
    CMD_XDG_OPEN,
    COLOR_CARD_BG,
    COLOR_CARD_BORDER,
    COLOR_DARKRED,
    COLOR_FIREBRICK_HOVER,
    COLOR_MUTED_LABEL,
    COLOR_PANEL_PREVIEW_BG,
    COLOR_PRESET_BTN,
    COLOR_PRESET_BTN_HOVER,
    COLOR_TIP_TEXT,
    COLOR_TRANSPARENT,
    CORNER_RADIUS_MD,
    FONT_SIZE_BODY,
    FONT_SIZE_SM,
    FONT_SIZE_SUBTITLE,
    FONT_SIZE_XS,
    FONT_WEIGHT_BOLD,
    ICON_DELETE_TRASH,
    ICON_DOC,
    ICON_IMAGE,
    IMAGE_FILE_EXTENSIONS,
    PAD_10,
    PAD_CONTAINER,
    PAD_SM,
    PAD_XS,
    PREVIEW_TEXT_MAX_CHARS,
    SCROLL_HEIGHT_ATTACHMENTS,
    SHORTCUT_PASTE,
    STATE_DISABLED,
    TEXT_PREVIEW_EXTENSIONS,
    TEXT_START_INDEX,
    TEXTBOX_HEIGHT_FILE_PREVIEW,
    TEXTBOX_HEIGHT_PREVIEW,
)
from models.case import Case
from services.attachment_service import AttachmentService
from services.i18n_service import tr
from utils.ui_utils import bind_mouse_wheel_to_canvas


class AttachmentWidget(ctk.CTkFrame):
    def __init__(self, parent, attachment_service: AttachmentService):
        super().__init__(parent)
        self.attachment_service = attachment_service
        self.current_case: Case | None = None

        self.create_widgets()
        # Bind Ctrl+V for clipboard image paste
        tk.Misc.bind_all(self, SHORTCUT_PASTE, self.on_clipboard_paste)

    def create_widgets(self):
        # Header
        top_frame = ctk.CTkFrame(self, fg_color=COLOR_TRANSPARENT)
        top_frame.pack(fill="x", padx=PAD_10, pady=(PAD_10, PAD_CONTAINER))

        self.hdr_lbl = ctk.CTkLabel(top_frame, text=tr("attachments.title", "Fall-Dateianhänge"), font=ctk.CTkFont(size=FONT_SIZE_SUBTITLE, weight=FONT_WEIGHT_BOLD))
        self.hdr_lbl.pack(side="left")

        self.open_exp_btn = ctk.CTkButton(top_frame, text=tr("attachments.open_explorer", "📁 Explorer öffnen"), command=self.on_open_explorer, width=BTN_WIDTH_OPEN_EXPLORER)
        self.open_exp_btn.pack(side="right")

        # Scrollable file list
        self.scroll_frame = ctk.CTkScrollableFrame(self, fg_color=COLOR_TRANSPARENT, height=SCROLL_HEIGHT_ATTACHMENTS)
        self.scroll_frame.pack(fill="both", expand=True, padx=PAD_CONTAINER, pady=PAD_CONTAINER)

        # Preview Frame for Image or Text
        self.preview_frame = ctk.CTkFrame(self, height=TEXTBOX_HEIGHT_PREVIEW, fg_color=COLOR_PANEL_PREVIEW_BG)
        self.preview_frame.pack(fill="x", padx=PAD_CONTAINER, pady=PAD_XS)

        self.preview_label = ctk.CTkLabel(self.preview_frame, text=tr("attachments.no_preview", "Keine Datei zur Vorschau ausgewählt"), font=ctk.CTkFont(size=FONT_SIZE_SM), text_color=COLOR_MUTED_LABEL)
        self.preview_label.pack(expand=True, pady=PAD_10)

        # Bottom Bar
        btn_frame = ctk.CTkFrame(self, fg_color=COLOR_TRANSPARENT)
        btn_frame.pack(fill="x", padx=PAD_CONTAINER, pady=PAD_CONTAINER)

        self.add_file_btn = ctk.CTkButton(btn_frame, text=tr("attachments.add_file", "+ Datei hinzufügen..."), command=self.on_add_file, width=BTN_WIDTH_ADD_FILE)
        self.add_file_btn.pack(side="left")

        self.tip_lbl = ctk.CTkLabel(btn_frame, text=tr("attachments.tip", "💡 Tipp: Strg+V fügt Screenshot als PNG ein"), font=ctk.CTkFont(size=FONT_SIZE_XS), text_color=COLOR_TIP_TEXT)
        self.tip_lbl.pack(side="right")

    def refresh_ui_labels(self):
        if hasattr(self, "hdr_lbl"):
            self.hdr_lbl.configure(text=tr("attachments.title", "Fall-Dateianhänge"))
        if hasattr(self, "open_exp_btn"):
            self.open_exp_btn.configure(text=tr("attachments.open_explorer", "📁 Explorer öffnen"))
        plbl = getattr(self, "preview_label", None)
        if plbl is not None:
            try:
                if plbl.winfo_exists():
                    txt = plbl.cget("text")
                    if not txt.startswith(ICON_DOC) and not txt.startswith(ICON_IMAGE):
                        plbl.configure(text=tr("attachments.no_preview", "Keine Datei zur Vorschau ausgewählt"))
            except Exception:
                pass
        if hasattr(self, "add_file_btn"):
            self.add_file_btn.configure(text=tr("attachments.add_file", "+ Datei hinzufügen..."))
        if hasattr(self, "tip_lbl"):
            self.tip_lbl.configure(text=tr("attachments.tip", "💡 Tipp: Strg+V fügt Screenshot als PNG ein"))
        self.load_attachments(self.current_case)

    def load_attachments(self, case: Case | None):
        self.current_case = case
        self.clear_preview()
        for widget in self.scroll_frame.winfo_children():
            widget.destroy()

        if not case:
            ctk.CTkLabel(self.scroll_frame, text=tr("attachments.no_case", "Kein Fall ausgewählt.")).pack(pady=PAD_10)
            return

        files = self.attachment_service.list_attachments(case)
        if not files:
            ctk.CTkLabel(self.scroll_frame, text=tr("attachments.no_files", "Keine Dateianhänge im Fallordner.")).pack(pady=PAD_10)
            return

        for f in files:
            f_frame = ctk.CTkFrame(self.scroll_frame, fg_color=COLOR_CARD_BG, corner_radius=CORNER_RADIUS_MD, border_width=BORDER_WIDTH_PANEL, border_color=COLOR_CARD_BORDER)
            f_frame.pack(fill="x", pady=PAD_XS, padx=PAD_XS)

            is_img = f.suffix.lower() in IMAGE_FILE_EXTENSIONS
            icon = ICON_IMAGE if is_img else ICON_DOC
            size_kb = f.stat().st_size / BYTES_PER_KB
            lbl_str = f"{icon} {f.name} ({size_kb:.1f} KB)"

            btn_lbl = ctk.CTkButton(
                f_frame,
                text=lbl_str,
                anchor="w",
                font=ctk.CTkFont(size=FONT_SIZE_SM),
                fg_color=COLOR_TRANSPARENT,
                hover_color=COLOR_PRESET_BTN,
                command=lambda filepath=f: self.show_file_preview(filepath),
            )
            btn_lbl.pack(side="left", fill="x", expand=True, padx=PAD_SM, pady=PAD_XS)

            btn_open = ctk.CTkButton(
                f_frame,
                text=tr("common.open", "📂 Öffnen"),
                width=BTN_WIDTH_XS,
                fg_color=COLOR_PRESET_BTN,
                hover_color=COLOR_PRESET_BTN_HOVER,
                command=lambda filepath=f: self.open_in_os(filepath),
            )
            btn_open.pack(side="right", padx=PAD_XS)

            btn_del = ctk.CTkButton(
                f_frame,
                text=ICON_DELETE_TRASH,
                width=BTN_WIDTH_ICON_DELETE,
                fg_color=COLOR_DARKRED,
                hover_color=COLOR_FIREBRICK_HOVER,
                command=lambda filepath=f: self.delete_attachment(filepath),
            )
            btn_del.pack(side="right", padx=PAD_XS)

        bind_mouse_wheel_to_canvas(self.scroll_frame)

    def show_file_preview(self, filepath: Path):
        self.clear_preview()
        ext = filepath.suffix.lower()

        if ext in IMAGE_FILE_EXTENSIONS:
            try:
                pil_img = Image.open(filepath)
                lbl = ctk.CTkLabel(self.preview_frame, text=tr("attachments.image_preview_info", "🖼 Bild Vorschau: {name}\nAuflösung: {width} x {height} px | Format: {format}", name=filepath.name, width=pil_img.width, height=pil_img.height, format=pil_img.format), font=ctk.CTkFont(size=FONT_SIZE_BODY, weight=FONT_WEIGHT_BOLD))
                lbl.pack(expand=True, pady=PAD_10)
            except Exception as err:
                ctk.CTkLabel(self.preview_frame, text=tr("attachments.image_preview_error", "Bild-Vorschau nicht verfügbar: {err}", err=err)).pack(pady=PAD_10)

        elif ext in TEXT_PREVIEW_EXTENSIONS:
            try:
                content = filepath.read_text(encoding="utf-8", errors="ignore")[:PREVIEW_TEXT_MAX_CHARS]
                tb = ctk.CTkTextbox(self.preview_frame, height=TEXTBOX_HEIGHT_FILE_PREVIEW)
                tb.pack(fill="both", expand=True, padx=PAD_SM, pady=PAD_SM)
                tb.insert(TEXT_START_INDEX, content)
                tb.configure(state=STATE_DISABLED)
            except Exception as err:
                ctk.CTkLabel(self.preview_frame, text=tr("attachments.text_preview_error", "Text-Vorschau Fehler: {err}", err=err)).pack(pady=PAD_10)
        else:
            ctk.CTkLabel(self.preview_frame, text=tr("attachments.generic_preview_info", "📄 Vorschau für '{name}' (Doppelklick zum Öffnen im OS)", name=filepath.name)).pack(pady=PAD_10)

    def clear_preview(self):
        for w in self.preview_frame.winfo_children():
            w.destroy()
        self.preview_label = None

    def open_in_os(self, filepath: Path):
        try:
            if hasattr(os, "startfile"):
                os.startfile(filepath)
            else:
                subprocess.Popen([CMD_XDG_OPEN, str(filepath)])
        except Exception as e:
            print(f"Error opening file: {e}")

    def delete_attachment(self, filepath: Path):
        try:
            filepath.unlink(missing_ok=True)
            if self.current_case:
                self.load_attachments(self.current_case)
        except Exception as e:
            print(f"Error deleting file: {e}")

    def on_add_file(self):
        if not self.current_case:
            return
        file_path = filedialog.askopenfilename(title=tr("attachments.select_file_dialog_title", "Datei zum Anhängen auswählen"))
        if file_path:
            self.attachment_service.copy_attachment(self.current_case, Path(file_path))
            self.load_attachments(self.current_case)

    def on_open_explorer(self):
        if self.current_case:
            self.attachment_service.open_in_explorer(self.current_case)

    def on_clipboard_paste(self, event=None):
        if self.current_case:
            saved_path = self.attachment_service.save_clipboard_image(self.current_case)
            if saved_path:
                self.load_attachments(self.current_case)

