"""Adversarial stress tests for Milestone 4 & 5 (dialog string extraction & live language switching).

Covers the dialog layer that M3's adversarial suite does not reach:

1. BaseDialog window contract - title, Escape binding, close protocol, modality
2. ConfirmDialog semantics - confirm vs. cancel vs. Escape, Enter as default action
3. Destructive actions - nothing is deleted unless the confirmation was accepted
4. Unsaved-changes guard - dirty detection, and a declined discard keeps the dialog open
5. Live relabelling - register_i18n / refresh_ui_labels across DE, EN, SV including
   window titles, rapid cycling with dialogs open, registry pruning and listener leaks
6. Lazy view construction in the app shell - only the active layout is built
"""

from pathlib import Path
from typing import Any

import customtkinter as ctk
import pytest

from config import AppConfig
from enums import LayoutMode, get_layout_display
from models.profile import UserProfile
from models.snippet import Snippet
from services.i18n_service import get_i18n, tr
from services.snippet_service import SnippetService
from services.storage_service import StorageService


@pytest.fixture(autouse=True)
def reset_i18n_language():
    """Every test starts and ends with German active."""
    i18n = get_i18n()
    i18n.current_language = "de"
    yield
    i18n.current_language = "de"


@pytest.fixture
def headless_root():
    root = ctk.CTk()
    root.withdraw()
    yield root
    try:
        root.destroy()
    except Exception:
        pass


@pytest.fixture
def storage(tmp_path: Path):
    return StorageService(AppConfig(workspace_dir=tmp_path))


def _tag_dialog(root, storage_service, profile):
    from ui.dialogs.tag_management_dialog import TagManagementDialog

    dlg = TagManagementDialog(
        root,
        profile=profile,
        storage_service=storage_service,
        on_tags_updated=lambda: None,
    )
    dlg.update_idletasks()
    return dlg


# ============================================================================
# Section 1: BaseDialog window contract
# ============================================================================

class TestBaseDialogWindowContract:
    """Every dialog inherits the same window setup, keyboard and close behaviour."""

    def test_dialog_has_title_escape_binding_and_close_protocol(self, headless_root, storage):
        profile = UserProfile()
        dlg = _tag_dialog(headless_root, storage, profile)

        assert dlg.wm_title().strip(), "dialog opened without a window title"
        # Tk reports the binding in its normalised spelling, so accept both.
        bound = dlg.bind()
        assert any(seq in bound for seq in ("<Escape>", "<Key-Escape>")), (
            f"BaseDialog did not install the Escape binding, bound sequences: {bound}"
        )
        assert dlg.protocol("WM_DELETE_WINDOW"), "WM_DELETE_WINDOW handler missing"

        dlg.destroy()

    def test_escape_closes_dialog(self, headless_root, storage):
        profile = UserProfile()
        dlg = _tag_dialog(headless_root, storage, profile)

        dlg._on_escape()
        headless_root.update_idletasks()

        assert not dlg.winfo_exists(), "Escape did not close the dialog"

    def test_close_dialog_releases_grab_and_destroys(self, headless_root, storage):
        profile = UserProfile()
        dlg = _tag_dialog(headless_root, storage, profile)

        dlg.close_dialog()
        headless_root.update_idletasks()

        assert not dlg.winfo_exists()


# ============================================================================
# Section 2: ConfirmDialog semantics
# ============================================================================

class TestConfirmDialogSemantics:
    """The confirmation must never report success unless it was explicitly accepted."""

    def _confirm(self, parent):
        from ui.dialogs.confirm_dialog import ConfirmDialog

        dlg = ConfirmDialog(parent, "Wirklich löschen?")
        dlg.update_idletasks()
        return dlg

    def test_result_is_false_before_any_interaction(self, headless_root):
        dlg = self._confirm(headless_root)
        assert dlg.result is False
        dlg.destroy()

    def test_confirm_sets_result_and_closes(self, headless_root):
        dlg = self._confirm(headless_root)
        dlg.on_confirm()
        headless_root.update_idletasks()

        assert dlg.result is True
        assert not dlg.winfo_exists()

    def test_cancel_and_escape_keep_result_false(self, headless_root):
        for closer in ("request_close", "_on_escape"):
            dlg = self._confirm(headless_root)
            getattr(dlg, closer)()
            headless_root.update_idletasks()

            assert dlg.result is False, f"{closer} must not confirm the action"
            assert not dlg.winfo_exists()

    def test_enter_triggers_default_action(self, headless_root):
        dlg = self._confirm(headless_root)
        dlg._on_default_action()
        headless_root.update_idletasks()

        assert dlg.result is True, "Enter did not trigger the primary action"

    def test_enter_ignored_while_multiline_field_has_focus(self, headless_root):
        dlg = self._confirm(headless_root)
        textbox = ctk.CTkTextbox(dlg)
        dlg.focus_get = lambda: textbox  # type: ignore[method-assign]

        result = dlg._on_default_action()

        assert result is None, "Enter must fall through to a multi-line field"
        assert dlg.result is False, "Enter inside a textbox must not confirm"
        dlg.destroy()

    def test_notice_has_no_cancel_button(self, headless_root):
        from ui.dialogs.confirm_dialog import ConfirmDialog

        dlg = ConfirmDialog(headless_root, "Hinweis", show_cancel=False)
        dlg.update_idletasks()

        buttons = [
            child
            for container in dlg.winfo_children()
            for child in container.winfo_children()
            if isinstance(child, ctk.CTkButton)
        ]
        assert len(buttons) == 1, "a notice must offer exactly one button"
        dlg.destroy()


