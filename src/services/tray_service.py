"""System Tray service for minimize-to-tray with notification badge counter."""

from collections.abc import Callable
import logging
import sys
import threading

from PIL import Image, ImageDraw, ImageFont  # type: ignore
import pystray  # type: ignore

from constants import (
    APP_ID_NOTIFICATION,
    APP_NAME,
    NOTIFICATION_DURATION_SHORT,
    TRAY_BADGE_COLOR,
    TRAY_BADGE_FONT_NAME,
    TRAY_BADGE_FONT_SIZE_LG,
    TRAY_BADGE_FONT_SIZE_SM,
    TRAY_BADGE_MAX_COUNT,
    TRAY_BADGE_OFFSET,
    TRAY_BADGE_OVERFLOW_TEXT,
    TRAY_BADGE_RADIUS,
    TRAY_BASE_RADIUS,
    TRAY_BASE_RECT,
    TRAY_BG_COLOR,
    TRAY_CROSS_COLOR,
    TRAY_CROSS_HBAR,
    TRAY_CROSS_VBAR,
    TRAY_ICON_SIZE,
    TRAY_IMAGE_MODE,
    TRAY_TRANSPARENT_PIXEL,
)
from services.i18n_service import tr

logger = logging.getLogger("SupportCockpit")


def _create_tray_icon_image(badge_count: int = 0) -> Image.Image:  # pyright: ignore[reportInvalidTypeForm]
    # The `# type: ignore` on the `from PIL import Image` line above (needed
    # because pystray/PIL ship incomplete type info here) makes pyright treat
    # the imported `Image` submodule itself as an unresolved variable rather
    # than a proper module/class when it's then used as `Image.Image` in a
    # type position - a stub-resolution quirk, not an actual type problem
    # (`Image.Image` is Pillow's standard, correct way to type an image).
    """Generate a tray icon image with an optional red notification badge.

    The base icon is a medical-cross style icon matching the app's 🩺 theme.
    When badge_count > 0, a red circle with the count is drawn in the top-right corner.
    """
    img = Image.new(TRAY_IMAGE_MODE, (TRAY_ICON_SIZE, TRAY_ICON_SIZE), TRAY_TRANSPARENT_PIXEL)
    draw = ImageDraw.Draw(img)

    # Base icon: rounded teal/green square with a white cross
    draw.rounded_rectangle(TRAY_BASE_RECT, radius=TRAY_BASE_RADIUS, fill=TRAY_BG_COLOR)

    # White cross in the center
    draw.rectangle(TRAY_CROSS_VBAR, fill=TRAY_CROSS_COLOR)  # vertical bar
    draw.rectangle(TRAY_CROSS_HBAR, fill=TRAY_CROSS_COLOR)  # horizontal bar

    # Badge overlay
    if badge_count > 0:
        badge_x = TRAY_ICON_SIZE - TRAY_BADGE_RADIUS - TRAY_BADGE_OFFSET
        badge_y = TRAY_BADGE_RADIUS + TRAY_BADGE_OFFSET
        draw.ellipse(
            [badge_x - TRAY_BADGE_RADIUS, badge_y - TRAY_BADGE_RADIUS,
             badge_x + TRAY_BADGE_RADIUS, badge_y + TRAY_BADGE_RADIUS],
            fill=TRAY_BADGE_COLOR,
        )
        badge_text = str(badge_count) if badge_count <= TRAY_BADGE_MAX_COUNT else TRAY_BADGE_OVERFLOW_TEXT
        try:
            font_size = TRAY_BADGE_FONT_SIZE_LG if len(badge_text) <= 2 else TRAY_BADGE_FONT_SIZE_SM
            font = ImageFont.truetype(TRAY_BADGE_FONT_NAME, font_size)
        except OSError:
            font = ImageFont.load_default()
        bbox = draw.textbbox((0, 0), badge_text, font=font)
        tw = bbox[2] - bbox[0]
        th = bbox[3] - bbox[1]
        draw.text(
            (badge_x - tw // 2, badge_y - th // 2 - 1),
            badge_text,
            fill=TRAY_CROSS_COLOR,
            font=font,
        )

    return img


class TrayService:
    """Manages the system tray icon lifecycle, badge updates, and user interactions."""

    def __init__(self) -> None:
        self._icon: pystray.Icon | None = None
        self._thread: threading.Thread | None = None
        self._on_restore: Callable[[], None] | None = None
        self._on_quit: Callable[[], None] | None = None
        self._badge_count: int = 0

    def start(self, on_restore: Callable[[], None], on_quit: Callable[[], None]) -> None:
        """Start the system tray icon in a background thread.

        Args:
            on_restore: Callback invoked when the user double-clicks the tray icon or clicks 'Öffnen'.
            on_quit: Callback invoked when the user clicks 'Beenden' in the tray context menu.
        """
        self._on_restore = on_restore
        self._on_quit = on_quit

        if self._thread and self._thread.is_alive():
            logger.debug("System tray icon thread is already running.")
            return

        menu = pystray.Menu(
            pystray.MenuItem(tr("tray.open", "Öffnen"), self._handle_restore, default=True),
            pystray.Menu.SEPARATOR,
            pystray.MenuItem(tr("tray.quit", "Beenden"), self._handle_quit),
        )

        image = _create_tray_icon_image(self._badge_count)
        self._icon = pystray.Icon(
            name=APP_NAME,
            icon=image,
            title=self._get_tooltip(),
            menu=menu,
        )

        self._thread = threading.Thread(target=self._icon.run, daemon=True)
        self._thread.start()
        logger.info("System tray icon started.")

    def update_badge(self, count: int) -> None:
        """Update the tray icon badge with the current notification count."""
        self._badge_count = count
        if self._icon:
            try:
                self._icon.icon = _create_tray_icon_image(count)
                self._icon.title = self._get_tooltip()
            except Exception:
                pass

    def notify(self, title: str, message: str, launch: str | None = None) -> bool:
        """Send a native Windows system notification via winotify or tray icon.

        Args:
            title: Notification title.
            message: Notification text content.
            launch: URI the OS opens when the notification is clicked. Windows
                shows a toast without it, but clicking that toast does nothing -
                so this is what makes the notification actionable at all. The
                pystray fallbacks below have no equivalent and ignore it.

        Returns:
            True if notification was sent, False otherwise.
        """
        if self._icon and type(self._icon).__name__ == "DummyIcon":
            try:
                notify_fn = getattr(self._icon, "notify", None)
                if callable(notify_fn):
                    notify_fn(message, title)
                    logger.info(f"Mock tray notification recorded: {title}")
                    return True
            except Exception:
                pass

        if sys.platform.startswith("win"):
            try:
                from winotify import Notification  # type: ignore
                toast = Notification(
                    app_id=APP_ID_NOTIFICATION,
                    title=title,
                    msg=message,
                    duration=NOTIFICATION_DURATION_SHORT,
                    **({"launch": launch} if launch else {}),
                )
                toast.show()
                logger.info(f"Native winotify toast sent: {title}")
                return True
            except Exception as e:
                logger.debug(f"winotify toast failed: {e}")

        if self._icon:
            notify_fn = getattr(self._icon, "notify", None)
            if callable(notify_fn):
                try:
                    # notify() exists on pystray's real platform-specific Icon
                    # backend (win32/appindicator/xorg) at runtime.
                    notify_fn(message, title)
                    logger.info(f"Native tray notification sent via icon: {title}")
                    return True
                except Exception as e:
                    logger.warning(f"Could not send native tray notification via icon: {e}")

        return False

    def stop(self) -> None:
        """Remove the tray icon and stop the background thread."""
        if self._icon:
            try:
                self._icon.stop()
            except Exception:
                pass
            self._icon = None
        self._thread = None
        logger.info("System tray icon stopped.")

    def _get_tooltip(self) -> str:
        if self._badge_count > 0:
            return tr("tray.tooltip_due", "Support-Cockpit — {count} fällige Wiedervorlage(n)", count=self._badge_count)
        return tr("tray.tooltip_default", "Support-Cockpit")

    def _handle_restore(self, icon: pystray.Icon | None = None, item: pystray.MenuItem | None = None) -> None:
        if self._on_restore:
            self._on_restore()

    def _handle_quit(self, icon: pystray.Icon | None = None, item: pystray.MenuItem | None = None) -> None:
        if self._on_quit:
            self._on_quit()

