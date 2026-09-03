from collections.abc import Callable
from typing import Any
import customtkinter as ctk


def patch_ctk_scrollable_frame() -> None:
    """Fixes CustomTkinter event callback signature mismatches (e.g. Python 3.14/Windows Tcl events).
    
    CustomTkinter registers `<Configure>` on CTkScrollableFrame using `lambda e: ...`,
    and defines internal handlers with strict single-argument signatures `(self, event)`.
    Under certain Tcl event dispatches, callbacks are executed without positional arguments,
    triggering `TypeError: CTkScrollableFrame.__init__.<locals>.<lambda>() missing 1 required positional argument: 'e'`.
    This patch ensures all callbacks accept optional or variable arguments.
    """
    if getattr(ctk.CTkScrollableFrame, "_ctk_resilience_patched", False):
        return

    orig_init = ctk.CTkScrollableFrame.__init__
    orig_fit = getattr(ctk.CTkScrollableFrame, "_fit_frame_dimensions_to_canvas", None)
    orig_mw = getattr(ctk.CTkScrollableFrame, "_mouse_wheel_all", None)
    orig_sp = getattr(ctk.CTkScrollableFrame, "_keyboard_shift_press_all", None)
    orig_sr = getattr(ctk.CTkScrollableFrame, "_keyboard_shift_release_all", None)

    if orig_fit:
        def safe_fit(self, event=None):
            return orig_fit(self, event)
        ctk.CTkScrollableFrame._fit_frame_dimensions_to_canvas = safe_fit

    if orig_mw:
        def safe_mw(self, event=None):
            if event is None:
                return
            return orig_mw(self, event)
        ctk.CTkScrollableFrame._mouse_wheel_all = safe_mw

    if orig_sp:
        def safe_sp(self, event=None):
            return orig_sp(self, event)
        ctk.CTkScrollableFrame._keyboard_shift_press_all = safe_sp

    if orig_sr:
        def safe_sr(self, event=None):
            return orig_sr(self, event)
        ctk.CTkScrollableFrame._keyboard_shift_release_all = safe_sr

    # Also make CTkBaseClass dimension updates resilient to None/missing event
    if hasattr(ctk, "CTkBaseClass") and hasattr(ctk.CTkBaseClass, "_update_dimensions_event"):
        orig_update_dim = ctk.CTkBaseClass._update_dimensions_event
        def safe_update_dim(self, event=None):
            if event is None:
                return
            return orig_update_dim(self, event)
        ctk.CTkBaseClass._update_dimensions_event = safe_update_dim

    # Make CTk / CTkToplevel focus handlers resilient
    for cls in (getattr(ctk, "CTk", None), getattr(ctk, "CTkToplevel", None)):
        if cls and hasattr(cls, "_focus_in_event"):
            orig_focus = cls._focus_in_event
            def safe_focus(self, event=None, orig=orig_focus):
                if event is None:
                    return
                return orig(self, event)
            cls._focus_in_event = safe_focus

    def safe_init(self, *args, **kwargs):
        orig_init(self, *args, **kwargs)
        try:
            canvas = getattr(self, "_parent_canvas", None)
            if canvas is not None:
                # Re-bind <Configure> on the inner frame with a resilient handler accepting arbitrary arguments
                self.bind("<Configure>", lambda *a, **kw: canvas.configure(scrollregion=canvas.bbox("all")))
                # Re-bind <Configure> on the parent canvas with a resilient handler
                canvas.bind("<Configure>", lambda *a, **kw: self._fit_frame_dimensions_to_canvas(*a, **kw))
        except Exception:
            pass

    ctk.CTkScrollableFrame.__init__ = safe_init
    ctk.CTkScrollableFrame._ctk_resilience_patched = True


# Automatically apply patch on import
patch_ctk_scrollable_frame()



