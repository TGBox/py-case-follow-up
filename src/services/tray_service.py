"""System Tray service for minimize-to-tray with notification badge counter."""

import threading
import logging
from typing import Callable

from PIL import Image, ImageDraw, ImageFont

import pystray

logger = logging.getLogger("SupportCockpit")

# Icon dimensions
_ICON_SIZE = 64
_BADGE_RADIUS = 12


def _create_tray_icon_image(badge_count: int = 0) -> Image.Image:
    """Generate a tray icon image with an optional red notification badge.

    The base icon is a medical-cross style icon matching the app's 🩺 theme.
    When badge_count > 0, a red circle with the count is drawn in the top-right corner.
    """
    img = Image.new("RGBA", (_ICON_SIZE, _ICON_SIZE), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)

    # Base icon: rounded teal/green square with a white cross
    bg_color = (38, 130, 130, 255)  # Teal
    draw.rounded_rectangle([4, 4, 60, 60], radius=12, fill=bg_color)

    # White cross in the center
    cross_color = (255, 255, 255, 255)
    draw.rectangle([26, 14, 38, 50], fill=cross_color)  # vertical bar
    draw.rectangle([14, 26, 50, 38], fill=cross_color)  # horizontal bar

    # Badge overlay
    if badge_count > 0:
        badge_x = _ICON_SIZE - _BADGE_RADIUS - 2
        badge_y = _BADGE_RADIUS + 2
        draw.ellipse(
            [badge_x - _BADGE_RADIUS, badge_y - _BADGE_RADIUS,
             badge_x + _BADGE_RADIUS, badge_y + _BADGE_RADIUS],
            fill=(220, 38, 38, 255),  # Red
        )
        badge_text = str(badge_count) if badge_count <= 99 else "99+"
        try:
            font = ImageFont.truetype("arial.ttf", 13 if len(badge_text) <= 2 else 10)
        except OSError:
            font = ImageFont.load_default()
        bbox = draw.textbbox((0, 0), badge_text, font=font)
        tw = bbox[2] - bbox[0]
        th = bbox[3] - bbox[1]
        draw.text(
            (badge_x - tw // 2, badge_y - th // 2 - 1),
            badge_text,
            fill=(255, 255, 255, 255),
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
            pystray.MenuItem("Öffnen", self._handle_restore, default=True),
            pystray.Menu.SEPARATOR,
            pystray.MenuItem("Beenden", self._handle_quit),
        )

        image = _create_tray_icon_image(self._badge_count)
        self._icon = pystray.Icon(
            name="SupportCockpit",
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
            return f"Support-Cockpit — {self._badge_count} fällige Wiedervorlage(n)"
        return "Support-Cockpit"

    def _handle_restore(self, icon: pystray.Icon | None = None, item: pystray.MenuItem | None = None) -> None:
        if self._on_restore:
            self._on_restore()

    def _handle_quit(self, icon: pystray.Icon | None = None, item: pystray.MenuItem | None = None) -> None:
        if self._on_quit:
            self._on_quit()
