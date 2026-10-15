"""Fixtures for the end-to-end flows: start the real app headless on a workspace, clean it up afterwards."""

import tkinter as tk
import traceback
from pathlib import Path

import customtkinter as ctk
import pytest

from config import AppConfig
from e2e_helpers import cancel_pending_afters, is_alive
from services.storage_service import StorageService


@pytest.fixture
def start_app(monkeypatch: pytest.MonkeyPatch):
    """Starts SupportCockpitApp on a workspace like main.py --workspace does; cleans every app up afterwards."""
    from services.tray_service import TrayService
    from services.wiki_sync_service import WikiSyncService
    from ui.app import SupportCockpitApp

    # OS boundaries only: no real tray icon thread, no BookStack request at startup.
    monkeypatch.setattr(TrayService, "start", lambda self, on_restore, on_quit: None)
    monkeypatch.setattr(WikiSyncService, "sync_from_bookstack_async", lambda self, callback=None, mock_client=None: None)

    scaling_before = ctk.ScalingTracker.widget_scaling
    appearance_before = ctk.get_appearance_mode()
    apps: list = []
    callback_errors: list[str] = []

    def record_callback_error(exc, val, tb):
        # A queued <Configure> hitting a widget of an already destroyed dialog is a
        # harmless Tk teardown race (Tk only prints it); everything else fails the test.
        if isinstance(val, tk.TclError) and "invalid command name" in str(val):
            return
        callback_errors.append("".join(traceback.format_exception(exc, val, tb)))

    def _start(workspace: Path):
        config = AppConfig.load_user_config(cli_workspace=workspace)
        storage = StorageService(config)
        storage.perform_daily_backup()
        storage.auto_archive_completed_cases(threshold_days=30)
        app = SupportCockpitApp(config)
        # An exception inside a Tk callback (binding, after-timer) never reaches
        # the test on its own - collect it and fail the test at teardown.
        app.report_callback_exception = record_callback_error
        apps.append(app)
        app.update()
        return app

    yield _start

    for app in apps:
        if is_alive(app):
            try:
                app.on_quit_app()
            except Exception:
                try:
                    app.destroy()
                except Exception:
                    pass
        cancel_pending_afters(app)
    ctk.set_widget_scaling(scaling_before)
    ctk.set_appearance_mode(appearance_before)
    assert not callback_errors, "exception(s) in Tk callbacks:\n" + "\n".join(callback_errors)
