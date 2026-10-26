"""Reminder toasts, tray icon, notification-click hand-off (instance lock + launch URI), window restore, startup crash log."""
import importlib
import json
import os
import re
import sys
import threading
import time
from pathlib import Path
from typing import Any, cast
from unittest.mock import MagicMock

import customtkinter as ctk
import pytest

from services.instance_service import (
    HEARTBEAT_INTERVAL_SECONDS,
    LOCK_STALE_SECONDS,
    REQUEST_MAX_AGE_SECONDS,
    InstanceService,
    build_case_uri,
    parse_case_uri,
    should_register,
)
from services.tray_service import TrayService
from ui.app import SupportCockpitApp
from ui.widgets.toast_notification import ToastNotification

_REPO_ROOT = str(Path(__file__).resolve().parents[2])


def _main_module():
    if _REPO_ROOT not in sys.path:
        sys.path.insert(0, _REPO_ROOT)
    return importlib.import_module("main")


def _no_os_popups():
    return type("P", (), {"reminder_settings": type("R", (), {"os_popup_enabled": False})()})()


def _all_widgets(parent):
    for child in parent.winfo_children():
        yield child
        yield from _all_widgets(child)


# --- launch URI --------------------------------------------------------------

@pytest.mark.parametrize("case_id", [
    "T-2026-0042", "Fall 7/A", "Ü-1&2",
    "T-%41-1",  # unescaped, unquote() on the way back would turn %41 into "A"
    "T-1/",     # unescaped, the trailing separator would be stripped off
])
def test_case_id_survives_the_launch_uri_round_trip(case_id):
    """The URI travels through the Windows shell, so anything not quoted is lost."""
    assert parse_case_uri(build_case_uri(case_id)) == case_id


@pytest.mark.parametrize("raw, expected", [
    ("T-2026-0042", "T-2026-0042"),  # `--open-case T-1` from a shortcut or console
    ("supportcockpit://case/T-1/", "T-1"),
    ('"supportcockpit://case/T-1"', "T-1"),
    ("SupportCockpit://case/T-1", "T-1"),
    (None, None), ("", None), ("   ", None),
])
def test_parse_case_uri_accepts_shell_spellings(raw, expected):
    assert parse_case_uri(raw) == expected


@pytest.mark.parametrize("current, wanted, frozen, expected", [
    # A normal start must not touch the registry.
    ('"C:/App.exe" --open-case "%1"', '"C:/App.exe" --open-case "%1"', True, False),
    (None, '"C:/py.exe" main.py --open-case "%1"', False, True),
    # A run from source must not take the handler from the installed exe, but the built exe may take over.
    ('"C:/Program Files/Support-Cockpit.exe" --open-case "%1"', '"C:/py.exe" "C:/checkout/main.py" --open-case "%1"', False, False),
    ('"C:/py.exe" "C:/checkout/main.py" --open-case "%1"', '"C:/Program Files/Support-Cockpit.exe" --open-case "%1"', True, True),
])
def test_uri_handler_registration_policy(current, wanted, frozen, expected):
    assert should_register(current, wanted, frozen=frozen) is expected


# --- instance lock & hand-off ---------------------------------------------------

def test_the_lock_marks_an_instance_as_running_until_released(tmp_path):
    assert InstanceService(tmp_path).is_running() is False
    first = InstanceService(tmp_path)
    assert first.acquire() is True and first.owns_lock is True
    assert InstanceService(tmp_path).is_running() is True
    # Running two workspaces side by side is legitimate; the lock is per workspace.
    assert InstanceService(tmp_path / "other").is_running() is False

    first.release()
    assert InstanceService(tmp_path).is_running() is False
    assert InstanceService(tmp_path).acquire() is True


def test_a_lock_left_behind_by_a_crash_ages_out(tmp_path):
    """Otherwise a single crash would make every later click open a new window."""
    service = InstanceService(tmp_path)
    service.acquire()
    stale = time.time() - LOCK_STALE_SECONDS - 5
    os.utime(service.lock_path, (stale, stale))
    assert InstanceService(tmp_path).is_running() is False


