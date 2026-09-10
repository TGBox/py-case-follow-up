"""Tests for ensuring the application window reliably starts and remains in maximized/fullscreen mode."""

from pathlib import Path
import pytest
import customtkinter as ctk

from config import AppConfig
from services.storage_service import StorageService
from ui.app import SupportCockpitApp


@pytest.fixture
def app_config(tmp_path: Path) -> AppConfig:
    config = AppConfig(workspace_dir=tmp_path, username="test_agent")
    storage = StorageService(config)
    profile = storage.load_profile()
    storage.save_profile(profile)
    return config


def test_app_starts_in_zoomed_fullscreen(app_config: AppConfig):
    """Verifies that SupportCockpitApp starts automatically in zoomed (maximized) state."""
    app = SupportCockpitApp(app_config)
    try:
        app.update()
        assert app.state() == "zoomed"
        # Ensure it expanded beyond the minsize (900x650)
        assert app.winfo_width() >= 1024
        assert app.winfo_height() >= 700
    finally:
        app.destroy()


def test_app_starts_zoomed_with_custom_font_scale(app_config: AppConfig):
    """Verifies that non-default font scale does not clamp window dimensions to minsize."""
    storage = StorageService(app_config)
    profile = storage.load_profile()
    profile.ui_settings.font_scale = 1.25
    storage.save_profile(profile)

    app = SupportCockpitApp(app_config)
    try:
        app.update()
        assert app.state() == "zoomed"
        assert app.winfo_width() >= 1024
        assert app.winfo_height() >= 700
    finally:
        app.destroy()


def test_app_allows_restore_down_to_normal_state(app_config: AppConfig):
    """Verifies that users can freely unmaximize (Restore Down) without being forced back to zoomed."""
    app = SupportCockpitApp(app_config)
    try:
        app.update()
        assert app.state() == "zoomed"

        # User unmaximizes window
        app.state("normal")
        app.update()
        assert app.state() == "normal"
    finally:
        app.destroy()


def test_app_font_zoom_maintains_zoomed_state(app_config: AppConfig):
    """Verifies that dynamically adjusting font scale preserves zoomed state."""
    app = SupportCockpitApp(app_config)
    try:
        app.update()
        assert app.state() == "zoomed"
        initial_width = app.winfo_width()

        app.zoom_font(0.1)
        app.update()
        assert app.state() == "zoomed"
        assert app.winfo_width() == initial_width
    finally:
        app.destroy()
