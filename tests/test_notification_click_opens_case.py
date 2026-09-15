"""Clicking a reminder notification must bring the app forward and open that case.

Two routes lead here and both are covered:

  the app's own toast card - a CTkToplevel in the bottom-right corner, clicked
  inside the running process, and

  the native Windows toast - which cannot call back into the running process at
  all. Windows starts a second process with the toast's launch URI, so the
  chain under test is: launch URI -> second process -> hand-off file -> running
  app polls -> case opens.

The Windows-only links of that chain (winotify's launch activation and the
HKCU registry entry) cannot run on Linux/CI; what is asserted here is that the
app produces the URI, passes it on, and acts on it when it comes back.
"""

import time

import customtkinter as ctk
import pytest

from services.instance_service import (
    LOCK_STALE_SECONDS,
    REQUEST_MAX_AGE_SECONDS,
    InstanceService,
    build_case_uri,
    parse_case_uri,
)
from ui.widgets.toast_notification import ToastNotification


# --- launch URI ---

@pytest.mark.parametrize(
    "case_id",
    [
        "T-2026-0042",
        "Fall 7/A",
        "Ü-1&2",
        "T-1",
        "T-%41-1",   # unescaped, unquote() on the way back would turn %41 into "A"
        "T-1/",      # unescaped, the trailing separator would be stripped off
    ],
)
def test_case_id_survives_the_launch_uri_round_trip(case_id):
    """The URI travels through the Windows shell, so anything not quoted is lost."""
    assert parse_case_uri(build_case_uri(case_id)) == case_id


def test_a_bare_case_id_is_accepted_too():
    """`--open-case T-1` from a shortcut or the console must work like the URI."""
    assert parse_case_uri("T-2026-0042") == "T-2026-0042"


def test_uri_spellings_the_shell_produces():
    assert parse_case_uri("supportcockpit://case/T-1/") == "T-1"
    assert parse_case_uri('"supportcockpit://case/T-1"') == "T-1"
    assert parse_case_uri("SupportCockpit://case/T-1") == "T-1"


def test_nothing_to_open_stays_nothing():
    assert parse_case_uri(None) is None
    assert parse_case_uri("") is None
    assert parse_case_uri("   ") is None


# --- instance lock ---

def test_a_fresh_workspace_has_no_running_instance(tmp_path):
    assert InstanceService(tmp_path).is_running() is False


def test_the_lock_marks_an_instance_as_running_until_it_is_released(tmp_path):
    service = InstanceService(tmp_path)
    assert service.acquire() is True
    assert InstanceService(tmp_path).is_running() is True

    service.release()
    assert InstanceService(tmp_path).is_running() is False


def test_a_lock_left_behind_by_a_crash_ages_out(tmp_path):
    """Otherwise a single crash would make every later click open a new window."""
    service = InstanceService(tmp_path)
    service.acquire()
    stale = time.time() - LOCK_STALE_SECONDS - 5
    import os
    os.utime(service.lock_path, (stale, stale))

    assert InstanceService(tmp_path).is_running() is False


def test_two_workspaces_do_not_lock_each_other_out(tmp_path):
    """Running two workspaces side by side is legitimate; the lock is per workspace."""
    first = InstanceService(tmp_path / "a")
    first.acquire()
    assert InstanceService(tmp_path / "b").is_running() is False


# --- hand-off ---

def test_the_case_is_handed_over_exactly_once(tmp_path):
    service = InstanceService(tmp_path)
    assert service.write_open_case_request("T-1") is True
    assert service.consume_open_case_request() == "T-1"
    assert service.consume_open_case_request() is None, "Fall wuerde bei jedem Poll erneut geoeffnet"


def test_an_outdated_request_is_dropped_instead_of_opened(tmp_path):
    """A request written while the app was shutting down must not hijack the next start."""
    service = InstanceService(tmp_path)
    service.write_open_case_request("T-1")
    import json
    payload = json.loads(service.request_path.read_text(encoding="utf-8"))
    payload["ts"] = time.time() - REQUEST_MAX_AGE_SECONDS - 10
    service.request_path.write_text(json.dumps(payload), encoding="utf-8")

    assert service.consume_open_case_request() is None
    assert not service.request_path.exists(), "veralteter Request bleibt liegen und wird endlos neu gelesen"


