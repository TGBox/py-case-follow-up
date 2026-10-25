"""Utilities (PII anonymizer, security helpers, icons, ui_utils helpers) and caching/view-switch performance guarantees."""

import contextlib
import os
from pathlib import Path
from unittest.mock import MagicMock, patch

import customtkinter as ctk
import pytest

from constants import (
    COLOR_ICON_WHITE, ICON_KEY_BELL, ICON_KEY_COPY, ICON_KEY_HELP, ICON_KEY_QUIT, ICON_KEY_THEME, ICON_KEY_USER,
    ICON_SIZE_ACTION, ICON_SIZE_HEADER,
)
from models.case import Case, CaseCustomer
from models.profile import UISettings
from services.anonymizer_service import PiiAnonymizer
from utils.icon_utils import clear_icon_cache, get_icon
from utils.security import load_env_file, normalize_url, resolve_secret
from utils.ui_utils import enable_textbox_cursor_autoscroll, get_app_monitor_bounds

ICON_KEYS = [ICON_KEY_USER, ICON_KEY_BELL, ICON_KEY_HELP, ICON_KEY_THEME, ICON_KEY_QUIT, ICON_KEY_COPY]


# --- PII anonymizer --------------------------------------------------------------

def test_anonymizer_masks_email_and_restores():
    anonymizer = PiiAnonymizer(enable_anonymization=True)
    text = "Bitte an dr.mueller@praxis-gesund.de schicken oder unter 089-12345678 anrufen."
    anonymized, mapping = anonymizer.anonymize(text)
    assert "dr.mueller@praxis-gesund.de" not in anonymized
    assert mapping.get("[EMAIL_1]") == "dr.mueller@praxis-gesund.de"
    assert anonymizer.deanonymize(anonymized, mapping) == text


def test_anonymizer_masks_case_context_and_patient_names():
    anonymizer = PiiAnonymizer(enable_anonymization=True)
    case = Case(case_id="FALL-2026-99", customer=CaseCustomer(
        customer_id="KD-100", practice_name="Gemeinschaftspraxis Dr. Med. Sonnenstein",
        contact_person="Frau Sabine Meyer", email="kontakt@sonnenstein.de", phone="030-998877"))
    prompt = ("Zusammenfassung für FALL-2026-99 von Gemeinschaftspraxis Dr. Med. Sonnenstein. "
              "Ansprechpartner ist Frau Sabine Meyer (kontakt@sonnenstein.de). "
              "Patient Herr Max Mustermann klagt über Fehler beim PVS-Import.")
    anonymized, mapping = anonymizer.anonymize(prompt, case=case)
    for secret in ("FALL-2026-99", "Gemeinschaftspraxis Dr. Med. Sonnenstein", "Frau Sabine Meyer",
                   "kontakt@sonnenstein.de", "Max Mustermann"):
        assert secret not in anonymized
    assert anonymizer.deanonymize(anonymized, mapping) == prompt


def test_anonymizer_disabled_is_passthrough():
    assert PiiAnonymizer(enable_anonymization=False).anonymize("Hallo dr.test@example.com") == ("Hallo dr.test@example.com", {})


# --- Security helpers ------------------------------------------------------------

def test_load_env_file(tmp_path: Path, monkeypatch):
    load_env_file(tmp_path / "does_not_exist.env")
    load_env_file(tmp_path)  # a directory is ignored, not raised
    monkeypatch.chdir(tmp_path)
    load_env_file(None)  # cwd fallback without .env

    for key in ("TEST_KEY_PLAIN", "TEST_KEY_DQUOTES", "TEST_KEY_SQUOTES", "TEST_KEY_SPACES", "EMPTY_KEY"):
        monkeypatch.delenv(key, raising=False)
    (tmp_path / ".env").write_text(
        "# Comment line\n\nINVALID_LINE_NO_EQUALS\n=VALUE_WITHOUT_KEY\nTEST_KEY_PLAIN=simple_value\n"
        "TEST_KEY_DQUOTES=\"double_quoted\"\nTEST_KEY_SQUOTES='single_quoted'\n"
        "  TEST_KEY_SPACES  =   spaced_value   \nEMPTY_KEY=\n", encoding="utf-8")
    load_env_file(tmp_path / ".env")

    assert os.environ.get("TEST_KEY_PLAIN") == "simple_value"
    assert os.environ.get("TEST_KEY_DQUOTES") == "double_quoted"
    assert os.environ.get("TEST_KEY_SQUOTES") == "single_quoted"
    assert os.environ.get("TEST_KEY_SPACES") == "spaced_value"
    assert os.environ.get("EMPTY_KEY") == ""


