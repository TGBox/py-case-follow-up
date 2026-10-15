"""Runtime language switching of views, dialogs and the main app without restart."""

from typing import Any, cast

import customtkinter as ctk
import pytest

from services.i18n_service import get_i18n


def _switch(lang: str, *views) -> None:
    get_i18n().current_language = lang
    for view in views:
        view.refresh_ui_labels()


def _tab_texts(tabview) -> dict[str, str]:
    """Visible segment texts keyed by the internal (German) tab name - no public accessor exists."""
    buttons = cast(Any, tabview)._segmented_button._buttons_dict
    return {name: btn.cget("text") for name, btn in buttons.items()}


@pytest.fixture
def services(config, storage):
    from services.attachment_service import AttachmentService
    from services.scoring_service import ScoringService
    from services.wiki_sync_service import WikiSyncService

    profile = storage.load_profile()
    return dict(
        scoring_service=ScoringService(profile.scoring_matrix),
        attachment_service=AttachmentService(config),
        app_config=config,
    ), WikiSyncService(config, profile.wiki_settings)


def test_cockpit_relabels_filters_and_tabs_and_keeps_loaded_case(root, storage, services):
    from models.case import Case, CaseCustomer, Classification, WorkflowStatus
    from ui.views.cockpit_view import CockpitView

    kwargs, wiki = services
    cockpit = CockpitView(parent=root, author_name="Tester", wiki_service=wiki, storage_service=storage, **kwargs)
    case = Case(
        case_id="T-2026-PRESERVE",
        created_at="2026-09-02T10:00:00",
        updated_at="2026-09-02T10:00:00",
        customer=CaseCustomer(practice_name="Praxis Dr. Preserved", contact_person="Dr. Preserved"),
        classification=Classification(title="Preserved Unsaved Ticket Title"),
        workflow_status=WorkflowStatus(is_completed=False),
    )
    cockpit.on_select_case_from_list(case)
    lf = cockpit.left_frame

    expected = {
        # lang: (all, urgent, followup, timeline, attachments, wiki)
        "de": ("Alle", "Dringend", "Wiedervorlage", "Zeitleiste", "Anhänge", "Wiki / Wissensdatenbank"),
        "en": ("All", "Urgent", "Follow-up", "Timeline", "Attachments", "Wiki / Knowledge Base"),
        "sv": ("Alla", "Brådskande", "Uppföljning", "Tidslinje", "Bilagor", "Wiki / Kunskapsbas"),
    }
    for lang in ("de", "en", "sv", "de"):
        _switch(lang, cockpit)
        all_, urgent, followup, timeline, attachments, wiki_txt = expected[lang]
        assert lf.qfilter_all_btn.cget("text") == all_
        assert urgent in lf.qfilter_urgent_btn.cget("text")
        assert followup in lf.qfilter_followup_btn.cget("text")
        tabs = _tab_texts(cockpit.right_tabview)
        assert (tabs["Zeitleiste"], tabs["Anhänge"], tabs["Wiki"]) == (timeline, attachments, wiki_txt)

    # Relabelling must not touch the case being edited.
    assert cockpit.current_case is not None
    assert cockpit.current_case.case_id == "T-2026-PRESERVE"
    assert cockpit.current_case.classification.title == "Preserved Unsaved Ticket Title"
    assert cockpit.current_case.customer.practice_name == "Praxis Dr. Preserved"


def test_table_view_relabels_detail_tabs_and_column_titles(root, services):
    from ui.views.table_view import COL_TITLE_MAP, TableView

    kwargs, _wiki = services
    tv = TableView(parent=root, author_name="Tester", on_case_updated=lambda c: None,
                   on_case_selected=lambda c: None, **kwargs)
    expected = {
        "en": ("Form & Fill", "Timeline", "Attachments", "Practice / Customer ⇅", "Responsibility ⇅"),
        "sv": ("Formulär", "Tidslinje", "Bilagor", "Mottagning / Kund ⇅", "Ansvar ⇅"),
        "de": ("Formular", "Zeitleiste", "Anhänge", "Praxis / Kunde ⇅", "Zuständigkeit ⇅"),
    }
    for lang, (form, timeline, attachments, practice, actor) in expected.items():
        _switch(lang, tv)
        tabs = _tab_texts(tv.detail_tabview)
        assert form in tabs["📝 Formular & Ausfüllen"]
        assert timeline in tabs["🕒 Zeitleiste"]
        assert attachments in tabs["📎 Anhänge"]
        assert (COL_TITLE_MAP["practice"], COL_TITLE_MAP["actor"]) == (practice, actor)


def test_board_rebuild_uses_column_headers_of_active_language(root):
    from ui.views.board_view import BoardView

    def noop(_case):
        return None

    board = BoardView(parent=root, on_select_case=noop, on_switch_to_cockpit=noop, on_open_followup=noop,
                      on_toggle_complete=noop, on_change_actor=noop)
    expected = {"de": "✓ Erledigte Fälle", "en": "✓ Completed Cases", "sv": "✓ Slutförda ärenden"}
    for lang, completed in expected.items():
        get_i18n().current_language = lang
        board.create_board()
        assert board.col_headers["completed"].cget("text") == completed
        assert "Hotline" in board.col_headers["hotline"].cget("text")


def test_app_retitles_window_when_language_changes(config):
    """Regression: app construction once raised UnboundLocalError; as i18n listener it retitles itself."""
    from ui.app import SupportCockpitApp

    app = SupportCockpitApp(config)
    try:
        expected = {
            "en": "Support Cockpit & Ticket Management",
            "sv": "Support Cockpit & Ärendehantering",
            "de": "Support-Cockpit & Ticket Management",
        }
        for lang, title in expected.items():
            get_i18n().current_language = lang
            assert app.title() == title
    finally:
        try:
            app.tray_service.stop()
        except Exception:
            pass
        app.destroy()


def test_translated_placeholder_is_re_evaluated_on_language_change(root):
    """A register_i18n placeholder whose own value is translated must not freeze."""
    from ui.dialogs.base_dialog import BaseDialog

    class Demo(BaseDialog):
        def __init__(self, parent):
            super().__init__(parent)
            self.setup_window(parent, "Demo", (300, 200), modal=False)

    dialog = Demo(root)
    calls = {"n": 0}

    def actor_name():
        calls["n"] += 1
        return f"Stelle-{calls['n']}"

    label = dialog.register_i18n(
        ctk.CTkLabel(dialog, text="start"), "does.not.exist", "Zuständig: {actor}", actor=actor_name,
    )
    dialog.refresh_ui_labels()
    assert label.cget("text") == "Zuständig: Stelle-1"
    dialog.refresh_ui_labels()
    assert label.cget("text") == "Zuständig: Stelle-2", "Platzhalter wurde nicht neu ausgewertet"
    dialog.destroy()
