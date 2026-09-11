"""Small modal yes/no dialog, used before destructive actions.

The application deliberately does not use tkinter.messagebox anywhere, so this
keeps confirmations in the same CustomTkinter look as the rest of the UI.
"""

import customtkinter as ctk

from constants import DIALOG_DIMENSIONS
from ui.dialogs.base_dialog import BaseDialog


class ConfirmDialog(BaseDialog):
    """Modal confirmation with a confirm and a cancel button. Result is in .result."""

    def __init__(
        self,
        parent,
        message: str,
        title: str | None = None,
        confirm_text: str | None = None,
        cancel_text: str | None = None,
        danger: bool = True,
        show_cancel: bool = True,
    ):
        super().__init__(parent)
        from services.i18n_service import tr

        self.result = False

        w, h = DIALOG_DIMENSIONS["confirm"]
        self.setup_window(
            parent,
            title or tr("confirm.title", "Bitte bestätigen"),
            (w, h),
            resizable=False,
        )

        body = ctk.CTkFrame(self, fg_color="transparent")
        body.pack(fill="both", expand=True, padx=20, pady=(20, 10))

        ctk.CTkLabel(
            body,
            text=message,
            wraplength=w - 70,
            justify="left",
            anchor="w",
            font=ctk.CTkFont(size=13),
        ).pack(fill="both", expand=True)

        btn_row = ctk.CTkFrame(self, fg_color="transparent")
        btn_row.pack(fill="x", padx=20, pady=(0, 18))

        self.confirm_btn = ctk.CTkButton(
            btn_row,
            text=confirm_text or tr("common.ok", "OK"),
            width=150,
            fg_color="red" if danger else None,
            hover_color="darkred" if danger else None,
            command=self.on_confirm,
        )
        self.confirm_btn.pack(side="right")

        if show_cancel:
            ctk.CTkButton(
                btn_row,
                text=cancel_text or tr("common.cancel", "Abbrechen"),
                width=120,
                fg_color="gray40",
                hover_color="gray30",
                command=self.request_close,
            ).pack(side="right", padx=(0, 10))

        self.set_default_action(self.on_confirm)
        try:
            self.confirm_btn.focus_set()
        except Exception:
            pass

    def on_confirm(self) -> None:
        self.result = True
        self.close_dialog()


def _restore_parent_grab(parent, previous) -> None:
    """Gives the input grab back to whoever held it before the confirmation.

    A modal parent loses its own grab when the confirmation releases the grab on
    close - without this, the dialog underneath would silently stop being modal.
    """
    if previous is None or previous == "":
        return
    try:
        previous.grab_set()
    except Exception:
        try:
            parent.grab_set()
        except Exception:
            pass


def ask_confirmation(
    parent,
    message: str,
    title: str | None = None,
    confirm_text: str | None = None,
    cancel_text: str | None = None,
    danger: bool = True,
) -> bool:
    """Shows a modal confirmation and returns True only if the user confirmed.

    Escape, the X button and Cancel all return False, so a mis-click never
    triggers the destructive action.
    """
    try:
        previous_grab = parent.grab_current()
    except Exception:
        previous_grab = None

    dialog = ConfirmDialog(
        parent,
        message,
        title=title,
        confirm_text=confirm_text,
        cancel_text=cancel_text,
        danger=danger,
    )
    try:
        parent.wait_window(dialog)
    except Exception:
        # No running event loop (headless context): treat as "not confirmed".
        return bool(getattr(dialog, "result", False))
    finally:
        _restore_parent_grab(parent, previous_grab)
    return bool(dialog.result)


def show_notice(parent, message: str, title: str | None = None) -> None:
    """Shows a modal message with a single OK button.

    Used where an action is deliberately blocked, so the button does not simply
    appear broken to the user.
    """
    from services.i18n_service import tr
    try:
        previous_grab = parent.grab_current()
    except Exception:
        previous_grab = None

    dialog = ConfirmDialog(
        parent,
        message,
        title=title or tr("common.info", "Information"),
        confirm_text=tr("common.ok", "OK"),
        danger=False,
        show_cancel=False,
    )
    try:
        parent.wait_window(dialog)
    except Exception:
        pass
    finally:
        _restore_parent_grab(parent, previous_grab)
