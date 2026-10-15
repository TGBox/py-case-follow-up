"""ProfileSettingsDialog (all tabs, AI tab actions, profile switching, font scale) plus the profile/path persistence it relies on."""

import json
import threading
import time
from pathlib import Path
from unittest.mock import MagicMock, patch

import customtkinter as ctk
import pytest
from customtkinter import ScalingTracker

import services.ai_service as ai_service_module
from config import AppConfig, get_default_workspace_dir
from models.export_template import ExportTemplate
from models.profile import (
    AiSettings,
    PathSettings,
    ScoringMatrix,
    ShortcutSettings,
    UISettings,
    UserInfo,
    UserProfile,
    WikiSettings,
)
from models.schema import QuestionSchema, SchemaField
from services.storage_service import StorageService
from ui.dialogs.profile_settings_dialog import ProfileSettingsDialog
from ui.dialogs.profile_settings_ui_tab import get_font_scale_display, get_font_scale_val_from_display

PATH_ATTRS = [
    "custom_cases_path", "custom_archive_path", "custom_customers_path", "custom_app_profile_path",
    "custom_colleagues_path", "custom_question_schemas_path", "custom_export_templates_path", "custom_wiki_db_path",
]


@pytest.fixture(autouse=True)
def _reset_widget_scaling():
    yield
    ctk.set_widget_scaling(1.0)


def _mock_storage(tmp_path: Path, profiles: list[str]) -> MagicMock:
    svc = MagicMock(spec=StorageService)
    svc.config = MagicMock()
    svc.config.workspace_dir = tmp_path / "workspace"
    svc.config.data_dir = tmp_path / "workspace" / "data"
    svc.config.attachments_dir = tmp_path / "workspace" / "attachments"
    for attr in PATH_ATTRS:
        setattr(svc.config, attr, None)
    svc.list_profiles.return_value = profiles
    return svc


class _FakeAiService:
    """Stands in for AiService: same call surface, instant canned results (class-level knobs)."""

    is_online = True
    installed_models = ["qwen3.5:9b", "llama3:8b"]
    running_models: list[str] = []
    gemini_ok, gemini_msg = True, "Gemini Key gültig"
    start_ok, start_msg = True, "Ollama Server gestartet"
    preload_ok, preload_msg = True, "Modell geladen"
    unload_ok, unload_msg = True, "Modell entladen"
    create_pvs_ok, create_pvs_msg = True, "pvs-support Modell erstellt"

    def __init__(self, *args, **kwargs):
        pass

    def check_ollama_status(self):
        return _FakeAiService.is_online, list(_FakeAiService.installed_models)

    def get_running_models(self):
        return list(_FakeAiService.running_models)

    def check_gemini_status(self, api_key=None, model=None):
        return _FakeAiService.gemini_ok, _FakeAiService.gemini_msg

    def start_ollama_server(self):
        return _FakeAiService.start_ok, _FakeAiService.start_msg

    def stop_ollama_server(self):
        return True, "Ollama Server beendet"

    def preload_model(self, model_name=None):
        return _FakeAiService.preload_ok, _FakeAiService.preload_msg

    def unload_model(self, model_name=None):
        return _FakeAiService.unload_ok, _FakeAiService.unload_msg

    def create_pvs_support_model(self, modelfile_path=None, base_model_override=None):
        return _FakeAiService.create_pvs_ok, _FakeAiService.create_pvs_msg


class _ImmediateThread:
    """Runs target() synchronously on the main thread: a real worker thread touching Tk without
    a mainloop raises "main thread is not in main loop". self.after(0, done) still queues normally."""

    def __init__(self, target=None, args=(), kwargs=None, daemon=None):
        self._target, self._args, self._kwargs = target, args, kwargs or {}

    def start(self):
        if self._target:
            self._target(*self._args, **self._kwargs)


def _is_shown(widget) -> bool:
    # winfo_ismapped() is always False under a withdrawn root; the geometry manager reflects pack()/pack_forget().
    return bool(widget.winfo_manager())