def test_only_the_lock_owner_answers_hand_offs_and_releases(tmp_path):
    """Two apps on one workspace would otherwise race for the request file, and the second would delete the first's lock."""
    first = InstanceService(tmp_path)
    first.acquire()
    second = InstanceService(tmp_path)
    assert second.acquire() is False and not second.owns_lock
    second.handoff_or_claim(None)
    assert not second.owns_lock
    second.release()
    assert first.is_running() is True


def test_the_case_is_handed_over_exactly_once(tmp_path):
    service = InstanceService(tmp_path)
    assert service.write_open_case_request("T-1") is True
    assert service.consume_open_case_request() == "T-1"
    assert service.consume_open_case_request() is None, "case would reopen on every poll"


def test_outdated_or_damaged_requests_are_dropped(tmp_path):
    """A request written during shutdown must not hijack the next start; a broken one must not be retried forever."""
    service = InstanceService(tmp_path)
    service.write_open_case_request("T-1")
    payload = json.loads(service.request_path.read_text(encoding="utf-8"))
    payload["ts"] = time.time() - REQUEST_MAX_AGE_SECONDS - 10
    service.request_path.write_text(json.dumps(payload), encoding="utf-8")
    assert service.consume_open_case_request() is None
    assert not service.request_path.exists()

    service.request_path.write_text("{kein json", encoding="utf-8")
    assert service.consume_open_case_request() is None
    assert not service.request_path.exists()


def test_a_second_process_hands_the_case_over_instead_of_starting(tmp_path):
    running = InstanceService(tmp_path)
    running.acquire()
    assert InstanceService(tmp_path).handoff_or_claim(None) is False, "a plain start never hands anything over"
    assert InstanceService(tmp_path).handoff_or_claim("T-1") is True
    assert running.consume_open_case_request() == "T-1"


def test_a_cold_start_with_a_case_starts_normally(tmp_path):
    service = InstanceService(tmp_path)
    assert service.handoff_or_claim("T-1") is False
    assert service.is_running() is True
    assert service.consume_open_case_request() is None


def test_an_unwritable_workspace_starts_the_app_instead_of_swallowing_the_click(tmp_path, monkeypatch):
    """A click that opens nothing at all is the worse failure."""
    InstanceService(tmp_path).acquire()
    second = InstanceService(tmp_path)
    monkeypatch.setattr(second, "write_open_case_request", lambda case_id: False)
    assert second.handoff_or_claim("T-1") is False


# --- the app end of the chain -----------------------------------------------------

class _CockpitStub:
    def __init__(self):
        self.selected = []

    def on_select_case_from_list(self, case):
        self.selected.append(case)


class _CaseStub:
    def __init__(self, case_id, followup_at=None, title=""):
        self.case_id = case_id
        self.workflow_status = type("W", (), {"followup_at": followup_at, "is_completed": False})()
        self.classification = type("C", (), {"title": title})()


class AppStub(ctk.CTk):
    """The real methods under test, on a root without the full app's services."""

    find_case_by_id: Any = SupportCockpitApp.find_case_by_id
    request_open_case: Any = SupportCockpitApp.request_open_case
    _poll_open_case_request: Any = SupportCockpitApp._poll_open_case_request
    switch_to_cockpit_view_for_case: Any = SupportCockpitApp.switch_to_cockpit_view_for_case
    check_due_followups: Any = SupportCockpitApp.check_due_followups
    _check_mobile_ntfy_reminders: Any = SupportCockpitApp._check_mobile_ntfy_reminders
    is_on_call_active: Any = SupportCockpitApp.is_on_call_active
    _is_cockpit_active = lambda self: True  # noqa: E731
    _open_case_timer_id: str | None = None

    def __init__(self, cases):
        super().__init__()
        self.withdraw()
        self.cases = cases
        self.cockpit_view = _CockpitStub()
        self.active_case = None
        self.foregrounded = 0
        self.profile = _no_os_popups()

    def bring_to_foreground(self):
        self.foregrounded += 1

    def selected_ids(self):
        return [c.case_id for c in self.cockpit_view.selected]

    def poll_once(self):
        self._poll_open_case_request()
        if self._open_case_timer_id is not None:
            self.after_cancel(self._open_case_timer_id)


