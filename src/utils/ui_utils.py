from collections.abc import Callable
import re
import webbrowser
from typing import Any, Literal, cast
import tkinter as tk
import customtkinter as ctk

from constants import (
    ATTR_AUTO_HIDE_SCROLLBAR_INSTALLED,
    ATTR_LINK_CLICK_HANDLER,
    COLOR_FALLBACK_TEXT_BG,
    COLOR_ON_ACCENT_DARK,
    COLOR_ON_ACCENT_LIGHT,
    COLOR_SEARCH_HIGHLIGHT,
    LINK_DRAG_TOLERANCE_PX,
    CURSOR_ARROW,
    CURSOR_HAND,
    DEFAULT_FONT_FAMILY_FALLBACK,
    DEFAULT_FONT_SIZE_FALLBACK,
    DEFAULT_POPUP_DISPLAY_TARGET,
    FALLBACK_CHAR_PIXEL_WIDTH,
    HIGHLIGHT_LABEL_MAX_CHARS,
    HIGHLIGHT_LABEL_MAX_LINES,
    MIN_WINDOW_VISIBLE_DIM,
    MINIMIZED_WINDOW_COORD_THRESHOLD,
    MOUSEWHEEL_DELTA_UNIT,
    SCROLLBAR_CHECK_DELAYS_MS,
    SCROLLBAR_HYSTERESIS_PX,
    SCROLLBAR_MAX_FLIPS,
    WINDOW_CENTER_FALLBACK_HEIGHT,
    WINDOW_CENTER_FALLBACK_WIDTH,
)


