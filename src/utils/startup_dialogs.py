"""Message boxes for the moments before (or instead of) the main window.

A windowed PyInstaller build has no console: whatever goes wrong before the
main window exists is invisible unless it is put in front of the user. These
helpers need no Tk root on Windows (a plain Win32 message box), so they work
even when Tk itself is what failed, and they never raise - a broken dialog
must not replace the error it was supposed to report.
"""

import logging
import sys

logger = logging.getLogger("SupportCockpit")

_KIND_ERROR = "error"
_KIND_QUESTION = "question"

# Win32 MessageBoxW flags / return values
_MB_YESNO = 0x00000004
_MB_ICONERROR = 0x00000010
_MB_ICONWARNING = 0x00000030
_MB_SETFOREGROUND = 0x00010000
_MB_TOPMOST = 0x00040000
_IDYES = 6


def _show_native(title: str, message: str, kind: str) -> bool:
    """Shows the box and returns True for "yes" (always False for an error box).

    The one place that really opens a window - tests replace it.
    """
    if sys.platform.startswith("win"):
        import ctypes

        icon = _MB_ICONWARNING | _MB_YESNO if kind == _KIND_QUESTION else _MB_ICONERROR
        result = ctypes.windll.user32.MessageBoxW(None, message, title, icon | _MB_SETFOREGROUND | _MB_TOPMOST)
        return kind == _KIND_QUESTION and result == _IDYES

    import tkinter
    from tkinter import messagebox

    root = tkinter.Tk()
    root.withdraw()
    try:
        if kind == _KIND_QUESTION:
            return bool(messagebox.askyesno(title, message, parent=root))
        messagebox.showerror(title, message, parent=root)
        return False
    finally:
        root.destroy()


def _echo(title: str, message: str) -> None:
    """Also writes the text to the console of a source run (the exe has none)."""
    stream = sys.stderr if sys.stderr is not None else sys.stdout
    if stream is None:
        return
    try:
        print(f"[!] {title}: {message}", file=stream)
        stream.flush()
    except Exception:
        pass


def show_error(title: str, message: str) -> None:
    """Tells the user why the app is not starting."""
    _echo(title, message)
    try:
        _show_native(title, message, _KIND_ERROR)
    except Exception as err:
        logger.warning(f"Could not show startup error dialog: {err}")


def ask_yes_no(title: str, message: str) -> bool:
    """Asks a yes/no question; False when the question cannot be shown at all."""
    _echo(title, message)
    try:
        return _show_native(title, message, _KIND_QUESTION)
    except Exception as err:
        logger.warning(f"Could not show startup question dialog: {err}")
        return False