@pytest.mark.parametrize("raw, expected", [
    ("", ""), ("   ", ""), (None, ""),
    ("[BookStack](https://wiki.intern.lan/api/)", "https://wiki.intern.lan/api"),
    ("[Dokumentation](http://localhost:8080)", "http://localhost:8080"),
    ("https://support.praxis.de/", "https://support.praxis.de"),
    ("https://support.praxis.de///", "https://support.praxis.de"),
    ("http://192.168.1.100:8000/api", "http://192.168.1.100:8000/api"),
])
def test_normalize_url(raw, expected):
    assert normalize_url(raw) == expected


def test_resolve_secret(monkeypatch):
    monkeypatch.setenv("MY_OLLAMA_KEY", "secret_ollama_123")
    monkeypatch.setenv("ENV_FULL_KEY", "secret_full_456")
    assert resolve_secret("") == ""
    assert resolve_secret("plain_secret_value") == "plain_secret_value"
    assert resolve_secret("ENV_MY_OLLAMA_KEY") == "secret_ollama_123"
    assert resolve_secret("ENV_FULL_KEY") == "secret_full_456"
    assert resolve_secret("ENV_NON_EXISTENT") == ""


# --- Icons -----------------------------------------------------------------------

@pytest.fixture
def icon_cache():
    clear_icon_cache()
    yield
    clear_icon_cache()


@pytest.mark.parametrize("font_missing", [False, True], ids=["mdl2-font", "procedural-fallback"])
def test_get_icon_builds_every_key(icon_cache, font_missing):
    with patch("utils.icon_utils.MDL2_PATH", "C:\\nonexistent_path\\segmdl2.ttf") if font_missing else contextlib.nullcontext():
        clear_icon_cache()
        for key in ICON_KEYS:
            img = get_icon(key, size=ICON_SIZE_ACTION)
            assert isinstance(img, ctk.CTkImage) and img._size == ICON_SIZE_ACTION
    assert isinstance(get_icon(ICON_KEY_BELL, size=ICON_SIZE_HEADER,
                               light_color=COLOR_ICON_WHITE, dark_color=COLOR_ICON_WHITE), ctk.CTkImage)


def test_get_icon_cache(icon_cache):
    img1 = get_icon(ICON_KEY_USER, size=ICON_SIZE_HEADER)
    img2 = get_icon(ICON_KEY_USER, size=ICON_SIZE_HEADER)
    assert img1._light_image is img2._light_image and img1._dark_image is img2._dark_image
    assert get_icon(ICON_KEY_USER, size=(24, 24))._light_image is not img1._light_image
    clear_icon_cache()
    assert get_icon(ICON_KEY_USER, size=ICON_SIZE_HEADER)._light_image is not img1._light_image


def test_icon_renders_in_dark_mode(root, icon_cache):
    """Icons pass an explicit Tk master, otherwise 'image pyimageX does not exist' with several roots."""
    previous = ctk.get_appearance_mode()
    ctk.set_appearance_mode("dark")
    try:
        label = ctk.CTkLabel(root, text="", image=get_icon(ICON_KEY_BELL, size=ICON_SIZE_HEADER))
        label.pack()
        root.update()
        assert getattr(label, "_label", label).cget("image")
    finally:
        ctk.set_appearance_mode(previous)


# --- ui_utils helpers / popup settings -------------------------------------------

def test_popup_display_target_setting():
    data = UISettings().to_dict()
    assert data["popup_display_target"] == "APP_SCREEN"
    restored = UISettings.from_dict({**data, "popup_display_target": "PRIMARY_SCREEN"})
    assert restored.popup_display_target == "PRIMARY_SCREEN"
    assert UISettings.from_dict({**data, "popup_display_target": "INVALID"}).popup_display_target == "APP_SCREEN"
    restored.reset_column_widths()
    assert restored.popup_display_target == "APP_SCREEN"


