"""Shared base class for the application's modal dialogs.

Before this class every dialog repeated the same window setup block (title,
geometry, minsize, centering, transient, grab_set) and none of them reacted to
Escape, offered an Enter shortcut, or warned about unsaved input. Putting that
behaviour here means a change to the dialog basics happens once instead of in
26 files.

Subclasses call setup_window(...) right after super().__init__(parent) and
otherwise build their widgets exactly as before.
"""

from collections.abc import Callable, Sequence

import customtkinter as ctk

# Widget classes whose content counts as user input for the unsaved-changes guard.
_TEXT_INPUT_CLASSES = {"CTkEntry", "CTkComboBox", "CTkOptionMenu", "CTkSwitch", "CTkCheckBox", "CTkSegmentedButton"}
_MULTILINE_CLASSES = {"CTkTextbox", "Text"}


class BaseDialog(ctk.CTkToplevel):
    """Common window setup, keyboard handling and close guard for dialogs."""

    # Subclasses can turn the Escape shortcut off (e.g. a dialog that must not
    # be dismissed by accident while a background job is running).
    escape_closes = True

    def setup_window(
        self,
        parent,
        title: str,
        size: Sequence[int],
        *,
        min_size: Sequence[int] | None = None,
        resizable: bool = True,
        modal: bool = True,
        center: bool = True,
    ) -> None:
        """Applies the standard window setup. Call once, directly after super().__init__()."""
        width, height = size[0], size[1]
        self.title(title)
        self.geometry(f"{width}x{height}")

        if resizable:
            if min_size:
                self.minsize(min_size[0], min_size[1])
        else:
            self.resizable(False, False)

        if center:
            from utils.ui_utils import center_window
            center_window(self, width, height)

        # transient() before grab_set(): a modal window without a parent
        # reference can end up behind the main window while still blocking input.
        if parent is not None:
            self.transient(parent)
        if modal:
            self.grab_set()

        self._install_dialog_bindings()

    def _install_dialog_bindings(self) -> None:
        if self.escape_closes:
            self.bind("<Escape>", self._on_escape)
        self.protocol("WM_DELETE_WINDOW", self.request_close)

    # --- Keyboard ---

    def _on_escape(self, event=None):
        self.request_close()
        return "break"

    def set_default_action(self, callback: Callable[[], None]) -> None:
        """Binds Enter to the dialog's primary action (Save / OK).

        Enter is ignored while a multi-line text field has focus, so typing a
        note or an e-mail body never triggers the button by accident.
        """
        self._default_action = callback
        self.bind("<Return>", self._on_default_action)
        self.bind("<KP_Enter>", self._on_default_action)

    def _on_default_action(self, event=None):
        try:
            focused = self.focus_get()
        except Exception:
            focused = None
        if focused is not None and focused.__class__.__name__ in _MULTILINE_CLASSES:
            return None

        callback = getattr(self, "_default_action", None)
        if callback is not None:
            callback()
        return "break"

    # --- Unsaved changes guard ---

    def enable_unsaved_guard(self) -> None:
        """Starts watching the dialog's input fields for changes.

        Call after the widgets are built and pre-filled. Closing the dialog then
        asks for confirmation instead of silently discarding what was typed.
        """
        self._unsaved_guard_enabled = True
        self.mark_clean()

    def mark_clean(self) -> None:
        """Takes a fresh reference snapshot, e.g. right after a successful save."""
        self._clean_snapshot = self._collect_input_snapshot()

    def _iter_input_widgets(self, parent=None):
        parent = parent if parent is not None else self
        try:
            children = parent.winfo_children()
        except Exception:
            return
        for child in children:
            yield child
            yield from self._iter_input_widgets(child)

    def _collect_input_snapshot(self) -> dict[str, str]:
        snapshot: dict[str, str] = {}
        for widget in self._iter_input_widgets():
            class_name = widget.__class__.__name__
            try:
                if class_name in _MULTILINE_CLASSES:
                    snapshot[str(widget)] = widget.get("1.0", "end-1c")
                elif class_name in _TEXT_INPUT_CLASSES:
                    snapshot[str(widget)] = str(widget.get())
            except Exception:
                continue
        return snapshot

    def is_dirty(self) -> bool:
        """Reports whether the user changed any input since the last clean snapshot."""
        if not getattr(self, "_unsaved_guard_enabled", False):
            return False

        baseline = getattr(self, "_clean_snapshot", None)
        if baseline is None:
            return False

        current = self._collect_input_snapshot()
        for key, value in current.items():
            if key in baseline:
                if value != baseline[key]:
                    return True
            elif str(value).strip():
                # A field that did not exist at snapshot time (e.g. a repeatable
                # block the user added) and already carries content.
                return True
        return False

    # --- Closing ---

    def request_close(self) -> None:
        """Entry point for Escape and the window's X button."""
        if self.is_dirty() and not self._confirm_discard():
            return
        self.close_dialog()

    def _confirm_discard(self) -> bool:
        from services.i18n_service import tr
        from ui.dialogs.confirm_dialog import ask_confirmation
        return ask_confirmation(
            self,
            tr("confirm.unsaved_message", "Es gibt ungespeicherte Eingaben. Wirklich schließen und verwerfen?"),
            title=tr("confirm.unsaved_title", "Ungespeicherte Eingaben"),
            confirm_text=tr("confirm.discard", "Verwerfen"),
            cancel_text=tr("confirm.keep_editing", "Weiter bearbeiten"),
        )

    def close_dialog(self) -> None:
        """Actually closes the dialog. Override for custom cleanup on close."""
        try:
            self.grab_release()
        except Exception:
            pass
        self.destroy()
