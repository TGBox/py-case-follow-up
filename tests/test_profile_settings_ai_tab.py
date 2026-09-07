"""Tests for src/ui/dialogs/profile_settings_ai_tab.py (AiSettingsTabMixin).

ProfileSettingsDialog.__init__() already calls setup_ai_tab() (which itself
calls scan_ollama_status() once), so every existing test that constructs
ProfileSettingsDialog already exercises the initial widget-construction path
- a coverage audit that only greps for the literal string
"profile_settings_ai_tab" misses that entirely. What no test exercises is
any of the tab's actual interactive behavior: provider switching, the
Modelfile-rules toggle, showing/hiding the Gemini key, selecting an Ollama
model, testing a Gemini key, or the Ollama server/model management actions.

Those actions spawn daemon threads that call the REAL AiService (real HTTP
requests to Ollama/Gemini) - unsuitable for a fast, deterministic test suite,
so every test here monkeypatches services.ai_service.AiService with a fake
that returns immediately, and pumps the Tk event loop briefly to let the
worker's self.after(0, ...) callback run (AiService is looked up fresh via a
local `from services.ai_service import AiService` on every call, so patching
the module attribute is enough to intercept it everywhere, including the
automatic scan_ollama_status() at dialog construction).

On real Python 3.14 / Windows runs (no app.mainloop() active - only
app.update()/update_idletasks() polling), a REAL background thread touching
Tk (self.winfo_exists(), self.ai_url_entry.get(), or self.after(...) itself)
raises "RuntimeError: main thread is not in main loop" and crashes the
worker before its self.after(0, done) callback is ever scheduled - so every
test further down here also monkeypatches threading.Thread with
_ImmediateThread, which runs worker() synchronously on the actual main
thread instead of a real OS thread. That keeps every Tk-touching call on
the real main thread (safe), while self.after(0, done) is still scheduled
through Tcl's normal event queue and only actually runs once the test pumps
the event loop - so the async hand-off behavior (and its ordering) is still
exercised, just without a real thread boundary.

Separately, winfo_ismapped() is not a reliable "is this frame currently
shown" check in this test setup: the root window is app.withdraw()-en and
no real mainloop()/screen-mapping cycle ever happens, so winfo_ismapped()
returns False even for widgets that are genuinely packed. _is_shown() below
checks winfo_manager() instead, which reflects whether a widget is
currently registered with a geometry manager (pack/grid/place) regardless
of whether the window is actually drawn on screen - exactly what
on_change_ai_provider()/scan_ollama_status() toggle via pack()/pack_forget().
"""

import threading
import time
from pathlib import Path
import customtkinter as ctk
import pytest

from config import AppConfig
from services.storage_service import StorageService
import services.ai_service as ai_service_module
from ui.dialogs.profile_settings_dialog import ProfileSettingsDialog


class _FakeAiService:
    """Stands in for AiService: same call surface, instant canned results."""

    # Class-level knobs the tests can adjust per-scenario.
    is_online = True
    installed_models = ["qwen3.5:9b", "llama3:8b"]
    running_models: list[str] = []
    gemini_ok = True
    gemini_msg = "Gemini Key gültig"
    start_ok = True
    start_msg = "Ollama Server gestartet"
    stop_msg = "Ollama Server beendet"
    preload_ok = True
    preload_msg = "Modell geladen"
    unload_ok = True
    unload_msg = "Modell entladen"
    create_pvs_ok = True
    create_pvs_msg = "pvs-support Modell erstellt"

    def __init__(self, provider="OLLAMA", ollama_url="", model_name="", gemini_api_key="", gemini_model="", enable_anonymization=True):
        self.provider = provider
        self.ollama_url = ollama_url
        self.model_name = model_name
        self.gemini_api_key = gemini_api_key
        self.gemini_model = gemini_model

    def check_ollama_status(self):
        return _FakeAiService.is_online, list(_FakeAiService.installed_models)

    def get_running_models(self):
        return list(_FakeAiService.running_models)

    def check_gemini_status(self, api_key=None, model=None):
        return _FakeAiService.gemini_ok, _FakeAiService.gemini_msg

    def start_ollama_server(self):
        return _FakeAiService.start_ok, _FakeAiService.start_msg

    def stop_ollama_server(self):
        return True, _FakeAiService.stop_msg

    def preload_model(self, model_name=None):
        return _FakeAiService.preload_ok, _FakeAiService.preload_msg

    def unload_model(self, model_name=None):
        return _FakeAiService.unload_ok, _FakeAiService.unload_msg

    def create_pvs_support_model(self, modelfile_path=None, base_model_override=None):
        return _FakeAiService.create_pvs_ok, _FakeAiService.create_pvs_msg


