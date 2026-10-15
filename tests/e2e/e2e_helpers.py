"""Widget-driving helpers for the e2e flows (imported by the tests; the fixtures live in conftest.py)."""

import re
import time
import tkinter as tk
from collections.abc import Callable, Iterator
from pathlib import Path

import customtkinter as ctk

from config import AppConfig
from services.storage_service import StorageService


def wait_until(app, cond: Callable[[], object], timeout: float = 3.0, what: str = "condition"):
    """Pumps the Tk event loop until cond() is truthy; fails the test after timeout seconds."""
    deadline = time.monotonic() + timeout
    while True:
        app.update()
        result = cond()
        if result:
            return result
        if time.monotonic() > deadline:
            raise AssertionError(f"timed out after {timeout}s waiting for {what}")
        time.sleep(0.01)


def walk(widget) -> Iterator:
    """Every descendant widget (including Toplevel dialogs parented anywhere below)."""
    for child in widget.winfo_children():
        yield child
        yield from walk(child)


def widget_text(widget) -> str:
    try:
        if isinstance(widget, (ctk.CTkTextbox, tk.Text)):
            return widget.get("1.0", "end-1c")
        return str(widget.cget("text"))
    except Exception:
        return ""


def visible_texts(root) -> list[str]:
    """Texts of all labels, buttons and text areas below root."""
    return [t for w in walk(root) if isinstance(w, (ctk.CTkLabel, ctk.CTkButton, ctk.CTkTextbox, tk.Text)) if (t := widget_text(w))]


def find_button(root, text: str) -> ctk.CTkButton:
    """The single live CTkButton below root whose caption contains text."""
    hits = [w for w in walk(root) if isinstance(w, ctk.CTkButton) and w.winfo_exists() and text in widget_text(w)]
    assert len(hits) == 1, f"expected one button containing {text!r}, found {[widget_text(h) for h in hits]}"
    return hits[0]


def find_dialog(app, cls, timeout: float = 2.0):
    """Waits for an open dialog of the given class anywhere in the app's widget tree."""
    def _find():
        for w in walk(app):
            if isinstance(w, cls) and w.winfo_exists():
                return w
        return None
    return wait_until(app, _find, timeout, what=f"dialog {cls.__name__}")


def dialog_closed(app, dialog) -> None:
    wait_until(app, lambda: not dialog.winfo_exists(), what=f"{type(dialog).__name__} to close")


def type_into(entry, text: str) -> None:
    """Replaces the content of a CTkEntry / CTkTextbox like a user selecting all and typing."""
    if isinstance(entry, ctk.CTkTextbox):
        entry.delete("1.0", "end")
        entry.insert("1.0", text)
    else:
        entry.delete(0, "end")
        entry.insert(0, text)


def choose(option_menu, value: str) -> None:
    """Picks an entry of a CTkOptionMenu the way its dropdown does: set + command callback."""
    assert value in option_menu.cget("values"), f"{value!r} not in {option_menu.cget('values')}"
    option_menu.set(value)
    command = option_menu._command  # the callback the dropdown fires on selection
    if command is not None:
        command(value)


def press_key(widget, sequence: str, keysym: str = "") -> None:
    """Fires the widget's own key binding for sequence (e.g. "<Return>", "<KeyRelease>").

    The app runs withdrawn, and an unmapped window can never hold the keyboard
    focus - Tk silently drops a synthetic key event (event_generate) for it. So
    the Tcl script Tk would run for that event is executed directly instead,
    with the event fields filled in; the text itself is typed beforehand with
    insert(), exactly as the entry's class binding would have done.
    """
    target = getattr(widget, "_entry", None) or getattr(widget, "_textbox", None) or widget
    script = target.bind(sequence)
    assert script, f"{type(widget).__name__} has no {sequence} binding"
    fields = {"%W": target._w, "%K": keysym or sequence.strip("<>"), "%A": "{}"}
    script = re.sub(r"%[#a-zA-Z]", lambda m: fields.get(m.group(0), "0"), script)
    code = int(target.tk.call("catch", script))
    assert code in (0, 3), f"{sequence} binding failed (Tcl code {code})"  # TCL_OK / TCL_BREAK


def fresh_storage(workspace: Path) -> StorageService:
    """A brand-new StorageService on the workspace - reads only what really reached the disk."""
    return StorageService(AppConfig(workspace_dir=workspace, workspace_from_cli=True))


def quit_via_menu(app) -> None:
    """Clicks the menu bar's quit button - the path that flushes all pending saves before exiting."""
    from services.i18n_service import tr
    quit_btn = find_button(app.menu_frame, tr("menu.quit", "Beenden"))
    app._e2e_shutting_down = True  # tells the fixture's callback-error check that shutdown races are expected
    quit_btn.invoke()
    assert not is_alive(app)
    cancel_pending_afters(app)


def cancel_pending_afters(app) -> None:
    """Drops the after() callbacks a quit app left in its Tcl interpreter.

    In production the process ends right after quitting; in a test run the
    next app's event loop would otherwise fire them against dead widgets.
    """
    try:
        for after_id in app.tk.splitlist(app.tk.call("after", "info")):
            app.tk.call("after", "cancel", after_id)
    except Exception:
        pass


def is_alive(app) -> bool:
    try:
        return bool(app.winfo_exists())
    except Exception:
        return False


def click(widget) -> None:
    """Left-clicks a widget that reacts to <Button-1> bindings (CTk widgets bind on their inner canvas/label)."""
    target = getattr(widget, "_canvas", None) or widget
    # A freshly built widget has no native window until the idle queue ran;
    # pointer events sent to it before that are lost.
    target.update_idletasks()
    target.event_generate("<ButtonPress-1>", x=2, y=2)
    # Release too: a press without release leaves Tk's implicit pointer grab on
    # this window and the next click would be delivered here again.
    target.event_generate("<ButtonRelease-1>", x=2, y=2, state=0x100)