def _pump(app, predicate, timeout=3.0):
    deadline = time.time() + timeout
    while time.time() < deadline:
        app.update()
        if predicate():
            return True
        time.sleep(0.01)
    return predicate()


# ---------------------------------------------------------------------------
# Dialog with a mocked storage: layout of all tabs, signature files, paths tab, font-scale preview
# ---------------------------------------------------------------------------


def test_dialog_tabs_layout_signature_paths_and_font_preview(root, tmp_path):
    initial_sig = "Mit freundlichen Grüßen\nSupport Team\nTel: 12345"
    profile = UserProfile(
        user=UserInfo(name="Daniel Rösch", email_signature=initial_sig, user_color="#10b981"),
        ui_settings=UISettings(font_scale=1.1),
    )
    storage = _mock_storage(tmp_path, ["Daniel Rösch"])
    d = ProfileSettingsDialog(root, profile=profile, storage_service=storage)

    # Four consolidated tabs, old names kept as aliases
    assert [t[0] for t in d._tab_keys] == ["tab_user", "tab_paths", "tab_ai", "tab_scoring"]
    assert "Benutzerprofil" in d._tab_name_map["tab_user"]
    assert "Speicherort & Datenexport" in d._tab_name_map["tab_paths"]
    assert "Sonstiges" in d._tab_name_map["tab_scoring"]
    assert d.tab_ui is d.tab_user and d.tab_backup is d.tab_paths and d.tab_wiki is d.tab_scoring

    # User tab: two columns side by side, compact field widths
    assert d.user_name_entry.master is not d.language_combo.master
    assert d.user_name_entry.master.master is d.language_combo.master.master
    widths = {
        d.user_name_entry: 185, d.user_dept_entry: 185, d.user_ext_entry: 185, d.user_mobile_entry: 185,
        d.user_email_entry: 380, d.language_combo: 380, d.theme_combo: 380, d.layout_combo: 380,
        d.popup_target_combo: 380, d.btn_save_sig: 185, d.btn_load_sig: 185,
    }
    assert {w: w.cget("width") for w in widths} == widths
    assert d.user_sig_txt.cget("border_width") == 1

    # Colour marker preview sits in its own row and names the user
    assert int(d.preview_lbl.master.grid_info()["row"]) == 17
    assert "Daniel Rösch" in d.preview_sample_lbl.cget("text")

    # Shortcuts tab: record buttons and entries are right-aligned
    assert len(d.rec_buttons) >= 12
    assert all(b.cget("width") == 100 and b.pack_info()["side"] == "right" for b in d.rec_buttons)
    assert all(e.pack_info()["side"] == "right" for e in d.shortcut_entries.values())

    # Multi-line signature: shown, exported to file, imported from file
    assert d.user_sig_txt.get("1.0", "end-1c") == initial_sig
    assert d.user_sig_entry.get() == initial_sig  # duck-typed get() without index args
    export_file = tmp_path / "exported_sig.txt"
    with patch("tkinter.filedialog.asksaveasfilename", return_value=str(export_file)):
        d.on_export_signature()
    assert export_file.read_text(encoding="utf-8") == initial_sig
    assert "erfolgreich gespeichert" in d.status_lbl.cget("text")
    new_sig_file = tmp_path / "new_sig.txt"
    new_sig_file.write_text("Beste Grüße\nNeuer Mitarbeiter", encoding="utf-8")
    with patch("tkinter.filedialog.askopenfilename", return_value=str(new_sig_file)):
        d.on_import_signature()
    assert d.user_sig_txt.get("1.0", "end-1c") == "Beste Grüße\nNeuer Mitarbeiter"
    assert "geladen" in d.status_lbl.cget("text")

    # Paths tab: changing the workspace re-derives all 8 file paths, save persists, reset clears
    path_entries = {
        "custom_cases_path": (d.path_cases_entry, "cases.json"),
        "custom_archive_path": (d.path_archive_entry, "archive.json"),
        "custom_customers_path": (d.path_cust_entry, "customers.json"),
        "custom_app_profile_path": (d.path_profile_entry, "app_profile.json"),
        "custom_colleagues_path": (d.path_colleagues_entry, "colleagues.json"),
        "custom_question_schemas_path": (d.path_schemas_entry, "question_schemas.json"),
        "custom_export_templates_path": (d.path_templates_entry, "export_templates.json"),
        "custom_wiki_db_path": (d.path_wiki_entry, "wiki_index.sqlite"),
    }
    new_ws = tmp_path / "MyNewWorkspace"
    d.ws_entry.delete(0, "end")
    d.ws_entry.insert(0, str(new_ws))
    d.on_workspace_entry_changed()
    data_dir = new_ws / "data"
    assert {a: e.get() for a, (e, _) in path_entries.items()} == {a: str(data_dir / f) for a, (_, f) in path_entries.items()}

    d.save_paths_settings()
    for attr, (_, fname) in path_entries.items():
        assert getattr(d.profile.path_settings, attr) == str(data_dir / fname)
        assert getattr(storage.config, attr) == data_dir / fname

    d.on_reset_paths()
    assert all(e.get() == "" for e, _ in path_entries.values())

    # A workspace that already is a 'data' folder must not become data/data
    data_as_ws = tmp_path / "SubProject" / "data"
    d.update_paths_from_workspace(str(data_as_ws))
    assert d.path_cases_entry.get() == str(data_as_ws / "cases.json")

    # Font scale: preview applies live, closing without saving reverts to the profile's scale
    assert "110%" in d.font_scale_combo.get()
    d.on_font_scale_preview("120% (Groß)")
    assert abs(ScalingTracker.widget_scaling - 1.2) < 0.05
    d.on_close()
    assert abs(ScalingTracker.widget_scaling - 1.1) < 0.05