def test_a_damaged_request_is_dropped_instead_of_retried_forever(tmp_path):
    service = InstanceService(tmp_path)
    service.request_path.write_text("{kein json", encoding="utf-8")
    assert service.consume_open_case_request() is None
    assert not service.request_path.exists()


# --- routing of a starting process ---

def test_a_second_process_hands_the_case_over_instead_of_starting(tmp_path):
    running = InstanceService(tmp_path)
    running.acquire()

    second = InstanceService(tmp_path)
    assert second.handoff_or_claim("T-1") is True, "zweiter Prozess wuerde ein weiteres Fenster oeffnen"
    assert running.consume_open_case_request() == "T-1"


def test_a_cold_start_with_a_case_starts_normally(tmp_path):
    service = InstanceService(tmp_path)
    assert service.handoff_or_claim("T-1") is False
    assert service.is_running() is True, "die gestartete Instanz haelt die Sperre nicht"
    assert service.consume_open_case_request() is None, "Fall wurde an niemanden uebergeben"


def test_a_normal_start_never_hands_anything_over(tmp_path):
    InstanceService(tmp_path).acquire()
    assert InstanceService(tmp_path).handoff_or_claim(None) is False


def test_only_one_instance_owns_the_hand_off(tmp_path):
    """Two apps on one workspace would otherwise race for the same request file."""
    first = InstanceService(tmp_path)
    assert first.acquire() is True
    assert first.owns_lock is True

    second = InstanceService(tmp_path)
    assert second.acquire() is False, "zweite Instanz reisst die Sperre an sich"
    assert second.owns_lock is False

    second.handoff_or_claim(None)
    assert second.owns_lock is False, "zweite Instanz beantwortet Uebergaben mit"


def test_the_lock_returns_to_a_fresh_start_after_the_holder_is_gone(tmp_path):
    first = InstanceService(tmp_path)
    first.acquire()
    first.release()
    assert InstanceService(tmp_path).acquire() is True


def test_releasing_a_lock_this_process_never_held_leaves_it_alone(tmp_path):
    """Sonst raeumt eine zweite Instanz beim Beenden die Sperre der ersten weg."""
    first = InstanceService(tmp_path)
    first.acquire()

    second = InstanceService(tmp_path)
    second.acquire()
    second.release()

    assert first.is_running() is True


# --- URI-Handler in der Registry ---

def test_an_unchanged_handler_is_not_rewritten():
    """Ein normaler Start soll die Registry gar nicht anfassen."""
    from services.instance_service import should_register

    assert should_register('"C:/App.exe" --open-case "%1"', '"C:/App.exe" --open-case "%1"', frozen=True) is False


def test_an_unregistered_handler_is_claimed_by_any_build():
    from services.instance_service import should_register

    assert should_register(None, '"C:/py.exe" main.py --open-case "%1"', frozen=False) is True


def test_a_run_from_source_does_not_take_the_handler_from_the_installed_exe():
    from services.instance_service import should_register

    installed = '"C:/Program Files/Support-Cockpit.exe" --open-case "%1"'
    from_source = '"C:/py.exe" "C:/checkout/main.py" --open-case "%1"'
    assert should_register(installed, from_source, frozen=False) is False
    assert should_register(from_source, installed, frozen=True) is True, "die gebaute Exe muss uebernehmen duerfen"


def test_an_unwritable_workspace_starts_the_app_instead_of_swallowing_the_click(tmp_path, monkeypatch):
    """A click that opens nothing at all is the worse failure."""
    running = InstanceService(tmp_path)
    running.acquire()

    second = InstanceService(tmp_path)
    monkeypatch.setattr(second, "write_open_case_request", lambda case_id: False)
    assert second.handoff_or_claim("T-1") is False


# --- the app end of the chain ---

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

    from ui.app import SupportCockpitApp
    find_case_by_id = SupportCockpitApp.find_case_by_id
    request_open_case = SupportCockpitApp.request_open_case
    _poll_open_case_request = SupportCockpitApp._poll_open_case_request
    switch_to_cockpit_view_for_case = SupportCockpitApp.switch_to_cockpit_view_for_case
    check_due_followups = SupportCockpitApp.check_due_followups
    _is_cockpit_active = lambda self: True  # noqa: E731

    def __init__(self, cases):
        super().__init__()
        self.withdraw()
        self.cases = cases
        self.cockpit_view = _CockpitStub()
        self.active_case = None
        self.foregrounded = 0
        self.profile = type(
            "P", (), {"reminder_settings": type("R", (), {"os_popup_enabled": False})()}
        )()

    def bring_to_foreground(self):
        self.foregrounded += 1


