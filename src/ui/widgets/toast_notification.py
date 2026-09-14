import sys
import logging
import customtkinter as ctk
from collections.abc import Callable
from constants import TOAST_DURATION_DEFAULT_MS

logger = logging.getLogger("SupportCockpit")


class ToastNotification(ctk.CTkToplevel):
    """Non-intrusive toast notification: uses native Windows OS notifications when available, with CTk overlay fallback."""

    def __init__(self, parent, title: str, message: str, duration_ms: int = TOAST_DURATION_DEFAULT_MS, on_open: Callable[[], None] | None = None, launch_uri: str | None = None):
        super().__init__(parent)
        from services.i18n_service import tr
        self.title(tr("toast.reminder_title", "Erinnerung"))
        self.on_open = on_open
        self.launch_uri = launch_uri

        # The native decision comes first: building the card and then throwing
        # it away meant every toast constructed its widgets twice - two frames,
        # two buttons and four labels stacked in one window.
        top_app = parent.winfo_toplevel() if hasattr(parent, "winfo_toplevel") else parent
        os_popup_enabled = True
        if hasattr(top_app, "profile") and hasattr(top_app.profile, "reminder_settings"):
            os_popup_enabled = getattr(top_app.profile.reminder_settings, "os_popup_enabled", True)

        native_sent = False
        if sys.platform.startswith("win") and os_popup_enabled:
            native_sent = self._send_native(top_app, title, message)

        if native_sent:
            if on_open:
                # Consumed when the app is brought back - via the tray icon, or
                # by a click on the OS notification itself (see open_case_request).
                top_app._pending_notification_callback = on_open
            self.withdraw()
            return

        # 1. Transient link to parent so window stays above parent on Windows OS
        try:
            self.transient(parent)
        except Exception:
            pass

        self.overrideredirect(True)

        width = 420 if on_open else 360
        height = 84

        target_setting = "APP_SCREEN"
        if hasattr(top_app, "profile") and hasattr(top_app.profile, "ui_settings"):
            target_setting = getattr(top_app.profile.ui_settings, "popup_display_target", "APP_SCREEN")

        if target_setting == "APP_SCREEN":
            from utils.ui_utils import get_app_monitor_bounds
            bx, by, bw, bh = get_app_monitor_bounds(self)
            x = max(0, bx + bw - width - 20)
            y = max(0, by + bh - height - 60)
        else:
            screen_w = self.winfo_screenwidth()
            screen_h = self.winfo_screenheight()
            x = screen_w - width - 20
            y = screen_h - height - 60

        self.geometry(f"{width}x{height}+{x}+{y}")

        frame = ctk.CTkFrame(self, fg_color=("gray90", "gray20"), border_width=2, border_color="dodgerblue", corner_radius=8)
        frame.pack(fill="both", expand=True)

        if on_open:
            btn_open = ctk.CTkButton(
                frame,
                text=tr("common.open", "👁 Öffnen"),
                width=95,
                height=32,
                font=ctk.CTkFont(size=12, weight="bold"),
                fg_color="dodgerblue",
                hover_color="deepskyblue",
                command=self.handle_open,
            )
            btn_open.pack(side="right", padx=(6, 12), pady=12)

        content_frame = ctk.CTkFrame(frame, fg_color="transparent")
        content_frame.pack(side="left", fill="both", expand=True, padx=(12, 6), pady=8)

        lbl_title = ctk.CTkLabel(content_frame, text=title, font=ctk.CTkFont(size=13, weight="bold"), text_color="dodgerblue", anchor="w")
        lbl_title.pack(anchor="w", pady=(0, 2))

        lbl_msg = ctk.CTkLabel(content_frame, text=message, font=ctk.CTkFont(size=11), text_color=("gray10", "white"), anchor="w")
        lbl_msg.pack(anchor="w", pady=(0, 2))

        if on_open:
            try:
                self.configure(cursor="hand2")
            except Exception:
                pass

        # 2. Lift and force topmost Z-order above maximized parent windows
        try:
            self.update_idletasks()
            self.lift()
            self.attributes("-topmost", True)
        except Exception:
            pass

        self.after(duration_ms, self.safe_destroy)

        # 3. Bind click handler recursively to all child widgets (including _label and _canvas)
        def click_handler(e):
            return self.handle_open() if on_open else self.safe_destroy()

        self._bind_click_recursive(frame, click_handler)

    def _send_native(self, top_app, title: str, message: str) -> bool:
        """Shows the OS notification. Returns False so the card is used instead.

        The launch URI is what makes the OS notification clickable at all: without
        it Windows shows the toast and a click does nothing. Clicking it starts
        the app with that URI, and the already-running instance picks the case up
        (see services/instance_service.py).
        """
        launch_uri = self.launch_uri or getattr(top_app, "pending_launch_uri", None)

        tray_svc = getattr(top_app, "tray_service", None)
        if tray_svc is not None:
            try:
                return bool(tray_svc.notify(title, message, launch=launch_uri))
            except TypeError:
                # Older tray service without launch support.
                return bool(tray_svc.notify(title, message))
            except Exception as err:
                logger.warning(f"Could not send native tray notification: {err}")
                return False

        try:
            from winotify import Notification  # type: ignore
            toast = Notification(
                app_id="Support-Cockpit",
                title=title,
                msg=message,
                duration="short",
                **({"launch": launch_uri} if launch_uri else {}),
            )
            toast.show()
            return True
        except Exception as err:
            logger.warning(f"Could not send native winotify notification: {err}")
            return False

    def _bind_click_recursive(self, widget, handler):
        try:
            widget.bind("<Button-1>", handler)
        except Exception:
            pass
        if hasattr(widget, "_label") and widget._label:
            try:
                widget._label.bind("<Button-1>", handler)
            except Exception:
                pass
        if hasattr(widget, "_canvas") and widget._canvas:
            try:
                widget._canvas.bind("<Button-1>", handler)
            except Exception:
                pass
        if hasattr(widget, "winfo_children"):
            for child in widget.winfo_children():
                self._bind_click_recursive(child, handler)

    def handle_open(self, event=None):
        cb = self.on_open
        self.on_open = None
        try:
            if hasattr(self, "master") and self.master:
                top = self.master.winfo_toplevel()
                if hasattr(top, "bring_to_foreground"):
                    # bring_to_foreground is a custom method only the real
                    # app-root (SupportCockpitApp) defines; winfo_toplevel()
                    # is typed generically as Tk | Toplevel, which doesn't
                    # declare it, hence the hasattr() guard above.
                    top.bring_to_foreground()  # pyright: ignore[reportAttributeAccessIssue]
                elif top:
                    if top.state() == "iconic" or not top.winfo_viewable():
                        top.deiconify()
                    top.lift()
                    top.focus_force()
        except Exception:
            pass
        self.safe_destroy()
        if cb:
            cb()

    def safe_destroy(self):
        try:
            self.destroy()
        except Exception:
            pass
