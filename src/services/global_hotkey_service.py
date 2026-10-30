"""System-wide hotkey (Windows) that works while the window sits in the tray.

A background thread owns the hotkey and its message loop. It never touches Tk:
it only sets a flag, and the app polls that flag from its own event loop.
"""

import ctypes
import logging
import re
import sys
import threading
from ctypes import wintypes

logger = logging.getLogger("SupportCockpit")

MOD_ALT = 0x0001
MOD_CONTROL = 0x0002
MOD_SHIFT = 0x0004
MOD_WIN = 0x0008
MOD_NOREPEAT = 0x4000
WM_HOTKEY = 0x0312
WM_QUIT = 0x0012
_HOTKEY_ID = 0x5C01
_START_TIMEOUT_SECONDS = 2.0
_STOP_TIMEOUT_SECONDS = 1.0
_VK_F1 = 0x70
_FUNCTION_KEY = re.compile(r"^f(\d{1,2})$")

_MODIFIERS = {
    "ctrl": MOD_CONTROL,
    "strg": MOD_CONTROL,
    "control": MOD_CONTROL,
    "alt": MOD_ALT,
    "shift": MOD_SHIFT,
    "win": MOD_WIN,
}


def parse_hotkey(text: str) -> tuple[int, int] | None:
    """(modifier flags, virtual-key code) for "Ctrl+Alt+N", or None if unusable.

    At least one modifier is required, so a plain letter can never be
    swallowed system-wide.
    """
    parts = [part.strip().lower() for part in (text or "").split("+") if part.strip()]
    if len(parts) < 2:
        return None
    modifiers = 0
    for name in parts[:-1]:
        flag = _MODIFIERS.get(name)
        if flag is None:
            return None
        modifiers |= flag
    key = parts[-1]
    if len(key) == 1 and key.isascii() and key.isalnum():
        return modifiers, ord(key.upper())
    match = _FUNCTION_KEY.match(key)
    if match and 1 <= int(match.group(1)) <= 12:
        return modifiers, _VK_F1 + int(match.group(1)) - 1
    return None


class GlobalHotkeyService:
    def __init__(self, hotkey: str) -> None:
        self.hotkey = hotkey
        self._pressed = threading.Event()
        self._registered = False
        self._thread: threading.Thread | None = None
        self._thread_id = 0

    def start(self) -> bool:
        """Registers the hotkey. False when unsupported, malformed or taken by another program."""
        if not sys.platform.startswith("win"):
            return False
        parsed = parse_hotkey(self.hotkey)
        if parsed is None:
            logger.warning("Global hotkey %r is not a valid combination.", self.hotkey)
            return False
        ready = threading.Event()
        self._thread = threading.Thread(
            target=self._run, args=(parsed[0] | MOD_NOREPEAT, parsed[1], ready), daemon=True, name="GlobalHotkey"
        )
        self._thread.start()
        ready.wait(_START_TIMEOUT_SECONDS)
        return self._registered

    def consume(self) -> bool:
        """True once per key press since the last call."""
        if self._pressed.is_set():
            self._pressed.clear()
            return True
        return False

    def stop(self) -> None:
        thread, self._thread = self._thread, None
        if thread is None or not thread.is_alive() or not self._thread_id:
            return
        try:
            ctypes.windll.user32.PostThreadMessageW(self._thread_id, WM_QUIT, 0, 0)
        except Exception as err:
            logger.debug("Could not stop the hotkey thread: %s", err)
        thread.join(_STOP_TIMEOUT_SECONDS)

    def _run(self, modifiers: int, key: int, ready: threading.Event) -> None:
        user32 = ctypes.windll.user32
        try:
            self._thread_id = ctypes.windll.kernel32.GetCurrentThreadId()
            self._registered = bool(user32.RegisterHotKey(None, _HOTKEY_ID, modifiers, key))
        except Exception as err:
            logger.warning("Could not register the global hotkey: %s", err)
        finally:
            ready.set()
        if not self._registered:
            logger.warning("Global hotkey %s is already used by another program.", self.hotkey)
            return
        try:
            msg = wintypes.MSG()
            while user32.GetMessageW(ctypes.byref(msg), None, 0, 0) > 0:
                if msg.message == WM_HOTKEY:
                    self._pressed.set()
        finally:
            user32.UnregisterHotKey(None, _HOTKEY_ID)