@pytest.fixture
def app():
    instance = AppStub([_CaseStub("T-1"), _CaseStub("T-2")])
    yield instance
    try:
        instance.destroy()
    except Exception:
        pass


def test_opening_a_case_brings_the_window_forward_and_selects_it(app):
    assert app.request_open_case("T-2") is True
    assert app.foregrounded == 1, "Anwendung kommt nicht in den Vordergrund"
    assert app.active_case.case_id == "T-2"
    assert [c.case_id for c in app.cockpit_view.selected] == ["T-2"]


def test_an_unknown_case_still_brings_the_window_forward(app):
    """The user clicked something; showing the app beats doing nothing visible."""
    assert app.request_open_case("T-999") is False
    assert app.foregrounded == 1
    assert app.cockpit_view.selected == []


def test_opening_a_case_clears_the_parked_tray_callback(app):
    """Otherwise the tray icon later replays the toast and jumps to another case."""
    app._pending_notification_callback = lambda: None
    app.request_open_case("T-1")
    assert app._pending_notification_callback is None


def test_the_poll_opens_a_handed_over_case(app, tmp_path):
    service = InstanceService(tmp_path)
    service.acquire()
    app.instance_service = service

    InstanceService(tmp_path).write_open_case_request("T-2")
    app._poll_open_case_request()

    assert [c.case_id for c in app.cockpit_view.selected] == ["T-2"]
    assert app.foregrounded == 1

    # And it keeps polling, otherwise only the first click of a session works.
    assert getattr(app, "_open_case_timer_id", None) is not None
    app.after_cancel(app._open_case_timer_id)


def test_the_poll_keeps_the_instance_lock_from_going_stale(app, tmp_path):
    """A long-running app whose lock ages out starts answering clicks with a second window."""
    import os

    from services.instance_service import HEARTBEAT_INTERVAL_SECONDS

    service = InstanceService(tmp_path)
    service.acquire()
    app.instance_service = service

    stale = time.time() - LOCK_STALE_SECONDS - 5
    os.utime(service.lock_path, (stale, stale))
    assert service.is_running() is False

    def poll_once():
        app._poll_open_case_request()
        app.after_cancel(app._open_case_timer_id)

    poll_once()
    assert service.is_running() is True, "die Sperre wird nie aufgefrischt"

    # ... aber nicht bei jedem Poll: das waere 75 Schreibzugriffe pro Minute.
    written_at = service.lock_path.stat().st_mtime_ns
    poll_once()
    assert service.lock_path.stat().st_mtime_ns == written_at, "Sperre wird bei jedem Poll geschrieben"

    # Nach Ablauf des Intervalls wieder - unabhaengig davon, wie oft gepollt wurde.
    app._last_heartbeat_at -= HEARTBEAT_INTERVAL_SECONDS + 1
    os.utime(service.lock_path, (stale, stale))
    poll_once()
    assert service.is_running() is True, "nach dem Intervall wird nicht mehr aufgefrischt"


def test_a_second_app_takes_over_once_the_first_one_is_closed(app, tmp_path):
    """Sonst beantwortet das offen gebliebene Fenster bis zum Neustart keinen Klick."""
    first = InstanceService(tmp_path)
    first.acquire()

    second = InstanceService(tmp_path)
    second.acquire()
    app.instance_service = second
    assert second.owns_lock is False

    InstanceService(tmp_path).write_open_case_request("T-2")
    app._poll_open_case_request()
    app.after_cancel(app._open_case_timer_id)
    assert app.cockpit_view.selected == [], "zweite Instanz greift der ersten vor"

    first.release()
    app._poll_open_case_request()
    app.after_cancel(app._open_case_timer_id)
    assert second.owns_lock is True, "Sperre wird nach dem Schliessen nicht uebernommen"
    assert [c.case_id for c in app.cockpit_view.selected] == ["T-2"]


def test_the_poll_is_harmless_without_an_instance_service(app):
    """Tests and any embedding of the app construct it without the hand-off files."""
    app._poll_open_case_request()
    assert app.cockpit_view.selected == []
    app.after_cancel(app._open_case_timer_id)


# --- the toast passes the launch URI on ---