class _ImmediateThread:
    """Stand-in for threading.Thread: runs target() synchronously on the
    calling (main) thread instead of spawning a real OS thread.

    Every AiSettingsTabMixin action does `import threading;
    threading.Thread(target=worker, daemon=True).start()`. Because that
    import resolves to the same module object we patch here, replacing the
    `Thread` attribute on the `threading` module intercepts every one of
    those call sites. Running worker() synchronously keeps its Tk-touching
    calls (self.winfo_exists(), self.ai_url_entry.get(), self.after(...))
    on the real main thread - avoiding "RuntimeError: main thread is not in
    main loop" - while self.after(0, done) still goes through Tcl's normal
    event queue, so a test must still pump the event loop for `done()` to run.
    """

    def __init__(self, target=None, args=(), kwargs=None, daemon=None):
        self._target = target
        self._args = args
        self._kwargs = kwargs or {}

    def start(self):
        if self._target:
            self._target(*self._args, **self._kwargs)

    def join(self, timeout=None):
        pass

    def is_alive(self):
        return False


def _is_shown(widget) -> bool:
    """True if `widget` is currently registered with a geometry manager
    (pack/grid/place) - i.e. shown - regardless of whether the (withdrawn,
    mainloop-less) root window would ever report it as winfo_ismapped()."""
    return bool(widget.winfo_manager())


def _pump(app, predicate, timeout=3.0):
    """Repeatedly services the Tk event loop until predicate() is true or a
    timeout is hit - needed because the mixin's actions schedule their UI
    update via `self.after(0, ...)`, which only fires while the event loop
    is pumped."""
    deadline = time.time() + timeout
    while time.time() < deadline:
        app.update()
        if predicate():
            return True
        time.sleep(0.02)
    return predicate()


@pytest.fixture
def dialog(tmp_path: Path, monkeypatch):
    monkeypatch.setattr(ai_service_module, "AiService", _FakeAiService)
    monkeypatch.setattr(threading, "Thread", _ImmediateThread)
    _FakeAiService.is_online = True
    _FakeAiService.installed_models = ["qwen3.5:9b", "llama3:8b"]
    _FakeAiService.running_models = []

    config = AppConfig(workspace_dir=tmp_path)
    storage = StorageService(config)
    profile = storage.load_profile()

    app = ctk.CTk()
    app.withdraw()

    d = ProfileSettingsDialog(app, profile=profile, storage_service=storage, on_profile_updated=lambda: None)
    d.update_idletasks()
    _pump(app, lambda: d.ollama_status_lbl.cget("text") != "🔍 Prüfe Ollama-Status...")

    yield app, d

    try:
        d.destroy()
    except Exception:
        pass
    try:
        app.destroy()
    except Exception:
        pass


# ---------------------------------------------------------------------------
# Initial construction (values loaded from profile, provider-dependent visibility)
# ---------------------------------------------------------------------------


def test_setup_ai_tab_loads_saved_gemini_key_and_model(dialog):
    app, d = dialog
    d.profile.ai_settings.gemini_api_key = "AIzaSyTESTKEY"
    d.profile.ai_settings.gemini_model = "gemini-2.5-pro"

    # Re-run setup to reflect the profile change (mirrors what a fresh dialog would show).
    for w in d.tab_ai.winfo_children():
        w.destroy()
    d.setup_ai_tab()
    _pump(app, lambda: d.ollama_status_lbl.cget("text") != "🔍 Prüfe Ollama-Status...")

    assert d.gemini_key_entry.get() == "AIzaSyTESTKEY"
    assert d.gemini_model_combo.get() == "gemini-2.5-pro"


def test_setup_ai_tab_shows_ollama_card_by_default(dialog):
    app, d = dialog
    assert _is_shown(d.ollama_card)
    assert not _is_shown(d.gemini_card)


# ---------------------------------------------------------------------------
# Provider switching
# ---------------------------------------------------------------------------


def test_on_change_ai_provider_shows_gemini_card_and_hides_ollama(dialog):
    app, d = dialog
    d.on_change_ai_provider("GOOGLE GEMINI (Cloud)")
    assert _is_shown(d.gemini_card)
    assert not _is_shown(d.ollama_card)


def test_on_change_ai_provider_back_to_ollama_shows_ollama_card(dialog):
    app, d = dialog
    d.on_change_ai_provider("GOOGLE GEMINI (Cloud)")
    d.on_change_ai_provider("OLLAMA (Lokal)")
    assert _is_shown(d.ollama_card)
    assert not _is_shown(d.gemini_card)


# ---------------------------------------------------------------------------
# Show/hide Gemini key
# ---------------------------------------------------------------------------