def enable_auto_hiding_scrollbar(scroll_frame: ctk.CTkScrollableFrame) -> None:
    """Enforces system-wide auto-hiding scrollbar behavior and proper full-height layout for CTkScrollableFrame without layout thrashing."""
    # CTkScrollableFrame.__init__ is patched to call this, and AutoScrollableFrame
    # calls it again after super().__init__(). Without this guard every
    # AutoScrollableFrame ends up with two independent controllers, each with its
    # own _last_visible memo, fighting over the same scrollbar and scheduling a
    # second set of <Configure> handlers and after() timers.
    if getattr(scroll_frame, ATTR_AUTO_HIDE_SCROLLBAR_INSTALLED, False):
        return
    try:
        setattr(scroll_frame, ATTR_AUTO_HIDE_SCROLLBAR_INSTALLED, True)
    except Exception:
        pass

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

    _updating = False
    _scheduled = False
    _last_visible: bool | None = None
    # Showing or hiding the bar resizes the canvas, which re-wraps the content,
    # which can flip the decision straight back - an endless hide/show cascade
    # that keeps the idle queue full, so update_idletasks() never returns and the
    # app (or a test calling it) freezes. Two brakes: a dead band around the
    # decision, and a hard cap on how often one frame may flip.
    _HYSTERESIS_PX = SCROLLBAR_HYSTERESIS_PX
    _MAX_FLIPS = SCROLLBAR_MAX_FLIPS
    _flips = 0

    def update_scrollbar_visibility(*_args):
        nonlocal _scheduled
        if _updating or _scheduled:
            return
        _scheduled = True

        def _do_update():
            nonlocal _updating, _scheduled, _last_visible, _flips
            _scheduled = False
            if _updating:
                return
            try:
                if not scroll_frame.winfo_exists() or not canvas.winfo_exists():
                    return
                _updating = True
                orientation = getattr(scroll_frame, "_orientation", "vertical")
                bbox = canvas.bbox("all")

                if orientation == "horizontal":
                    canvas_dim = canvas.winfo_width()
                    content_dim = (bbox[2] - bbox[0]) if bbox else 0
                else:
                    canvas_dim = canvas.winfo_height()
                    content_dim = (bbox[3] - bbox[1]) if bbox else 0

                if canvas_dim <= 1:
                    return

                if _last_visible:
                    # Already visible: only hide once the content clears the dead
                    # band, so a few pixels of reflow cannot toggle it back.
                    should_show = content_dim > (canvas_dim - _HYSTERESIS_PX)
                else:
                    should_show = content_dim > (canvas_dim + 2)

                if should_show == _last_visible:
                    return

                if _flips >= _MAX_FLIPS:
                    # This frame is oscillating. Settle on "visible", which is the
                    # harmless end state (a scrollbar too many beats content the
                    # user cannot reach), and stop reacting.
                    if _last_visible:
                        return
                    should_show = True

                _flips += 1
                _last_visible = should_show

                if not should_show:
                    try:
                        if orientation == "horizontal":
                            canvas.xview_moveto(0.0)
                        else:
                            canvas.yview_moveto(0.0)
                    except Exception:
                        pass
                    if hasattr(scrollbar, "grid_remove"):
                        scrollbar.grid_remove()
                    elif hasattr(scrollbar, "pack_forget"):
                        scrollbar.pack_forget()
                else:
                    if hasattr(scrollbar, "grid"):
                        if orientation == "horizontal":
                            scrollbar.grid(row=1, column=0, columnspan=2, sticky="ew")
                        else:
                            scrollbar.grid(row=0, column=1, rowspan=2, sticky="ns")
                    elif hasattr(scrollbar, "pack"):
                        if orientation == "horizontal":
                            scrollbar.pack(side="bottom", fill="x")
                        else:
                            scrollbar.pack(side="right", fill="y")
            except Exception:
                pass
            finally:
                _updating = False

        try:
            scroll_frame.after_idle(_do_update)
        except Exception:
            _do_update()

    canvas.bind("<Configure>", update_scrollbar_visibility, add="+")
    scroll_frame.bind("<Configure>", update_scrollbar_visibility, add="+")
    scroll_frame.bind("<Map>", update_scrollbar_visibility, add="+")
    try:
        for delay in SCROLLBAR_CHECK_DELAYS_MS:
            scroll_frame.after(delay, update_scrollbar_visibility)
    except Exception:
        pass


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

    # Also make CTkBaseClass dimension updates resilient to None/missing event and re-entrant loops.
    # CTkBaseClass is an internal customtkinter class not exported/declared in
    # its public API across all versions - hence the hasattr(ctk, ...) guard
    # before ever touching it.
    if hasattr(ctk, "CTkBaseClass") and hasattr(ctk.CTkBaseClass, "_update_dimensions_event"):  # pyright: ignore[reportAttributeAccessIssue]
        orig_update_dim = ctk.CTkBaseClass._update_dimensions_event  # pyright: ignore[reportAttributeAccessIssue]
        def safe_update_dim(self, event=None):
            if event is None:
                return
            if getattr(self, "_in_update_dim", False):
                return
            try:
                self._in_update_dim = True
                return orig_update_dim(self, event)
            finally:
                self._in_update_dim = False
        ctk.CTkBaseClass._update_dimensions_event = safe_update_dim  # pyright: ignore[reportAttributeAccessIssue]

    # Prevent CTkScrollbar._draw from triggering re-entrant update_idletasks
    # cascades. Same undeclared-internal situation as CTkBaseClass above.
    if hasattr(ctk, "CTkScrollbar") and hasattr(ctk.CTkScrollbar, "_draw"):  # pyright: ignore[reportAttributeAccessIssue]
        orig_draw = ctk.CTkScrollbar._draw  # pyright: ignore[reportAttributeAccessIssue]
        def safe_draw(self, *args, **kwargs):
            if getattr(self, "_in_draw", False):
                return
            try:
                self._in_draw = True
                return orig_draw(self, *args, **kwargs)
            finally:
                self._in_draw = False
        ctk.CTkScrollbar._draw = safe_draw  # pyright: ignore[reportAttributeAccessIssue]

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
            enable_auto_hiding_scrollbar(self)
        except Exception:
            pass

    ctk.CTkScrollableFrame.__init__ = safe_init
    # Idempotency marker invented by this patch itself (read back via getattr(
    # ..., False) at the top of this function) - not a real customtkinter attribute.
    ctk.CTkScrollableFrame._ctk_resilience_patched = True  # pyright: ignore[reportAttributeAccessIssue]