# ---------------------------------------------------------------------------
# Dialog with a real storage: switching, auto-save on switch, creating a profile, saving
# ---------------------------------------------------------------------------


def test_profile_switch_create_and_save_round_trip(root, tmp_path):
    storage = StorageService(AppConfig(workspace_dir=tmp_path / "workspace_default"))
    p_a = UserProfile(
        user=UserInfo(name="Agent Alpha", department="Hotline", extension="999", email="alpha@support.de", email_signature="Signature 1"),
        ui_settings=UISettings(theme="Dark", default_layout="BOARD"),
        path_settings=PathSettings(workspace_dir=str(tmp_path / "ws_alpha"), custom_cases_path=str(tmp_path / "alpha_cases.json")),
        wiki_settings=WikiSettings(api_url="https://alpha-wiki.de/api", token_id="old_id", token_secret="old_sec"),
        ai_settings=AiSettings(provider="GEMINI", gemini_api_key="KEY_ALPHA", model_name="custom_m"),
        shortcuts=ShortcutSettings(new_case="<Control-n>"),
        scoring_matrix=ScoringMatrix(vip_bonus_points=40),
    )
    p_b = UserProfile(
        user=UserInfo(name="Agent Beta", department="SecondLevel", email="beta@support.de", email_signature="Signature 2\nLine 2"),
        path_settings=PathSettings(workspace_dir=str(tmp_path / "ws_beta"), custom_customers_path=str(tmp_path / "beta_cust.json")),
        wiki_settings=WikiSettings(api_url="https://beta-wiki.de/api"),
        ai_settings=AiSettings(gemini_api_key="KEY_BETA"),
        scoring_matrix=ScoringMatrix(vip_bonus_points=95),
    )
    storage.save_profile(p_a, sync=True)
    storage.save_profile(p_b, sync=True)

    d = ProfileSettingsDialog(root, profile=p_a, storage_service=storage)

    def fields():
        return {
            "name": d.user_name_entry.get(), "dept": d.user_dept_entry.get(), "ws": d.ws_entry.get(),
            "wiki": d.wiki_url_entry.get(), "gemini": d.gemini_key_entry.get(), "vip": d.vip_bonus_entry.get(),
            "sig": d.user_sig_txt.get("1.0", "end-1c"),
        }

    assert fields() == {
        "name": "Agent Alpha", "dept": "Hotline", "ws": str(tmp_path / "ws_alpha"), "wiki": "https://alpha-wiki.de/api",
        "gemini": "KEY_ALPHA", "vip": "40", "sig": "Signature 1",
    }
    assert d.path_cases_entry.get() == str(tmp_path / "alpha_cases.json")

    # Unsaved edits must be auto-saved when switching away
    d.user_dept_entry.delete(0, "end")
    d.user_dept_entry.insert(0, "Special Operations")
    d.wiki_url_entry.delete(0, "end")
    d.wiki_url_entry.insert(0, "https://modified-wiki.de/api")

    d.on_switch_profile("Agent Beta")
    assert fields() == {
        "name": "Agent Beta", "dept": "SecondLevel", "ws": str(tmp_path / "ws_beta"), "wiki": "https://beta-wiki.de/api",
        "gemini": "KEY_BETA", "vip": "95", "sig": "Signature 2\nLine 2",
    }
    assert d.path_cust_entry.get() == str(tmp_path / "beta_cust.json")

    d.on_switch_profile("Agent Alpha")
    assert fields() == {
        "name": "Agent Alpha", "dept": "Special Operations", "ws": str(tmp_path / "ws_alpha"),
        "wiki": "https://modified-wiki.de/api", "gemini": "KEY_ALPHA", "vip": "40", "sig": "Signature 1",
    }

    # Creating a new profile resets every tab to defaults
    with patch("customtkinter.CTkInputDialog.get_input", return_value="Newbie"):
        d.open_create_profile_dialog()
    assert d.profile.user.name == "Newbie"
    assert (d.user_name_entry.get(), d.user_dept_entry.get(), d.user_ext_entry.get(), d.user_email_entry.get()) == ("Newbie", "Support", "", "")
    assert d.profile.ui_settings.theme == "SYSTEM"
    assert "Cockpit" in d.layout_combo.get()
    assert d.ws_entry.get() == str(get_default_workspace_dir())
    assert d.path_cases_entry.get() == d.path_cust_entry.get() == d.path_wiki_entry.get() == ""
    assert d.retention_daily_entry.get() == "7"
    assert d.wiki_url_entry.get() == ""
    assert d.wiki_token_id_entry.get() == "ENV_BOOKSTACK_TOKEN_ID"
    assert d.gemini_key_entry.get() == ""
    assert "OLLAMA" in d.ai_provider_seg.get().upper()
    assert d.vip_bonus_entry.get() == "50"

    # Saving keeps the chosen font scale and signature; closing afterwards does not revert the scale
    d.user_sig_txt.delete("1.0", "end")
    d.user_sig_txt.insert("1.0", "Neue Signatur")
    d.font_scale_combo.set("120% (Groß)")
    d.save_settings()
    assert d.profile.ui_settings.font_scale == 1.2
    assert d.profile.user.email_signature == "Neue Signatur"
    d.on_close()
    assert abs(ScalingTracker.widget_scaling - 1.2) < 0.05