def test_toggle_show_gemini_key_reveals_and_hides_again(dialog):
    app, d = dialog
    assert d.gemini_key_entry.cget("show") == "*"

    d.on_toggle_show_gemini_key()
    assert d.gemini_key_entry.cget("show") == ""
    assert d.btn_toggle_key_show.cget("text") == "🔒"

    d.on_toggle_show_gemini_key()
    assert d.gemini_key_entry.cget("show") == "*"
    assert d.btn_toggle_key_show.cget("text") == "👁"


# ---------------------------------------------------------------------------
# Modelfile system-rules toggle (pure text manipulation, no filesystem/network)
# ---------------------------------------------------------------------------


def test_toggle_gemini_modelfile_rules_appends_and_removes_marker_text(dialog, monkeypatch):
    app, d = dialog
    monkeypatch.setattr(d, "get_modelfile_prompt_text", lambda: "Du bist ein Support-Assistent.")

    d.ai_base_rules_txt.delete("1.0", "end")
    d.ai_base_rules_txt.insert("1.0", "Bestehende Basis-Regel.")

    d.gemini_modelfile_chk_var.set(True)
    d.on_toggle_gemini_modelfile_rules()

    text_with = d.ai_base_rules_txt.get("1.0", "end-1c")
    assert "Bestehende Basis-Regel." in text_with
    assert "Du bist ein Support-Assistent." in text_with
    assert "--- MODELFILE SYSTEM-REGELN ---" in text_with

    d.gemini_modelfile_chk_var.set(False)
    d.on_toggle_gemini_modelfile_rules()

    text_without = d.ai_base_rules_txt.get("1.0", "end-1c")
    assert "Du bist ein Support-Assistent." not in text_without
    assert "--- MODELFILE SYSTEM-REGELN ---" not in text_without
    assert "Bestehende Basis-Regel." in text_without


def test_toggle_gemini_modelfile_rules_does_nothing_when_modelfile_empty(dialog, monkeypatch):
    app, d = dialog
    monkeypatch.setattr(d, "get_modelfile_prompt_text", lambda: "")

    d.ai_base_rules_txt.delete("1.0", "end")
    d.ai_base_rules_txt.insert("1.0", "Unveränderter Text.")

    d.gemini_modelfile_chk_var.set(True)
    d.on_toggle_gemini_modelfile_rules()

    assert d.ai_base_rules_txt.get("1.0", "end-1c") == "Unveränderter Text."


def test_switching_to_ollama_strips_modelfile_rules_that_were_added_for_gemini(dialog, monkeypatch):
    app, d = dialog
    monkeypatch.setattr(d, "get_modelfile_prompt_text", lambda: "Systemregeln aus Modelfile.")

    d.ai_base_rules_txt.delete("1.0", "end")
    d.gemini_modelfile_chk_var.set(True)
    d.on_toggle_gemini_modelfile_rules()
    assert "Systemregeln aus Modelfile." in d.ai_base_rules_txt.get("1.0", "end-1c")

    d.on_change_ai_provider("OLLAMA (Lokal)")

    assert "Systemregeln aus Modelfile." not in d.ai_base_rules_txt.get("1.0", "end-1c")


# ---------------------------------------------------------------------------
# Ollama model selection (synchronous, no network)
# ---------------------------------------------------------------------------


def test_on_select_ai_model_updates_entry_profile_and_label(dialog):
    app, d = dialog
    d.on_select_ai_model("llama3:8b")

    assert d.ai_model_entry.get() == "llama3:8b"
    assert d.profile.ai_settings.model_name == "llama3:8b"
    assert "llama3:8b" in d.ollama_action_lbl.cget("text")


# ---------------------------------------------------------------------------
# Gemini key test
# ---------------------------------------------------------------------------


def test_test_gemini_key_shows_warning_when_key_empty(dialog):
    app, d = dialog
    d.gemini_key_entry.delete(0, "end")
    d.on_test_gemini_key()
    assert "API Key" in d.gemini_status_lbl.cget("text")


def test_test_gemini_key_shows_success_for_valid_key(dialog):
    app, d = dialog
    _FakeAiService.gemini_ok = True
    _FakeAiService.gemini_msg = "Key ist gültig"

    d.gemini_key_entry.delete(0, "end")
    d.gemini_key_entry.insert(0, "AIzaSyVALIDKEY")
    d.on_test_gemini_key()

    _pump(app, lambda: "Key ist gültig" in d.gemini_status_lbl.cget("text"))
    assert "✅" in d.gemini_status_lbl.cget("text")


def test_test_gemini_key_shows_failure_for_invalid_key(dialog):
    app, d = dialog
    _FakeAiService.gemini_ok = False
    _FakeAiService.gemini_msg = "Ungültiger Key"

    d.gemini_key_entry.delete(0, "end")
    d.gemini_key_entry.insert(0, "AIzaSyINVALIDKEY")
    d.on_test_gemini_key()

    _pump(app, lambda: "Ungültiger Key" in d.gemini_status_lbl.cget("text"))
    assert "❌" in d.gemini_status_lbl.cget("text")