def patch_ctk_tabview() -> None:
    """Ensures CTkTabview child tabs retain theme color tuples across appearance mode changes.

    By default, CustomTkinter's CTkTabview._create_tab and CTkTabview._draw call
    `self._apply_appearance_mode(self._fg_color)` which collapses the ('gray86', 'gray17')
    color tuple into a static single string ('gray86' in Light mode, 'gray17' in Dark mode).
    When child widgets (frames, scrollables, labels) detect their master's background color,
    they inherit this single string. Subsequent calls to `ctk.set_appearance_mode(...)` fail
    to update the child backgrounds, causing solid light-gray boxes behind transparent
    widgets in Dark mode and vice-versa.

    This patch ensures tabs are always configured with the raw color tuples `self._fg_color`
    and `self._bg_color` directly, preserving dynamic appearance mode evaluation.
    """
    if getattr(ctk.CTkTabview, "_ctk_resilience_patched", False):
        return

    def safe_create_tab(self):
        new_tab: Any = ctk.CTkFrame(self, height=0, width=0, border_width=0, corner_radius=0)
        target_color = getattr(self, "_bg_color", None) if getattr(self, "_fg_color", None) == "transparent" else getattr(self, "_fg_color", None)
        new_tab.configure(fg_color=target_color, bg_color=target_color)
        return new_tab

    orig_draw = getattr(ctk.CTkTabview, "_draw", None)

    def safe_draw(self, no_color_updates: bool = False):
        if orig_draw:
            orig_draw(self, no_color_updates)
        target_color = getattr(self, "_bg_color", None) if getattr(self, "_fg_color", None) == "transparent" else getattr(self, "_fg_color", None)
        tab_dict: dict[str, Any] = getattr(self, "_tab_dict", {})
        for tab in tab_dict.values():
            tab.configure(fg_color=target_color, bg_color=target_color)

    ctk.CTkTabview._create_tab = safe_create_tab  # pyright: ignore[reportAttributeAccessIssue]
    ctk.CTkTabview._draw = safe_draw  # pyright: ignore[reportAttributeAccessIssue]
    ctk.CTkTabview._ctk_resilience_patched = True  # pyright: ignore[reportAttributeAccessIssue]


def patch_ctk_rendering() -> None:
    """Configures CustomTkinter DrawEngine to use polygon shapes instead of font shapes.

    On Windows, CustomTkinter defaults to `font_shapes` which rasterizes font glyphs for rounded
    borders and corners. When moving windows between displays with differing DPI scales or resolutions,
    font glyph scaling distorts outlines and borders of dropdowns and widgets. Setting
    `DrawEngine.preferred_drawing_method = "polygon_shapes"` renders native vector polygons.
    """
    try:
        import importlib
        core_rendering = importlib.import_module("customtkinter.windows.widgets.core_rendering")
        draw_engine = getattr(core_rendering, "DrawEngine", None)
        if draw_engine is not None:
            draw_engine.preferred_drawing_method = "polygon_shapes"
    except Exception:
        pass


# Automatically apply patches on import
patch_ctk_scrollable_frame()
patch_ctk_tabview()
patch_ctk_rendering()



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
    # curr can never actually be None here (the walk only ever reassigns it to
    # a master that's just been checked to be non-None, above) but pyright's
    # loop-carried type for `curr` widens to include None/Any across the
    # back-edge - the `window` fallback is unreachable in practice, just a
    # type-safe guard.
    return curr if curr is not None else window


