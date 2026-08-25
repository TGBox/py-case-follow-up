import customtkinter as ctk


def center_window(window: ctk.CTk | ctk.CTkToplevel, width: int | None = None, height: int | None = None) -> None:
    """Centers a Tkinter / CustomTkinter window on the screen."""
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

    def update_scrollbar_visibility(*_args):
        try:
            scroll_frame.update_idletasks()
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

    canvas.bind("<Configure>", update_scrollbar_visibility, add="+")
    scroll_frame.bind("<Configure>", update_scrollbar_visibility, add="+")
    scroll_frame.after(50, update_scrollbar_visibility)
    scroll_frame.after(200, update_scrollbar_visibility)


class AutoScrollableFrame(ctk.CTkScrollableFrame):
    """CTkScrollableFrame that automatically hides its scrollbar when content fits without overflowing."""

    def __init__(self, master, **kwargs):
        super().__init__(master, **kwargs)
        enable_auto_hiding_scrollbar(self)
