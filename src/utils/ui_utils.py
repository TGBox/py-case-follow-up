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