def get_app_monitor_bounds(window: ctk.CTk | ctk.CTkToplevel) -> tuple[int, int, int, int]:
    """Returns (x, y, width, height) of the monitor/window area where the app is located or last located."""
    top_app = get_main_app_window(window)

    # 1. Try last stored geometry from app if window is iconic/minimized
    last_geom = getattr(top_app, "_last_geometry", None)

    parent_x = top_app.winfo_x()
    parent_y = top_app.winfo_y()
    parent_w = top_app.winfo_width()
    parent_h = top_app.winfo_height()

    if (parent_w <= MIN_WINDOW_VISIBLE_DIM or parent_h <= MIN_WINDOW_VISIBLE_DIM or parent_x <= MINIMIZED_WINDOW_COORD_THRESHOLD or parent_y <= MINIMIZED_WINDOW_COORD_THRESHOLD) and last_geom:
        parent_x, parent_y, parent_w, parent_h = last_geom

    # Fallback to screen dimensions if window coordinates are invalid
    screen_w = top_app.winfo_screenwidth()
    screen_h = top_app.winfo_screenheight()

    if parent_w <= MIN_WINDOW_VISIBLE_DIM or parent_h <= MIN_WINDOW_VISIBLE_DIM:
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
        w = width or WINDOW_CENTER_FALLBACK_WIDTH
        h = height or WINDOW_CENTER_FALLBACK_HEIGHT

    top_app = get_main_app_window(window)
    target_setting = DEFAULT_POPUP_DISPLAY_TARGET
    # .profile is a custom attribute only the real app root (SupportCockpitApp)
    # has; top_app is typed generically as CTk | CTkToplevel, hence the
    # hasattr() guards.
    if hasattr(top_app, "profile") and hasattr(top_app.profile, "ui_settings"):  # pyright: ignore[reportAttributeAccessIssue]
        target_setting = getattr(top_app.profile.ui_settings, "popup_display_target", DEFAULT_POPUP_DISPLAY_TARGET)  # pyright: ignore[reportAttributeAccessIssue]

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


def watch_scroll_position(scroll_frame: Any, callback: Callable[[float, float], None]) -> bool:
    """Calls callback(first, last) on every scroll of a CTkScrollableFrame.

    Hooked into the canvas' yscrollcommand rather than <MouseWheel>, because
    neither of the two ways a user actually scrolls reaches a binding on the
    canvas: the wheel event is delivered to the card under the pointer (which
    scrolls the canvas itself, see bind_mouse_wheel_to_canvas), and dragging the
    scrollbar produces no event at all. Anything that loads more content while
    scrolling therefore waited for events that never arrived.

    yscrollcommand is set once by CTkScrollableFrame.__init__ and fires for every
    view change, whatever caused it. Returns False if the frame has no usable
    canvas or the watch is already installed.
    """
    canvas = getattr(scroll_frame, "_parent_canvas", None) or getattr(scroll_frame, "_canvas", None)
    if canvas is None or getattr(canvas, "_scroll_position_watch", False):
        return False

    try:
        vorher = canvas.cget("yscrollcommand")
    except Exception:
        return False

    def _relay(first, last):
        if vorher:
            try:
                canvas.tk.call(vorher, first, last)
            except Exception:
                pass
        # Rendering inside the callback moves the view again, which calls this
        # relay a second time - without the guard that recurses until Tk gives up.
        if getattr(canvas, "_scroll_position_busy", False):
            return
        canvas._scroll_position_busy = True
        try:
            callback(float(first), float(last))
        except Exception:
            pass
        finally:
            canvas._scroll_position_busy = False

    try:
        canvas.configure(yscrollcommand=_relay)
        canvas._scroll_position_watch = True
    except Exception:
        return False
    return True


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
                canvas.yview_scroll(int(-1 * (delta / MOUSEWHEEL_DELTA_UNIT)), "units")
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
            w._mw_bound = True
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
        return lambda s: len(s) * FALLBACK_CHAR_PIXEL_WIDTH


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



