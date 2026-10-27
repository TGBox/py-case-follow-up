"""Tags and Programmbereiche are listed alphabetically; a tag just added in the
"new case" dialog stays at the end until the dialog is opened again."""

from typing import Any
from unittest.mock import patch

import customtkinter as ctk
import pytest

from models.profile import UserProfile
from utils.sorting import alpha_sorted


def _all_widgets(parent):
    for child in parent.winfo_children():
        yield child
        yield from _all_widgets(child)


def _shown_in_order(container, names):
    """The names as they appear top to bottom in the container's labels."""
    texts = [w.cget("text") for w in _all_widgets(container) if isinstance(w, ctk.CTkLabel)]
    return [n for t in texts for n in names if t.endswith(n)]


@pytest.mark.parametrize("items, expected", [
    (["Zahn", "abrechnung", "Berechtigung"], ["abrechnung", "Berechtigung", "Zahn"]),
    # Umlauts sort like their base letter, not after "z".
    (["Zahn", "Ärzte", "Arzt", "Übergabe", "Termin"], ["Arzt", "Ärzte", "Termin", "Übergabe", "Zahn"]),
    ([], []),
])
def test_alpha_sorted(items, expected):
    assert alpha_sorted(items) == expected


def test_loaded_profile_lists_are_sorted():
    profile = UserProfile.from_dict({"available_tags": ["PVS", "Abrechnung", "Hardware"],
                                     "available_module_tags": ["Terminkalender", "Fakturaübersicht"]})
    assert profile.available_tags == ["Abrechnung", "Hardware", "PVS"]
    assert profile.available_module_tags == ["Fakturaübersicht", "Terminkalender"]


def _new_case_dialog(parent, tags, added):
    from ui.dialogs.new_case_dialog import NewCaseDialog
    return NewCaseDialog(parent, customers=[], schemas=[], created_by="Tester", on_case_created=lambda c: None,
                         available_tags=tags, on_tag_added=added.append)


def test_a_new_tag_stays_at_the_end_until_the_dialog_is_opened_again(root):
    profile_tags = ["PVS", "Abrechnung", "Hardware"]
    added: list[str] = []

    dlg = _new_case_dialog(root, profile_tags, added)
    assert dlg.available_tags == ["Abrechnung", "Hardware", "PVS"]

    with patch("customtkinter.CTkInputDialog.get_input", return_value="Drucker"):
        dlg.open_quick_add_tag()
    assert dlg.available_tags == ["Abrechnung", "Hardware", "PVS", "Drucker"]
    assert added == ["Drucker"]
    dlg.destroy()

    profile_tags.append("Drucker")  # what the app does in on_tag_added
    reopened = _new_case_dialog(root, profile_tags, added)
    assert reopened.available_tags == ["Abrechnung", "Drucker", "Hardware", "PVS"]
    reopened.destroy()


def test_tag_management_lists_tags_and_modules_alphabetically(root, storage):
    from ui.dialogs.tag_management_dialog import TagManagementDialog

    profile = UserProfile()
    profile.available_tags = ["PVS", "Abrechnung"]
    profile.available_module_tags = ["Terminkalender", "Abrechnung", "Fakturaübersicht"]
    dialog = TagManagementDialog(root, profile=profile, storage_service=storage, on_tags_updated=lambda: None)

    dialog.new_tag_entry.insert(0, "Hardware")
    dialog.on_add_tag()
    root.update_idletasks()

    assert _shown_in_order(dialog.tags_scroll, ["PVS", "Abrechnung", "Hardware"]) == ["Abrechnung", "Hardware", "PVS"]
    assert _shown_in_order(dialog.modules_scroll, ["Terminkalender", "Abrechnung", "Fakturaübersicht"]) == \
        ["Abrechnung", "Fakturaübersicht", "Terminkalender"]
    dialog.destroy()


def test_module_picker_lists_programmbereiche_alphabetically(root):
    from ui.widgets.dynamic_form_widget import ModuleTagPickerPopup

    popup: Any = ModuleTagPickerPopup(parent=root, available_tags=["Terminkalender", "Abrechnung"],
                                      selected_tags=[], on_apply=lambda t: None)
    assert popup.available_tags == ["Abrechnung", "Terminkalender"]
    popup.destroy()
