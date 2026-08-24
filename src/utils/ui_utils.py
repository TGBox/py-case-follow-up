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
    """Enforces system-wide auto-hiding scrollbar behavior: hides vertical scrollbar when content fits without overflowing."""
    canvas = getattr(scroll_frame, "_parent_canvas", getattr(scroll_frame, "_canvas", None))
    scrollbar = getattr(scroll_frame, "_scrollbar", None)

    if not canvas or not scrollbar:
        return

    def update_scrollbar_visibility(*_args):
        try:
            scroll_frame.update_idletasks()
            top, bottom = canvas.yview()
            if top <= 0.001 and bottom >= 0.999:
                # All content is visible -> hide scrollbar
                if hasattr(scrollbar, "grid_remove"):
                    scrollbar.grid_remove()
                elif hasattr(scrollbar, "pack_forget"):
                    scrollbar.pack_forget()
            else:
                # Content overflows -> show scrollbar
                if hasattr(scrollbar, "grid"):
                    scrollbar.grid(row=0, column=1, sticky="ns")
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
