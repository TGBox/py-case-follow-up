import customtkinter as ctk


class ToastNotification(ctk.CTkToplevel):
    """Non-intrusive toast popup notification displayed in the bottom-right corner."""

    def __init__(self, parent, title: str, message: str, duration_ms: int = 5000):
        super().__init__(parent)
        self.title("Erinnerung")
        self.overrideredirect(True)
        self.attributes("-topmost", True)

        screen_w = self.winfo_screenwidth()
        screen_h = self.winfo_screenheight()

        width = 340
        height = 80
        x = screen_w - width - 20
        y = screen_h - height - 60

        self.geometry(f"{width}x{height}+{x}+{y}")

        frame = ctk.CTkFrame(self, fg_color="gray20", border_width=2, border_color="dodgerblue", corner_radius=8)
        frame.pack(fill="both", expand=True)

        lbl_title = ctk.CTkLabel(frame, text=title, font=ctk.CTkFont(size=13, weight="bold"), text_color="dodgerblue", anchor="w")
        lbl_title.pack(anchor="w", padx=12, pady=(8, 2))

        lbl_msg = ctk.CTkLabel(frame, text=message, font=ctk.CTkFont(size=11), text_color="white", anchor="w")
        lbl_msg.pack(anchor="w", padx=12, pady=(0, 8))

        self.after(duration_ms, self.safe_destroy)
        self.bind("<Button-1>", lambda e: self.safe_destroy())

    def safe_destroy(self):
        try:
            self.destroy()
        except Exception:
            pass
