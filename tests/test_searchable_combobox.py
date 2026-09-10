"""Tests for src/ui/widgets/searchable_combobox.py (SearchableCombobox).

Had ZERO test coverage before (confirmed via a test-coverage audit)."""

import customtkinter as ctk
import pytest

from ui.widgets.searchable_combobox import SearchableCombobox


@pytest.fixture
def app():
    a = ctk.CTk()
    a.withdraw()
    yield a
    try:
        a.destroy()
    except Exception:
        pass


def test_initial_values_select_first_by_default(app):
    combo = SearchableCombobox(app, values=["Praxis A", "Praxis B", "Praxis C"])
    assert combo.get() == "Praxis A"
    assert "Praxis A" in combo.btn.cget("text")


def test_empty_values_shows_placeholder(app):
    combo = SearchableCombobox(app, values=[], placeholder_text="– Bitte wählen –")
    assert combo.get() == ""
    assert "– Bitte wählen –" in combo.btn.cget("text")


def test_set_values_keeps_default_value_if_present(app):
    combo = SearchableCombobox(app, values=["A", "B"])
    combo.set_values(["A", "B", "C"], default_value="C")
    assert combo.get() == "C"


def test_set_values_falls_back_to_first_when_default_missing(app):
    combo = SearchableCombobox(app, values=["A", "B"])
    combo.set_values(["X", "Y"], default_value="Z")  # "Z" not in new values
    assert combo.get() == "X"


def test_set_values_with_empty_list_clears_selection(app):
    combo = SearchableCombobox(app, values=["A", "B"])
    combo.set_values([])
    assert combo.get() == ""


def test_set_and_get_alias_compat(app):
    combo = SearchableCombobox(app, values=["A", "B", "C"])
    combo.set("B")
    assert combo.get() == "B"


def test_open_popover_builds_search_entry_and_option_buttons(app):
    combo = SearchableCombobox(app, values=["Alpha", "Beta", "Gamma"])
    combo.open_popover()

    assert combo._popover is not None
    assert combo._popover.winfo_exists()
    assert combo.search_entry is not None

    option_texts = [
        w.cget("text") for w in combo.options_scroll.winfo_children()
        if isinstance(w, ctk.CTkButton)
    ]
    assert option_texts == ["Alpha", "Beta", "Gamma"]

    combo.close_popover()
    assert combo._popover is None


def test_open_popover_does_nothing_with_no_values(app):
    combo = SearchableCombobox(app, values=[])
    combo.open_popover()
    assert combo._popover is None


def test_toggle_popover_opens_then_closes(app):
    combo = SearchableCombobox(app, values=["A", "B"])
    combo.toggle_popover()
    assert combo._popover is not None

    combo.toggle_popover()
    assert combo._popover is None


def test_search_filters_options_case_insensitively(app):
    combo = SearchableCombobox(app, values=["Praxis Alpha", "Praxis Beta", "Klinik Gamma"])
    combo.open_popover()

    combo.search_entry.insert(0, "praxis")
    combo._on_search_changed()

    option_texts = [
        w.cget("text") for w in combo.options_scroll.winfo_children()
        if isinstance(w, ctk.CTkButton)
    ]
    assert option_texts == ["Praxis Alpha", "Praxis Beta"]


def test_search_with_no_matches_shows_no_results_label(app):
    combo = SearchableCombobox(app, values=["Praxis Alpha"])
    combo.open_popover()

    combo.search_entry.insert(0, "zzz-nonexistent")
    combo._on_search_changed()

    labels = [w for w in combo.options_scroll.winfo_children() if isinstance(w, ctk.CTkLabel)]
    buttons = [w for w in combo.options_scroll.winfo_children() if isinstance(w, ctk.CTkButton)]
    assert len(labels) == 1
    assert len(buttons) == 0


def test_selecting_item_updates_value_closes_popover_and_calls_command(app):
    selected = []
    combo = SearchableCombobox(app, values=["Alpha", "Beta"], command=lambda v: selected.append(v))
    combo.open_popover()

    combo._select_item("Beta")

    assert combo.get() == "Beta"
    assert combo._popover is None
    assert selected == ["Beta"]


def test_enter_pressed_selects_first_filtered_match(app):
    selected = []
    combo = SearchableCombobox(app, values=["Praxis Alpha", "Praxis Beta"], command=lambda v: selected.append(v))
    combo.open_popover()

    combo.search_entry.insert(0, "beta")
    combo._on_enter_pressed()

    assert combo.get() == "Praxis Beta"
    assert selected == ["Praxis Beta"]


def test_enter_pressed_with_no_matches_does_nothing(app):
    selected = []
    combo = SearchableCombobox(app, values=["Praxis Alpha"], command=lambda v: selected.append(v))
    combo.open_popover()

    combo.search_entry.insert(0, "zzz-nonexistent")
    combo._on_enter_pressed()

    assert selected == []
    assert combo.get() == "Praxis Alpha"  # unchanged (default first value)


