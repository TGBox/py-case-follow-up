import customtkinter as ctk
from typing import Callable


class ToastNotification(ctk.CTkToplevel):
    """Non-intrusive toast popup notification displayed in the bottom-right corner."""

    def __init__(self, parent, title: str, message: str, duration_ms: int = 5000, on_open: Callable[[], None] | None = None):
        super().__init__(parent)
        self.title("Erinnerung")
        self.overrideredirect(True)
        self.attributes("-topmost", True)
        self.on_open = on_open

        screen_w = self.winfo_screenwidth()
        screen_h = self.winfo_screenheight()

        width = 380 if on_open else 340
        height = 80
        x = screen_w - width - 20
        y = screen_h - height - 60

        self.geometry(f"{width}x{height}+{x}+{y}")

        frame = ctk.CTkFrame(self, fg_color=("gray90", "gray20"), border_width=2, border_color="dodgerblue", corner_radius=8)
        frame.pack(fill="both", expand=True)

        content_frame = ctk.CTkFrame(frame, fg_color="transparent")
        content_frame.pack(side="left", fill="both", expand=True, padx=(12, 4), pady=6)

        lbl_title = ctk.CTkLabel(content_frame, text=title, font=ctk.CTkFont(size=13, weight="bold"), text_color="dodgerblue", anchor="w")
        lbl_title.pack(anchor="w", pady=(2, 2))

        lbl_msg = ctk.CTkLabel(content_frame, text=message, font=ctk.CTkFont(size=11), text_color=("gray10", "white"), anchor="w")
        lbl_msg.pack(anchor="w", pady=(0, 2))

        if on_open:
            btn_open = ctk.CTkButton(
                frame,
                text="👁️ Öffnen",
                width=80,
                height=30,
                command=self.handle_open
            )
            btn_open.pack(side="right", padx=(4, 10), pady=10)

        self.after(duration_ms, self.safe_destroy)
        self.bind("<Button-1>", lambda e: self.handle_open() if on_open else self.safe_destroy())

    def handle_open(self):
        if self.on_open:
            try:
                self.on_open()
            except Exception:
                pass
        self.safe_destroy()

    def safe_destroy(self):
        try:
            self.destroy()
        except Exception:
            pass