# ---------------------------------------------------------------------------
# Ollama status scan (online/offline display switching)
# ---------------------------------------------------------------------------


def test_scan_ollama_status_shows_offline_frame_when_server_down(dialog):
    app, d = dialog
    _FakeAiService.is_online = False

    d.scan_ollama_status()
    _pump(app, lambda: _is_shown(d.ollama_offline_frame))

    assert _is_shown(d.ollama_offline_frame)
    assert not _is_shown(d.ollama_online_frame)


def test_scan_ollama_status_shows_online_frame_and_models_when_up(dialog):
    app, d = dialog
    _FakeAiService.is_online = True
    _FakeAiService.installed_models = ["qwen3.5:9b"]
    _FakeAiService.running_models = []

    d.scan_ollama_status()
    _pump(app, lambda: list(d.ai_model_combo.cget("values")) == ["qwen3.5:9b"])

    assert _is_shown(d.ollama_online_frame)
    assert not _is_shown(d.ollama_offline_frame)
    assert list(d.ai_model_combo.cget("values")) == ["qwen3.5:9b"]


def test_scan_ollama_status_shows_no_models_frame_when_none_installed(dialog):
    app, d = dialog
    _FakeAiService.is_online = True
    _FakeAiService.installed_models = []

    d.scan_ollama_status()
    _pump(app, lambda: _is_shown(d.ollama_no_models_frame))

    assert _is_shown(d.ollama_no_models_frame)


# ---------------------------------------------------------------------------
# Global AI on/off toggle
# ---------------------------------------------------------------------------


def test_toggle_global_ai_off_unloads_model_and_updates_profile(dialog):
    from constants import AI_STATUS_UNLOADED

    app, d = dialog
    d.profile.ai_settings.enable_ai = True
    d.ai_enable_chk.select()

    d.ai_enable_chk.deselect()
    d.on_toggle_global_ai()

    assert d.profile.ai_settings.enable_ai is False
    _pump(app, lambda: d.ollama_action_lbl.cget("text") == AI_STATUS_UNLOADED)
    assert d.ollama_action_lbl.cget("text") == AI_STATUS_UNLOADED


def test_toggle_global_ai_on_updates_profile_and_rescans(dialog):
    app, d = dialog
    d.profile.ai_settings.enable_ai = False
    d.ai_enable_chk.deselect()

    d.ai_enable_chk.select()
    d.on_toggle_global_ai()

    assert d.profile.ai_settings.enable_ai is True


# ---------------------------------------------------------------------------
# Server / model management actions (start/stop/preload/unload/create-pvs)
# ---------------------------------------------------------------------------


def test_start_ollama_server_shows_success_message(dialog):
    app, d = dialog
    _FakeAiService.start_ok = True
    _FakeAiService.start_msg = "Server gestartet"

    d.on_start_ollama_server()
    _pump(app, lambda: "Server gestartet" in d.ollama_action_lbl.cget("text"))
    assert "✅" in d.ollama_action_lbl.cget("text")


def test_start_ollama_server_shows_failure_message(dialog):
    app, d = dialog
    _FakeAiService.start_ok = False
    _FakeAiService.start_msg = "Konnte nicht starten"

    d.on_start_ollama_server()
    _pump(app, lambda: "Konnte nicht starten" in d.ollama_action_lbl.cget("text"))
    assert "❌" in d.ollama_action_lbl.cget("text")


def test_preload_model_shows_result_message(dialog):
    app, d = dialog
    _FakeAiService.preload_ok = True
    _FakeAiService.preload_msg = "Modell im Speicher"

    d.on_preload_model()
    _pump(app, lambda: "Modell im Speicher" in d.ollama_action_lbl.cget("text"))
    assert "✅" in d.ollama_action_lbl.cget("text")


def test_unload_model_shows_result_message(dialog):
    app, d = dialog
    _FakeAiService.unload_ok = True
    _FakeAiService.unload_msg = "Modell entladen"

    d.on_unload_model()
    _pump(app, lambda: "Modell entladen" in d.ollama_action_lbl.cget("text"))
    assert "✅" in d.ollama_action_lbl.cget("text")


def test_create_pvs_model_success_updates_profile_model_name(dialog):
    app, d = dialog
    _FakeAiService.create_pvs_ok = True
    _FakeAiService.create_pvs_msg = "pvs-support erstellt"

    d.on_create_pvs_model()
    _pump(app, lambda: d.profile.ai_settings.model_name == "pvs-support")

    assert d.profile.ai_settings.model_name == "pvs-support"
    assert "✅" in d.ollama_action_lbl.cget("text")
