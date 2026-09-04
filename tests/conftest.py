import os
import sys
from pathlib import Path
import pytest

# Ensure src directory is in sys.path for test discovery
src_dir = str(Path(__file__).parent.parent / "src")
if src_dir not in sys.path:
    sys.path.insert(0, src_dir)

# Ensure Tcl/Tk libraries can always be located by Tkinter on Windows
tcl_candidate = Path(sys.base_prefix) / "tcl"
if (tcl_candidate / "tcl8.6").exists() and "TCL_LIBRARY" not in os.environ:
    os.environ["TCL_LIBRARY"] = (tcl_candidate / "tcl8.6").as_posix()
if (tcl_candidate / "tk8.6").exists() and "TK_LIBRARY" not in os.environ:
    os.environ["TK_LIBRARY"] = (tcl_candidate / "tk8.6").as_posix()

# Prevent Windows Tkinter file locking / interpreter cleanup race conditions across tests
try:
    import _tkinter
    import gc
    import time

    if not getattr(_tkinter, "_is_resilient_patched", False):
        _orig_create = getattr(_tkinter, "create", None)
        if callable(_orig_create):
            _active_create = _orig_create
            def _resilient_create(*args, **kwargs):
                for attempt in range(4):
                    try:
                        return _active_create(*args, **kwargs)
                    except _tkinter.TclError:
                        if attempt == 3:
                            raise
                        gc.collect()
                        time.sleep(0.05 * (attempt + 1))
            setattr(_tkinter, "create", _resilient_create)  # type: ignore[assignment]
            setattr(_tkinter, "_is_resilient_patched", True)
except (ImportError, AttributeError):
    pass

# Suppress native Windows desktop notifications during tests
try:
    import winotify
    setattr(winotify.Notification, "show", lambda self, *args, **kwargs: None)
except (ImportError, AttributeError):
    pass

try:
    import pystray
    if hasattr(pystray, "Icon"):
        setattr(pystray.Icon, "notify", lambda self, *args, **kwargs: None)
except (ImportError, AttributeError):
    pass

# Suppress windows popping up, flickering and stealing focus during tests
try:
    import tkinter as tk
    import customtkinter as ctk

    # Disable CustomTkinter titlebar color manipulation which un-withdraws windows after 5ms
    setattr(ctk.CTk, "_deactivate_windows_window_header_manipulation", True)
    setattr(ctk.CTkToplevel, "_deactivate_windows_window_header_manipulation", True)

    _orig_wm_state = tk.Wm.wm_state
    _orig_wm_withdraw = tk.Wm.wm_withdraw

    def _headless_wm_state(self, newstate=None):
        if newstate is not None:
            self._simulated_state = str(newstate)
            try:
                _orig_wm_withdraw(self)
            except Exception:
                pass
            return ""
        return getattr(self, "_simulated_state", "withdrawn")

    def _headless_wm_deiconify(self):
        self._simulated_state = "normal"
        try:
            _orig_wm_withdraw(self)
        except Exception:
            pass
        return ""

    def _headless_wm_withdraw(self):
        self._simulated_state = "withdrawn"
        try:
            _orig_wm_withdraw(self)
        except Exception:
            pass
        return ""

    def _headless_wm_iconify(self):
        self._simulated_state = "iconic"
        try:
            _orig_wm_withdraw(self)
        except Exception:
            pass
        return ""

    setattr(tk.Wm, "wm_state", _headless_wm_state)
    setattr(tk.Wm, "state", _headless_wm_state)
    setattr(tk.Wm, "wm_deiconify", _headless_wm_deiconify)
    setattr(tk.Wm, "deiconify", _headless_wm_deiconify)
    setattr(tk.Wm, "wm_withdraw", _headless_wm_withdraw)
    setattr(tk.Wm, "withdraw", _headless_wm_withdraw)
    setattr(tk.Wm, "wm_iconify", _headless_wm_iconify)
    setattr(tk.Wm, "iconify", _headless_wm_iconify)

    # Prevent focus stealing during test runs
    setattr(tk.Misc, "focus_force", lambda self: None)

    _orig_tk_init = tk.Tk.__init__
    def _headless_tk_init(self, *args, **kwargs):
        _orig_tk_init(self, *args, **kwargs)
        try:
            _orig_wm_withdraw(self)
        except Exception:
            pass
        self._simulated_state = "withdrawn"
    setattr(tk.Tk, "__init__", _headless_tk_init)

    _orig_toplevel_init = tk.Toplevel.__init__
    def _headless_toplevel_init(self, *args, **kwargs):
        _orig_toplevel_init(self, *args, **kwargs)
        try:
            _orig_wm_withdraw(self)
        except Exception:
            pass
        self._simulated_state = "withdrawn"
    setattr(tk.Toplevel, "__init__", _headless_toplevel_init)

except (ImportError, AttributeError):
    pass


@pytest.fixture(autouse=True)
def isolate_global_supportcockpit_config(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    """Ensures test runs never overwrite the user's real APPDATA user_config.json."""
    fake_config_dir = tmp_path / "global_config_mock"
    fake_config_dir.mkdir(parents=True, exist_ok=True)
    monkeypatch.setenv("SUPPORTCOCKPIT_CONFIG_DIR", str(fake_config_dir))


@pytest.fixture(autouse=True)
def prevent_external_launch(monkeypatch: pytest.MonkeyPatch):
    """Prevents tests from launching external email/calendar applications on the user's OS."""
    if hasattr(os, "startfile"):
        monkeypatch.setattr(os, "startfile", lambda *args, **kwargs: None)
    import webbrowser
    monkeypatch.setattr(webbrowser, "open", lambda *args, **kwargs: True)