@pytest.fixture
def app():
    instance = AppStub([_CaseStub("T-1"), _CaseStub("T-2")])
    yield instance
    try:
        instance.destroy()
    except Exception:
        pass


def test_opening_a_case_brings_the_window_forward_and_selects_it(app):
    """Also clears the parked tray callback, otherwise the tray icon later replays the toast and jumps elsewhere."""
    app._pending_notification_callback = lambda: None
    assert app.request_open_case("T-2") is True
    assert app.foregrounded == 1
    assert app.active_case.case_id == "T-2"
    assert app.selected_ids() == ["T-2"]
    assert app._pending_notification_callback is None


def test_an_unknown_case_still_brings_the_window_forward(app):
    """The user clicked something; showing the app beats doing nothing visible."""
    assert app.request_open_case("T-999") is False
    assert app.foregrounded == 1
    assert app.selected_ids() == []


def test_the_poll_opens_a_handed_over_case_and_keeps_polling(app, tmp_path):
    app.poll_once()  # harmless without an instance service (tests, embedding)
    assert app.selected_ids() == []

    service = InstanceService(tmp_path)
    service.acquire()
    app.instance_service = service
    InstanceService(tmp_path).write_open_case_request("T-2")
    app._poll_open_case_request()

    assert app.selected_ids() == ["T-2"]
    assert app.foregrounded == 1
    # It keeps polling, otherwise only the first click of a session works.
    assert getattr(app, "_open_case_timer_id", None) is not None
    app.after_cancel(app._open_case_timer_id)


def test_the_poll_keeps_the_instance_lock_from_going_stale(app, tmp_path):
    """A long-running app whose lock ages out starts answering clicks with a second window."""
    service = InstanceService(tmp_path)
    service.acquire()
    app.instance_service = service
    stale = time.time() - LOCK_STALE_SECONDS - 5
    os.utime(service.lock_path, (stale, stale))
    assert service.is_running() is False

    app.poll_once()
    assert service.is_running() is True, "lock is never refreshed"

    # ... but not on every poll (75 writes per minute).
    written_at = service.lock_path.stat().st_mtime_ns
    app.poll_once()
    assert service.lock_path.stat().st_mtime_ns == written_at

    app._last_heartbeat_at -= HEARTBEAT_INTERVAL_SECONDS + 1
    os.utime(service.lock_path, (stale, stale))
    app.poll_once()
    assert service.is_running() is True, "no refresh after the interval"


def test_a_second_app_takes_over_once_the_first_one_is_closed(app, tmp_path):
    """Otherwise the window left open answers no click until restart."""
    first = InstanceService(tmp_path)
    first.acquire()
    second = InstanceService(tmp_path)
    second.acquire()
    app.instance_service = second

    InstanceService(tmp_path).write_open_case_request("T-2")
    app.poll_once()
    assert app.selected_ids() == [], "second instance pre-empts the first"

    first.release()
    app.poll_once()
    assert second.owns_lock is True
    assert app.selected_ids() == ["T-2"]


def test_the_app_attaches_a_launch_uri_to_the_due_reminder(app, monkeypatch):
    """The URI has to name the very case the message is about."""
    recorded = {}
    monkeypatch.setattr("ui.app.ToastNotification", lambda parent, **kwargs: recorded.update(kwargs))
    app.get_all_active_cases_for_reminder = lambda: [_CaseStub("T-2", followup_at="2020-01-01 08:00", title="Druckerproblem")]
    app.bell_btn = type("B", (), {"configure": lambda self, **k: None})()
    app.tray_service = type("T", (), {"update_badge": lambda self, n: None})()

    app.check_due_followups()
    app.after_cancel(app._followup_timer_id)

    assert recorded.get("launch_uri") == "supportcockpit://case/T-2"
    assert "T-2" in recorded.get("message", "")