def get_main_app_window(window: ctk.CTk | ctk.CTkToplevel) -> ctk.CTk | ctk.CTkToplevel:
    """Finds the root main application window (SupportCockpitApp) by walking up the master chain."""
    curr = window
    visited = set()
    while curr is not None and id(curr) not in visited:
        visited.add(id(curr))
        master = getattr(curr, "master", None)
        if master is None or master is curr or type(master).__name__ in ("MagicMock", "Mock", "str"):
            break
        curr = master
    return curr


def get_app_monitor_bounds(window: ctk.CTk | ctk.CTkToplevel) -> tuple[int, int, int, int]:
    """Returns (x, y, width, height) of the monitor/window area where the app is located or last located."""
    top_app = get_main_app_window(window)
    
    # 1. Try last stored geometry from app if window is iconic/minimized
    last_geom = getattr(top_app, "_last_geometry", None)
    
    parent_x = top_app.winfo_x()
    parent_y = top_app.winfo_y()
    parent_w = top_app.winfo_width()
    parent_h = top_app.winfo_height()

    if (parent_w <= 50 or parent_h <= 50 or parent_x <= -32000 or parent_y <= -32000) and last_geom:
        parent_x, parent_y, parent_w, parent_h = last_geom

    # Fallback to screen dimensions if window coordinates are invalid
    screen_w = top_app.winfo_screenwidth()
    screen_h = top_app.winfo_screenheight()

    if parent_w <= 50 or parent_h <= 50:
        return 0, 0, screen_w, screen_h

    return parent_x, parent_y, parent_w, parent_h


def center_window(window: ctk.CTk | ctk.CTkToplevel, width: int | None = None, height: int | None = None) -> None:
    """Centers a Tkinter / CustomTkinter window relative to app monitor or primary monitor."""
    try:
        from ui.widgets.ctk_tooltip import CTkTooltip
        CTkTooltip.dismiss_all()
    except Exception:
        pass

    window.update_idletasks()

    w = width if width is not None else window.winfo_width()
    h = height if height is not None else window.winfo_height()

    if w <= 1 or h <= 1:
        w = width or 800
        h = height or 600

    top_app = get_main_app_window(window)
    target_setting = "APP_SCREEN"
    if hasattr(top_app, "profile") and hasattr(top_app.profile, "ui_settings"):
        target_setting = getattr(top_app.profile.ui_settings, "popup_display_target", "APP_SCREEN")

    if target_setting == "APP_SCREEN":
        bx, by, bw, bh = get_app_monitor_bounds(window)
        x = bx + (bw - w) // 2
        y = by + (bh - h) // 2
    else:
        screen_w = window.winfo_screenwidth()
        screen_h = window.winfo_screenheight()
        x = (screen_w - w) // 2
        y = (screen_h - h) // 2

    window.geometry(f"{w}x{h}+{x}+{y}")