# ============================================================================
# Section 3: Destructive actions require an accepted confirmation
# ============================================================================

class TestDestructiveActionsRequireConfirmation:
    """A declined confirmation must leave the data untouched."""

    @pytest.fixture
    def patched_confirm(self, monkeypatch: pytest.MonkeyPatch):
        """Replaces ask_confirmation; returns a setter for the answer plus a call log."""
        import ui.dialogs.confirm_dialog as confirm_mod

        state: dict[str, Any] = {"answer": False, "calls": []}

        def fake_ask(parent, message, **kwargs):
            state["calls"].append(message)
            return state["answer"]

        monkeypatch.setattr(confirm_mod, "ask_confirmation", fake_ask)
        return state

    def test_declined_tag_deletion_keeps_the_tag(self, headless_root, storage, patched_confirm):
        profile = UserProfile()
        profile.available_tags = ["Schnittstelle", "Abrechnung"]
        dlg = _tag_dialog(headless_root, storage, profile)

        patched_confirm["answer"] = False
        dlg.confirm_delete_tag("Schnittstelle")

        assert "Schnittstelle" in profile.available_tags
        assert patched_confirm["calls"], "no confirmation was requested before deleting"
        dlg.destroy()

    def test_accepted_tag_deletion_removes_the_tag(self, headless_root, storage, patched_confirm):
        profile = UserProfile()
        profile.available_tags = ["Schnittstelle", "Abrechnung"]
        dlg = _tag_dialog(headless_root, storage, profile)

        patched_confirm["answer"] = True
        dlg.confirm_delete_tag("Schnittstelle")

        assert "Schnittstelle" not in profile.available_tags
        assert "Abrechnung" in profile.available_tags
        dlg.destroy()

    def test_declined_module_deletion_keeps_the_module(self, headless_root, storage, patched_confirm):
        profile = UserProfile()
        profile.available_module_tags = ["Rezeptdruck", "Abrechnung"]
        dlg = _tag_dialog(headless_root, storage, profile)

        patched_confirm["answer"] = False
        dlg.confirm_delete_module("Rezeptdruck")

        assert "Rezeptdruck" in profile.available_module_tags
        dlg.destroy()

    def test_snippet_deletion_respects_the_answer(self, headless_root, tmp_path: Path, patched_confirm):
        from ui.dialogs.snippet_management_dialog import SnippetManagementDialog

        service = SnippetService(workspace_dir=tmp_path)
        service.add_or_update_snippet(Snippet(snippet_id="S-1", title="Begrüßung", content="Hallo"))

        dlg = SnippetManagementDialog(headless_root, snippet_service=service, on_snippets_updated=lambda: None)
        dlg.update_idletasks()
        dlg.selected_snippet = service.get_all_snippets()[0]

        patched_confirm["answer"] = False
        dlg.confirm_click_delete()
        assert any(s.snippet_id == "S-1" for s in service.get_all_snippets())

        patched_confirm["answer"] = True
        dlg.selected_snippet = next(s for s in service.get_all_snippets() if s.snippet_id == "S-1")
        dlg.confirm_click_delete()
        assert not any(s.snippet_id == "S-1" for s in service.get_all_snippets())

        dlg.destroy()

    def test_last_schema_cannot_be_deleted(self, headless_root, storage, monkeypatch: pytest.MonkeyPatch):
        from ui.dialogs.schema_builder_dialog import SchemaBuilderDialog
        import ui.dialogs.confirm_dialog as confirm_mod

        notices: list[str] = []
        monkeypatch.setattr(confirm_mod, "show_notice", lambda parent, message, **kw: notices.append(message))
        monkeypatch.setattr(confirm_mod, "ask_confirmation", lambda *a, **k: True)

        from models.schema import QuestionSchema
        from services.schema_service import SchemaService

        # Build the schema here instead of loading it: a tmp workspace has no
        # data_examples folder, so storage would hand back an empty list.
        only_schema = QuestionSchema(schema_id="S-ONLY", display_name="Einziges Formular")
        dlg = SchemaBuilderDialog(
            headless_root,
            schemas=[only_schema],
            schema_service=SchemaService(storage),
            on_schemas_updated=lambda s: None,
        )
        dlg.update_idletasks()

        dlg.confirm_delete_schema()

        assert len(dlg.schemas) == 1, "the last remaining schema must not be deletable"
        assert notices, "the user got no explanation why nothing happened"
        dlg.destroy()