class _TrayStub:
    def __init__(self):
        self.calls = []

    def notify(self, title, message, launch=None):
        self.calls.append((title, message, launch))
        return True


def test_the_native_notification_carries_the_launch_uri(app):
    """Without it Windows shows the toast and clicking it does nothing at all.

    _send_native is called directly rather than by faking sys.platform: the
    platform string also steers CustomTkinter into Windows-only ctypes calls
    during widget construction, which have nothing to do with this contract.
    """
    tray = _TrayStub()
    toast = ToastNotification(
        app,
        title="🔔 Wiedervorlage",
        message="[T-2] Druckerproblem",
        duration_ms=1000,
        on_open=lambda: None,
        launch_uri=build_case_uri("T-2"),
    )
    app.tray_service = tray

    assert toast._send_native(app, "🔔 Wiedervorlage", "[T-2] Druckerproblem") is True
    assert tray.calls == [("🔔 Wiedervorlage", "[T-2] Druckerproblem", "supportcockpit://case/T-2")]
    toast.destroy()


def test_a_tray_service_without_launch_support_still_notifies(app):
    """An older tray service must not turn into a swallowed notification."""
    class _OldTrayStub:
        def __init__(self):
            self.calls = []

        def notify(self, title, message):
            self.calls.append((title, message))
            return True

    tray = _OldTrayStub()
    toast = ToastNotification(app, title="T", message="M", duration_ms=1000)
    app.tray_service = tray

    assert toast._send_native(app, "T", "M") is True
    assert tray.calls == [("T", "M")]
    toast.destroy()


def test_a_broken_tray_service_is_reported_instead_of_being_called_twice(app):
    """Ein TypeError *aus* notify() heraus darf nicht als alte Signatur gelten."""
    calls: list[tuple] = []

    class _BrokenTrayStub:
        def notify(self, title, message, launch=None):
            calls.append((title, message, launch))
            raise TypeError("etwas in notify() ist kaputt")

    toast = ToastNotification(app, title="T", message="M", duration_ms=1000, launch_uri="supportcockpit://case/T-2")
    app.tray_service = _BrokenTrayStub()

    assert toast._send_native(app, "T", "M") is False
    assert len(calls) == 1, "notify() wurde nach dem Fehler ein zweites Mal aufgerufen"
    toast.destroy()


def test_the_app_attaches_a_launch_uri_to_the_due_reminder(app, monkeypatch):
    """The URI has to name the very case the message is about."""
    from ui.app import SupportCockpitApp

    due_case = _CaseStub("T-2", followup_at="2020-01-01 08:00", title="Druckerproblem")

    recorded = {}

    def _recorder(parent, **kwargs):
        recorded.update(kwargs)

    monkeypatch.setattr("ui.app.ToastNotification", _recorder)
    app.get_all_active_cases_for_reminder = lambda: [due_case]
    app.bell_btn = type("B", (), {"configure": lambda self, **k: None})()
    app.tray_service = type("T", (), {"update_badge": lambda self, n: None})()

    SupportCockpitApp.check_due_followups(app)
    app.after_cancel(app._followup_timer_id)

    assert recorded.get("launch_uri") == "supportcockpit://case/T-2"
    assert "T-2" in recorded.get("message", "")


def test_the_toast_card_builds_its_widgets_only_once(app):
    """The card used to be built, then thrown away for the native toast and built again."""
    toast = ToastNotification(
        app,
        title="🔔 Wiedervorlage",
        message="[T-2] Druckerproblem",
        duration_ms=1000,
        on_open=lambda: None,
    )
    app.update()

    widgets = []

    def walk(parent):
        for child in parent.winfo_children():
            widgets.append(child)
            walk(child)

    walk(toast)
    assert len([w for w in widgets if isinstance(w, ctk.CTkButton)]) == 1, "Oeffnen-Knopf doppelt"
    assert len([w for w in widgets if isinstance(w, ctk.CTkLabel)]) == 2, "Texte doppelt uebereinander"
    toast.destroy()


def test_clicking_the_toast_card_opens_the_case(app):
    toast = ToastNotification(
        app,
        title="🔔 Wiedervorlage",
        message="[T-1] Druckerproblem",
        duration_ms=1000,
        on_open=lambda: app.request_open_case("T-1"),
    )
    app.update()

    toast.handle_open()
    assert [c.case_id for c in app.cockpit_view.selected] == ["T-1"]
    assert app.foregrounded >= 1