# ---------------------------------------------------------------------------
# AI tab (AiService faked, worker threads run synchronously)
# ---------------------------------------------------------------------------


@pytest.fixture
def ai_dialog(root, storage, monkeypatch):
    monkeypatch.setattr(ai_service_module, "AiService", _FakeAiService)
    monkeypatch.setattr(threading, "Thread", _ImmediateThread)
    # Re-set every knob through monkeypatch so changes made by a test are undone afterwards.
    for knob, value in list(vars(_FakeAiService).items()):
        if not knob.startswith("_") and not callable(value):
            monkeypatch.setattr(_FakeAiService, knob, value)

    d = ProfileSettingsDialog(root, profile=storage.load_profile(), storage_service=storage, on_profile_updated=lambda: None)
    d.update_idletasks()
    _pump(root, lambda: d.ollama_status_lbl.cget("text") != "🔍 Prüfe Ollama-Status...")
    yield root, d
    try:
        d.destroy()
    except Exception:
        pass


def test_ai_tab_provider_key_and_rules_controls(ai_dialog, monkeypatch):
    app, d = ai_dialog

    # Rebuilding the tab picks up saved Gemini key/model
    d.profile.ai_settings.gemini_api_key = "AIzaSyTESTKEY"
    d.profile.ai_settings.gemini_model = "gemini-2.5-pro"
    for w in d.tab_ai.winfo_children():
        w.destroy()
    d.setup_ai_tab()
    _pump(app, lambda: d.ollama_status_lbl.cget("text") != "🔍 Prüfe Ollama-Status...")
    assert d.gemini_key_entry.get() == "AIzaSyTESTKEY"
    assert d.gemini_model_combo.get() == "gemini-2.5-pro"

    # Provider switching toggles the cards
    assert _is_shown(d.ollama_card) and not _is_shown(d.gemini_card)
    d.on_change_ai_provider("GOOGLE GEMINI (Cloud)")
    assert _is_shown(d.gemini_card) and not _is_shown(d.ollama_card)
    d.on_change_ai_provider("OLLAMA (Lokal)")
    assert _is_shown(d.ollama_card) and not _is_shown(d.gemini_card)

    # Show/hide key
    assert d.gemini_key_entry.cget("show") == "*"
    d.on_toggle_show_gemini_key()
    assert (d.gemini_key_entry.cget("show"), d.btn_toggle_key_show.cget("text")) == ("", "🔒")
    d.on_toggle_show_gemini_key()
    assert (d.gemini_key_entry.cget("show"), d.btn_toggle_key_show.cget("text")) == ("*", "👁")

    # Empty key -> warning without contacting the service
    d.gemini_key_entry.delete(0, "end")
    d.on_test_gemini_key()
    assert "API Key" in d.gemini_status_lbl.cget("text")

    # Modelfile rules: empty Modelfile is a no-op
    def rules():
        return d.ai_base_rules_txt.get("1.0", "end-1c")

    def set_rules(text):
        d.ai_base_rules_txt.delete("1.0", "end")
        d.ai_base_rules_txt.insert("1.0", text)

    monkeypatch.setattr(d, "get_modelfile_prompt_text", lambda: "")
    set_rules("Unveränderter Text.")
    d.gemini_modelfile_chk_var.set(True)
    d.on_toggle_gemini_modelfile_rules()
    assert rules() == "Unveränderter Text."

    # ... otherwise appended with marker and removed again, keeping the user's own rules
    monkeypatch.setattr(d, "get_modelfile_prompt_text", lambda: "Du bist ein Support-Assistent.")
    set_rules("Bestehende Basis-Regel.")
    d.on_toggle_gemini_modelfile_rules()
    assert "Bestehende Basis-Regel." in rules()
    assert "Du bist ein Support-Assistent." in rules() and "--- MODELFILE SYSTEM-REGELN ---" in rules()
    d.gemini_modelfile_chk_var.set(False)
    d.on_toggle_gemini_modelfile_rules()
    assert "Du bist ein Support-Assistent." not in rules() and "--- MODELFILE SYSTEM-REGELN ---" not in rules()
    assert "Bestehende Basis-Regel." in rules()

    # Switching to Ollama strips Modelfile rules that were added for Gemini
    set_rules("")
    d.gemini_modelfile_chk_var.set(True)
    d.on_change_ai_provider("GOOGLE GEMINI (Cloud)")
    assert "Du bist ein Support-Assistent." in rules()
    d.on_change_ai_provider("OLLAMA (Lokal)")
    assert "Du bist ein Support-Assistent." not in rules()

    # Selecting an Ollama model
    d.on_select_ai_model("llama3:8b")
    assert d.ai_model_entry.get() == "llama3:8b"
    assert d.profile.ai_settings.model_name == "llama3:8b"
    assert "llama3:8b" in d.ollama_action_lbl.cget("text")


