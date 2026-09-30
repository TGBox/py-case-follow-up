"""Hoehe des Eingabefelds "Neue Notiz" in der Timeline: per Griff verstellbar,
im Profil gespeichert (ui_settings.custom_textbox_heights) und beim
Zuruecksetzen der Spaltenbreiten mit zurueckgesetzt."""
from types import SimpleNamespace
from unittest.mock import MagicMock

import customtkinter as ctk
import pytest

from constants import (
    TEXTBOX_HEIGHT_SM,
    TIMELINE_NOTE_HEIGHT_KEY,
    TIMELINE_NOTE_MAX_HEIGHT,
    TIMELINE_NOTE_MIN_HEIGHT,
)
from models.profile import UISettings, UserProfile
from ui.widgets.timeline_widget import TimelineWidget


@pytest.fixture
def root():
    r = ctk.CTk()
    r.withdraw()
    yield r
    try:
        r.destroy()
    except Exception:
        pass


def _widget(root, profile=None, storage=None):
    return TimelineWidget(root, "Tester", lambda _e: None, profile=profile, storage_service=storage)


def _drag(handle, dy: int):
    handle.on_press(SimpleNamespace(y_root=100))
    handle.on_drag(SimpleNamespace(y_root=100 + dy))
    handle.on_release(SimpleNamespace(y_root=100 + dy))


def test_default_height_without_stored_value(root):
    w = _widget(root, profile=UserProfile())
    assert int(w.note_textbox.cget("height")) == TEXTBOX_HEIGHT_SM


def test_stored_height_is_applied(root):
    p = UserProfile()
    p.ui_settings.custom_textbox_heights[TIMELINE_NOTE_HEIGHT_KEY] = 180
    w = _widget(root, profile=p)
    assert int(w.note_textbox.cget("height")) == 180


def test_stored_height_is_clamped(root):
    p = UserProfile()
    p.ui_settings.custom_textbox_heights[TIMELINE_NOTE_HEIGHT_KEY] = 99999
    assert int(_widget(root, profile=p).note_textbox.cget("height")) == TIMELINE_NOTE_MAX_HEIGHT


def test_drag_saves_height_to_profile_without_touching_form_default(root):
    p = UserProfile()
    form_default = p.ui_settings.textbox_height
    storage = MagicMock()
    w = _widget(root, profile=p, storage=storage)

    _drag(w.note_resize_handle, 100)

    expected = TEXTBOX_HEIGHT_SM + 100
    assert int(w.note_textbox.cget("height")) == expected
    assert p.ui_settings.custom_textbox_heights[TIMELINE_NOTE_HEIGHT_KEY] == expected
    assert p.ui_settings.textbox_height == form_default
    storage.save_profile.assert_called_once_with(p)


def test_drag_respects_min_height(root):
    p = UserProfile()
    w = _widget(root, profile=p, storage=MagicMock())
    _drag(w.note_resize_handle, -500)
    assert p.ui_settings.custom_textbox_heights[TIMELINE_NOTE_HEIGHT_KEY] == TIMELINE_NOTE_MIN_HEIGHT


def test_drag_is_scaling_independent(root, monkeypatch):
    """Bei 150 % Schriftskalierung darf ein Klick ohne Bewegung die Hoehe nicht aendern."""
    p = UserProfile()
    w = _widget(root, profile=p, storage=MagicMock())
    monkeypatch.setattr(w.note_textbox, "_get_widget_scaling", lambda: 1.5)
    _drag(w.note_resize_handle, 0)
    assert p.ui_settings.custom_textbox_heights[TIMELINE_NOTE_HEIGHT_KEY] == TEXTBOX_HEIGHT_SM
    _drag(w.note_resize_handle, 150)  # 150 echte Pixel = 100 unskalierte
    assert p.ui_settings.custom_textbox_heights[TIMELINE_NOTE_HEIGHT_KEY] == TEXTBOX_HEIGHT_SM + 100


def test_resize_works_without_profile(root):
    w = _widget(root)
    _drag(w.note_resize_handle, 40)
    assert int(w.note_textbox.cget("height")) == TEXTBOX_HEIGHT_SM + 40


def test_height_survives_profile_round_trip():
    p = UserProfile()
    p.ui_settings.custom_textbox_heights[TIMELINE_NOTE_HEIGHT_KEY] = 222
    restored = UISettings.from_dict(p.ui_settings.to_dict())
    assert restored.custom_textbox_heights[TIMELINE_NOTE_HEIGHT_KEY] == 222


def test_reset_column_widths_restores_default_height(root):
    p = UserProfile()
    p.ui_settings.custom_textbox_heights[TIMELINE_NOTE_HEIGHT_KEY] = 300
    w = _widget(root, profile=p)
    p.ui_settings.reset_column_widths()
    w.apply_stored_note_height(p)
    assert int(w.note_textbox.cget("height")) == TEXTBOX_HEIGHT_SM
