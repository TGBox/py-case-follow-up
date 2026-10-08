"""flush_all must not hang when a background save never finishes.

Reproduces the exit hang seen on Windows: the garbage collector ran a
CTkFont.__del__ inside the debounced-save thread, Tcl waited for the main
thread, and the main thread waited in flush_all for that save - forever.
"""

import json
import threading
import time

import services.storage_service as storage_service
from services.storage_service import DebouncedSaver


def test_flush_all_returns_and_writes_when_background_save_is_stuck(tmp_path, monkeypatch):
    target = tmp_path / "profile.json"
    release = threading.Event()
    entered = threading.Event()
    real_save = storage_service.atomic_save_json

    def save(path, data, temp_tag=""):
        if threading.current_thread() is not threading.main_thread():
            entered.set()
            release.wait(10)  # stands in for the blocked Tcl call
            return
        real_save(path, data, temp_tag=temp_tag)

    monkeypatch.setattr(storage_service, "atomic_save_json", save)
    saver = DebouncedSaver()
    saver.save_debounced(target, {"v": 1}, delay_seconds=0)
    assert entered.wait(2), "background save did not start"

    start = time.monotonic()
    saver.flush_all(timeout=0.3)
    elapsed = time.monotonic() - start
    release.set()

    assert elapsed < 2, f"flush_all blocked for {elapsed:.1f}s"
    assert json.loads(target.read_text(encoding="utf-8")) == {"v": 1}
    assert not list(tmp_path.glob("*.tmp.json"))


def test_flush_all_waits_for_a_normal_background_save(tmp_path):
    target = tmp_path / "cases.json"
    saver = DebouncedSaver()
    saver.save_debounced(target, [1, 2, 3], delay_seconds=0)
    saver.flush_all()
    assert json.loads(target.read_text(encoding="utf-8")) == [1, 2, 3]
