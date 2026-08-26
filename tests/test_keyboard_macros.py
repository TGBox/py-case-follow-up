"""Tests for expanded keyboard macros and custom shortcut settings."""

import pytest
from models.profile import ShortcutSettings, UserProfile
from models.snippet import Snippet


def test_shortcut_settings_defaults_and_serialization():
    s = ShortcutSettings()
    assert s.new_case == "<Control-n>"
    assert s.save_case == "<Control-s>"
    assert s.archive_case == "<Control-Shift-A>"
    assert s.open_settings == "<Control-p>"
    assert s.snippet_picker == "<Control-m>"
    assert s.view_cockpit == "<Control-1>"
    assert s.view_board == "<Control-2>"
    assert s.view_table == "<Control-3>"
    assert s.toggle_theme == "<Control-t>"

    data = s.to_dict()
    restored = ShortcutSettings.from_dict(data)
    assert restored.archive_case == "<Control-Shift-A>"
    assert restored.toggle_theme == "<Control-t>"


def test_shortcut_settings_backward_compatibility():
    old_data = {
        "new_case": "<Control-n>",
        "export_dialog": "<Control-e>",
        "wiki_search": "<Control-w>",
    }
    restored = ShortcutSettings.from_dict(old_data)
    assert restored.new_case == "<Control-n>"
    assert restored.save_case == "<Control-s>"
    assert restored.archive_case == "<Control-Shift-A>"
    assert restored.toggle_theme == "<Control-t>"


def test_snippet_shortcut_serialization():
    snip = Snippet(
        snippet_id="SNIP-10",
        title="Test Macro",
        category="Test",
        content="Hello Macro",
        shortcut="<Control-Alt-9>",
    )
    data = snip.to_dict()
    assert data["shortcut"] == "<Control-Alt-9>"

    restored = Snippet.from_dict(data)
    assert restored.shortcut == "<Control-Alt-9>"


def test_shortcut_conflict_detection_logic():
    app_shortcuts = ShortcutSettings(
        new_case="<Control-n>",
        save_case="<Control-s>",
    )
    snip_1 = Snippet(snippet_id="S1", title="A", content="a", shortcut="<Control-Alt-1>")
    snip_2 = Snippet(snippet_id="S2", title="B", content="b", shortcut="<Control-Alt-2>")

    all_keys = [
        app_shortcuts.new_case,
        app_shortcuts.save_case,
        snip_1.shortcut,
        snip_2.shortcut,
    ]
    # No duplicates
    assert len(all_keys) == len(set(all_keys))

    # Add conflicting key
    snip_3 = Snippet(snippet_id="S3", title="C", content="c", shortcut="<Control-s>")
    conflicting_keys = all_keys + [snip_3.shortcut]
    assert len(conflicting_keys) != len(set(conflicting_keys))
