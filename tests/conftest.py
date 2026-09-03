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
        if _orig_create is not None:
            def _resilient_create(*args, **kwargs):
                for attempt in range(4):
                    try:
                        return _orig_create(*args, **kwargs)
                    except _tkinter.TclError:
                        if attempt == 3:
                            raise
                        gc.collect()
                        time.sleep(0.05 * (attempt + 1))
            setattr(_tkinter, "create", _resilient_create)  # type: ignore[assignment]
            setattr(_tkinter, "_is_resilient_patched", True)
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
