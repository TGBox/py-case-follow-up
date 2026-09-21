"""Tests verifying:
1. Vertically flush right-aligned buttons in ShortcutsSettingsTabMixin (Sonstiges Tab).
2. All 8 configurable custom paths in PathsSettingsTabMixin (Speicherort Tab) and automatic relative adaptation upon selecting a workspace folder.
3. Dedicated preview row for the user color marker in UserSettingsTabMixin (Benutzerprofil Tab).
"""

from pathlib import Path
from unittest.mock import MagicMock
import customtkinter as ctk
import pytest

from models.profile import UserProfile
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


def test_shortcuts_tab_buttons_right_aligned(dummy_app):
    """Verify rec_btn and entry are packed to the right in both hotkey actions and snippets."""
    mock_storage = MagicMock()
    mock_storage.config.workspace_dir = Path("C:/dummy_ws")
    mock_storage.config.custom_cases_path = None
    mock_storage.config.custom_archive_path = None
    mock_storage.config.custom_customers_path = None
    mock_storage.config.custom_app_profile_path = None
    mock_storage.config.custom_colleagues_path = None
    mock_storage.config.custom_question_schemas_path = None
    mock_storage.config.custom_export_templates_path = None
    mock_storage.config.custom_wiki_db_path = None

    profile = UserProfile()
    dialog = ProfileSettingsDialog(parent=dummy_app, profile=profile, storage_service=mock_storage)

    # All rec buttons in shortcuts tab should have width 100
    assert len(dialog.rec_buttons) >= 12
    for btn in dialog.rec_buttons:
        assert btn.cget("width") == 100
        # The pack info side should be 'right'
        pack_info = btn.pack_info()
        assert pack_info["side"] == "right"

    # All shortcut entries should be packed to the right
    for entry in dialog.shortcut_entries.values():
        pack_info = entry.pack_info()
        assert pack_info["side"] == "right"

    dialog.destroy()