def test_ai_tab_async_actions_report_service_results(ai_dialog):
    from constants import AI_STATUS_UNLOADED

    app, d = ai_dialog
    fake = _FakeAiService

    def lbl():
        return d.ollama_action_lbl.cget("text")

    # Gemini key check: valid and invalid
    for ok, msg, icon in [(True, "Key ist gültig", "✅"), (False, "Ungültiger Key", "❌")]:
        fake.gemini_ok, fake.gemini_msg = ok, msg
        d.gemini_key_entry.delete(0, "end")
        d.gemini_key_entry.insert(0, "AIzaSyKEY")
        d.on_test_gemini_key()
        assert _pump(app, lambda: msg in d.gemini_status_lbl.cget("text"))
        assert icon in d.gemini_status_lbl.cget("text")

    # Ollama status scan: offline, online with models, online without models
    fake.is_online = False
    d.scan_ollama_status()
    assert _pump(app, lambda: _is_shown(d.ollama_offline_frame))
    assert not _is_shown(d.ollama_online_frame)

    fake.is_online, fake.installed_models = True, ["qwen3.5:9b"]
    d.scan_ollama_status()
    assert _pump(app, lambda: list(d.ai_model_combo.cget("values")) == ["qwen3.5:9b"])
    assert _is_shown(d.ollama_online_frame) and not _is_shown(d.ollama_offline_frame)

    fake.installed_models = []
    d.scan_ollama_status()
    assert _pump(app, lambda: _is_shown(d.ollama_no_models_frame))

    # Server / model actions show the service's message with a success or failure icon
    actions = [
        (d.on_start_ollama_server, "start", True, "Server gestartet", "✅"),
        (d.on_start_ollama_server, "start", False, "Konnte nicht starten", "❌"),
        (d.on_preload_model, "preload", True, "Modell im Speicher", "✅"),
        (d.on_unload_model, "unload", True, "Modell entladen", "✅"),
    ]
    for action, knob, ok, msg, icon in actions:
        setattr(fake, f"{knob}_ok", ok)
        setattr(fake, f"{knob}_msg", msg)
        action()
        assert _pump(app, lambda: msg in lbl()), msg
        assert icon in lbl()

    fake.create_pvs_ok, fake.create_pvs_msg = True, "pvs-support erstellt"
    d.on_create_pvs_model()
    assert _pump(app, lambda: d.profile.ai_settings.model_name == "pvs-support")
    assert "✅" in lbl()

    # Global AI switch: off unloads and updates the profile, on re-enables
    d.ai_enable_chk.select()
    d.profile.ai_settings.enable_ai = True
    d.ai_enable_chk.deselect()
    d.on_toggle_global_ai()
    assert d.profile.ai_settings.enable_ai is False
    assert _pump(app, lambda: lbl() == AI_STATUS_UNLOADED)

    d.ai_enable_chk.select()
    d.on_toggle_global_ai()
    assert d.profile.ai_settings.enable_ai is True