# --- toast: native dispatch -----------------------------------------------------------

class DummyIcon:
    """TrayService.notify recognises this class by name (see src) and records instead of showing."""

    def __init__(self):
        self.last_notification: dict[str, Any] | None = None

    def notify(self, message, title=None):
        self.last_notification = {"title": title, "message": message}


def test_tray_service_notify_delegates_to_the_icon():
    service = TrayService()
    dummy = DummyIcon()
    service._icon = cast(Any, dummy)
    assert service.notify(title="Test Titel", message="Test Inhalt") is True
    assert dummy.last_notification == {"title": "Test Titel", "message": "Test Inhalt"}


class _BlockingIcon:
    """Stands in for pystray.Icon: run() blocks until stop(), like the real tray loop (the dummy backend raises at once)."""

    def __init__(self, **kwargs):
        self._stopped = threading.Event()

    def run(self):
        self._stopped.wait(5)

    def stop(self):
        self._stopped.set()


def test_tray_service_start_is_idempotent_and_stop_cleans_up(monkeypatch):
    """start() twice must not launch a second tray thread."""
    import services.tray_service as tray_module

    monkeypatch.setattr(tray_module.pystray, "Icon", _BlockingIcon)
    service = TrayService()
    service.start(on_restore=MagicMock(), on_quit=MagicMock())
    first_thread = service._thread
    assert first_thread is not None
    service.start(on_restore=MagicMock(), on_quit=MagicMock())
    assert service._thread is first_thread
    assert first_thread.is_alive()
    service.stop()
    assert service._icon is None and service._thread is None
    first_thread.join(1)
    assert not first_thread.is_alive(), "stop() must end the tray loop"


def test_tray_service_on_call_menu_and_tooltip():
    service = TrayService()
    is_active = [False]
    toggled = [0]

    def _toggle():
        toggled[0] += 1
        is_active[0] = not is_active[0]

    service._is_on_call_active = lambda: is_active[0]
    service._on_toggle_on_call = _toggle

    # Tooltip without on-call
    assert "[Notdienst]" not in service._get_tooltip()

    # Tooltip with on-call
    is_active[0] = True
    assert "[Notdienst]" in service._get_tooltip()

    # Menu creation includes on_call item
    menu = service._create_menu()
    items = list(cast(Any, menu).items)
    on_call_item = next((item for item in items if getattr(item, "text", "") == "Notdienst / Rufbereitschaft"), None)
    assert on_call_item is not None
    assert on_call_item.checked is True

    # Trigger toggle handler
    service._handle_toggle_on_call()
    assert toggled[0] == 1
    assert not is_active[0]


@pytest.mark.skipif(sys.platform != "win32", reason="native toasts only on Windows")
def test_toast_notification_dispatches_native_when_win(root):
    """On Windows the OS shows the toast; the card is not built at all (it used to be built and thrown away)."""
    root.tray_service = TrayService()
    dummy = DummyIcon()
    root.tray_service._icon = cast(Any, dummy)
    opened = []
    toast = ToastNotification(root, title="🔔 Wiedervorlage fällig", message="Fall T-2026-001 ist bereit.",
                              on_open=lambda: opened.append(True))

    assert dummy.last_notification == {"title": "🔔 Wiedervorlage fällig",
                                       "message": "Fall T-2026-001 ist bereit."}
    assert toast.winfo_children() == []
    callback = root._pending_notification_callback
    callback()
    assert opened == [True]


class _TrayStub:
    def __init__(self):
        self.calls = []

    def notify(self, title, message, launch=None):
        self.calls.append((title, message, launch))
        return True


class _OldTrayStub:
    def __init__(self):
        self.calls = []

    def notify(self, title, message):
        self.calls.append((title, message))
        return True