def test_refresh_ui_labels_updates_placeholder_when_nothing_selected(app):
    combo = SearchableCombobox(app, values=[])
    combo.refresh_ui_labels()
    assert combo.placeholder_text in combo.btn.cget("text")


def test_refresh_ui_labels_does_not_override_an_actual_selection(app):
    combo = SearchableCombobox(app, values=["Alpha"])
    combo.refresh_ui_labels()
    assert "Alpha" in combo.btn.cget("text")
# --- Focus handling after the popover closes ------------------------------
# Regression guard: on Windows the destroyed overrideredirect popover left the
# owning dialog without keyboard activation, so the next entry silently
# swallowed every keystroke until the user clicked another window and back.


def _run_after_immediately(monkeypatch, combo):
    """Executes `combo.after(...)` callbacks synchronously (no mainloop in tests)."""
    monkeypatch.setattr(combo, "after", lambda _ms, func=None, *a: func(*a) if func else None)


def test_close_popover_restores_focus_by_default(app, monkeypatch):
    combo = SearchableCombobox(app, values=["A", "B"])
    combo.open_popover()

    calls = []
    monkeypatch.setattr(combo, "_restore_parent_focus", lambda *a: calls.append(a))

    combo.close_popover()

    assert combo._popover is None
    assert len(calls) == 1


def test_focus_out_closes_popover_without_pulling_focus_back(app, monkeypatch):
    combo = SearchableCombobox(app, values=["A", "B"])
    combo.open_popover()

    calls = []
    monkeypatch.setattr(combo, "_restore_parent_focus", lambda *a: calls.append(a))
    _run_after_immediately(monkeypatch, combo)

    combo._on_focus_out()

    assert combo._popover is None
    assert calls == []  # the user clicked elsewhere on purpose


def test_close_popover_on_already_closed_popover_is_a_noop(app, monkeypatch):
    combo = SearchableCombobox(app, values=["A"])

    calls = []
    monkeypatch.setattr(combo, "_restore_parent_focus", lambda *a: calls.append(a))

    combo.close_popover()

    assert combo._popover is None
    assert calls == []


def test_select_item_hands_focus_to_configured_next_widget(app, monkeypatch):
    next_entry = ctk.CTkEntry(app)
    combo = SearchableCombobox(app, values=["Alpha", "Beta"])
    combo.set_next_focus_widget(next_entry)
    combo.open_popover()

    captured = {}
    monkeypatch.setattr(
        combo,
        "_restore_parent_focus",
        lambda top, prev_grab, focus_target: captured.update(target=focus_target),
    )

    combo._select_item("Beta")

    assert captured["target"] is next_entry


def test_select_item_without_next_widget_keeps_focus_on_picker(app, monkeypatch):
    combo = SearchableCombobox(app, values=["Alpha", "Beta"])
    combo.open_popover()

    captured = {}
    monkeypatch.setattr(
        combo,
        "_restore_parent_focus",
        lambda top, prev_grab, focus_target: captured.update(target=focus_target),
    )

    combo._select_item("Beta")

    assert captured["target"] is None  # falls back to the picker button


def test_restore_parent_focus_reactivates_toplevel(app, monkeypatch):
    combo = SearchableCombobox(app, values=["A"])
    next_entry = ctk.CTkEntry(app)

    events = []
    monkeypatch.setattr(app, "lift", lambda: events.append("lift"))
    monkeypatch.setattr(app, "focus_force", lambda: events.append("focus_force"))
    monkeypatch.setattr(next_entry, "focus_set", lambda: events.append("target"))
    _run_after_immediately(monkeypatch, combo)

    combo._restore_parent_focus(app, None, next_entry)

    assert events == ["lift", "focus_force", "target"]


def test_restore_parent_focus_falls_back_to_button_for_dead_target(app, monkeypatch):
    combo = SearchableCombobox(app, values=["A"])
    dead_entry = ctk.CTkEntry(app)
    dead_entry.destroy()

    focused = []
    monkeypatch.setattr(combo.btn, "focus_set", lambda: focused.append("btn"))
    _run_after_immediately(monkeypatch, combo)

    combo._restore_parent_focus(app, None, dead_entry)

    assert focused == ["btn"]


def test_restore_parent_focus_rearms_a_lost_modal_grab(app, monkeypatch):
    combo = SearchableCombobox(app, values=["A"])

    grabs = []
    monkeypatch.setattr(app, "grab_current", lambda: None)  # grab is gone
    monkeypatch.setattr(app, "grab_set", lambda: grabs.append("grab_set"))
    _run_after_immediately(monkeypatch, combo)

    combo._restore_parent_focus(app, app, None)

    assert grabs == ["grab_set"]


def test_restore_parent_focus_leaves_an_intact_grab_alone(app, monkeypatch):
    combo = SearchableCombobox(app, values=["A"])

    grabs = []
    monkeypatch.setattr(app, "grab_current", lambda: app)  # grab still held
    monkeypatch.setattr(app, "grab_set", lambda: grabs.append("grab_set"))
    _run_after_immediately(monkeypatch, combo)

    combo._restore_parent_focus(app, app, None)

    assert grabs == []
