from unittest.mock import patch
import customtkinter as ctk
import pytest

from config import AppConfig, get_default_workspace_dir
from models.profile import (
    UserInfo,
    UserProfile,
    PathSettings,
    WikiSettings,
    AiSettings,
    ShortcutSettings,
    ScoringMatrix,
    UISettings,
)
from services.storage_service import StorageService
from ui.dialogs.profile_settings_dialog import ProfileSettingsDialog


@pytest.fixture
def dummy_app():
    root = ctk.CTk()
    root.withdraw()
    yield root
    try:
        root.destroy()
    except Exception:
        pass


@pytest.fixture
def test_storage(tmp_path):
    ws_dir = tmp_path / "workspace_default"
    cfg = AppConfig(workspace_dir=ws_dir)
    svc = StorageService(cfg)
    return svc


def test_path_settings_model_defaults_and_serialization():
    # Test PathSettings defaults
    ps = PathSettings()
    assert ps.workspace_dir == ""
    assert ps.custom_cases_path == ""
    assert ps.custom_customers_path == ""
    assert ps.custom_wiki_db_path == ""

    # Test dict conversion
    d = ps.to_dict()
    assert isinstance(d, dict)
    assert d["workspace_dir"] == ""

    # Test from_dict
    ps2 = PathSettings.from_dict({
        "workspace_dir": "C:/CustomWS",
        "custom_cases_path": "C:/Cases.json",
    })
    assert ps2.workspace_dir == "C:/CustomWS"
    assert ps2.custom_cases_path == "C:/Cases.json"

    # Test UserProfile inclusion
    p = UserProfile(path_settings=ps2)
    p_dict = p.to_dict()
    assert "path_settings" in p_dict
    assert p_dict["path_settings"]["workspace_dir"] == "C:/CustomWS"

    p_restored = UserProfile.from_dict(p_dict)
    assert p_restored.path_settings.workspace_dir == "C:/CustomWS"
    assert p_restored.path_settings.custom_cases_path == "C:/Cases.json"


def test_storage_service_mirrors_profiles_and_applies_paths(tmp_path, monkeypatch):
    global_dir = tmp_path / "global_appdata"
    monkeypatch.setattr("config.get_global_config_dir", lambda: global_dir)

    ws_a = tmp_path / "ws_a"
    cfg = AppConfig(workspace_dir=ws_a)
    svc = StorageService(cfg)

    p_a = UserProfile(
        user=UserInfo(name="User Alpha"),
        path_settings=PathSettings(
            workspace_dir=str(ws_a),
            custom_cases_path=str(ws_a / "custom_cases.json"),
        )
    )
    svc.save_profile(p_a, sync=True)

    # Verify profile file exists in both workspace and global profiles directory
    assert (svc.profiles_dir / "profile_User_Alpha.json").exists()
    assert (svc.global_profiles_dir / "profile_User_Alpha.json").exists()

    # Verify list_profiles sees User Alpha
    assert "User Alpha" in svc.list_profiles()

    # Apply paths to storage config
    ws_b = tmp_path / "ws_b"
    p_b = UserProfile(
        user=UserInfo(name="User Beta"),
        path_settings=PathSettings(
            workspace_dir=str(ws_b),
            custom_customers_path=str(ws_b / "customers.json"),
        )
    )
    svc.apply_profile_paths(p_b)
    assert svc.config.workspace_dir == ws_b
    assert svc.config.custom_customers_path == ws_b / "customers.json"
    assert svc.config.custom_cases_path is None
    assert (ws_b / "data").exists()


def test_profile_settings_dialog_resets_all_tabs_on_create(dummy_app, test_storage, tmp_path):
    # Create an initial profile with customized non-default values in all tabs
    p_initial = UserProfile(
        user=UserInfo(name="Old User", department="Dev", extension="999", email="old@dev.de", mobile="0123"),
        ui_settings=UISettings(theme="Dark", default_layout="BOARD", font_scale=1.2),
        path_settings=PathSettings(
            workspace_dir=str(tmp_path / "custom_ws"),
            custom_cases_path=str(tmp_path / "cases.json"),
            custom_customers_path=str(tmp_path / "cust.json"),
            custom_wiki_db_path=str(tmp_path / "wiki.sqlite"),
        ),
        wiki_settings=WikiSettings(api_url="https://old-wiki.de/api", token_id="old_id", token_secret="old_sec"),
        ai_settings=AiSettings(provider="GEMINI", gemini_api_key="OLD_KEY", model_name="custom_m"),
        shortcuts=ShortcutSettings(new_case="<Control-n>"),
        scoring_matrix=ScoringMatrix(vip_bonus_points=123),
    )
    test_storage.save_profile(p_initial, sync=True)

    dialog = ProfileSettingsDialog(dummy_app, profile=p_initial, storage_service=test_storage)

    # Simulate creating a brand new profile "Newbie"
    with patch("customtkinter.CTkInputDialog.get_input", return_value="Newbie"):
        dialog.open_create_profile_dialog()

    # 1. User tab should be reset to Newbie and default department
    assert dialog.profile.user.name == "Newbie"
    assert dialog.user_name_entry.get() == "Newbie"
    assert dialog.user_dept_entry.get() == "Support"
    assert dialog.user_ext_entry.get() == ""
    assert dialog.user_email_entry.get() == ""

    # 2. UI section should be reset to default values
    assert dialog.profile.ui_settings.theme == "SYSTEM"
    assert "Cockpit" in dialog.layout_combo.get()

    # 3. Paths tab should be reset to standard default values
    assert dialog.ws_entry.get() == str(get_default_workspace_dir())
    assert dialog.path_cases_entry.get() == ""
    assert dialog.path_cust_entry.get() == ""
    assert dialog.path_wiki_entry.get() == ""
    assert dialog.retention_daily_entry.get() == "7"

    # 4. Wiki tab should be reset to default values
    assert dialog.wiki_url_entry.get() == ""
    assert dialog.wiki_token_id_entry.get() == "ENV_BOOKSTACK_TOKEN_ID"

    # 5. AI tab should be reset to defaults
    assert dialog.gemini_key_entry.get() == ""
    assert "OLLAMA" in dialog.ai_provider_seg.get().upper()

    # 6. Scoring tab should be reset to defaults
    assert dialog.vip_bonus_entry.get() == "50"

    dialog.destroy()