# ---------------------------------------------------------------------------
# Font scale outside the dialog (model, display helpers, table view, app zoom)
# ---------------------------------------------------------------------------


def test_font_scale_model_and_display_helpers():
    ui = UISettings()
    assert ui.font_scale == 1.0
    ui.font_scale = 1.2
    assert UISettings.from_dict(ui.to_dict()).font_scale == 1.2
    for invalid in (0.2, 3.5, "not_a_number"):
        assert UISettings.from_dict({"font_scale": invalid}).font_scale == 1.0
    ui.reset_column_widths()
    assert ui.font_scale == 1.0

    for scale, pct in [(1.0, "100%"), (1.2, "120%"), (0.9, "90%")]:
        assert pct in get_font_scale_display(scale)
    for text, val in [("120% (Groß)", 1.2), ("100% (Standard)", 1.0), ("90% (Kompakt)", 0.9), ("110%", 1.1)]:
        assert get_font_scale_val_from_display(text) == val


def test_table_view_row_height_follows_font_scale(root):
    from tkinter import ttk
    from ui.views.table_view import TableView

    table = TableView(
        root, author_name="Tester", scoring_service=MagicMock(), attachment_service=MagicMock(),
        on_case_updated=MagicMock(), on_case_selected=MagicMock(),
        app_config=UserProfile(ui_settings=UISettings(font_scale=1.3)),
    )
    assert int(ttk.Style().lookup("Matrix.Treeview", "rowheight")) == round(32 * 1.3)
    table.destroy()


