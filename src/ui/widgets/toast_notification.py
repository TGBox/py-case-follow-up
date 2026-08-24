import customtkinter as ctk
from typing import Callable


class ToastNotification(ctk.CTkToplevel):
    """Non-intrusive toast popup notification displayed in the bottom-right corner."""

    def __init__(self, parent, title: str, message: str, duration_ms: int = 5000, on_open: Callable[[], None] | None = None):
        super().__init__(parent)
        self.title("Erinnerung")
        self.on_open = on_open

        # 1. Transient link to parent so window stays above parent on Windows OS
        try:
            self.transient(parent)
        except Exception:
            pass

        self.overrideredirect(True)

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

        # 2. Lift and force topmost Z-order above maximized parent windows
        try:
            self.update_idletasks()
            self.lift()
            self.attributes("-topmost", True)
        except Exception:
            pass

        self.after(duration_ms, self.safe_destroy)

        # 3. Bind click handler recursively to all child widgets (including _label and _canvas)
        click_handler = lambda e: self.handle_open() if on_open else self.safe_destroy()
        self._bind_click_recursive(frame, click_handler)

    def _bind_click_recursive(self, widget, handler):
        try:
            widget.bind("<Button-1>", handler)
        except Exception:
            pass
        if hasattr(widget, "_label") and widget._label:
            try:
                widget._label.bind("<Button-1>", handler)
            except Exception:
                pass
        if hasattr(widget, "_canvas") and widget._canvas:
            try:
                widget._canvas.bind("<Button-1>", handler)
            except Exception:
                pass
        if hasattr(widget, "winfo_children"):
            for child in widget.winfo_children():
                self._bind_click_recursive(child, handler)

    def handle_open(self, event=None):
        cb = self.on_open
        self.on_open = None
        self.safe_destroy()
        if cb:
            cb()

    def safe_destroy(self):
        try:
            self.destroy()
        except Exception:
            pass
