import customtkinter as ctk
from typing import Any
from collections.abc import Callable
from constants import (
    ANCHOR_WEST,
    BORDER_WIDTH_TOOLTIP,
    COLOR_TOOLTIP_BG,
    COLOR_TOOLTIP_BORDER,
    COLOR_TOOLTIP_TEXT,
    CORNER_RADIUS_CARD,
    EVENT_BUTTON_1,
    EVENT_BUTTON_2,
    EVENT_BUTTON_3,
    EVENT_BUTTON_PRESS,
    EVENT_BUTTON_RELEASE_1,
    EVENT_DESTROY,
    EVENT_ENTER,
    EVENT_FOCUS_OUT,
    EVENT_LEAVE,
    EVENT_UNMAP,
    FONT_SIZE_SM,
    JUSTIFY_LEFT,
    PAD_10,
    PAD_MD,
    PAD_XS,
    TOOLTIP_DEFAULT_DELAY_MS,
    TOOLTIP_POINTER_OFFSET_X,
    TOOLTIP_POINTER_OFFSET_Y,
    WINDOW_ATTR_TOPMOST,
)


class CTkTooltip:
    """Hover Overlay Tooltip for CustomTkinter widgets and containers."""

    _active_tooltips: set[CTkTooltip] = set()

    @classmethod
    def dismiss_all(cls):
        """Immediately destroys all open tooltip windows across the app."""
        for tooltip in list(cls._active_tooltips):
            tooltip.cancel_timer()
            tooltip.hide_tooltip()

    @classmethod
    def attach_lazy(
        cls,
        widget: Any,
        text_or_func: str | Callable[[], str],
        delay_ms: int = TOOLTIP_DEFAULT_DELAY_MS,
    ) -> None:
        """Defers the tooltip until the widget is first hovered.

        _bind_events walks the whole subtree and binds nine events per widget.
        For a list that rebuilds every card on each keystroke that is thousands
        of bindings nobody ever triggers, so the real binding is postponed until
        a pointer actually arrives.
        """
        state: dict[str, Any] = {"tip": None}

        def _on_first_enter(event: Any = None) -> None:
            if state["tip"] is not None:
                return
            try:
                if not widget.winfo_exists():
                    return
                state["tip"] = cls(widget, text_or_func, delay_ms=delay_ms)
                # The real handler missed this very <Enter>, so replay it.
                state["tip"].on_enter(event)
            except Exception:
                pass

        try:
            widget.bind(EVENT_ENTER, _on_first_enter, add="+")
        except Exception:
            pass

    def __init__(
        self,
        widget: Any,
        text_or_func: str | Callable[[], str],
        delay_ms: int = TOOLTIP_DEFAULT_DELAY_MS,
    ):
        self.widget = widget
        self.text_or_func = text_or_func
        self.delay_ms = delay_ms
        self.tooltip_window: ctk.CTkToplevel | None = None
        self._timer_id: str | None = None

        self._bind_events(self.widget)

    def _bind_events(self, w):
        try:
            w.bind(EVENT_ENTER, self.on_enter, add="+")
            w.bind(EVENT_LEAVE, self.on_leave, add="+")
            w.bind(EVENT_FOCUS_OUT, self.on_leave, add="+")
            w.bind(EVENT_UNMAP, self.on_leave, add="+")
            w.bind(EVENT_BUTTON_1, self.on_click, add="+")
            w.bind(EVENT_BUTTON_2, self.on_click, add="+")
            w.bind(EVENT_BUTTON_3, self.on_click, add="+")
            w.bind(EVENT_BUTTON_RELEASE_1, self.on_click, add="+")
            w.bind(EVENT_DESTROY, self.on_destroy, add="+")
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
            if not hasattr(self.widget, "winfo_exists") or not self.widget.winfo_exists():
                return

            text = self.text_or_func() if callable(self.text_or_func) else self.text_or_func
            if not text:
                return

            # Verify pointer is still inside the target widget bounds
            px = self.widget.winfo_pointerx()
            py = self.widget.winfo_pointery()
            wx = self.widget.winfo_rootx()
            wy = self.widget.winfo_rooty()
            ww = self.widget.winfo_width()
            wh = self.widget.winfo_height()
            if not (wx <= px <= wx + ww and wy <= py <= wy + wh):
                return

            x = px + TOOLTIP_POINTER_OFFSET_X
            y = py + TOOLTIP_POINTER_OFFSET_Y

            toplevel = self.widget.winfo_toplevel()
            self.tooltip_window = ctk.CTkToplevel(toplevel)
            self.tooltip_window.wm_overrideredirect(True)
            self.tooltip_window.attributes(WINDOW_ATTR_TOPMOST, True)
            self.tooltip_window.geometry(f"+{x}+{y}")

            # Bind to top level window focus out / unmap to auto dismiss floating tooltip
            try:
                toplevel.bind(EVENT_FOCUS_OUT, lambda e: CTkTooltip.dismiss_all(), add="+")
                toplevel.bind(EVENT_UNMAP, lambda e: CTkTooltip.dismiss_all(), add="+")
                toplevel.bind(EVENT_BUTTON_PRESS, lambda e: CTkTooltip.dismiss_all(), add="+")
            except Exception:
                pass

            frame = ctk.CTkFrame(
                self.tooltip_window,
                fg_color=COLOR_TOOLTIP_BG,
                border_color=COLOR_TOOLTIP_BORDER,
                border_width=BORDER_WIDTH_TOOLTIP,
                corner_radius=CORNER_RADIUS_CARD,
            )
            frame.pack(fill="both", expand=True, padx=PAD_XS, pady=PAD_XS)

            lbl = ctk.CTkLabel(
                frame,
                text=text,
                justify=JUSTIFY_LEFT,
                anchor=ANCHOR_WEST,
                font=ctk.CTkFont(size=FONT_SIZE_SM),
                text_color=COLOR_TOOLTIP_TEXT,
            )
            lbl.pack(padx=PAD_10, pady=PAD_MD)

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

