from collections.abc import Callable
from typing import Any
import customtkinter as ctk


def center_window(window: ctk.CTk | ctk.CTkToplevel, width: int | None = None, height: int | None = None) -> None:
    """Centers a Tkinter / CustomTkinter window on the screen and dismisses lingering tooltips."""
    try:
        from ui.widgets.ctk_tooltip import CTkTooltip
        CTkTooltip.dismiss_all()
    except Exception:
        pass

    window.update_idletasks()

    w = width if width is not None else window.winfo_width()
    h = height if height is not None else window.winfo_height()

    if w <= 1 or h <= 1:
        # Fallback to requested size or defaults
        w = width or 800
        h = height or 600

    screen_w = window.winfo_screenwidth()
    screen_h = window.winfo_screenheight()

    x = max(0, (screen_w - w) // 2)
    y = max(0, (screen_h - h) // 2)

    window.geometry(f"{w}x{h}+{x}+{y}")


def enable_auto_hiding_scrollbar(scroll_frame: ctk.CTkScrollableFrame) -> None:
    """Enforces system-wide auto-hiding scrollbar behavior and proper full-height layout for CTkScrollableFrame."""
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

    def update_scrollbar_visibility(*_args):
        nonlocal _updating
        if _updating:
            return
        try:
            if not scroll_frame.winfo_exists() or not canvas.winfo_exists():
                return
            _updating = True
            bbox = canvas.bbox("all")
            canvas_h = canvas.winfo_height()
            content_h = (bbox[3] - bbox[1]) if bbox else 0

            if canvas_h > 1 and content_h <= canvas_h + 2:
                # All content fits in canvas -> reset view offset to top & hide scrollbar
                canvas.yview_moveto(0.0)
                if hasattr(scrollbar, "grid_remove"):
                    scrollbar.grid_remove()
                elif hasattr(scrollbar, "pack_forget"):
                    scrollbar.pack_forget()
            else:
                # Content overflows -> show scrollbar
                if hasattr(scrollbar, "grid"):
                    scrollbar.grid(row=0, column=1, rowspan=2, sticky="ns")
                elif hasattr(scrollbar, "pack"):
                    scrollbar.pack(side="right", fill="y")
        except Exception:
            pass
        finally:
            _updating = False

    canvas.bind("<Configure>", update_scrollbar_visibility, add="+")
    scroll_frame.bind("<Configure>", update_scrollbar_visibility, add="+")
    try:
        scroll_frame.after(50, update_scrollbar_visibility)
        scroll_frame.after(200, update_scrollbar_visibility)
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