def test_app_zoom_font_steps_clamps_and_resets():
    from ui.app import SupportCockpitApp

    profile = UserProfile(ui_settings=UISettings(font_scale=1.0))
    app = MagicMock(spec=SupportCockpitApp)
    app.profile, app.storage_service, app.table_view = profile, MagicMock(), MagicMock()

    with patch("ui.widgets.toast_notification.ToastNotification"):
        SupportCockpitApp.zoom_font(app, 0.1)
        assert profile.ui_settings.font_scale == 1.1
        app.storage_service.save_profile.assert_called_with(profile)
        app.table_view.setup_treeview_style.assert_called()
        for delta, expected in [(-0.2, 0.9), (-0.5, 0.8), (1.0, 1.5)]:
            SupportCockpitApp.zoom_font(app, delta)
            assert profile.ui_settings.font_scale == expected
        SupportCockpitApp.zoom_font(app, 0.0, reset=True)
        assert profile.ui_settings.font_scale == 1.0


# ---------------------------------------------------------------------------
# Profile paths persistence (StorageService side of the paths tab)
# ---------------------------------------------------------------------------


def test_path_settings_round_trip_through_profile():
    assert PathSettings().to_dict()["workspace_dir"] == ""
    ps = PathSettings.from_dict({"workspace_dir": "C:/CustomWS", "custom_cases_path": "C:/Cases.json"})
    restored = UserProfile.from_dict(UserProfile(path_settings=ps).to_dict()).path_settings
    assert (restored.workspace_dir, restored.custom_cases_path, restored.custom_customers_path) == ("C:/CustomWS", "C:/Cases.json", "")


def test_storage_mirrors_profiles_globally_and_applies_paths(tmp_path, monkeypatch):
    monkeypatch.setattr("config.get_global_config_dir", lambda: tmp_path / "global_appdata")
    ws_a = tmp_path / "ws_a"
    svc = StorageService(AppConfig(workspace_dir=ws_a))

    svc.save_profile(UserProfile(user=UserInfo(name="User Alpha"), path_settings=PathSettings(workspace_dir=str(ws_a))), sync=True)
    assert (svc.profiles_dir / "profile_User_Alpha.json").exists()
    assert (svc.global_profiles_dir / "profile_User_Alpha.json").exists()
    assert "User Alpha" in svc.list_profiles()

    ws_b = tmp_path / "ws_b"
    svc.apply_profile_paths(UserProfile(
        user=UserInfo(name="User Beta"),
        path_settings=PathSettings(workspace_dir=str(ws_b), custom_customers_path=str(ws_b / "customers.json")),
    ))
    assert svc.config.workspace_dir == ws_b
    assert svc.config.custom_customers_path == ws_b / "customers.json"
    assert svc.config.custom_cases_path is None
    assert (ws_b / "data").exists()


def test_existing_path_overrides_survive_the_first_start(tmp_path):
    """Nur vier Pfade stehen im Dialog - die anderen duerfen nicht verloren gehen."""
    from services.storage_service import PROFILE_PATH_OVERRIDES

    extern = tmp_path / "extern"
    extern.mkdir()
    cfg = AppConfig(workspace_dir=tmp_path / "ws", **{a: extern / f"{a}.json" for a in PATH_ATTRS})
    svc = StorageService(cfg)
    svc.apply_profile_paths(svc.load_profile())
    assert [a for a in PROFILE_PATH_OVERRIDES if getattr(cfg, a) is None] == []


def test_an_explicit_workspace_argument_wins_over_the_profile(tmp_path):
    """Sonst lenkt ein kopierter Datenordner die App auf den fremden Pfad um."""
    ws_cli = tmp_path / "ws_cli"
    ws_cli.mkdir()
    svc = StorageService(AppConfig.load_user_config(cli_workspace=ws_cli))
    svc.apply_profile_paths(UserProfile(
        user=UserInfo(name="Kollegin"),
        path_settings=PathSettings(workspace_dir=str(tmp_path / "vom_anderen_rechner")),
    ))
    assert svc.config.workspace_dir == ws_cli
    assert not (tmp_path / "vom_anderen_rechner").exists()