def debounce(widget, key: str, delay_ms: int, callback: Callable[[], None]) -> None:
    """Runs callback after delay_ms, cancelling an earlier pending call with the same key.

    Used for keystroke handlers: without it every single key press in a search
    field triggers a full filter + re-render of the case list (hundreds of
    widgets), so typing a 10-character query rebuilt the list 10 times.
    The pending after-id is stored on the widget itself, keyed per use site.
    """
    attr = f"_debounce_after_{key}"
    pending = getattr(widget, attr, None)
    if pending:
        try:
            widget.after_cancel(pending)
        except Exception:
            pass

    def _run():
        setattr(widget, attr, None)
        callback()

    try:
        setattr(widget, attr, widget.after(delay_ms, _run))
    except Exception:
        # No usable Tk event loop (e.g. widget already destroyed) - run directly
        # so behaviour never silently degrades to "nothing happens".
        setattr(widget, attr, None)
        callback()


def cancel_debounce(widget, key: str) -> None:
    """Cancels a pending debounced call, e.g. when a widget or dialog is destroyed."""
    attr = f"_debounce_after_{key}"
    pending = getattr(widget, attr, None)
    if pending:
        try:
            widget.after_cancel(pending)
        except Exception:
            pass
    setattr(widget, attr, None)


def create_highlighted_label(
    parent: Any,
    text: str,
    query: str | list[str],
    font: tuple[str, int] | tuple[str, int, str] | ctk.CTkFont,
    text_color: str | tuple[str, str],
    bg_color: str | tuple[str, str],
    highlight_color: str | tuple[str, str] = COLOR_SEARCH_HIGHLIGHT,
    highlight_font: tuple[str, int] | tuple[str, int, str] | ctk.CTkFont | None = None,
    wrap: Literal["none", "char", "word"] = "word",
    on_click: Callable[[Any], Any] | None = None,
    scroll_frame: ctk.CTkScrollableFrame | None = None,
    max_height_chars: int = HIGHLIGHT_LABEL_MAX_CHARS,
    max_display_lines: int = HIGHLIGHT_LABEL_MAX_LINES,
) -> tk.Text:
    """Creates a seamless, borderless tk.Text widget with highlighted query occurrences.

    Supports single search string or list of search terms, tagging matching substrings
    with a prominent gold/yellow highlight color while preserving smooth scrolling and click handling.
    """
    mode = ctk.get_appearance_mode().lower()

    def _resolve(c: str | tuple[str, str]) -> str:
        if isinstance(c, (tuple, list)):
            return c[1] if mode == "dark" else c[0]
        return c

    res_bg = _resolve(bg_color)
    if res_bg == "transparent":
        # Walk up the widget chain: a transparent row inside a transparent frame
        # still has to inherit the colour of the first opaque ancestor, otherwise
        # the label renders a visibly mismatched rectangle (light mode especially).
        node = parent
        for _ in range(8):
            if node is None or not hasattr(node, "cget"):
                break
            try:
                p_fg = node.cget("fg_color")
            except Exception:
                p_fg = None
            if p_fg and p_fg != "transparent":
                res_bg = _resolve(p_fg)
                break
            node = getattr(node, "master", None)
        if res_bg == "transparent":
            res_bg = COLOR_FALLBACK_TEXT_BG[1] if mode == "dark" else COLOR_FALLBACK_TEXT_BG[0]
    res_text = _resolve(text_color)
    res_hl = _resolve(highlight_color)

    # Height/width are recomputed from real font metrics below; these are only
    # the initial values so the widget does not flash at the wrong size.
    if wrap == "none" or ("\n" not in text and len(text) <= max_height_chars):
        h = 1
    else:
        h = 2

    init_width = 1
    if wrap == "none":
        # tk.Text width is measured in units of the font's '0' glyph, not in
        # characters. For a proportional font len(text) under-sizes strings with
        # wide glyphs (caps, umlauts) and the tail is silently clipped, so
        # convert pixels -> '0'-units instead.
        try:
            measure = _get_measure_func(font)
            zero_w = max(1, int(measure("0")))
            init_width = max(1, -(-int(measure(text)) // zero_w) + 1)
        except Exception:
            init_width = max(1, len(text))

    txt = tk.Text(
        parent,
        height=h,
        width=init_width,
        font=cast(Any, font),
        wrap=wrap,
        relief="flat",
        borderwidth=0,
        highlightthickness=0,
        padx=0,
        pady=0,
        spacing1=0,
        spacing2=0,
        spacing3=0,
        bg=res_bg,
        cursor=CURSOR_HAND if on_click else CURSOR_ARROW,
        takefocus=0,
    )

    if highlight_font is None:
        if isinstance(font, ctk.CTkFont):
            font_any: Any = font
            family = font_any.cget("family") if hasattr(font_any, "cget") else getattr(font_any, "_family", DEFAULT_FONT_FAMILY_FALLBACK)
            size = font_any.cget("size") if hasattr(font_any, "cget") else getattr(font_any, "_size", DEFAULT_FONT_SIZE_FALLBACK)
            hl_f: Any = ctk.CTkFont(family=family, size=size, weight="bold")
        elif isinstance(font, tuple) and len(font) >= 2:
            hl_f = (font[0], font[1], "bold")
        else:
            hl_f = font
    else:
        hl_f = highlight_font

    txt.tag_configure("normal", foreground=res_text, font=cast(Any, font))
    txt.tag_configure("match", foreground=res_hl, font=cast(Any, hl_f))

    if isinstance(query, str):
        raw_terms = [query.strip()] if query.strip() else []
    else:
        raw_terms = [t.strip() for t in query if t and t.strip()]

    terms = [t for t in raw_terms if t]
    if not terms:
        txt.insert("end", text, "normal")
    else:
        lower_text = text.lower()
        terms_info = [(t.lower(), len(t)) for t in terms]
        pos = 0
        text_len = len(text)
        while pos < text_len:
            best_idx = -1
            best_len = 0
            for t_low, t_len in terms_info:
                idx = lower_text.find(t_low, pos)
                if idx != -1:
                    if best_idx == -1 or idx < best_idx:
                        best_idx = idx
                        best_len = t_len
                    elif idx == best_idx and t_len > best_len:
                        best_len = t_len

            if best_idx == -1:
                txt.insert("end", text[pos:], "normal")
                break

            if best_idx > pos:
                txt.insert("end", text[pos:best_idx], "normal")

            txt.insert("end", text[best_idx : best_idx + best_len], "match")
            pos = best_idx + best_len

    txt.configure(state="disabled")

    if wrap != "none":
        # A fixed height of 2 lines silently swallows everything past line 2
        # (wiki snippets, long case subtitles). Re-measure the real number of
        # display lines whenever the widget is resized and grow to fit.
        _applied_h = [h]

        def _fit_height(_event=None, _w=txt):
            try:
                if not _w.winfo_exists() or _w.winfo_width() <= 1:
                    return
                # Text.count("displaylines") returns the number of display-line
                # *breaks* between the two indices, and Tk/Tkinter reports that as
                # None for 0, a bare int on Python 3.13+, or a 1-tuple on older
                # versions - so normalise all three before adding the first line.
                raw = _w.count("1.0", "end - 1 chars", "displaylines")
                if raw is None:
                    breaks = 0
                elif isinstance(raw, (tuple, list)):
                    breaks = int(raw[0]) if raw else 0
                else:
                    breaks = int(raw)
                needed = max(1, min(breaks + 1, max_display_lines))
                if needed != _applied_h[0]:
                    _applied_h[0] = needed
                    _w.configure(height=needed)
            except Exception:
                pass

        txt.bind("<Configure>", _fit_height, add="+")
        try:
            txt.after_idle(_fit_height)
        except Exception:
            pass

    if on_click:
        # Only the widget-level binding. Tk invokes tag bindings *in addition to*
        # the widget binding, so also tag_bind-ing on_click fired it twice per
        # click (opened wiki links twice, and cancelled out toggle handlers).
        txt.bind("<Button-1>", on_click)
        txt.bind("<B1-Motion>", lambda e: "break")

    if scroll_frame:
        bind_mouse_wheel_to_canvas(txt, scroll_frame)

    return txt


# ============================================================================
# Farben mischen (Nutzerfarbe als Ton auf Karten)
# ============================================================================

def _rgb8(widget: Any, color: str) -> tuple[int, int, int]:
    """Resolves any Tk colour (hex or a name like "gray23") to 8-bit RGB."""
    r, g, b = widget.winfo_rgb(color)
    return r >> 8, g >> 8, b >> 8


def mix_colors(widget: Any, color: str, base: str, ratio: float) -> str:
    """Blends ``ratio`` of ``color`` into ``base`` and returns a hex string.

    Tk resolves both colours, so CTk-style names ("gray23") work as base.
    Raises tk.TclError for an unknown colour, so the caller can fall back.
    """
    ratio = max(0.0, min(1.0, ratio))
    c = _rgb8(widget, color)
    b = _rgb8(widget, base)
    mixed = (round(b[i] + (c[i] - b[i]) * ratio) for i in range(3))
    return "#{:02x}{:02x}{:02x}".format(*mixed)


def _relative_luminance(rgb: tuple[int, int, int]) -> float:
    def _lin(v: int) -> float:
        s = v / 255
        return s / 12.92 if s <= 0.04045 else ((s + 0.055) / 1.055) ** 2.4
    r, g, b = (_lin(v) for v in rgb)
    return 0.2126 * r + 0.7152 * g + 0.0722 * b


def readable_text_on(widget: Any, color: str) -> str:
    """Light or dark text colour, whichever contrasts better with ``color`` (WCAG)."""
    lum = _relative_luminance(_rgb8(widget, color))
    light = _relative_luminance(_rgb8(widget, COLOR_ON_ACCENT_LIGHT))
    dark = _relative_luminance(_rgb8(widget, COLOR_ON_ACCENT_DARK))
    contrast_light = (light + 0.05) / (lum + 0.05)
    contrast_dark = (lum + 0.05) / (dark + 0.05)
    return COLOR_ON_ACCENT_LIGHT if contrast_light >= contrast_dark else COLOR_ON_ACCENT_DARK



def contrast_ratio(widget: Any, color_a: str, color_b: str) -> float:
    """WCAG contrast ratio between two Tk colours (1.0 .. 21.0)."""
    la = _relative_luminance(_rgb8(widget, color_a))
    lb = _relative_luminance(_rgb8(widget, color_b))
    hi, lo = max(la, lb), min(la, lb)
    return (hi + 0.05) / (lo + 0.05)


def readable_variant(widget: Any, color: str, background: str, min_contrast: float = 4.5) -> str:
    """``color`` darkened (light background) or lightened (dark background)
    just enough to be readable as text on ``background``.

    Keeps the hue recognisable: a yellow user colour becomes a deep ochre on
    a light card and stays a light yellow on a dark one.
    """
    bg_lum = _relative_luminance(_rgb8(widget, background))
    toward = "#000000" if bg_lum > 0.18 else "#ffffff"
    step = 0.0
    candidate = mix_colors(widget, color, color, 1.0)
    while contrast_ratio(widget, candidate, background) < min_contrast and step < 1.0:
        step = min(1.0, step + 0.05)
        candidate = mix_colors(widget, toward, color, step)
    return candidate

# ============================================================================
# Klickbare Links in read-only tk.Text (Timeline-Notizen)
# ============================================================================

#: http(s)/ftp/file-URLs, mailto: und nacktes "www." - bis zum naechsten
#: Leerzeichen oder Anfuehrungszeichen.
_LINK_RE = re.compile(r"(?:https?://|ftp://|file:///?|mailto:|www\.)[^\s<>\"']+", re.IGNORECASE)
#: Satzzeichen, die beim Tippen direkt hinter einem Link landen, aber nicht
#: dazugehoeren ("siehe https://x.de/a." / "(https://x.de/a)").
_LINK_TRAILING = ".,;:!?)]}>"
_LINK_PAIRS = {")": "(", "]": "[", "}": "{"}


def find_links(text: str) -> list[tuple[str, str]]:
    """Links in ``text`` as (text as written, target to open), in order.

    Trailing punctuation is dropped unless it closes a bracket that the link
    itself opened (Wikipedia-style ``.../Foo_(Bar)``). A bare ``www.`` link
    opens as https.
    """
    found: list[tuple[str, str]] = []
    for m in _LINK_RE.finditer(text or ""):
        raw = m.group(0)
        while raw and raw[-1] in _LINK_TRAILING:
            opener = _LINK_PAIRS.get(raw[-1])
            if opener and raw.count(opener) >= raw.count(raw[-1]):
                break
            raw = raw[:-1]
        scheme = re.match(r"(?:https?://|ftp://|file:///?|mailto:|www\.)", raw, re.IGNORECASE)
        if not scheme or len(raw) == scheme.end():
            continue  # nur "https://" o.ae. ohne Ziel
        target = f"https://{raw}" if raw.lower().startswith("www.") else raw
        found.append((raw, target))
    return found


class LinkClickHandler:
    """Opens a link on a plain click; a press that turns into a drag is a
    text selection (copying a link out of a note) and opens nothing."""

    def __init__(self, txt: tk.Text, opener: Callable[[str], Any]):
        self.txt = txt
        self.opener = opener
        self._press_xy: tuple[int, int] | None = None

    def press(self, event: Any) -> None:
        self._press_xy = (event.x, event.y)

    def release(self, event: Any, target: str) -> bool:
        start, self._press_xy = self._press_xy, None
        if start is None:
            return False
        if abs(event.x - start[0]) > LINK_DRAG_TOLERANCE_PX or abs(event.y - start[1]) > LINK_DRAG_TOLERANCE_PX:
            return False
        try:
            if self.txt.tag_ranges("sel"):
                return False
        except tk.TclError:
            return False
        try:
            self.opener(target)
        except Exception:
            return False
        return True


def linkify_text_widget(
    txt: tk.Text,
    link_color: str | tuple[str, str],
    opener: Callable[[str], Any] | None = None,
) -> list[str]:
    """Marks every link in a (read-only) tk.Text and makes it clickable.

    A plain click opens the link in the default browser / mail program. A
    press that turns into a drag is a text selection and opens nothing, so
    copying a link out of a note keeps working. Returns the link targets.
    """
    try:
        content = txt.get("1.0", "end-1c")
    except tk.TclError:
        return []
    links = find_links(content)
    if not links:
        return []

    if isinstance(link_color, (tuple, list)):
        link_color = link_color[1] if ctk.get_appearance_mode().lower() == "dark" else link_color[0]
    handler = LinkClickHandler(txt, opener or webbrowser.open)
    # Kept on the widget so the handler lives as long as the bindings do (and
    # tests can drive it without a mapped window).
    setattr(txt, ATTR_LINK_CLICK_HANDLER, handler)
    base_cursor = txt.cget("cursor") or CURSOR_ARROW

    txt.tag_configure("link", foreground=link_color, underline=True)
    txt.tag_raise("link")

    search_from = "1.0"
    for idx, (raw, target) in enumerate(links):
        # Search instead of counting characters: Tk and Python count some
        # characters (emoji) differently, a character offset could drift.
        start = txt.search(raw, search_from, stopindex="end", exact=True)
        if not start:
            continue
        end = f"{start}+{len(raw)}c"
        tag = f"link-{idx}"
        txt.tag_add("link", start, end)
        txt.tag_add(tag, start, end)
        txt.tag_bind(tag, "<ButtonPress-1>", handler.press, add="+")
        txt.tag_bind(tag, "<ButtonRelease-1>", lambda e, t=target: handler.release(e, t), add="+")
        search_from = end

    txt.tag_bind("link", "<Enter>", lambda _e: txt.configure(cursor=CURSOR_HAND))
    txt.tag_bind("link", "<Leave>", lambda _e: txt.configure(cursor=base_cursor))
    return [t for _, t in links]