def bind_mouse_wheel_to_canvas(container_or_widget: Any, scroll_frame: ctk.CTkScrollableFrame | None = None) -> None:
    """Recursively binds MouseWheel events on all child widgets of a scrollable frame to ensure 100% fluid, stutter-free scrolling everywhere."""
    if scroll_frame is None and isinstance(container_or_widget, ctk.CTkScrollableFrame):
        scroll_frame = container_or_widget

    if not scroll_frame:
        return

    canvas = getattr(scroll_frame, "_parent_canvas", getattr(scroll_frame, "_canvas", None))
    if not canvas or not hasattr(canvas, "yview_scroll"):
        return

    def _scroll_canvas(delta: int):
        try:
            if delta != 0:
                canvas.yview_scroll(int(-1 * (delta / 120)), "units")
        except Exception:
            pass

    def _on_mouse_wheel(event):
        _scroll_canvas(event.delta)

    def _on_button_4(event):
        try:
            canvas.yview_scroll(-1, "units")
        except Exception:
            pass

    def _on_button_5(event):
        try:
            canvas.yview_scroll(1, "units")
        except Exception:
            pass

    def _on_textbox_mouse_wheel(event, textbox):
        try:
            tk_text = getattr(textbox, "_textbox", None)
            if tk_text:
                top, bottom = tk_text.yview()
                all_text_visible = (top <= 0.001 and bottom >= 0.999)
                if not all_text_visible:
                    can_scroll_up = (event.delta > 0 and top > 0.001)
                    can_scroll_down = (event.delta < 0 and bottom < 0.999)
                    if can_scroll_up or can_scroll_down:
                        return
            _scroll_canvas(event.delta)
            return "break"
        except Exception:
            pass

    def _apply_recursive(w):
        if w is None or not hasattr(w, "bind"):
            return

        if getattr(w, "_mw_bound", False):
            return
        try:
            setattr(w, "_mw_bound", True)
        except Exception:
            pass

        if isinstance(w, ctk.CTkTextbox):
            tb_target = getattr(w, "_textbox", w)
            try:
                tb_target.bind("<MouseWheel>", lambda e, tb=w: _on_textbox_mouse_wheel(e, tb))
            except Exception:
                pass
        else:
            sub_targets = [w]
            for attr in ("_label", "_canvas", "_entry", "_button", "_text_label"):
                t = getattr(w, attr, None)
                if t and hasattr(t, "bind"):
                    sub_targets.append(t)

            for target in sub_targets:
                try:
                    target.bind("<MouseWheel>", _on_mouse_wheel)
                    target.bind("<Button-4>", _on_button_4)
                    target.bind("<Button-5>", _on_button_5)
                except Exception:
                    pass

        if hasattr(w, "winfo_children"):
            try:
                children = w.winfo_children()
                for child in children:
                    _apply_recursive(child)
            except Exception:
                pass

    _apply_recursive(container_or_widget)


def enable_auto_hiding_scrollbar(scroll_frame: ctk.CTkScrollableFrame) -> None:
    """Enforces system-wide auto-hiding scrollbar behavior and proper full-height layout for CTkScrollableFrame without layout thrashing."""
    canvas = getattr(scroll_frame, "_parent_canvas", getattr(scroll_frame, "_canvas", None))
    scrollbar = getattr(scroll_frame, "_scrollbar", None)

    if not canvas or not scrollbar:
        return

    # Fix CustomTkinter grid placement: ensure canvas starts at row 0 with rowspan 2 so canvas isn't pushed down to row 1 (y=218)
    try:
        master = canvas.master
        canvas.grid_configure(row=0, rowspan=2, sticky="nsew")
        if hasattr(scrollbar, "grid_info"):
            scrollbar.grid_configure(row=0, column=1, rowspan=2, sticky="ns")
        if hasattr(master, "rowconfigure"):
            master.rowconfigure(0, weight=1)
            master.rowconfigure(1, weight=1)
            master.columnconfigure(0, weight=1)
    except Exception:
        pass

    _last_dims = (0, 0)
    _scheduled = False

    def update_scrollbar_visibility(*_args):
        nonlocal _last_dims, _scheduled
        if _scheduled:
            return
        _scheduled = True

        def _do_update():
            nonlocal _last_dims, _scheduled
            _scheduled = False
            try:
                if not scroll_frame.winfo_exists() or not canvas.winfo_exists():
                    return
                canvas_h = canvas.winfo_height()
                bbox = canvas.bbox("all")
                content_h = (bbox[3] - bbox[1]) if bbox else 0

                curr_dims = (canvas_h, content_h)
                if curr_dims == _last_dims:
                    return
                _last_dims = curr_dims

                if canvas_h > 1 and content_h <= canvas_h + 2:
                    if hasattr(scrollbar, "grid_remove"):
                        scrollbar.grid_remove()
                    elif hasattr(scrollbar, "pack_forget"):
                        scrollbar.pack_forget()
                else:
                    if hasattr(scrollbar, "grid"):
                        scrollbar.grid(row=0, column=1, rowspan=2, sticky="ns")
                    elif hasattr(scrollbar, "pack"):
                        scrollbar.pack(side="right", fill="y")
            except Exception:
                pass

        try:
            scroll_frame.after_idle(_do_update)
        except Exception:
            _do_update()

    canvas.bind("<Configure>", update_scrollbar_visibility, add="+")
    scroll_frame.bind("<Configure>", update_scrollbar_visibility, add="+")
    try:
        scroll_frame.after(100, update_scrollbar_visibility)
    except Exception:
        pass