def test_a_workspace_that_cannot_be_created_leaves_the_app_running(tmp_path, monkeypatch):
    """Ein fremdes Laufwerk im Profil darf den Start nicht verhindern."""
    ws = tmp_path / "ws"
    cfg = AppConfig(workspace_dir=ws)
    cfg.ensure_directories()
    svc = StorageService(cfg)

    def _refuse(*args, **kwargs):
        raise OSError(2, "No such file or directory")

    monkeypatch.setattr(AppConfig, "ensure_directories", _refuse)
    svc.apply_profile_paths(UserProfile(
        user=UserInfo(name="Kollegin"),
        path_settings=PathSettings(workspace_dir="D:/Nicht/Auf/Diesem/Rechner"),
    ))
    assert svc.config.workspace_dir == ws
    assert isinstance(svc.load_cases(), list)


# ---------------------------------------------------------------------------
# Toggling the default schemas/templates must not lose the user's own entries
# ---------------------------------------------------------------------------


@pytest.fixture
def example_storage(tmp_path):
    cfg = MagicMock()
    cfg.workspace_dir = tmp_path / "workspace"
    cfg.data_dir = tmp_path / "workspace" / "data"
    cfg.data_dir.mkdir(parents=True)
    cfg.attachments_dir = tmp_path / "workspace" / "attachments"
    cfg.attachments_dir.mkdir(parents=True)
    for name in ("question_schemas", "export_templates", "profiles", "cases", "customers", "colleagues", "snippets"):
        setattr(cfg, f"{name}_path", cfg.data_dir / f"{name}.json")
    cfg.custom_cases_path = cfg.custom_customers_path = cfg.custom_wiki_db_path = None
    cfg.log_file_path = tmp_path / "test.log"
    ex_dir = tmp_path / "examples"
    ex_dir.mkdir()
    cfg.get_example_path = lambda filename: ex_dir / filename
    (ex_dir / "question_schemas.json").write_text(json.dumps({"schemas": [
        {"schema_id": sid, "display_name": sid, "fields": [{"field_id": "f1", "label": "Feld", "field_type": "text", "order": 1}]}
        for sid in ("schema_default_a", "schema_default_b")
    ]}), encoding="utf-8")
    (ex_dir / "export_templates.json").write_text(json.dumps({"templates": [{
        "template_id": "tmpl_default_1", "display_name": "Vorlage 1", "target_type": "CLIPBOARD_TEXT",
        "applicable_cases": [], "template_string": "Hello {{ customer.practice_name }}",
    }]}), encoding="utf-8")
    return StorageService(cfg)


@pytest.mark.parametrize("kind", ["schemas", "templates"])
def test_toggle_defaults_keeps_custom_entries_and_writes_backup(example_storage, kind):
    svc = example_storage
    if kind == "schemas":
        svc.save_schemas([QuestionSchema(
            schema_id="custom", display_name="Eigenes Formular",
            fields=[SchemaField(field_id="c1", label="Eigenes Feld", field_type="text", order=1, required=True)],
        )], sync=True)
        toggle, has_defaults, id_of, path = svc.toggle_default_schemas, svc.has_default_schemas, (lambda s: s.schema_id), svc.config.question_schemas_path
        defaults = {"schema_default_a", "schema_default_b"}
    else:
        svc.save_templates([ExportTemplate(
            template_id="custom", display_name="Eigene Vorlage", target_type="CLIPBOARD_TEXT",
            applicable_cases=[], template_string="Custom",
        )], sync=True)
        toggle, has_defaults, id_of, path = svc.toggle_default_templates, svc.has_default_templates, (lambda t: t.template_id), svc.config.export_templates_path
        defaults = {"tmpl_default_1"}

    assert not has_defaults()
    items, added = toggle()
    assert added is True and has_defaults()
    assert {id_of(i) for i in items} == {"custom"} | defaults
    bak = json.loads(path.with_suffix(".json.bak").read_text(encoding="utf-8"))
    assert "custom" in json.dumps(bak)

    items, added = toggle()
    assert added is False and not has_defaults()
    assert {id_of(i) for i in items} == {"custom"}