@pytest.mark.parametrize("tray_cls, launch_uri, expected_call", [
    # Without the URI Windows shows the toast and clicking it does nothing at all.
    (_TrayStub, "supportcockpit://case/T-2", ("T", "M", "supportcockpit://case/T-2")),
    # An older tray service must not turn into a swallowed notification.
    (_OldTrayStub, None, ("T", "M")),
])
def test_native_notification_passes_the_launch_uri_when_supported(app, tray_cls, launch_uri, expected_call):
    """_send_native is called directly: faking sys.platform steers CustomTkinter into Windows-only ctypes calls."""
    toast = ToastNotification(app, title="T", message="M", duration_ms=1000, on_open=lambda: None, launch_uri=launch_uri)
    app.tray_service = tray_cls()
    assert toast._send_native(app, "T", "M") is True
    assert app.tray_service.calls == [expected_call]
    toast.destroy()


def test_a_broken_tray_service_is_reported_instead_of_being_called_twice(app):
    """A TypeError raised *inside* notify() must not be mistaken for the old signature."""
    calls = []

    class _BrokenTrayStub:
        def notify(self, title, message, launch=None):
            calls.append((title, message, launch))
            raise TypeError("etwas in notify() ist kaputt")

    toast = ToastNotification(app, title="T", message="M", duration_ms=1000, launch_uri="supportcockpit://case/T-2")
    app.tray_service = _BrokenTrayStub()
    assert toast._send_native(app, "T", "M") is False
    assert len(calls) == 1
    toast.destroy()


# --- toast: in-app card ------------------------------------------------------------

def test_the_toast_card_is_built_once_and_clicking_it_opens_the_case(app):
    """The card used to be built, thrown away for the native toast and built again (two buttons, doubled labels)."""
    toast = ToastNotification(app, title="🔔 Wiedervorlage", message="[T-1] Druckerproblem", duration_ms=1000,
                              on_open=lambda: app.request_open_case("T-1"))
    app.update()

    widgets = list(_all_widgets(toast))
    buttons = [w for w in widgets if isinstance(w, ctk.CTkButton)]
    assert len(buttons) == 1
    assert "Öffnen" in buttons[0].cget("text")
    assert buttons[0].cget("width") >= 90, "open button must be fully visible"
    assert sorted(w.cget("text") for w in widgets if isinstance(w, ctk.CTkLabel)) == ["[T-1] Druckerproblem", "🔔 Wiedervorlage"]

    toast.handle_open()
    assert app.selected_ids() == ["T-1"]
    assert app.foregrounded >= 1


def test_a_toast_without_action_is_a_plain_card(root):
    toast = ToastNotification(root, title="Status", message="In-App Nachricht")
    toast.update_idletasks()
    assert toast.winfo_exists()
    assert not any(isinstance(w, ctk.CTkButton) for w in _all_widgets(toast))
    toast.safe_destroy()


# --- restoring the window from the tray ----------------------------------------------

class WindowStub:
    """Records window-manager calls; Tk's deiconify drops "zoomed" on Windows, which Linux cannot reproduce."""

    _remember_window_state: Any = SupportCockpitApp._remember_window_state
    _apply_remembered_window_state: Any = SupportCockpitApp._apply_remembered_window_state
    bring_to_foreground: Any = SupportCockpitApp.bring_to_foreground
    _hide_until_drawn: Any = SupportCockpitApp._hide_until_drawn
    _reveal_after_restore: Any = SupportCockpitApp._reveal_after_restore

    def __init__(self, state="zoomed", geometry="1200x800+40+30", viewable=True):
        self.tk = object()
        self._state = state
        self._geometry = geometry
        self._viewable = viewable
        self._x, self._y = 40, 30
        self.calls: list[tuple] = []
        self._restore_state = "zoomed"
        self._restore_geometry = None
        self._restore_fullscreen = False
        self._is_fullscreen = False

    def state(self, new=None):
        if new is None:
            return self._state
        self.calls.append(("state", new))
        self._state = new

    def geometry(self, new=None):
        if new is None:
            return self._geometry
        self.calls.append(("geometry", new))
        self._geometry = new

    def winfo_viewable(self):
        return self._viewable

    def winfo_x(self):
        return self._x

    def winfo_y(self):
        return self._y

    def deiconify(self):
        self.calls.append(("deiconify",))
        self._viewable = True
        self._state = "normal"

    def withdraw(self):
        self._viewable = False
        self._state = "withdrawn"

    def attributes(self, *args):
        self.calls.append(("attributes", *args))

    def lift(self):
        pass

    def focus_force(self):
        pass

    def _update_fullscreen_button(self):
        pass

    def after(self, _ms, fn):
        fn()

    def after_idle(self, fn):
        self.calls.append(("after_idle",))
        fn()

    def hide_and_restore(self):
        self._remember_window_state()
        self.withdraw()
        self.calls.clear()
        self.bring_to_foreground()


