import customtkinter as ctk
import tkinter as tk
from typing import Any, Callable


class CTkTooltip:
    """Hover Overlay Tooltip for CustomTkinter widgets and containers."""

    _active_tooltips: set["CTkTooltip"] = set()

    @classmethod
    def dismiss_all(cls):
        """Immediately destroys all open tooltip windows across the app."""
        for tooltip in list(cls._active_tooltips):
            tooltip.cancel_timer()
            tooltip.hide_tooltip()

    def __init__(
        self,
        widget: Any,
        text_or_func: str | Callable[[], str],
        delay_ms: int = 300,
    ):
        self.widget = widget
        self.text_or_func = text_or_func
        self.delay_ms = delay_ms
        self.tooltip_window: ctk.CTkToplevel | None = None
        self._timer_id: str | None = None

        self._bind_events(self.widget)

    def _bind_events(self, w):
        try:
            w.bind("<Enter>", self.on_enter, add="+")
            w.bind("<Leave>", self.on_leave, add="+")
            w.bind("<Button-1>", self.on_click, add="+")
            w.bind("<ButtonRelease-1>", self.on_click, add="+")
            w.bind("<Destroy>", self.on_destroy, add="+")
        except Exception:
            pass

        if hasattr(w, "winfo_children"):
            for child in w.winfo_children():
                self._bind_events(child)

    def on_click(self, event=None):
        CTkTooltip.dismiss_all()

    def on_destroy(self, event=None):
        self.cancel_timer()
        self.hide_tooltip()

    def on_enter(self, event=None):
        self.cancel_timer()
        try:
            self._timer_id = self.widget.after(self.delay_ms, self.show_tooltip)
        except Exception:
            pass

    def on_leave(self, event=None):
        self.cancel_timer()
        self.hide_tooltip()

    def cancel_timer(self):
        if self._timer_id:
            try:
                self.widget.after_cancel(self._timer_id)
            except Exception:
                pass
            self._timer_id = None

    def show_tooltip(self):
        CTkTooltip.dismiss_all()

        try:
            text = self.text_or_func() if callable(self.text_or_func) else self.text_or_func
            if not text:
                return

            x = self.widget.winfo_pointerx() + 15
            y = self.widget.winfo_pointery() + 15

            self.tooltip_window = ctk.CTkToplevel(self.widget.winfo_toplevel())
            self.tooltip_window.wm_overrideredirect(True)
            self.tooltip_window.attributes("-topmost", True)
            self.tooltip_window.geometry(f"+{x}+{y}")

            frame = ctk.CTkFrame(
                self.tooltip_window,
                fg_color=("gray20", "gray10"),
                border_color=("gray60", "gray40"),
                border_width=1,
                corner_radius=8,
            )
            frame.pack(fill="both", expand=True, padx=2, pady=2)

            lbl = ctk.CTkLabel(
                frame,
                text=text,
                justify="left",
                anchor="w",
                font=ctk.CTkFont(size=11),
                text_color=("gray95", "gray95"),
            )
            lbl.pack(padx=10, pady=8)

            CTkTooltip._active_tooltips.add(self)
        except Exception:
            self.hide_tooltip()

    def hide_tooltip(self):
        CTkTooltip._active_tooltips.discard(self)
        if self.tooltip_window:
            try:
                self.tooltip_window.destroy()
            except Exception:
                pass
            self.tooltip_window = None
