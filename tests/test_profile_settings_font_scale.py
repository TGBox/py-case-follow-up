from unittest.mock import MagicMock
import customtkinter as ctk
import pytest
from models.profile import UISettings, UserInfo, UserProfile
from services.storage_service import StorageService
from ui.dialogs.profile_settings_dialog import (
    ProfileSettingsDialog,
    get_font_scale_display,
    get_font_scale_val_from_display,
)
from ui.views.table_view import TableView


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
    svc.list_profiles.return_value = ["Test User"]
    return svc


def test_ui_settings_font_scale_serialization():
    # 1. Default value
    ui = UISettings()
    assert ui.font_scale == 1.0

    # 2. Serialization and Deserialization
    ui.font_scale = 1.2
    d = ui.to_dict()
    assert d["font_scale"] == 1.2

    loaded = UISettings.from_dict(d)
    assert loaded.font_scale == 1.2

    # 3. Out-of-bounds check (clamping / fallback to 1.0)
    invalid_low = UISettings.from_dict({"font_scale": 0.2})
    assert invalid_low.font_scale == 1.0

    invalid_high = UISettings.from_dict({"font_scale": 3.5})
    assert invalid_high.font_scale == 1.0

    invalid_type = UISettings.from_dict({"font_scale": "not_a_number"})
    assert invalid_type.font_scale == 1.0

    # 4. Reset
    ui.reset_column_widths()
    assert ui.font_scale == 1.0


def test_font_scale_helpers():
    assert "100%" in get_font_scale_display(1.0)
    assert "120%" in get_font_scale_display(1.2)
    assert "90%" in get_font_scale_display(0.9)

    assert get_font_scale_val_from_display("120% (Groß)") == 1.2
    assert get_font_scale_val_from_display("100% (Standard)") == 1.0
    assert get_font_scale_val_from_display("90% (Kompakt)") == 0.9
    assert get_font_scale_val_from_display("110%") == 1.1


def test_profile_settings_dialog_font_scale(dummy_app, storage_service_mock):
    profile = UserProfile(
        user=UserInfo(name="Test User"),
        ui_settings=UISettings(font_scale=1.1),
    )
    dialog = ProfileSettingsDialog(dummy_app, profile=profile, storage_service=storage_service_mock)

    assert hasattr(dialog, "font_scale_combo")
    assert hasattr(dialog, "font_scale_lbl")
    assert "110%" in dialog.font_scale_combo.get()

    # Test preview scaling
    dialog.on_font_scale_preview("120% (Groß)")
    from customtkinter import ScalingTracker
    assert abs(ScalingTracker.widget_scaling - 1.2) < 0.05

    # Test closing without save reverts to initial scale (1.1)
    dialog.on_close()
    assert abs(ScalingTracker.widget_scaling - 1.1) < 0.05


def test_profile_settings_dialog_save_font_scale(dummy_app, storage_service_mock):
    profile = UserProfile(
        user=UserInfo(name="Test User"),
        ui_settings=UISettings(font_scale=1.0),
    )
    dialog = ProfileSettingsDialog(dummy_app, profile=profile, storage_service=storage_service_mock)

    dialog.font_scale_combo.set("120% (Groß)")
    dialog.save_settings()

    assert dialog.profile.ui_settings.font_scale == 1.2
    assert dialog._saved is True

    # Closing now keeps 1.2
    dialog.on_close()
    from customtkinter import ScalingTracker
    assert abs(ScalingTracker.widget_scaling - 1.2) < 0.05

    # Reset scaling back to 1.0 for subsequent tests
    ctk.set_widget_scaling(1.0)


def test_table_view_font_scaling(dummy_app):
    from tkinter import ttk
    from unittest.mock import MagicMock
    profile = UserProfile(ui_settings=UISettings(font_scale=1.3))
    table = TableView(
        dummy_app,
        author_name="Tester",
        scoring_service=MagicMock(),
        attachment_service=MagicMock(),
        on_case_updated=MagicMock(),
        on_case_selected=MagicMock(),
        app_config=profile,
    )

    style = ttk.Style()
    rowheight = style.lookup("Matrix.Treeview", "rowheight")
    # Default is 32, with 1.3 scaling it should be round(32 * 1.3) = 42
    assert int(rowheight) == round(32 * 1.3)

    table.destroy()
    ctk.set_widget_scaling(1.0)


def test_app_zoom_font_logic():
    from ui.app import SupportCockpitApp
    from unittest.mock import patch

    profile = UserProfile(ui_settings=UISettings(font_scale=1.0))
    app_mock = MagicMock(spec=SupportCockpitApp)
    app_mock.profile = profile
    app_mock.storage_service = MagicMock()
    app_mock.table_view = MagicMock()

    with patch("ui.widgets.toast_notification.ToastNotification"):
        SupportCockpitApp.zoom_font(app_mock, 0.1)
        assert app_mock.profile.ui_settings.font_scale == 1.1
        app_mock.storage_service.save_profile.assert_called_with(profile)
        app_mock.table_view.setup_treeview_style.assert_called()

        SupportCockpitApp.zoom_font(app_mock, -0.2)
        assert app_mock.profile.ui_settings.font_scale == 0.9

        # Clamp at min 0.8
        SupportCockpitApp.zoom_font(app_mock, -0.5)
        assert app_mock.profile.ui_settings.font_scale == 0.8

        # Clamp at max 1.5
        SupportCockpitApp.zoom_font(app_mock, 1.0)
        assert app_mock.profile.ui_settings.font_scale == 1.5

        # Reset
        SupportCockpitApp.zoom_font(app_mock, 0.0, reset=True)
        assert app_mock.profile.ui_settings.font_scale == 1.0

    ctk.set_widget_scaling(1.0)