def _window(x, y, w, h, last_geometry=None):
    win = MagicMock()
    win.winfo_toplevel.return_value = win
    win._last_geometry = last_geometry
    win.winfo_x.return_value, win.winfo_y.return_value = x, y
    win.winfo_width.return_value, win.winfo_height.return_value = w, h
    win.winfo_screenwidth.return_value, win.winfo_screenheight.return_value = 1920, 1080
    return win


@pytest.mark.parametrize("window, expected", [
    (_window(100, 150, 1200, 800), (100, 150, 1200, 800)),
    (_window(-32000, -32000, 1, 1, last_geometry=(250, 300, 1400, 900)), (250, 300, 1400, 900)),  # minimized
])
def test_get_app_monitor_bounds(window, expected):
    assert get_app_monitor_bounds(window) == expected


def test_textbox_cursor_autoscroll_binds_typing_and_click_events(root):
    box = ctk.CTkTextbox(root)
    enable_textbox_cursor_autoscroll(box)
    for event in ("<KeyRelease>", "<KeyPress>", "<ButtonRelease>"):
        assert box._textbox.bind(event)


# --- Caching and volume guarantees -----------------------------------------------

def test_storage_case_cache_and_invalidation(storage):
    c1 = Case(case_id="FALL-001", customer=CaseCustomer(customer_id="C1", practice_name="Praxis A"))
    storage.save_cases([c1])
    loaded = storage.load_cases(use_cache=True)
    assert [c.case_id for c in loaded] == ["FALL-001"]
    assert storage.load_cases(use_cache=True) is loaded

    c1.classification.title = "Updated Title"
    storage.update_single_case(c1)
    assert storage.load_cases(use_cache=True)[0].classification.title == "Updated Title"

    storage.invalidate_cache()
    fresh = storage.load_cases(use_cache=True)
    assert fresh is not loaded and fresh[0].classification.title == "Updated Title"


def test_p2p_diff_and_zip_backup_handle_many_cases(storage, tmp_path):
    from services.p2p_sync_service import P2PSyncService
    from services.zip_backup_service import ZipBackupService

    cases = [Case(case_id=f"BULK-{i:03d}", customer=CaseCustomer(customer_id=f"C-{i}", practice_name=f"Praxis {i}"))
             for i in range(30)]
    storage.save_cases(cases)
    assert len(storage.load_cases()) == 30

    remote = [Case.from_dict(c.to_dict()) for c in cases]
    remote[0].updated_at = "2099-08-25T12:00:00"
    assert len(P2PSyncService(storage).compute_diff(remote)) == 30

    out = tmp_path / "backup.zip"
    assert ZipBackupService.export_backup_zip(storage, out)["file_count"] >= 1
    assert out.exists()


# --- View switching: the old view stays visible until the new one is filled ------
# Reported: switching to the Kanban board flickered (overlapping labels, grey
# column blocks) because the old view was hidden before the new one was built.

def test_the_previous_view_stays_visible_until_the_new_one_is_filled(config, seeded_storage):
    from enums import LayoutMode, get_layout_display
    from ui.app import SupportCockpitApp

    app = SupportCockpitApp(config)
    try:
        app.update()
        order: list[str] = []
        board = app._get_view(LayoutMode.BOARD.value)
        orig_set_cases, orig_forget = board.set_cases, app.active_view.pack_forget
        board.set_cases = lambda *a, **k: (order.append("filled"), orig_set_cases(*a, **k))[1]
        app.active_view.pack_forget = lambda *a, **k: (order.append("hidden"), orig_forget(*a, **k))[1]

        app.switch_layout(get_layout_display(LayoutMode.BOARD.value))
        app.update()
        assert "filled" in order and "hidden" in order
        assert order.index("filled") < order.index("hidden"), order
    finally:
        app.destroy()


def test_switching_to_the_active_layout_does_not_hide_it(config, storage):
    """Otherwise the view blinks when the already selected layout is picked again."""
    from enums import get_layout_display
    from ui.app import SupportCockpitApp

    storage.save_profile(storage.load_profile())
    app = SupportCockpitApp(config)
    try:
        app.update()
        hidden: list[str] = []
        orig_forget = app.active_view.pack_forget
        app.active_view.pack_forget = lambda *a, **k: (hidden.append("x"), orig_forget(*a, **k))[1]
        app.switch_layout(get_layout_display(app._active_layout))
        app.update()
        assert hidden == []
    finally:
        app.destroy()
