from typing import Any
from unittest.mock import MagicMock, patch
import customtkinter as ctk
import pytest
from models.profile import UserInfo, UserProfile
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
def storage_service_mock(tmp_path):
    svc = MagicMock(spec=StorageService)
    svc.config = MagicMock()
    svc.config.workspace_dir = tmp_path / "workspace"
    svc.config.data_dir = tmp_path / "workspace" / "data"
    svc.config.attachments_dir = tmp_path / "workspace" / "attachments"
    svc.config.custom_cases_path = None
    svc.config.custom_customers_path = None
    svc.config.custom_wiki_db_path = None
    svc.list_profiles.return_value = ["Test User", "Second User"]
    return svc


def test_consolidated_tabs_count_and_titles(dummy_app, storage_service_mock):
    profile = UserProfile(user=UserInfo(name="Test User", email_signature="Mit freundlichen Grüßen\nMax Mustermann"))
    dialog = ProfileSettingsDialog(dummy_app, profile=profile, storage_service=storage_service_mock)

    # Verify exactly 5 tabs in _tab_keys
    tab_ids = [t[0] for t in dialog._tab_keys]
    assert tab_ids == ["tab_user", "tab_paths", "tab_wiki", "tab_ai", "tab_scoring"]

    # Verify tab names
    assert "Benutzerprofil" in dialog._tab_name_map["tab_user"]
    assert "Speicherort & Datenexport" in dialog._tab_name_map["tab_paths"]

    # Verify backward compatibility aliases
    assert dialog.tab_ui is dialog.tab_user
    assert dialog.tab_backup is dialog.tab_paths

    dialog.destroy()


def test_field_width_constraints(dummy_app, storage_service_mock):
    profile = UserProfile(user=UserInfo(name="Test User"))
    dialog = ProfileSettingsDialog(dummy_app, profile=profile, storage_service=storage_service_mock)

    # Ensure single-line entries have constrained width (380px)
    assert dialog.user_name_entry.cget("width") == 380
    assert dialog.user_dept_entry.cget("width") == 380
    assert dialog.user_ext_entry.cget("width") == 380
    assert dialog.user_email_entry.cget("width") == 380
    assert dialog.user_mobile_entry.cget("width") == 380

    # Ensure dropdowns in user profile have constrained width (380px)
    assert dialog.language_combo.cget("width") == 380
    assert dialog.theme_combo.cget("width") == 380
    assert dialog.layout_combo.cget("width") == 380
    assert dialog.popup_target_combo.cget("width") == 380

    # Ensure scrollable container exists
    assert hasattr(dialog, "user_scroll")
    assert isinstance(dialog.user_scroll, ctk.CTkScrollableFrame)

    dialog.destroy()


def test_multiline_email_signature_and_save_load_buttons(dummy_app, storage_service_mock, tmp_path):
    initial_sig = "Mit freundlichen Grüßen\nSupport Team\nTel: 12345"
    profile = UserProfile(user=UserInfo(name="Test User", email_signature=initial_sig))
    dialog = ProfileSettingsDialog(dummy_app, profile=profile, storage_service=storage_service_mock)

    # Verify signature widget is CTkTextbox
    assert hasattr(dialog, "user_sig_txt")
    assert isinstance(dialog.user_sig_txt, ctk.CTkTextbox)
    assert dialog.user_sig_txt.get("1.0", "end-1c") == initial_sig

    # Verify duck-typed get() without arguments
    user_sig_duck: Any = dialog.user_sig_entry
    assert user_sig_duck.get() == initial_sig

    # Verify save & load signature buttons exist
    assert hasattr(dialog, "btn_save_sig")
    assert hasattr(dialog, "btn_load_sig")
    assert isinstance(dialog.btn_save_sig, ctk.CTkButton)
    assert isinstance(dialog.btn_load_sig, ctk.CTkButton)

    # Test export signature
    export_file = tmp_path / "exported_sig.txt"
    with patch("tkinter.filedialog.asksaveasfilename", return_value=str(export_file)):
        dialog.on_export_signature()

    assert export_file.exists()
    assert export_file.read_text(encoding="utf-8") == initial_sig
    assert "erfolgreich gespeichert" in dialog.status_lbl.cget("text")

    # Test import signature
    new_sig_file = tmp_path / "new_sig.txt"
    new_sig_content = "Beste Grüße\nNeuer Mitarbeiter\nSupport & Dev"
    new_sig_file.write_text(new_sig_content, encoding="utf-8")

    with patch("tkinter.filedialog.askopenfilename", return_value=str(new_sig_file)):
        dialog.on_import_signature()

    assert dialog.user_sig_txt.get("1.0", "end-1c") == new_sig_content
    assert "geladen" in dialog.status_lbl.cget("text")

    # Test saving settings persists the imported signature
    dialog.save_settings()
    assert dialog.profile.user.email_signature == new_sig_content

    dialog.destroy()


def test_profile_switch_reloads_signature(dummy_app, storage_service_mock):
    p1 = UserProfile(user=UserInfo(name="Test User", email_signature="Signature 1"))
    p2 = UserProfile(user=UserInfo(name="Second User", email_signature="Signature 2\nLine 2"))

    storage_service_mock.load_profile_by_name.side_effect = lambda name: p2 if name == "Second User" else p1
    dialog = ProfileSettingsDialog(dummy_app, profile=p1, storage_service=storage_service_mock)

    assert dialog.user_sig_txt.get("1.0", "end-1c") == "Signature 1"

    dialog.on_switch_profile("Second User")
    assert dialog.user_sig_txt.get("1.0", "end-1c") == "Signature 2\nLine 2"

    dialog.destroy()


def test_paths_and_dataexport_consolidated(dummy_app, storage_service_mock):
    profile = UserProfile()
    dialog = ProfileSettingsDialog(dummy_app, profile=profile, storage_service=storage_service_mock)

    # Verify paths_scroll exists
    assert hasattr(dialog, "paths_scroll")
    assert isinstance(dialog.paths_scroll, ctk.CTkScrollableFrame)

    # Verify workspace entry is present
    assert hasattr(dialog, "ws_entry")

    # Verify ZIP export & import buttons are in the tab
    assert hasattr(dialog, "on_click_export_zip")
    assert hasattr(dialog, "on_click_import_zip")

    dialog.destroy()