def test_paths_tab_all_eight_paths_and_workspace_sync(dummy_app, tmp_path: Path):
    """Verify all 8 path entries exist, can be edited/saved, reset, and auto-update on workspace change."""
    mock_storage = MagicMock()
    mock_storage.config.workspace_dir = tmp_path
    for attr in [
        "custom_cases_path", "custom_archive_path", "custom_customers_path",
        "custom_app_profile_path", "custom_colleagues_path",
        "custom_question_schemas_path", "custom_export_templates_path", "custom_wiki_db_path"
    ]:
        setattr(mock_storage.config, attr, None)

    profile = UserProfile()
    dialog = ProfileSettingsDialog(parent=dummy_app, profile=profile, storage_service=mock_storage)

    # Verify all 8 path entries exist
    entries = [
        dialog.path_cases_entry,
        dialog.path_archive_entry,
        dialog.path_cust_entry,
        dialog.path_profile_entry,
        dialog.path_colleagues_entry,
        dialog.path_schemas_entry,
        dialog.path_templates_entry,
        dialog.path_wiki_entry,
    ]
    for e in entries:
        assert isinstance(e, ctk.CTkEntry)

    # 1. Test updating workspace updates all 8 individual paths to relative data structure
    new_ws = tmp_path / "MyNewWorkspace"
    dialog.ws_entry.delete(0, "end")
    dialog.ws_entry.insert(0, str(new_ws))
    dialog.on_workspace_entry_changed()

    expected_data_dir = new_ws / "data"
    assert dialog.path_cases_entry.get() == str(expected_data_dir / "cases.json")
    assert dialog.path_archive_entry.get() == str(expected_data_dir / "archive.json")
    assert dialog.path_cust_entry.get() == str(expected_data_dir / "customers.json")
    assert dialog.path_profile_entry.get() == str(expected_data_dir / "app_profile.json")
    assert dialog.path_colleagues_entry.get() == str(expected_data_dir / "colleagues.json")
    assert dialog.path_schemas_entry.get() == str(expected_data_dir / "question_schemas.json")
    assert dialog.path_templates_entry.get() == str(expected_data_dir / "export_templates.json")
    assert dialog.path_wiki_entry.get() == str(expected_data_dir / "wiki_index.sqlite")

    # 2. Test saving persists all 8 paths into profile.path_settings and storage_service.config
    dialog.save_paths_settings()
    assert dialog.profile.path_settings.custom_cases_path == str(expected_data_dir / "cases.json")
    assert dialog.profile.path_settings.custom_archive_path == str(expected_data_dir / "archive.json")
    assert dialog.profile.path_settings.custom_customers_path == str(expected_data_dir / "customers.json")
    assert dialog.profile.path_settings.custom_app_profile_path == str(expected_data_dir / "app_profile.json")
    assert dialog.profile.path_settings.custom_colleagues_path == str(expected_data_dir / "colleagues.json")
    assert dialog.profile.path_settings.custom_question_schemas_path == str(expected_data_dir / "question_schemas.json")
    assert dialog.profile.path_settings.custom_export_templates_path == str(expected_data_dir / "export_templates.json")
    assert dialog.profile.path_settings.custom_wiki_db_path == str(expected_data_dir / "wiki_index.sqlite")

    assert mock_storage.config.custom_cases_path == expected_data_dir / "cases.json"
    assert mock_storage.config.custom_archive_path == expected_data_dir / "archive.json"
    assert mock_storage.config.custom_customers_path == expected_data_dir / "customers.json"
    assert mock_storage.config.custom_app_profile_path == expected_data_dir / "app_profile.json"
    assert mock_storage.config.custom_colleagues_path == expected_data_dir / "colleagues.json"
    assert mock_storage.config.custom_question_schemas_path == expected_data_dir / "question_schemas.json"
    assert mock_storage.config.custom_export_templates_path == expected_data_dir / "export_templates.json"
    assert mock_storage.config.custom_wiki_db_path == expected_data_dir / "wiki_index.sqlite"

    # 3. Test on_reset_paths clears all 8 entries
    dialog.on_reset_paths()
    for e in entries:
        assert e.get() == ""

    # 4. If selected workspace folder itself ends with 'data', do not double 'data/data'
    data_as_ws = tmp_path / "SubProject" / "data"
    dialog.update_paths_from_workspace(str(data_as_ws))
    assert dialog.path_cases_entry.get() == str(data_as_ws / "cases.json")
    assert "data\\data" not in dialog.path_cases_entry.get() and "data/data" not in dialog.path_cases_entry.get()

    dialog.destroy()


def test_user_tab_color_preview_dedicated_row(dummy_app):
    """Verify user tab color preview resides in its own dedicated row (row 17) and is legible."""
    mock_storage = MagicMock()
    mock_storage.config.workspace_dir = Path("C:/dummy_ws")
    for attr in [
        "custom_cases_path", "custom_archive_path", "custom_customers_path",
        "custom_app_profile_path", "custom_colleagues_path",
        "custom_question_schemas_path", "custom_export_templates_path", "custom_wiki_db_path"
    ]:
        setattr(mock_storage.config, attr, None)

    profile = UserProfile()
    profile.user.name = "Daniel Rösch"
    profile.user.user_color = "#10b981"
    dialog = ProfileSettingsDialog(parent=dummy_app, profile=profile, storage_service=mock_storage)

    assert hasattr(dialog, "preview_lbl")
    assert hasattr(dialog, "preview_tile")
    assert hasattr(dialog, "preview_sample_lbl")

    # Verify preview widgets are parented to a frame on row 17
    parent_frame = dialog.preview_lbl.master
    assert parent_frame is not None
    grid_info = parent_frame.grid_info()
    assert int(grid_info["row"]) == 17

    # Sample text should contain user name
    sample_text = dialog.preview_sample_lbl.cget("text")
    assert "Daniel Rösch" in sample_text

    dialog.destroy()
