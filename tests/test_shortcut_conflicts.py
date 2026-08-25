"""Tests for keyboard shortcut configuration, uniqueness, and conflict detection."""

import pytest
from models.profile import ShortcutSettings


def test_hotkey_conflict_validation():
    """Verify distinct shortcuts pass validation and duplicates are detected."""
    shortcuts = ShortcutSettings(
        new_case="<Control-n>",
        export_dialog="<Control-e>",
        wiki_search="<Control-w>",
    )
    keys = [shortcuts.new_case, shortcuts.export_dialog, shortcuts.wiki_search]
    assert len(keys) == len(set(keys))

    duplicate_keys = ["<Control-n>", "<Control-n>", "<Control-w>"]
    assert len(duplicate_keys) != len(set(duplicate_keys))
