import customtkinter as ctk
from pathlib import Path
from tkinter import filedialog
from src.models.case import Case
from src.services.attachment_service import AttachmentService


class AttachmentWidget(ctk.CTkFrame):
    def __init__(self, parent, attachment_service: AttachmentService):
        super().__init__(parent)
        self.attachment_service = attachment_service
        self.current_case: Case | None = None

        self.create_widgets()
        # Bind Ctrl+V for clipboard image paste
        self.bind_all("<Control-v>", self.on_clipboard_paste)

    def create_widgets(self):
        # Header
        top_frame = ctk.CTkFrame(self, fg_color="transparent")
        top_frame.pack(fill="x", padx=10, pady=(10, 5))

        ctk.CTkLabel(top_frame, text="Fall-Dateianhänge", font=ctk.CTkFont(size=14, weight="bold")).pack(side="left")

        open_exp_btn = ctk.CTkButton(top_frame, text="📁 Explorer öffnen", command=self.on_open_explorer, width=120)
        open_exp_btn.pack(side="right")

        # Scrollable file list
        self.scroll_frame = ctk.CTkScrollableFrame(self, fg_color="transparent", height=100)
        self.scroll_frame.pack(fill="both", expand=True, padx=5, pady=5)

        # Bottom Bar
        btn_frame = ctk.CTkFrame(self, fg_color="transparent")
        btn_frame.pack(fill="x", padx=5, pady=5)

        add_file_btn = ctk.CTkButton(btn_frame, text="+ Datei hinzufügen...", command=self.on_add_file, width=150)
        add_file_btn.pack(side="left")

        ctk.CTkLabel(btn_frame, text="💡 Tip: Strg+V fügt Screenshot als PNG ein", font=ctk.CTkFont(size=10), text_color="gray70").pack(side="right")

    def load_attachments(self, case: Case | None):
        self.current_case = case
        for widget in self.scroll_frame.winfo_children():
            widget.destroy()

        if not case:
            ctk.CTkLabel(self.scroll_frame, text="Kein Fall ausgewählt.").pack(pady=10)
            return

        files = self.attachment_service.list_attachments(case)
        if not files:
            ctk.CTkLabel(self.scroll_frame, text="Keine Dateianhänge im Fallordner.").pack(pady=10)
            return

        for f in files:
            f_frame = ctk.CTkFrame(self.scroll_frame, fg_color="gray20")
            f_frame.pack(fill="x", pady=2, padx=2)

            icon = "🖼️" if f.suffix.lower() in (".png", ".jpg", ".jpeg", ".bmp") else "📄"
            lbl_str = f"{icon} {f.name} ({f.stat().st_size / 1024:.1f} KB)"

            ctk.CTkLabel(f_frame, text=lbl_str, anchor="w", font=ctk.CTkFont(size=11)).pack(side="left", padx=8, pady=4)

    def on_add_file(self):
        if not self.current_case:
            return
        file_path = filedialog.askopenfilename()
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