def test_profile_settings_dialog_reloads_all_tabs_on_switch(dummy_app, test_storage, tmp_path):
    # Set up Profile A
    p_a = UserProfile(
        user=UserInfo(name="Agent Alpha", department="Hotline", email="alpha@support.de"),
        path_settings=PathSettings(workspace_dir=str(tmp_path / "ws_alpha"), custom_cases_path=str(tmp_path / "alpha_cases.json")),
        wiki_settings=WikiSettings(api_url="https://alpha-wiki.de/api"),
        ai_settings=AiSettings(gemini_api_key="KEY_ALPHA"),
        scoring_matrix=ScoringMatrix(vip_bonus_points=40),
    )
    test_storage.save_profile(p_a, sync=True)

    # Set up Profile B
    p_b = UserProfile(
        user=UserInfo(name="Agent Beta", department="SecondLevel", email="beta@support.de"),
        path_settings=PathSettings(workspace_dir=str(tmp_path / "ws_beta"), custom_customers_path=str(tmp_path / "beta_cust.json")),
        wiki_settings=WikiSettings(api_url="https://beta-wiki.de/api"),
        ai_settings=AiSettings(gemini_api_key="KEY_BETA"),
        scoring_matrix=ScoringMatrix(vip_bonus_points=95),
    )
    test_storage.save_profile(p_b, sync=True)

    dialog = ProfileSettingsDialog(dummy_app, profile=p_a, storage_service=test_storage)

    # Check initially Profile A fields
    assert dialog.user_name_entry.get() == "Agent Alpha"
    assert dialog.ws_entry.get() == str(tmp_path / "ws_alpha")
    assert dialog.path_cases_entry.get() == str(tmp_path / "alpha_cases.json")
    assert dialog.wiki_url_entry.get() == "https://alpha-wiki.de/api"
    assert dialog.gemini_key_entry.get() == "KEY_ALPHA"
    assert dialog.vip_bonus_entry.get() == "40"

    # Switch to Profile B
    dialog.on_switch_profile("Agent Beta")

    # Check Profile B fields are loaded across all tabs
    assert dialog.user_name_entry.get() == "Agent Beta"
    assert dialog.user_dept_entry.get() == "SecondLevel"
    assert dialog.ws_entry.get() == str(tmp_path / "ws_beta")
    assert dialog.path_cust_entry.get() == str(tmp_path / "beta_cust.json")
    assert dialog.wiki_url_entry.get() == "https://beta-wiki.de/api"
    assert dialog.gemini_key_entry.get() == "KEY_BETA"
    assert dialog.vip_bonus_entry.get() == "95"

    # Switch back to Profile A
    dialog.on_switch_profile("Agent Alpha")
    assert dialog.user_name_entry.get() == "Agent Alpha"
    assert dialog.ws_entry.get() == str(tmp_path / "ws_alpha")
    assert dialog.wiki_url_entry.get() == "https://alpha-wiki.de/api"
    assert dialog.gemini_key_entry.get() == "KEY_ALPHA"
    assert dialog.vip_bonus_entry.get() == "40"

    dialog.destroy()


def test_profile_switch_persists_pending_changes(dummy_app, test_storage, tmp_path):
    p_a = UserProfile(
        user=UserInfo(name="Worker One"),
        path_settings=PathSettings(workspace_dir=str(tmp_path / "ws_one")),
        wiki_settings=WikiSettings(api_url="https://orig-wiki.de/api"),
    )
    test_storage.save_profile(p_a, sync=True)

    p_b = UserProfile(
        user=UserInfo(name="Worker Two"),
        path_settings=PathSettings(workspace_dir=str(tmp_path / "ws_two")),
    )
    test_storage.save_profile(p_b, sync=True)

    dialog = ProfileSettingsDialog(dummy_app, profile=p_a, storage_service=test_storage)

    # Edit fields in Worker One without clicking "Speichern"
    dialog.user_dept_entry.delete(0, "end")
    dialog.user_dept_entry.insert(0, "Special Operations")
    dialog.wiki_url_entry.delete(0, "end")
    dialog.wiki_url_entry.insert(0, "https://modified-wiki.de/api")

    # Switch to Worker Two -> should auto-save Worker One
    dialog.on_switch_profile("Worker Two")
    assert dialog.user_name_entry.get() == "Worker Two"

    # Switch back to Worker One
    dialog.on_switch_profile("Worker One")
    assert dialog.user_dept_entry.get() == "Special Operations"
    assert dialog.wiki_url_entry.get() == "https://modified-wiki.de/api"

    dialog.destroy()
