"""Shared base class for the application's modal dialogs.

Before this class every dialog repeated the same window setup block (title,
geometry, minsize, centering, transient, grab_set) and none of them reacted to
Escape, offered an Enter shortcut, or warned about unsaved input. Putting that
behaviour here means a change to the dialog basics happens once instead of in
26 files.

Subclasses call setup_window(...) right after super().__init__(parent) and
otherwise build their widgets exactly as before.
"""

import logging
from collections.abc import Callable, Iterator, Sequence
from typing import Any

import customtkinter as ctk

logger = logging.getLogger("SupportCockpit")

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
        title_factory: Callable[[], str] | None = None,
    ) -> None:
        """Applies the standard window setup. Call once, directly after super().__init__().

        title_factory re-evaluates the title expression on a language change; without
        it the window keeps the title it was opened with.
        """
        width, height = size[0], size[1]
        self._title_factory = title_factory
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
        self._register_language_listener()

    # --- Language switching ---

    def _register_language_listener(self) -> None:
        """Subscribes to language changes if the subclass can relabel itself.

        A dialog that defines refresh_ui_labels() is updated in place when the
        language changes while it is open; dialogs without that method are simply
        not subscribed. The listener is removed again in destroy(), so a closed
        dialog never keeps the service alive or fires on dead widgets.
        """
        if not callable(getattr(self, "refresh_ui_labels", None)):
            return
        try:
            from services.i18n_service import get_i18n
            self._language_listener = self._on_language_changed
            get_i18n().register_listener(self._language_listener)
        except Exception as err:
            logger.warning(f"Could not register language listener for {type(self).__name__}: {err}")

    def _unregister_language_listener(self) -> None:
        listener = getattr(self, "_language_listener", None)
        if listener is None:
            return
        self._language_listener = None
        try:
            from services.i18n_service import get_i18n
            get_i18n().unregister_listener(listener)
        except Exception as err:
            logger.warning(f"Could not unregister language listener for {type(self).__name__}: {err}")

    def _on_language_changed(self, lang_code: str) -> None:
        try:
            if not self.winfo_exists():
                self._unregister_language_listener()
                return
        except Exception:
            return
        try:
            self.refresh_ui_labels()
        except Exception as err:
            logger.warning(f"refresh_ui_labels failed for {type(self).__name__}: {err}")

    # --- Translatable widgets ---

    def register_i18n(self, widget, key: str, default: str = "", attr: str = "text", **fmt):
        """Remembers which translation key produced a widget's text.

        Wrapping a widget at creation time is what makes the generic
        refresh_ui_labels() below possible - the finished widget itself carries
        only the translated string, with no way back to its key.
        Returns the widget, so the call can wrap the constructor in place.
        """
        registry = getattr(self, "_i18n_widgets", None)
        if registry is None:
            registry = self._i18n_widgets = []
        # Rows in list views are destroyed and rebuilt constantly; drop dead
        # entries now and then so the registry cannot grow without bound.
        if len(registry) > 400:
            self._prune_i18n_widgets()
            registry = self._i18n_widgets
        registry.append((widget, attr, key, default, fmt))
        return widget

    def _prune_i18n_widgets(self) -> None:
        registry = getattr(self, "_i18n_widgets", None)
        if not registry:
            return
        alive = []
        for entry in registry:
            try:
                if entry[0].winfo_exists():
                    alive.append(entry)
            except Exception:
                continue
        self._i18n_widgets = alive

    def refresh_ui_labels(self) -> None:
        """Re-applies every registered translation in the current language.

        Subclasses with dynamically built content (list rows) override this,
        call super() and then re-render their lists.
        """
        from services.i18n_service import tr

        factory = getattr(self, "_title_factory", None)
        if factory is not None:
            try:
                self.title(factory())
            except Exception as err:
                logger.warning(f"Could not refresh title of {type(self).__name__}: {err}")

        registry = getattr(self, "_i18n_widgets", None)
        if not registry:
            return
        alive = []
        for entry in registry:
            widget, attr, key, default, fmt = entry
            try:
                if not widget.winfo_exists():
                    continue
                widget.configure(**{attr: tr(key, default, **fmt)})
                alive.append(entry)
            except Exception:
                continue
        self._i18n_widgets = alive

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

    def _iter_input_widgets(self, parent: Any = None) -> Iterator[Any]:
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

    def destroy(self) -> None:
        # Covers every close path, including dialogs that call destroy() directly
        # instead of going through close_dialog().
        self._unregister_language_listener()
        super().destroy()