class AutoScrollableFrame(ctk.CTkScrollableFrame):
    """CTkScrollableFrame that automatically hides its scrollbar when content fits without overflowing."""

    def __init__(self, master, **kwargs):
        super().__init__(master, **kwargs)
        enable_auto_hiding_scrollbar(self)


def _get_measure_func(font: Any) -> Callable:
    if hasattr(font, "measure"):
        return font.measure
    try:
        import tkinter.font as tkfont
        tk_f = tkfont.Font(font=font)
        return tk_f.measure
    except Exception:
        return lambda s: len(s) * 7


def wrap_and_truncate_text(
    text: str,
    font: Any = None,
    max_width: int = 300,
    max_lines: int = 2,
    ellipsis: str = "...",
) -> tuple[str, bool]:
    """Wraps text into at most `max_lines` lines matching `max_width` pixels.

    If the text exceeds `max_lines`, line `max_lines` is truncated with `ellipsis`
    and `is_truncated=True` is returned.
    """
    if not text:
        return "", False
    if max_lines < 1:
        return "", True

    measure = _get_measure_func(font)
    norm_text = text.replace("\r\n", " ").replace("\n", " ").strip()
    if not norm_text:
        return "", False

    if max_width <= 0:
        max_width = 300

    # If the entire normalized text fits in a single line
    if measure(norm_text) <= max_width:
        return norm_text, False

    words = norm_text.split(" ")
    lines: list[str] = []
    current_words: list[str] = []
    truncated = False

    word_idx = 0
    while word_idx < len(words):
        word = words[word_idx]
        if not word:
            word_idx += 1
            continue

        test_line = (" ".join(current_words) + " " + word) if current_words else word

        # If we are on the last allowed line
        if len(lines) == max_lines - 1:
            is_last_word = (word_idx == len(words) - 1)
            test_with_ellipsis = test_line if is_last_word else (test_line + ellipsis)

            if measure(test_with_ellipsis) <= max_width:
                current_words.append(word)
                word_idx += 1
            else:
                # Word doesn't fit on the last line
                if not current_words:
                    # Single word doesn't fit on the last line, truncate chars
                    w = word
                    while w and measure(w + ellipsis) > max_width:
                        w = w[:-1]
                    current_words.append(w + ellipsis)
                    truncated = True
                    word_idx = len(words)
                else:
                    truncated = True
                    break
        else:
            # Not on the last line yet
            if measure(test_line) <= max_width:
                current_words.append(word)
                word_idx += 1
            else:
                if not current_words:
                    # Word is wider than max_width, split word
                    w = word
                    while w and measure(w) > max_width:
                        w = w[:-1]
                    if not w:
                        w = word[0]
                    lines.append(w)
                    words[word_idx] = word[len(w):]
                else:
                    lines.append(" ".join(current_words))
                    current_words = []

    if current_words:
        last_str = " ".join(current_words)
        if truncated and not last_str.endswith(ellipsis):
            last_str += ellipsis
        lines.append(last_str)
    elif truncated and lines and not lines[-1].endswith(ellipsis):
        lines[-1] += ellipsis

    if word_idx < len(words):
        truncated = True
        if lines and not lines[-1].endswith(ellipsis):
            lines[-1] += ellipsis

    return "\n".join(lines), truncated


def enable_textbox_cursor_autoscroll(textbox: ctk.CTkTextbox) -> None:
    """Ensures a CTkTextbox automatically scrolls to keep the insertion cursor in view while typing."""
    inner = getattr(textbox, "_textbox", textbox)
    
    def _scroll_to_cursor(event=None):
        try:
            inner.see("insert")
        except Exception:
            pass

    try:
        inner.bind("<KeyRelease>", _scroll_to_cursor, add="+")
        inner.bind("<KeyPress>", _scroll_to_cursor, add="+")
        inner.bind("<ButtonRelease>", _scroll_to_cursor, add="+")
    except Exception:
        pass

