import os
import sys
import traceback
import warnings
from typing import Any
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

    # Prevent CTkInputDialog from blocking on wait_window if get_input is unmocked in tests
    if hasattr(ctk, "CTkInputDialog"):
        def _nonblocking_get_input(self):
            if hasattr(self, "_user_input") and self._user_input is not None:
                return self._user_input
            try:
                self.destroy()
            except Exception:
                pass
            return getattr(self, "_test_input", "TestUser")
        setattr(ctk.CTkInputDialog, "get_input", _nonblocking_get_input)

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
    # In a source run the default workspace is Path.cwd() (= the repo with the
    # developer's real data/), so no test may run with the repo as cwd.
    monkeypatch.chdir(tmp_path)


@pytest.fixture(autouse=True)
def isolate_temp_dir(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    """Gives every test its own tempfile.gettempdir().

    Export, print and e-mail dialogs write fixed names (Fallbericht_<id>.html,
    Support_Entwurf.eml) into the system temp folder, and the demo seed hands
    every test the same case ids. Under pytest-xdist two workers would write
    the same file at once - on Windows that fails with a sharing violation.
    It also keeps the developer's real %TEMP% free of test leftovers.
    """
    import tempfile

    temp_dir = tmp_path / "system_temp"
    temp_dir.mkdir()
    monkeypatch.setattr(tempfile, "tempdir", str(temp_dir))


@pytest.fixture(autouse=True)
def prevent_external_launch(monkeypatch: pytest.MonkeyPatch):
    """Prevents tests from launching external email/calendar applications on the user's OS."""
    if hasattr(os, "startfile"):
        monkeypatch.setattr(os, "startfile", lambda *args, **kwargs: None)
    import webbrowser
    monkeypatch.setattr(webbrowser, "open", lambda *args, **kwargs: True)


@pytest.fixture(autouse=True)
def block_update_check_network(monkeypatch: pytest.MonkeyPatch):
    """No test may reach GitHub: the update check always reports 'no information'.

    Tests of the fetch itself import the real function at module level (before
    this patch applies) and mock urlopen instead.
    """
    from services import update_check_service
    monkeypatch.setattr(update_check_service, "fetch_latest_version", lambda *args, **kwargs: None)


@pytest.fixture(autouse=True)
def no_real_tray_icon(monkeypatch: pytest.MonkeyPatch):
    """No test creates a real Windows tray icon.

    Every SupportCockpitApp(config) used to start a pystray icon with its own
    Win32 message-loop thread, and app.destroy() never stops it - a parallel
    run showed eleven of them alive in one worker, each a real icon in the
    system tray. Tests of the tray itself drive TrayService with a dummy icon.
    """
    from services.tray_service import TrayService

    real_start = TrayService.start
    monkeypatch.setattr(TrayService, "start", lambda self, *args, **kwargs: None)
    monkeypatch.setattr(TrayService, "real_start", real_start, raising=False)


@pytest.fixture(autouse=True)
def block_real_network(monkeypatch: pytest.MonkeyPatch):
    """No test may reach the internet (weather, DING departures, Ollama, ntfy, wiki).

    Every UI test that built the end-of-day panel used to fire real HTTP
    requests from background threads - slow, dependent on the network, and
    the threads outlived the test. All services already fall back on a
    URLError, so they behave exactly as if offline. Tests that need a
    response mock urlopen themselves; their patch applies after this one.
    """
    import urllib.request
    from urllib.error import URLError

    from services import ntfy_service, update_check_service

    def offline(*args, **kwargs):
        raise URLError("network access is disabled in tests")

    monkeypatch.setattr(urllib.request, "urlopen", offline)
    monkeypatch.setattr(ntfy_service, "urlopen", offline)
    monkeypatch.setattr(update_check_service, "urlopen", offline)


@pytest.fixture(autouse=True)
def reset_default_locale():
    """Ensures each test starts and finishes with the default German locale."""
    from services.i18n_service import get_i18n
    get_i18n().current_language = "de"
    yield
    get_i18n().current_language = "de"


# --- Shared fixtures (use these instead of redefining per file) -------------

# after() loops CustomTkinter keeps alive on the root; they must survive the per-test cleanup.
_CTK_LOOP_CALLBACKS = ("check_dpi_scaling", "AppearanceModeTracker", "update_loop")
_CTK_ROOT_DEFAULT_GEOMETRY = "600x500"
# tkinter creates these on the root on first use; they must outlive a test.
_TK_LAZY_INTERNALS = frozenset({"_last_child_ids", "_tclCommands"})
_worker_root: list = []


def _alive_worker_root():
    """The one hidden CTk root of this pytest process (one per xdist worker), re-created if a test killed it."""
    if _worker_root and _worker_root[0].winfo_exists():
        return _worker_root[0]
    _worker_root.clear()
    app = ctk.CTk()
    app.withdraw()
    _worker_root.append(app)
    return app


def _cancel_test_afters(app) -> None:
    """Drops every pending after() a test left behind, except CustomTkinter's own tracker loops.

    With one interpreter per worker, a widget's 500 ms debounce or a dialog's
    watchdog would otherwise fire during the next test against destroyed
    widgets. Tk's after-command names carry the Python function name, which
    is how the tracker loops are told apart.
    """
    try:
        for after_id in app.tk.splitlist(app.tk.call("after", "info")):
            script = str(app.tk.call("after", "info", after_id))
            if any(name in script for name in _CTK_LOOP_CALLBACKS):
                continue
            app.tk.call("after", "cancel", after_id)
    except Exception:
        pass


def _purge_dead_ctk_callbacks(app, test_name: str) -> None:
    """Drops CustomTkinter tracker entries whose Tk widget no longer exists.

    ScalingTracker and AppearanceModeTracker keep a callback per widget and
    only forget it in the widget's Python destroy(). A widget whose Tk window
    died without that call stays registered, and the next set_widget_scaling()
    or appearance switch anywhere in the process raises
    "invalid command name". A fresh interpreter per test hid such leaks (the
    root's whole entry went with it); the shared root needs this sweep. The
    warning names the leaking test, because the same leak crashes the real
    app on a font zoom.
    """
    # Reached through the package, not the submodules: the local stub in
    # typings/customtkinter knows only the top-level names.
    scaling_tracker: Any = ctk.ScalingTracker
    appearance_tracker: Any = ctk.AppearanceModeTracker

    def is_dead(callback) -> bool:
        widget = getattr(callback, "__self__", None)
        if widget is None or not hasattr(widget, "winfo_exists"):
            return False
        try:
            return not widget.winfo_exists()
        except Exception:
            return True

    dead: list[str] = []
    callbacks = scaling_tracker.window_widgets_dict.get(app)
    if callbacks is not None:
        kept = []
        for cb in callbacks:
            if is_dead(cb):
                dead.append(str(getattr(cb.__self__, "_w", cb.__self__)))
            else:
                kept.append(cb)
        callbacks[:] = kept
    appearance_tracker.callback_list[:] = [cb for cb in appearance_tracker.callback_list if not is_dead(cb)]
    if dead:
        warnings.warn(
            f"{test_name} left {len(dead)} destroyed widget(s) registered in CustomTkinter's trackers: "
            + ", ".join(sorted(set(dead))[:5]),
            stacklevel=2,
        )


@pytest.fixture(scope="session", autouse=True)
def _destroy_worker_root_at_exit():
    yield
    if _worker_root:
        try:
            _worker_root[0].destroy()
        except Exception:
            pass


@pytest.fixture
def root(request: Any):
    """Headless CustomTkinter root, shared by every test of this worker and cleaned after each.

    Creating a CTk costs ~100 ms on Windows (a Tcl interpreter, Tk, the theme):
    one root per test was about a third of the UI suite's run time. The root
    is now created once per process (one per xdist worker); after each test its
    children, pending timers, geometry and error hook are reset so nothing
    carries over. Tests that need their own interpreter create ctk.CTk() themselves.
    """
    app = _alive_worker_root()
    attrs_before = dict(vars(app))
    yield app
    if not app.winfo_exists():
        return
    _cancel_test_afters(app)
    for child in list(app.winfo_children()):
        try:
            child.destroy()
        except Exception:
            # A destroy() that raises half-way leaves Tk widgets behind whose
            # Python side is already gone - the next test then sees them as
            # leaked. In the app the same exception would hit on closing a view.
            warnings.warn(
                f"{request.node.nodeid}: destroying {child} raised:\n{traceback.format_exc()}",
                stacklevel=2,
            )
    # Attributes a test hung on the root (root.tray_service, root.profile, its
    # own report_callback_exception) must not be visible to the next test.
    for name in list(vars(app)):
        if name not in attrs_before and name not in _TK_LAZY_INTERNALS:
            delattr(app, name)
    vars(app).update(attrs_before)
    _purge_dead_ctk_callbacks(app, request.node.nodeid)
    try:
        app.geometry(_CTK_ROOT_DEFAULT_GEOMETRY)
        app.withdraw()
    except Exception:
        pass


@pytest.fixture
def config(tmp_path: Path):
    from config import AppConfig
    return AppConfig(workspace_dir=tmp_path, username="test_agent")


@pytest.fixture
def storage(config):
    """Empty workspace in tmp_path."""
    from services.storage_service import StorageService
    return StorageService(config)


@pytest.fixture
def seeded_storage(storage):
    """Workspace with the demo seed (12 cases, customers, schemas, templates)."""
    from services.seed_service import SeedService
    SeedService(storage).run_seed(force=True)
    return storage
