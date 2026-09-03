import os
import subprocess
import customtkinter as ctk
from pathlib import Path
from tkinter import filedialog
from PIL import Image  # type: ignore
from models.case import Case
from services.attachment_service import AttachmentService


class AttachmentWidget(ctk.CTkFrame):
    def __init__(self, parent, attachment_service: AttachmentService):
        super().__init__(parent)
        self.attachment_service = attachment_service
        self.current_case: Case | None = None

        self.create_widgets()
        # Bind Ctrl+V for clipboard image paste
        import tkinter as tk
        tk.Misc.bind_all(self, "<Control-v>", self.on_clipboard_paste)

    def create_widgets(self):
        from services.i18n_service import tr

        # Header
        top_frame = ctk.CTkFrame(self, fg_color="transparent")
        top_frame.pack(fill="x", padx=10, pady=(10, 5))

        self.hdr_lbl = ctk.CTkLabel(top_frame, text=tr("attachments.title", "Fall-Dateianhänge"), font=ctk.CTkFont(size=14, weight="bold"))
        self.hdr_lbl.pack(side="left")

        self.open_exp_btn = ctk.CTkButton(top_frame, text=tr("attachments.open_explorer", "📁 Explorer öffnen"), command=self.on_open_explorer, width=120)
        self.open_exp_btn.pack(side="right")

        # Scrollable file list
        self.scroll_frame = ctk.CTkScrollableFrame(self, fg_color="transparent", height=130)
        self.scroll_frame.pack(fill="both", expand=True, padx=5, pady=5)

        # Preview Frame for Image or Text
        self.preview_frame = ctk.CTkFrame(self, height=120, fg_color=("gray90", "gray15"))
        self.preview_frame.pack(fill="x", padx=5, pady=2)
        
        self.preview_label = ctk.CTkLabel(self.preview_frame, text=tr("attachments.no_preview", "Keine Datei zur Vorschau ausgewählt"), font=ctk.CTkFont(size=11), text_color=("gray50", "gray60"))
        self.preview_label.pack(expand=True, pady=10)

        # Bottom Bar
        btn_frame = ctk.CTkFrame(self, fg_color="transparent")
        btn_frame.pack(fill="x", padx=5, pady=5)

        self.add_file_btn = ctk.CTkButton(btn_frame, text=tr("attachments.add_file", "+ Datei hinzufügen..."), command=self.on_add_file, width=150)
        self.add_file_btn.pack(side="left")

        self.tip_lbl = ctk.CTkLabel(btn_frame, text=tr("attachments.tip", "💡 Tipp: Strg+V fügt Screenshot als PNG ein"), font=ctk.CTkFont(size=10), text_color=("gray40", "gray70"))
        self.tip_lbl.pack(side="right")

    def refresh_ui_labels(self):
        from services.i18n_service import tr
        if hasattr(self, "hdr_lbl"):
            self.hdr_lbl.configure(text=tr("attachments.title", "Fall-Dateianhänge"))
        if hasattr(self, "open_exp_btn"):
            self.open_exp_btn.configure(text=tr("attachments.open_explorer", "📁 Explorer öffnen"))
        if getattr(self, "preview_label", None) is not None:
            try:
                if self.preview_label.winfo_exists():
                    txt = self.preview_label.cget("text")
                    if not txt.startswith("📄") and not txt.startswith("🖼"):
                        self.preview_label.configure(text=tr("attachments.no_preview", "Keine Datei zur Vorschau ausgewählt"))
            except Exception:
                pass
        if hasattr(self, "add_file_btn"):
            self.add_file_btn.configure(text=tr("attachments.add_file", "+ Datei hinzufügen..."))
        if hasattr(self, "tip_lbl"):
            self.tip_lbl.configure(text=tr("attachments.tip", "💡 Tipp: Strg+V fügt Screenshot als PNG ein"))
        self.load_attachments(self.current_case)

    def load_attachments(self, case: Case | None):
        from services.i18n_service import tr

        self.current_case = case
        self.clear_preview()
        for widget in self.scroll_frame.winfo_children():
            widget.destroy()

        if not case:
            ctk.CTkLabel(self.scroll_frame, text=tr("attachments.no_case", "Kein Fall ausgewählt.")).pack(pady=10)
            return

        files = self.attachment_service.list_attachments(case)
        if not files:
            ctk.CTkLabel(self.scroll_frame, text=tr("attachments.no_files", "Keine Dateianhänge im Fallordner.")).pack(pady=10)
            return

        for f in files:
            f_frame = ctk.CTkFrame(self.scroll_frame, fg_color=("gray85", "gray20"))
            f_frame.pack(fill="x", pady=2, padx=2)

            is_img = f.suffix.lower() in (".png", ".jpg", ".jpeg", ".bmp", ".gif")
            icon = "🖼" if is_img else "📄"
            lbl_str = f"{icon} {f.name} ({f.stat().st_size / 1024:.1f} KB)"

            btn_lbl = ctk.CTkButton(
                f_frame,
                text=lbl_str,
                anchor="w",
                font=ctk.CTkFont(size=11),
                fg_color="transparent",
                hover_color=("gray75", "gray30"),
                command=lambda filepath=f: self.show_file_preview(filepath),
            )
            btn_lbl.pack(side="left", fill="x", expand=True, padx=4, pady=2)

            btn_open = ctk.CTkButton(
                f_frame,
                text=tr("common.open", "📂 Öffnen"),
                width=65,
                fg_color="gray30",
                hover_color="gray40",
                command=lambda filepath=f: self.open_in_os(filepath),
            )
            btn_open.pack(side="right", padx=2)

            btn_del = ctk.CTkButton(
                f_frame,
                text="🗑",
                width=30,
                fg_color="darkred",
                hover_color="firebrick",
                command=lambda filepath=f: self.delete_attachment(filepath),
            )
            btn_del.pack(side="right", padx=2)

        from utils.ui_utils import bind_mouse_wheel_to_canvas
        bind_mouse_wheel_to_canvas(self.scroll_frame)

    def show_file_preview(self, filepath: Path):
        from services.i18n_service import tr
        self.clear_preview()
        ext = filepath.suffix.lower()

        if ext in (".png", ".jpg", ".jpeg", ".bmp", ".gif"):
            try:
                pil_img = Image.open(filepath)
                lbl = ctk.CTkLabel(self.preview_frame, text=tr("attachments.image_preview_info", "🖼 Bild Vorschau: {name}\nAuflösung: {width} x {height} px | Format: {format}", name=filepath.name, width=pil_img.width, height=pil_img.height, format=pil_img.format), font=ctk.CTkFont(size=12, weight="bold"))
                lbl.pack(expand=True, pady=10)
            except Exception as err:
                ctk.CTkLabel(self.preview_frame, text=tr("attachments.image_preview_error", "Bild-Vorschau nicht verfügbar: {err}", err=err)).pack(pady=10)

        elif ext in (".txt", ".log", ".json", ".csv", ".md", ".py"):
            try:
                content = filepath.read_text(encoding="utf-8", errors="ignore")[:500]
                tb = ctk.CTkTextbox(self.preview_frame, height=90)
                tb.pack(fill="both", expand=True, padx=4, pady=4)
                tb.insert("1.0", content)
                tb.configure(state="disabled")
            except Exception as err:
                ctk.CTkLabel(self.preview_frame, text=tr("attachments.text_preview_error", "Text-Vorschau Fehler: {err}", err=err)).pack(pady=10)
        else:
            ctk.CTkLabel(self.preview_frame, text=tr("attachments.generic_preview_info", "📄 Vorschau für '{name}' (Doppelklick zum Öffnen im OS)", name=filepath.name)).pack(pady=10)

    def clear_preview(self):
        for w in self.preview_frame.winfo_children():
            w.destroy()
        self.preview_label = None

    def open_in_os(self, filepath: Path):
        try:
            if hasattr(os, "startfile"):
                os.startfile(filepath)
            else:
                subprocess.Popen(["xdg-open", str(filepath)])
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
        from services.i18n_service import tr
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
