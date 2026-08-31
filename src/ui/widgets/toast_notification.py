import customtkinter as ctk
from typing import Callable
from constants import TOAST_DURATION_DEFAULT_MS


class ToastNotification(ctk.CTkToplevel):
    """Non-intrusive toast popup notification displayed in the bottom-right corner."""

    def __init__(self, parent, title: str, message: str, duration_ms: int = TOAST_DURATION_DEFAULT_MS, on_open: Callable[[], None] | None = None):
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

        width = 420 if on_open else 360
        height = 84
        x = screen_w - width - 20
        y = screen_h - height - 60

        self.geometry(f"{width}x{height}+{x}+{y}")

        frame = ctk.CTkFrame(self, fg_color=("gray90", "gray20"), border_width=2, border_color="dodgerblue", corner_radius=8)
        frame.pack(fill="both", expand=True)

        if on_open:
            btn_open = ctk.CTkButton(
                frame,
                text="👁 Öffnen",
                width=95,
                height=32,
                font=ctk.CTkFont(size=12, weight="bold"),
                fg_color="dodgerblue",
                hover_color="deepskyblue",
                command=self.handle_open,
            )
            btn_open.pack(side="right", padx=(6, 12), pady=12)

        content_frame = ctk.CTkFrame(frame, fg_color="transparent")
        content_frame.pack(side="left", fill="both", expand=True, padx=(12, 6), pady=8)

        lbl_title = ctk.CTkLabel(content_frame, text=title, font=ctk.CTkFont(size=13, weight="bold"), text_color="dodgerblue", anchor="w")
        lbl_title.pack(anchor="w", pady=(0, 2))

        lbl_msg = ctk.CTkLabel(content_frame, text=message, font=ctk.CTkFont(size=11), text_color=("gray10", "white"), anchor="w")
        lbl_msg.pack(anchor="w", pady=(0, 2))


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
        try:
            if hasattr(self, "master") and self.master:
                top = self.master.winfo_toplevel()
                if hasattr(top, "bring_to_foreground"):
                    top.bring_to_foreground()
                elif top:
                    if top.state() == "iconic" or not top.winfo_viewable():
                        top.deiconify()
                    top.lift()
                    top.focus_force()
        except Exception:
            pass
        self.safe_destroy()
        if cb:
            cb()

    def safe_destroy(self):
        try:
            self.destroy()
        except Exception:
            pass