# ============================================================================
# Section 4: Unsaved changes guard
# ============================================================================

class TestUnsavedChangesGuard:
    """Closing a dialog with typed-in content must ask first."""

    def test_dirty_detection_and_mark_clean(self, headless_root, storage):
        profile = UserProfile()
        dlg = _tag_dialog(headless_root, storage, profile)
        dlg.enable_unsaved_guard()

        assert dlg.is_dirty() is False

        dlg.new_tag_entry.insert(0, "Neuer Tag")
        assert dlg.is_dirty() is True, "typed text was not detected as a change"

        dlg.mark_clean()
        assert dlg.is_dirty() is False, "mark_clean did not reset the baseline"

        dlg.destroy()

    def test_guard_is_off_until_enabled(self, headless_root, storage):
        profile = UserProfile()
        dlg = _tag_dialog(headless_root, storage, profile)

        dlg.new_tag_entry.insert(0, "Ohne Guard")
        assert dlg.is_dirty() is False, "the guard must stay off until enable_unsaved_guard()"
        dlg.destroy()

    def test_declined_discard_keeps_dialog_open(self, headless_root, storage, monkeypatch: pytest.MonkeyPatch):
        import ui.dialogs.confirm_dialog as confirm_mod

        profile = UserProfile()
        dlg = _tag_dialog(headless_root, storage, profile)
        dlg.enable_unsaved_guard()
        dlg.new_tag_entry.insert(0, "Nicht verlieren")

        monkeypatch.setattr(confirm_mod, "ask_confirmation", lambda *a, **k: False)
        dlg.request_close()
        headless_root.update_idletasks()
        assert dlg.winfo_exists(), "a declined discard must keep the dialog open"

        monkeypatch.setattr(confirm_mod, "ask_confirmation", lambda *a, **k: True)
        dlg.request_close()
        headless_root.update_idletasks()
        assert not dlg.winfo_exists(), "an accepted discard must close the dialog"


# ============================================================================
# Section 5: Live relabelling of open dialogs
# ============================================================================