@pytest.mark.parametrize("state, geometry, fullscreen, expected_call", [
    ("zoomed", "1200x800+40+30", False, ("state", "zoomed")),
    ("normal", "1111x777+120+80", False, ("geometry", "1111x777+120+80")),
    ("zoomed", "1200x800+40+30", True, ("attributes", "-fullscreen", True)),
])
def test_window_comes_back_from_the_tray_as_it_was(state, geometry, fullscreen, expected_call):
    """Regression: a maximized app reappeared after a notification click as a small default window."""
    win = WindowStub(state=state, geometry=geometry)
    win._is_fullscreen = fullscreen
    win.hide_and_restore()
    assert expected_call in win.calls
    if not fullscreen:
        assert (win._state, win._geometry) == (state, geometry)


def test_restore_stays_transparent_until_drawn():
    """Re-maximizing redraws every widget; the window stays transparent until Tk is idle so the user never sees it."""
    win = WindowStub(state="zoomed")
    win.hide_and_restore()
    alpha = [i for i, c in enumerate(win.calls) if c[:2] == ("attributes", "-alpha")]
    assert win.calls[alpha[0]] == ("attributes", "-alpha", 0.0)
    assert alpha[0] < win.calls.index(("deiconify",))
    assert ("after_idle",) in win.calls
    assert win.calls[alpha[-1]] == ("attributes", "-alpha", 1.0)


def test_visible_window_is_left_alone():
    """Bringing an already visible window forward must not re-maximize it or make it transparent."""
    win = WindowStub(state="normal", geometry="900x600+10+10")
    win._restore_state = "zoomed"
    win.bring_to_foreground()
    assert not any(c[0] in ("deiconify", "state", "geometry") or c[:2] == ("attributes", "-alpha") for c in win.calls)


@pytest.mark.parametrize("hidden_state, x, geometry", [
    ("iconic", 10, "160x30+-32000+-32000"),
    ("withdrawn", 10, "160x30+-32000+-32000"),
    # A minimizing window briefly reports Windows' -32000 parking spot while still "normal".
    ("normal", -32000, "900x600+-32000+-32000"),
])
def test_hidden_or_parked_window_does_not_overwrite_the_recorded_state(hidden_state, x, geometry):
    win = WindowStub(state="normal", geometry="900x600+10+10")
    win._remember_window_state()
    win._state, win._x, win._y, win._geometry = hidden_state, x, x, geometry
    win._remember_window_state()
    assert (win._restore_state, win._restore_geometry) == ("normal", "900x600+10+10")


# --- startup crash logging -------------------------------------------------------------

@pytest.mark.parametrize("subdir", ["", "ablage"])
def test_a_crash_while_building_the_window_lands_in_the_workspace_crash_log(tmp_path, monkeypatch, subdir):
    """In the packaged exe stdout is None, so without the log a startup crash looks like 'the app just does not start'."""
    main_mod = _main_module()
    workspace = tmp_path / subdir
    workspace.mkdir(exist_ok=True)
    monkeypatch.setattr(sys, "argv", ["main.py", "--workspace", str(workspace)])
    monkeypatch.setattr(main_mod, "_crash_log_dir_override", None)  # main() sets it globally

    def _boom(*args, **kwargs):
        raise RuntimeError("Fensteraufbau fehlgeschlagen (Testfall)")

    monkeypatch.setattr("ui.app.SupportCockpitApp", _boom)
    with pytest.raises(SystemExit) as exited:
        main_mod.main()

    assert exited.value.code == 1
    log = workspace / "logs" / "tkinter_error.log"
    assert log.exists(), "no crash log - the crash would leave no trace"
    text = log.read_text(encoding="utf-8")
    assert "Fensteraufbau fehlgeschlagen (Testfall)" in text and "RuntimeError" in text


