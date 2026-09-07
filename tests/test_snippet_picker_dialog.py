"""Tests for src/ui/dialogs/snippet_picker_dialog.py (SnippetPickerDialog).

Had ZERO test coverage before (confirmed via a test-coverage audit)."""

from pathlib import Path
import customtkinter as ctk
import pytest

from models.snippet import Snippet
from services.snippet_service import SnippetService
from ui.dialogs.snippet_picker_dialog import SnippetPickerDialog


@pytest.fixture
def app():
    a = ctk.CTk()
    a.withdraw()
    yield a
    try:
        a.destroy()
    except Exception:
        pass


@pytest.fixture
def service(tmp_path: Path) -> SnippetService:
    svc = SnippetService(workspace_dir=tmp_path)
    # Replace the (translated, unpredictable) default seed data with fixed
    # snippets so the tests don't depend on the current locale content.
    svc.snippets = [
        Snippet(snippet_id="S-1", title="Screenshot anfordern", category="Rückfrage",
                content="Bitte senden Sie uns einen Screenshot.", tags=["screenshot", "fehler"]),
        Snippet(snippet_id="S-2", title="PVS neustarten", category="Anleitung",
                content="1. PVS beenden.\n2. PVS neu starten.", tags=["pvs", "neustart"],
                shortcut="<Control-Alt-1>"),
        Snippet(snippet_id="S-3", title="Fallabschluss", category="Standardantwort",
                content="Vielen Dank, der Fall ist gelöst.", tags=["abschluss"]),
    ]
    svc.save_snippets()
    return svc


def test_dialog_lists_all_snippets_initially(app, service):
    dialog = SnippetPickerDialog(app, snippet_service=service, on_snippet_selected=lambda text: None)
    dialog.update_idletasks()

    cards = [
        w for w in dialog.list_scroll.winfo_children()
        if isinstance(w, ctk.CTkFrame)
    ]
    assert len(cards) == 3

    dialog.destroy()


def test_select_snippet_fills_preview_and_enables_insert_button(app, service):
    dialog = SnippetPickerDialog(app, snippet_service=service, on_snippet_selected=lambda text: None)
    dialog.update_idletasks()

    target = next(s for s in service.get_all_snippets() if s.snippet_id == "S-2")
    dialog.select_snippet(target)

    assert dialog.selected_snippet is target
    assert dialog.preview_textbox.get("1.0", "end").strip() == target.content
    assert dialog.insert_btn.cget("state") == "normal"

    dialog.destroy()


def test_insert_button_disabled_until_a_snippet_is_selected(app, service):
    dialog = SnippetPickerDialog(app, snippet_service=service, on_snippet_selected=lambda text: None)
    dialog.update_idletasks()

    assert dialog.insert_btn.cget("state") == "disabled"

    dialog.destroy()


def test_on_click_insert_invokes_callback_with_selected_content_and_closes(app, service):
    received = []

    dialog = SnippetPickerDialog(app, snippet_service=service, on_snippet_selected=lambda text: received.append(text))
    dialog.update_idletasks()

    target = next(s for s in service.get_all_snippets() if s.snippet_id == "S-3")
    dialog.select_snippet(target)
    dialog.on_click_insert()

    assert received == [target.content]


def test_on_click_insert_does_nothing_when_nothing_selected(app, service):
    received = []
    dialog = SnippetPickerDialog(app, snippet_service=service, on_snippet_selected=lambda text: received.append(text))
    dialog.update_idletasks()

    dialog.on_click_insert()

    assert received == []
    dialog.destroy()


def test_search_filters_the_visible_snippet_list(app, service):
    dialog = SnippetPickerDialog(app, snippet_service=service, on_snippet_selected=lambda text: None)
    dialog.update_idletasks()

    dialog.search_entry.insert(0, "PVS")
    dialog.refresh_snippet_list()

    cards = [w for w in dialog.list_scroll.winfo_children() if isinstance(w, ctk.CTkFrame)]
    assert len(cards) == 1

    dialog.destroy()


def test_search_with_no_matches_shows_placeholder_label(app, service):
    dialog = SnippetPickerDialog(app, snippet_service=service, on_snippet_selected=lambda text: None)
    dialog.update_idletasks()

    dialog.search_entry.insert(0, "zzz-nonexistent-query")
    dialog.refresh_snippet_list()

    cards = [w for w in dialog.list_scroll.winfo_children() if isinstance(w, ctk.CTkFrame)]
    labels = [w for w in dialog.list_scroll.winfo_children() if isinstance(w, ctk.CTkLabel)]
    assert len(cards) == 0
    assert len(labels) == 1

    dialog.destroy()


def test_category_filter_narrows_the_list(app, service):
    dialog = SnippetPickerDialog(app, snippet_service=service, on_snippet_selected=lambda text: None)
    dialog.update_idletasks()

    dialog.cat_combo.set("Anleitung")
    dialog.refresh_snippet_list()

    cards = [w for w in dialog.list_scroll.winfo_children() if isinstance(w, ctk.CTkFrame)]
    assert len(cards) == 1

    dialog.destroy()