class TestDialogLiveRelabelling:
    """register_i18n plus refresh_ui_labels must retranslate an open dialog."""

    def test_registry_is_populated(self, headless_root, storage):
        profile = UserProfile()
        dlg = _tag_dialog(headless_root, storage, profile)

        assert getattr(dlg, "_i18n_widgets", []), "no widget registered its translation key"
        dlg.destroy()

    def test_widget_texts_follow_language_switch(self, headless_root, storage):
        i18n = get_i18n()
        profile = UserProfile()
        dlg = _tag_dialog(headless_root, storage, profile)

        german = [w.cget(attr) for w, attr, *_ in dlg._i18n_widgets if w.winfo_exists()]

        i18n.current_language = "en"
        headless_root.update_idletasks()
        english = [w.cget(attr) for w, attr, *_ in dlg._i18n_widgets if w.winfo_exists()]

        assert any(a != b for a, b in zip(german, english, strict=False)), "no label changed on the language switch"

        i18n.current_language = "de"
        headless_root.update_idletasks()
        back = [w.cget(attr) for w, attr, *_ in dlg._i18n_widgets if w.winfo_exists()]
        assert back == german, "switching back did not restore the German labels"

        dlg.destroy()

    def test_window_title_follows_language_switch(self, headless_root, storage):
        i18n = get_i18n()
        profile = UserProfile()
        dlg = _tag_dialog(headless_root, storage, profile)

        german_title = dlg.wm_title()
        i18n.current_language = "en"
        headless_root.update_idletasks()

        assert dlg.wm_title() != german_title, "the window title did not follow the language"
        dlg.destroy()

    def test_all_three_languages_produce_distinct_labels(self, headless_root, storage):
        i18n = get_i18n()
        profile = UserProfile()
        dlg = _tag_dialog(headless_root, storage, profile)

        seen = {}
        for lang in ("de", "en", "sv"):
            i18n.current_language = lang
            headless_root.update_idletasks()
            seen[lang] = dlg.wm_title()

        assert len({v for v in seen.values()}) >= 2, f"titles did not vary across languages: {seen}"
        dlg.destroy()

    def test_rapid_language_cycling_with_open_dialogs(self, headless_root, storage):
        i18n = get_i18n()
        profile = UserProfile()
        dialogs = [_tag_dialog(headless_root, storage, profile) for _ in range(2)]

        langs = ["de", "en", "sv"]
        for i in range(30):
            i18n.current_language = langs[i % len(langs)]
        headless_root.update_idletasks()

        for dlg in dialogs:
            assert dlg.winfo_exists(), "a dialog died during rapid language cycling"
            dlg.destroy()

    def test_destroyed_widgets_are_pruned_from_the_registry(self, headless_root, storage):
        i18n = get_i18n()
        profile = UserProfile()
        dlg = _tag_dialog(headless_root, storage, profile)

        # Re-rendering the tag list destroys and recreates its rows.
        before = len(dlg._i18n_widgets)
        dlg.render_tags_list()
        dlg.render_tags_list()
        headless_root.update_idletasks()

        i18n.current_language = "en"
        headless_root.update_idletasks()

        alive = [entry for entry in dlg._i18n_widgets if entry[0].winfo_exists()]
        assert len(alive) == len(dlg._i18n_widgets), "registry still holds destroyed widgets"
        assert before > 0

        dlg.destroy()

    def test_closing_a_dialog_unregisters_its_listener(self, headless_root, storage):
        i18n = get_i18n()
        profile = UserProfile()
        baseline = len(i18n._listeners)

        dlg = _tag_dialog(headless_root, storage, profile)
        assert len(i18n._listeners) == baseline + 1, "dialog did not subscribe to language changes"

        dlg.destroy()
        headless_root.update_idletasks()
        assert len(i18n._listeners) == baseline, "listener leaked after the dialog was closed"

    def test_repeated_open_and_close_does_not_leak_listeners(self, headless_root, storage):
        i18n = get_i18n()
        profile = UserProfile()
        baseline = len(i18n._listeners)

        for _ in range(10):
            dlg = _tag_dialog(headless_root, storage, profile)
            dlg.destroy()
        headless_root.update_idletasks()

        assert len(i18n._listeners) == baseline, "listeners accumulated over repeated dialog cycles"

    def test_language_switch_after_close_does_not_raise(self, headless_root, storage):
        i18n = get_i18n()
        profile = UserProfile()
        dlg = _tag_dialog(headless_root, storage, profile)
        dlg.destroy()
        headless_root.update_idletasks()

        for lang in ("en", "sv", "de"):
            i18n.current_language = lang  # must not raise on the dead dialog

    def test_help_dialog_articles_follow_language(self, headless_root):
        from ui.dialogs.help_dialog import HelpDialog

        i18n = get_i18n()
        dlg = HelpDialog(headless_root)
        dlg.update_idletasks()

        german_titles = [a["title"] for a in dlg.articles]
        assert german_titles

        i18n.current_language = "en"
        headless_root.update_idletasks()
        english_titles = [a["title"] for a in dlg.articles]

        assert len(english_titles) == len(german_titles)
        assert any(a != b for a, b in zip(german_titles, english_titles, strict=False)), "help articles stayed German"

        dlg.destroy()


# ============================================================================
# Section 6: Lazy view construction in the app shell
# ============================================================================

class TestLazyViewConstruction:
    """Only the layout the user actually sees is built."""

    def test_only_the_default_layout_is_built_on_startup(self, tmp_path: Path):
        from ui.app import SupportCockpitApp

        config = AppConfig(workspace_dir=tmp_path, username="test_agent")
        app = SupportCockpitApp(config)
        app.withdraw()
        try:
            built = [k for k in ("COCKPIT", "BOARD", "TABLE", "ANALYTICS") if app.is_view_built(k)]
            assert len(built) == 1, f"expected exactly one view at startup, got {built}"

            app.switch_layout(get_layout_display(LayoutMode.BOARD.value))
            assert app.is_view_built(LayoutMode.BOARD.value)

            app.switch_layout(get_layout_display(LayoutMode.ANALYTICS.value))
            assert app.is_view_built(LayoutMode.ANALYTICS.value)
        finally:
            try:
                app.destroy()
            except Exception:
                pass

    def test_switching_all_layouts_keeps_views_cached(self, tmp_path: Path):
        from ui.app import SupportCockpitApp

        config = AppConfig(workspace_dir=tmp_path, username="test_agent")
        app = SupportCockpitApp(config)
        app.withdraw()
        try:
            for value in ("BOARD", "TABLE", "ANALYTICS", "COCKPIT"):
                app.switch_layout(get_layout_display(value))
            first = app.board_view
            app.switch_layout(get_layout_display(LayoutMode.BOARD.value))
            assert app.board_view is first, "the view was rebuilt instead of reused"
        finally:
            try:
                app.destroy()
            except Exception:
                pass


def test_tr_is_importable_for_dialog_defaults():
    """Guards the import the dialogs rely on for their in-code fallbacks."""
    assert tr("common.save", "Speichern")
