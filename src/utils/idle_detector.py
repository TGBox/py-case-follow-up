import ctypes
from ctypes import Structure, c_uint, sizeof, byref
import logging
import sys

logger = logging.getLogger("SupportCockpit")

# Win32 desktop access constant
DESKTOP_SWITCHDESKTOP = 0x0100


class LASTINPUTINFO(Structure):
    _fields_ = [
        ("cbSize", c_uint),
        ("dwTime", c_uint),
    ]


class IdleDetector:
    """Detects system idle time and workstation lock status on Windows with test mock support."""

    _mock_idle_seconds: float | None = None
    _mock_locked: bool | None = None

    @classmethod
    def set_mock_state(cls, idle_seconds: float | None = None, is_locked: bool | None = None) -> None:
        """Sets simulated idle seconds and locked state for unit tests."""
        cls._mock_idle_seconds = idle_seconds
        cls._mock_locked = is_locked

    @classmethod
    def reset_mock(cls) -> None:
        """Clears test mocks."""
        cls._mock_idle_seconds = None
        cls._mock_locked = None

    @classmethod
    def get_idle_seconds(cls) -> float:
        """Returns elapsed seconds since last keyboard or mouse input."""
        if cls._mock_idle_seconds is not None:
            return max(0.0, float(cls._mock_idle_seconds))

        if sys.platform != "win32":
            return 0.0

        try:
            lii = LASTINPUTINFO()
            lii.cbSize = sizeof(LASTINPUTINFO)
            user32 = ctypes.windll.user32
            kernel32 = ctypes.windll.kernel32

            if user32.GetLastInputInfo(byref(lii)):
                current_tick = kernel32.GetTickCount()
                elapsed_ms = current_tick - lii.dwTime
                # Handle 32-bit tick wrap-around gracefully
                if elapsed_ms < 0:
                    elapsed_ms += 0x100000000
                return max(0.0, float(elapsed_ms) / 1000.0)
        except Exception as e:
            logger.debug(f"Could not retrieve GetLastInputInfo: {e}")

        return 0.0

    @classmethod
    def is_workstation_locked(cls) -> bool:
        """Checks if the Windows desktop is currently locked (Win + L or screensaver)."""
        if cls._mock_locked is not None:
            return cls._mock_locked

        if sys.platform != "win32":
            return False

        try:
            user32 = ctypes.windll.user32
            # Attempt to open the input desktop. When the workstation is locked,
            # OpenInputDesktop fails and returns NULL (0).
            h_desktop = user32.OpenInputDesktop(0, False, DESKTOP_SWITCHDESKTOP)
            if h_desktop == 0:
                return True
            user32.CloseDesktop(h_desktop)
            return False
        except Exception as e:
            logger.debug(f"Could not inspect workstation lock status: {e}")
            return False

    @classmethod
    def is_user_idle(cls, idle_threshold_seconds: float) -> bool:
        """Returns True if the workstation is locked OR idle time exceeds threshold."""
        if cls.is_workstation_locked():
            return True
        return cls.get_idle_seconds() >= max(0.0, idle_threshold_seconds)
