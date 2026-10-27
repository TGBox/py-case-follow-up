import tkinter as tk
from tkinter import font as tkfont
import customtkinter as ctk
from typing import Any
from collections.abc import Callable
from constants import (
    ANCHOR_WEST,
    BORDER_WIDTH_TOOLTIP,
    COLOR_TOOLTIP_BG,
    COLOR_TOOLTIP_BORDER,
    COLOR_TOOLTIP_TEXT,
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
    TOOLTIP_DEFAULT_DELAY_MS,
    TOOLTIP_POINTER_OFFSET_X,
    TOOLTIP_POINTER_OFFSET_Y,
    TOOLTIP_WATCHDOG_MS,
    WINDOW_ATTR_TOPMOST,
)


def _mode_color(color: str | tuple[str, str]) -> str:
    if isinstance(color, str):
        return color
    return color[1] if ctk.get_appearance_mode() == "Dark" else color[0]


class CTkTooltip:
    """Hover Overlay Tooltip for CustomTkinter widgets and containers.

    The overlay is a plain tkinter.Toplevel on purpose. CTkToplevel runs
    withdraw() + update() inside its constructor on Windows, i.e. the whole
    event loop re-enters show_tooltip before the window is registered. A
    nested show of the same tooltip could then overwrite tooltip_window and
    leave a topmost window that nothing references any more - an overlay
    that survived even minimizing to the tray. CTkToplevel also added a
    global <Button-1> binding and a delayed focus() call per tooltip.
    """

    _active_tooltips: set[CTkTooltip] = set()
    # Every overlay window that exists, registered the moment it is created, so
    # dismiss_all can still destroy one whose owner lost track of it.
    _open_windows: set[tk.Toplevel] = set()
    _hooked_toplevels: set[str] = set()
    _showing: bool = False

    @classmethod
    def dismiss_all(cls):
        """Immediately destroys all open tooltip windows across the app."""
        for tooltip in list(cls._active_tooltips):
            tooltip.cancel_timer()
            tooltip.hide_tooltip()
        for window in list(cls._open_windows):
            cls._destroy_window(window)

    @classmethod
    def _destroy_window(cls, window: tk.Toplevel) -> None:
        try:
            window.destroy()
        except Exception:
            try:
                window.withdraw()
            except Exception:
                pass
        cls._open_windows.discard(window)

    @classmethod
    def _hook_toplevel(cls, toplevel: Any) -> None:
        """Dismisses tooltips on focus loss / unmap / click of the main window - bound once, not per show."""
        try:
            key = str(toplevel)
            if key in cls._hooked_toplevels:
                return
            for event in (EVENT_FOCUS_OUT, EVENT_UNMAP, EVENT_BUTTON_PRESS):
                toplevel.bind(event, lambda e: CTkTooltip.dismiss_all(), add="+")
            cls._hooked_toplevels.add(key)
        except Exception:
            pass

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
        self.tooltip_window: tk.Toplevel | None = None
        self._timer_id: str | None = None
        self._watch_id: str | None = None

        self._bind_events(self.widget)

    @property
    def text(self) -> str:
        if callable(self.text_or_func):
            return self.text_or_func()
        return self.text_or_func

    @text.setter
    def text(self, value: str | Callable[[], str]):
        self.text_or_func = value

    def set_text(self, value: str | Callable[[], str]) -> None:
        """Helper to update tooltip text (same as assigning to .text)."""
        self.text_or_func = value

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
            self._timer_id = self.widget.after(self.delay_ms, self._on_timer)
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

    def _on_timer(self):
        self._timer_id = None
        self.show_tooltip()

    def _pointer_inside_widget(self) -> bool:
        w = self.widget
        if not w.winfo_exists():
            return False
        px, py = w.winfo_pointerx(), w.winfo_pointery()
        wx, wy = w.winfo_rootx(), w.winfo_rooty()
        return wx <= px <= wx + w.winfo_width() and wy <= py <= wy + w.winfo_height()

    def show_tooltip(self):
        if CTkTooltip._showing:
            return
        CTkTooltip.dismiss_all()

        CTkTooltip._showing = True
        try:
            if not hasattr(self.widget, "winfo_exists") or not self.widget.winfo_exists():
                return

            text = self.text_or_func() if callable(self.text_or_func) else self.text_or_func
            if not text:
                return

            # Verify pointer is still inside the target widget bounds
            if not self._pointer_inside_widget():
                return

            x = self.widget.winfo_pointerx() + TOOLTIP_POINTER_OFFSET_X
            y = self.widget.winfo_pointery() + TOOLTIP_POINTER_OFFSET_Y

            toplevel = self.widget.winfo_toplevel()
            CTkTooltip._hook_toplevel(toplevel)

            window = tk.Toplevel(toplevel)
            # Registered before anything else can run, so no path leaves it untracked.
            CTkTooltip._open_windows.add(window)
            self.tooltip_window = window
            CTkTooltip._active_tooltips.add(self)

            window.wm_overrideredirect(True)
            window.attributes(WINDOW_ATTR_TOPMOST, True)
            window.geometry(f"+{x}+{y}")
            window.configure(bg=_mode_color(COLOR_TOOLTIP_BG))

            try:
                scaling = ctk.ScalingTracker.get_widget_scaling(self.widget)
            except Exception:
                scaling = 1.0
            theme_font = ctk.CTkFont()  # theme default family; keep a reference while reading it
            family = tkfont.nametofont(str(theme_font)).actual("family")
            lbl = tk.Label(
                window,
                text=text,
                justify=JUSTIFY_LEFT,
                anchor=ANCHOR_WEST,
                font=(family, -round(FONT_SIZE_SM * scaling)),
                fg=_mode_color(COLOR_TOOLTIP_TEXT),
                bg=_mode_color(COLOR_TOOLTIP_BG),
                padx=round(PAD_10 * scaling),
                pady=round(PAD_MD * scaling),
                highlightthickness=BORDER_WIDTH_TOOLTIP,
                highlightbackground=_mode_color(COLOR_TOOLTIP_BORDER),
                highlightcolor=_mode_color(COLOR_TOOLTIP_BORDER),
            )
            lbl.pack(fill="both", expand=True)
            # Hovering or clicking the overlay itself closes it.
            lbl.bind(EVENT_BUTTON_PRESS, lambda e: CTkTooltip.dismiss_all())

            self._watch_id = window.after(TOOLTIP_WATCHDOG_MS, self._watchdog)
        except Exception:
            self.hide_tooltip()
        finally:
            CTkTooltip._showing = False

    def _watchdog(self):
        """Closes the overlay once the pointer is gone, even if no <Leave> ever arrived."""
        self._watch_id = None
        window = self.tooltip_window
        if window is None:
            return
        try:
            # winfo_viewable is False once the main window is withdrawn to the tray or iconified.
            keep = self.widget.winfo_viewable() and self._pointer_inside_widget()
        except Exception:
            keep = False
        if not keep:
            self.cancel_timer()
            self.hide_tooltip()
            return
        try:
            self._watch_id = window.after(TOOLTIP_WATCHDOG_MS, self._watchdog)
        except Exception:
            self.hide_tooltip()

    def hide_tooltip(self):
        CTkTooltip._active_tooltips.discard(self)
        window = self.tooltip_window
        self.tooltip_window = None
        if window is not None:
            if self._watch_id:
                try:
                    window.after_cancel(self._watch_id)
                except Exception:
                    pass
            CTkTooltip._destroy_window(window)
        self._watch_id = None