def test_tk_exception_reporter_accepts_hook_and_method_signatures(tmp_path, monkeypatch):
    """Regression: Tk calls report_callback_exception with self, sys.excepthook without it."""
    main_mod = _main_module()
    monkeypatch.setattr(main_mod, "_crash_log_dir_override", None)
    monkeypatch.chdir(tmp_path)  # default crash-log dir of a source run is the working directory
    try:
        raise ValueError("Test error for exception handler")
    except ValueError as e:
        main_mod._report_tkinter_exception(type(e), e, e.__traceback__)
        main_mod._report_tkinter_exception(object(), type(e), e, e.__traceback__)
    log = (tmp_path / "logs" / "tkinter_error.log").read_text(encoding="utf-8")
    assert log.count("Test error for exception handler") >= 2


# --- widget regressions from the same bug-fix session ------------------------------------

def test_case_list_card_shows_score_first_in_its_top_row(root):
    from enums import Actor, UrgencyLevel
    from models.case import Case, CaseCustomer, Classification, WorkflowStatus
    from ui.widgets.case_list_widget import CaseListWidget

    widget = CaseListWidget(root, on_case_selected=lambda c: None, on_search_changed=lambda s: None)
    widget.set_cases([Case(
        case_id="TEST-001",
        customer=CaseCustomer(customer_id="C01", practice_name="Test Practice"),
        classification=Classification(title="Test", calculated_score=85.0, urgency_level=UrgencyLevel.RED),
        workflow_status=WorkflowStatus(current_actor=Actor.SUPPORT),
    )])
    (card,) = widget.scroll_frame.winfo_children()
    top_row = card.winfo_children()[0].winfo_children()
    assert len(top_row) == 3
    assert "Pkt.: 85" in top_row[0].cget("text")


def test_textbox_field_uses_the_profile_height(root):
    """Regression: looking up the custom height on a UserProfile raised AttributeError."""
    from models.profile import UserProfile
    from models.schema import SchemaField
    from ui.widgets.dynamic_form_field_renderers import FieldRendererMixin

    class Renderer(FieldRendererMixin):
        def __init__(self, profile):
            self.profile = profile
            self.storage_service = None

    profile = UserProfile()
    profile.ui_settings.custom_textbox_heights["test_field"] = 120
    target = {}
    Renderer(profile)._render_textbox_field(
        ctk.CTkFrame(root), SchemaField(field_id="test_field", field_type="textbox", label="Test Textbox"), "value", target)
    ftype, textbox = target["test_field"]
    assert ftype == "textbox"
    assert textbox.cget("height") == 120


def test_scrollable_frame_callbacks_tolerate_missing_event_args(root):
    """Regression: Tcl invoked the <Configure> callbacks with no arguments and they raised TypeError."""
    from utils.ui_utils import patch_ctk_scrollable_frame

    patch_ctk_scrollable_frame()
    frame = ctk.CTkScrollableFrame(root)
    frame.pack()
    root.update()

    for widget in (frame, frame._parent_canvas):
        match = re.search(r"\[([^\s]+)", widget.bind("<Configure>"))
        assert match is not None
        root.tk.call(match.group(1))
    frame._fit_frame_dimensions_to_canvas()
    frame._mouse_wheel_all(None)
    frame._keyboard_shift_press_all()
    frame._keyboard_shift_release_all()


def test_tooltip_dismiss_all_hides_every_active_tooltip():
    from ui.widgets.ctk_tooltip import CTkTooltip

    tips = [MagicMock(), MagicMock()]
    CTkTooltip._active_tooltips.clear()
    CTkTooltip._active_tooltips.update(tips)
    CTkTooltip.dismiss_all()
    for tip in tips:
        tip.cancel_timer.assert_called_once()
        tip.hide_tooltip.assert_called_once()
