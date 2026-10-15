"""Board, table, analytics and cockpit views plus their embedded widgets (attachments, form, wiki, tooltips) and language refresh."""

import ast
import json
import time
from pathlib import Path

import customtkinter as ctk
import pytest
from PIL import Image

from enums import Actor, BoardColumn, FieldType, UrgencyLevel, get_layout_display
from models.case import Case, CaseCustomer, Classification, TimelineEntry, WorkflowStatus
from models.schema import QuestionSchema, SchemaField
from services.attachment_service import AttachmentService
from services.i18n_service import get_i18n, tr
from services.scoring_service import ScoringService
from services.wiki_sync_service import WikiSyncService
from ui.views.board_view import BoardView, KanbanCardWidget
from ui.views.cockpit_view import CockpitView
from ui.views.table_view import TableView

REPO = Path(__file__).resolve().parents[2]
LANGS = ("de", "en", "sv")


def _make_board(root, case_count: int = 12, **kw) -> BoardView:
    board = BoardView(
        root,
        on_select_case=lambda c: None,
        on_switch_to_cockpit=lambda c: None,
        on_open_followup=lambda c: None,
        on_toggle_complete=lambda c: None,
        on_change_actor=lambda c: None,
        **kw,
    )
    board.pack(fill="both", expand=True)
    board.set_cases([
        Case(
            case_id=f"T-{i:04d}",
            customer=CaseCustomer(customer_id=f"K-{i}", practice_name=f"Praxis {i}"),
            classification=Classification(title=f"Fall {i}"),
            workflow_status=WorkflowStatus(current_actor=Actor.DEVELOPMENT if i % 2 else Actor.SUPPORT),
        )
        for i in range(case_count)
    ])
    return board


def _make_table(root, config, storage) -> TableView:
    return TableView(
        root,
        author_name="Tester",
        scoring_service=ScoringService(storage.load_profile().scoring_matrix),
        attachment_service=AttachmentService(config),
        on_case_updated=lambda c: None,
        on_case_selected=lambda c: None,
        app_config=config,
    )


@pytest.fixture
def cockpit(root, config, storage):
    profile = storage.load_profile()
    view = CockpitView(
        root,
        author_name="Tester",
        scoring_service=ScoringService(profile.scoring_matrix),
        attachment_service=AttachmentService(config),
        wiki_service=WikiSyncService(config, profile.wiki_settings),
        on_case_updated=lambda c: None,
        on_case_selected=lambda c: None,
        on_search_changed=lambda s: None,
        on_open_export_dialog=lambda c: None,
        on_archive_case=lambda c: None,
        app_config=config,
        profile=profile,
        storage_service=storage,
    )
    view.pack(fill="both", expand=True)
    return view


# --- BoardView ---------------------------------------------------------------

def test_board_headers_collapse_and_language_refresh(root, config):
    cases = [
        Case(case_id="T-1", classification=Classification(title="Open 1", calculated_score=80), workflow_status=WorkflowStatus(current_actor="SUPPORT")),
        Case(case_id="T-2", classification=Classification(title="Dev 1", calculated_score=60), workflow_status=WorkflowStatus(current_actor="DEVELOPMENT")),
        Case(case_id="T-3", classification=Classification(title="Followup 1", calculated_score=40),
             workflow_status=WorkflowStatus(followup_at="2026-09-05T10:00:00")),
        Case(case_id="T-4", classification=Classification(title="Done 1", calculated_score=20),
             workflow_status=WorkflowStatus(is_completed=True)),
    ]
    board = BoardView(
        root,
        on_select_case=lambda c: None,
        on_switch_to_cockpit=lambda c: None,
        on_open_followup=lambda c: None,
        on_toggle_complete=lambda c: None,
        on_change_actor=lambda c: None,
        app_config=config,
    )
    board.set_cases(cases)
    for key, text in (("hotline", "Hotline (1)"), ("dev", "Entwicklung (1)"), ("followup", "Wiedervorlage (1)"), ("completed", "Erledigt (1)")):
        assert text in board.col_headers[key].cget("text")

    board.toggle_column_collapse("hotline")
    assert board.collapsed_states["hotline"] is True

    get_i18n().current_language = "en"
    board.refresh_ui_labels()
    assert board.collapsed_states["hotline"] is True, "collapse survives a language switch"
    assert "Follow-up (1)" in board.col_headers["followup"].cget("text")
    board.toggle_column_collapse("hotline")
    assert board.collapsed_states["hotline"] is False
    assert "Hotline (1)" in board.col_headers["hotline"].cget("text")

    get_i18n().current_language = "sv"
    board.refresh_ui_labels()
    assert "Utveckling (1)" in board.col_headers["dev"].cget("text")
    assert "Uppföljning (1)" in board.col_headers["followup"].cget("text")

    # An unknown column key falls back to a full rebuild and still keeps all columns.
    board.toggle_column_collapse("support")
    assert board.collapsed_states["support"] is True
    assert len(board.col_frames) == 6


def test_collapsing_one_column_rebuilds_only_that_column(root):
    root.geometry("1200x700")
    board = _make_board(root)
    root.update()

    frames_before = {key: str(frame) for key, frame in board.col_frames.items()}
    hotline_cards = [str(w) for w in board.col_scrolls["hotline"].winfo_children() if isinstance(w, KanbanCardWidget)]
    assert hotline_cards
    signatures_before = dict(board._col_signatures)

    board.toggle_column_collapse("dev")
    root.update()

    frames_after = {key: str(frame) for key, frame in board.col_frames.items()}
    assert [k for k in frames_before if frames_before[k] != frames_after[k]] == ["dev"]
    assert set(frames_after) == {"hotline", "tech", "dev", "customer", "followup", "completed"}
    assert board.collapsed_states["dev"] is True
    assert "dev" not in board.col_scrolls, "collapsed column needs no scroll area"
    # Cards of untouched columns survive.
    assert [str(w) for w in board.col_scrolls["hotline"].winfo_children() if isinstance(w, KanbanCardWidget)] == hotline_cards
    assert board._col_signatures.get("hotline") == signatures_before.get("hotline")

    board.toggle_column_collapse("dev")
    root.update()
    assert board.collapsed_states["dev"] is False
    assert "dev" in board.col_scrolls and "dev" in board.col_headers
    assert len(board.col_frames) == 6


def test_board_renders_in_batches_and_scrolling_reaches_every_case(root):
    """Only a screenful of cards is built up front (was ~15 ms per card, linear).

    Scrolling the canvas itself must pull in batches: a test that called
    _on_scrolled() directly once stayed green while nothing reloaded in the app.
    """
    root.geometry("1200x700")
    board = _make_board(root, case_count=80)
    root.update()

    pending = board._pending_cases["hotline"]
    rendered = board._rendered_counts["hotline"]
    assert len(pending) > board.RENDER_BATCH_SIZE
    assert 0 < rendered <= board.RENDER_BATCH_SIZE * 2

    canvas = board._col_canvas("hotline")
    canvas.yview_moveto(1.0)
    root.update()
    root.update_idletasks()
    root.update()
    assert board._rendered_counts["hotline"] > rendered, "scrolling loads nothing"

    for _ in range(60):
        if board._rendered_counts["hotline"] >= len(pending):
            break
        canvas.yview_moveto(1.0)
        root.update()
        root.update_idletasks()
    assert board._rendered_counts["hotline"] == len(pending)

    board.render_all_cards()
    root.update()
    for key, cases in board._pending_cases.items():
        assert board._rendered_counts[key] == len(cases), key
        if cases:
            assert len(board.col_scrolls[key].winfo_children()) == len(cases)

    # A refresh without changes keeps the cards (signature check survives batching).
    before = [str(w) for w in board.col_scrolls["hotline"].winfo_children()]
    board.refresh_board()
    root.update()
    assert [str(w) for w in board.col_scrolls["hotline"].winfo_children()] == before


def test_scroll_watch_leaves_the_scrollbar_working(root):
    from utils.ui_utils import watch_scroll_position

    root.geometry("300x200")
    frame = ctk.CTkScrollableFrame(root, height=120)
    frame.pack(fill="both", expand=True)
    for i in range(40):
        ctk.CTkLabel(frame, text=f"Zeile {i}").pack()
    root.update()

    positions = []
    assert watch_scroll_position(frame, lambda first, last: positions.append((first, last)))
    frame._parent_canvas.yview_moveto(1.0)
    root.update()

    assert positions, "hook not called on scroll"
    assert frame._scrollbar.get()[1] > 0.5, "scrollbar no longer follows"  # type: ignore[attr-defined]


# --- TableView ---------------------------------------------------------------

def test_table_view_sorting_tabs_and_language_refresh(root, config, storage):
    tv = _make_table(root, config, storage)
    tv.pack(fill="both", expand=True)
    assert "Falldetails" in tv.detail_title_label.cget("text")
    assert "Speichern" in tv.save_btn.cget("text")

    cases = [
        Case(case_id="T-TV-01", customer=CaseCustomer(customer_id="K-1", practice_name="Praxis Alpha"),
             classification=Classification(title="Erster Fall"), workflow_status=WorkflowStatus(board_column=BoardColumn.NEW)),
        Case(case_id="T-TV-02", customer=CaseCustomer(customer_id="K-2", practice_name="Praxis Beta"),
             classification=Classification(title="Zweiter Fall"), workflow_status=WorkflowStatus(board_column=BoardColumn.IN_PROGRESS)),
    ]
    tv.set_cases(cases)
    tv.on_header_click("case_id")
    tv.on_header_click("score")
    tv.update_idletasks()
    assert len(tv.tree.get_children()) == 2
    tv.select_case(cases[0])

    tabs = ("📝 Formular & Ausfüllen", "🕒 Zeitleiste", "📎 Anhänge")
    keys = ("table.tab_form", "table.tab_timeline", "table.tab_attachments")
    for lang, tab in zip(LANGS, tabs):
        tv.detail_tabview.set(tab)
        get_i18n().current_language = lang
        tv.refresh_ui_labels()
        btns = tv.detail_tabview._segmented_button._buttons_dict
        for name, key in zip(tabs, keys):
            assert btns[name].cget("text") == tr(key, name)
    assert "spara" in tv.save_btn.cget("text").lower()


def test_table_view_timeline_changes_reach_the_case():
    """Regression: the table view used to drop notes added in its timeline tab."""
    class Dummy:
        saved = 0

        def on_click_save(self):
            Dummy.saved += 1

    view = Dummy()
    view.selected_case = Case(case_id="T-1", customer=CaseCustomer(), classification=Classification())  # type: ignore[attr-defined]
    new_entries = [TimelineEntry(timestamp="2026-09-01T10:00:00", author="A", note="x")]
    TableView.on_timeline_updated(view, new_entries)  # type: ignore[arg-type]
    assert view.selected_case.timeline == new_entries  # type: ignore[attr-defined]
    assert Dummy.saved == 1


# --- AnalyticsView -----------------------------------------------------------

def test_analytics_view_kpis_across_languages(root):
    from ui.views.analytics_view import AnalyticsView

    cases = [
        Case(case_id="T-1", classification=Classification(urgency_level=UrgencyLevel.RED),
             workflow_status=WorkflowStatus(current_actor=Actor.SUPPORT, is_completed=False)),
        Case(case_id="T-2", classification=Classification(urgency_level=UrgencyLevel.YELLOW),
             workflow_status=WorkflowStatus(current_actor=Actor.DEVELOPMENT, is_completed=False)),
        Case(case_id="T-3", classification=Classification(urgency_level=UrgencyLevel.GREEN), workflow_status=WorkflowStatus(is_completed=True)),
    ]
    view = AnalyticsView(root)
    view.pack(fill="both", expand=True)
    expected = {"de": ("Auswertungen", "Statistik-Bericht"), "en": (None, "Copy"), "sv": (None, "Kopiera")}
    for lang in LANGS:
        get_i18n().current_language = lang
        if lang != "de":
            view.create_widgets()
        view.set_cases(cases)
        title, copy = expected[lang]
        if title:
            assert title in view.top_bar_title.cget("text")
        assert copy in view.copy_report_btn.cget("text")
        assert view.scroll_frame.winfo_children()


# --- CockpitView -------------------------------------------------------------

def _cockpit_case(**wf) -> Case:
    return Case(
        case_id="T-LAYOUT-01",
        customer=CaseCustomer(customer_id="K-1", practice_name="Praxis Layout", contact_person="Dr. Layout"),
        classification=Classification(title="Layout Test"),
        workflow_status=WorkflowStatus(board_column=BoardColumn.NEW, **wf),
    )


def test_cockpit_layout_and_pane_widths(cockpit):
    from ui.widgets.attachment_widget import AttachmentWidget
    from ui.widgets.case_list_widget import CaseListWidget
    from ui.widgets.dynamic_form_widget import DynamicFormWidget
    from ui.widgets.timeline_widget import TimelineWidget
    from ui.widgets.wiki_widget import WikiWidget

    assert isinstance(cockpit.left_frame, CaseListWidget)
    assert isinstance(cockpit.form_widget, DynamicFormWidget)
    assert isinstance(cockpit.timeline_widget, TimelineWidget)
    assert isinstance(cockpit.attachment_widget, AttachmentWidget)
    assert isinstance(cockpit.wiki_widget, WikiWidget)
    assert cockpit.actor_combo.master == cockpit.toolbar_right
    assert cockpit.complete_btn.master == cockpit.toolbar_right

    cockpit.profile.ui_settings.column_widths = {"cockpit_left": 250, "cockpit_right": 400}
    assert cockpit._build_paned_window() == (250, 400)
    cockpit.profile = None
    cockpit.app_config = None
    assert cockpit._build_paned_window() == (300, 320)


def test_cockpit_refresh_ui_labels_reflects_case_state(cockpit):
    cockpit.current_case = None
    cockpit.refresh_ui_labels()
    assert cockpit.complete_btn.cget("text") == tr("cockpit.complete", "✓ Erledigt")
    assert cockpit.case_title_label.cget("text") == tr("cockpit.select_case_prompt", "Bitte einen Fall auswählen")
    assert cockpit.more_actions_combo.get() == tr("cockpit.more_actions", "⚙ Weitere Aktionen...")
    for btn, key in (("email_btn", "cockpit.email_ai"), ("cal_btn", "cockpit.calendar"), ("followup_btn", "cockpit.followup"),
                     ("save_btn", "cockpit.save"), ("archive_btn", "cockpit.archive")):
        assert getattr(cockpit, btn).cget("text") == tr(key)

    cockpit.current_case = _cockpit_case(is_completed=True, current_actor=Actor.SUPPORT)
    cockpit.refresh_ui_labels()
    assert cockpit.complete_btn.cget("text") == tr("cockpit.reopen", "✓ Wieder öffnen")

    vip = _cockpit_case(is_completed=False, current_actor=Actor.DEVELOPMENT)
    vip.customer.is_vip = True
    cockpit.current_case = vip
    cockpit.refresh_ui_labels()
    assert cockpit.complete_btn.cget("text") == tr("cockpit.complete", "✓ Erledigt")
    assert cockpit.actor_combo.get() == tr("cockpit.handover_action", "Übergabe")
    kunde = cockpit.kunde_label.cget("text")
    assert "Praxis Layout" in kunde and "K-1" in kunde and "VIP" in kunde

    internal = _cockpit_case()
    internal.customer.customer_id = "INTERNAL"
    assert internal.is_internal
    cockpit.current_case = internal
    cockpit.refresh_ui_labels()
    assert tr("cockpit.internal_task_title", "INTERNE AUFGABE / VORGANG") in cockpit.kunde_label.cget("text")


def test_cockpit_tabs_follow_language_while_switching_tabs(root, cockpit):
    tabs = ("Zeitleiste", "Anhänge", "Wiki")
    keys = ("cockpit.tab_timeline", "cockpit.tab_attachments", "cockpit.tab_wiki")
    for lang, tab in zip(LANGS, tabs):
        cockpit.right_tabview.set(tab)
        get_i18n().current_language = lang
        cockpit.refresh_ui_labels()
        root.update_idletasks()
        btns = cockpit.right_tabview._segmented_button._buttons_dict
        for name, key in zip(tabs, keys):
            assert btns[name].cget("text") == tr(key, name)


# --- embedded widgets --------------------------------------------------------

def test_attachment_widget_lists_files_and_previews_every_type(root, config, tmp_path):
    from ui.widgets.attachment_widget import AttachmentWidget

    svc = AttachmentService(config)
    widget = AttachmentWidget(root, svc)
    widget.pack(fill="both", expand=True)

    case = Case(case_id="ATTACH-1", customer=CaseCustomer(customer_id="K-1", practice_name="Praxis Attachment"))
    widget.load_attachments(case)
    assert svc.list_attachments(case) == []

    src = tmp_path / "screenshot.txt"
    src.write_text("dummy", encoding="utf-8")
    saved = svc.copy_attachment(case, src)
    widget.load_attachments(case)
    assert len(svc.list_attachments(case)) == 1
    saved.unlink()
    widget.load_attachments(case)
    assert svc.list_attachments(case) == []

    case_dir = tmp_path / "cases" / case.case_id / "attachments"
    case_dir.mkdir(parents=True, exist_ok=True)
    img = case_dir / "test_screenshot.png"
    Image.new("RGB", (200, 100), color="blue").save(img)
    txt = case_dir / "notes.txt"
    txt.write_text("Hello World\nLine 2\nLine 3", encoding="utf-8")
    pdf = case_dir / "document.pdf"
    pdf.write_bytes(b"%PDF-1.4 dummy binary content")
    empty = case_dir / "empty.log"
    empty.write_text("", encoding="utf-8")
    widget.load_attachments(case)

    for path in (img, txt, pdf, empty, case_dir / "non_existent.png"):
        widget.show_file_preview(path)
        for lang in ("en", "sv"):
            get_i18n().current_language = lang
            widget.refresh_ui_labels()

    # Switching between cases with differently many attachments.
    other = Case(case_id="CASE-2", classification=Classification(title="Case 2"))
    other_dir = tmp_path / "cases" / other.case_id / "attachments"
    other_dir.mkdir(parents=True)
    (other_dir / "file_0.txt").write_text("x", encoding="utf-8")
    for lang, c in zip(LANGS, (other, case, None)):
        get_i18n().current_language = lang
        widget.load_attachments(c)
        widget.refresh_ui_labels()


def test_attachment_widget_survives_repeated_refresh_after_preview_is_cleared(root, config):
    """Regression: refresh_ui_labels() configured a preview_label destroyed by clear_preview() (TclError)."""
    from ui.widgets.attachment_widget import AttachmentWidget

    widget = AttachmentWidget(root, attachment_service=AttachmentService(config))
    widget.refresh_ui_labels()
    get_i18n().current_language = "en"
    widget.refresh_ui_labels()

    widget.clear_preview()
    for lang in LANGS:
        get_i18n().current_language = lang
        widget.refresh_ui_labels()

    for child in widget.preview_frame.winfo_children():
        child.destroy()
    widget.preview_label = None
    for lang in LANGS:
        get_i18n().current_language = lang
        widget.refresh_ui_labels()


def test_dynamic_form_round_trips_all_field_types_across_languages(root, storage, config):
    from ui.widgets.dynamic_form_widget import DynamicFormWidget

    schema = QuestionSchema(
        schema_id="schema_full_test",
        display_name="Umfassendes Testschema",
        fields=[
            SchemaField(field_id="f_text", label="Textfeld", field_type=FieldType.TEXT, required=True),
            SchemaField(field_id="f_drop", label="Auswahl", field_type=FieldType.DROPDOWN, options=["Option A", "Option B"]),
            SchemaField(field_id="f_num", label="Zahl", field_type=FieldType.NUMBER),
            SchemaField(field_id="f_bool", label="Schalter", field_type=FieldType.BOOLEAN),
            SchemaField(field_id="f_date", label="Datum", field_type=FieldType.DATE),
            SchemaField(field_id="f_choice", label="Choice", field_type="select", options=["Opt 1", "Opt 2"]),
            SchemaField(field_id="f_textarea", label="Textarea", field_type="textarea"),
            SchemaField(field_id="f_tags", label="Tags", field_type="module_tags"),
        ],
    )
    data = {
        "f_text": "Hallo Welt", "f_drop": "Option A", "f_num": 42, "f_bool": True, "f_date": "2026-08-25",
        "f_choice": "Opt 2", "f_textarea": "Multi\nLine", "f_tags": ["T1", "T2"],
    }
    form = DynamicFormWidget(root, profile=storage.load_profile(), storage_service=storage, attachment_service=AttachmentService(config))
    form.pack(fill="both", expand=True)
    form.load_schema(schema, data, missing_fields=["f_text"])

    for lang in LANGS:
        get_i18n().current_language = lang
        form.refresh_ui_labels()
        extracted = form.get_form_data()
        assert extracted["f_text"] == "Hallo Welt"
        assert extracted["f_drop"] == "Option A"
        assert extracted["f_num"] == 42
        assert extracted["f_bool"] is True

    form.load_schema(None, {})
    form.refresh_ui_labels()

    bare = DynamicFormWidget(root)
    bare.load_schema(schema, data)
    assert bare.get_form_data()["f_text"] == "Hallo Welt"


def test_wiki_widget_labels_follow_language(root, config, storage):
    from ui.widgets.wiki_widget import WikiWidget

    widget = WikiWidget(root, WikiSyncService(config, storage.load_profile().wiki_settings))
    assert widget.hdr_lbl.cget("text") == "BookStack Offline Wiki"
    assert "Sync" in widget.sync_btn.cget("text")
    assert "durchsuchen" in widget.search_entry.cget("placeholder_text")
    get_i18n().current_language = "en"
    widget.refresh_ui_labels()
    assert "Search" in widget.search_entry.cget("placeholder_text")
    get_i18n().current_language = "sv"
    widget.refresh_ui_labels()
    assert "Sök" in widget.search_entry.cget("placeholder_text")


@pytest.mark.parametrize(("lang", "cal_title", "tag_title"), [
    ("de", "📅 Datum auswählen", "Programmbereiche auswählen"),
    ("en", "📅 Select Date", "Select"),
    ("sv", "📅 Välj datum", "Välj"),
])
def test_popup_titles_are_localized(root, lang, cal_title, tag_title):
    from ui.widgets.date_picker import CalendarDialog
    from ui.widgets.dynamic_form_widget import ModuleTagPickerPopup
    from ui.widgets.toast_notification import ToastNotification

    get_i18n().current_language = lang
    cal = CalendarDialog(parent=root)
    assert cal.title() == cal_title
    cal.destroy()
    popup = ModuleTagPickerPopup(parent=root, available_tags=["Tag1"], selected_tags=[], on_apply=lambda t: None)
    assert tag_title in popup.title()
    popup.destroy()
    ToastNotification(root, title=tr("cockpit.save"), message=tr("status_messages.saved", "Erfolgreich gespeichert.")).safe_destroy()


def test_tooltip_and_input_widgets_lifecycle(root):
    from ui.widgets.ctk_tooltip import CTkTooltip
    from ui.widgets.date_picker import DatePickerWidget
    from ui.widgets.searchable_combobox import SearchableCombobox

    btn = ctk.CTkButton(root, text="Tooltip Button")
    btn.pack(padx=20, pady=20)
    root.update_idletasks()
    tooltip = CTkTooltip(btn, "Hilfetext für Button")
    event = type("Event", (), {"x": 10, "y": 10})()
    tooltip.on_enter(event)
    tooltip.on_leave(event)
    CTkTooltip._active_tooltips.add(tooltip)  # shown only when the real pointer is inside the widget
    CTkTooltip.dismiss_all()
    assert tooltip not in CTkTooltip._active_tooltips
    tooltip.on_destroy(event)

    picker = DatePickerWidget(root, initial_value="2026-09-03 14:00")
    combo = SearchableCombobox(root, values=["Alpha", "Beta", "Gamma"], command=lambda v: None)
    get_i18n().current_language = "en"
    picker.refresh_ui_labels()
    combo.refresh_ui_labels()
    assert picker.get()
    assert combo.placeholder_text == tr("common.please_select")


def test_icons_render_in_dark_mode(root):
    from constants import ICON_KEY_COPY
    from utils.icon_utils import get_icon

    icon = get_icon(ICON_KEY_COPY)
    ctk.CTkButton(root, text="x", image=icon).pack()
    try:
        ctk.set_appearance_mode("dark")
        root.update_idletasks()
        assert any(key[2] == "dark" and photo is not None for key, photo in icon._robust_photo_cache.items())
    finally:
        ctk.set_appearance_mode("system")


# --- i18n wiring used by all views ----------------------------------------

def test_i18n_listener_failure_does_not_block_other_listeners():
    i18n = get_i18n()
    seen: list[str] = []

    def failing(_lang):
        raise RuntimeError("Simulated listener crash")

    def good(lang):
        seen.append(lang)

    for fn in (good, failing):
        i18n.register_listener(fn)
    try:
        try:
            i18n.current_language = "en"
        except Exception:
            pass
        assert "en" in seen
    finally:
        for fn in (good, failing):
            i18n.unregister_listener(fn)


def test_tr_tolerates_missing_none_and_extra_parameters():
    assert "{count}" in tr("case_list.count_cases") or "Support-Fälle" in tr("case_list.count_cases")
    res_none = tr("case_list.count_cases", count=None)
    assert "None" in res_none or "{count}" in res_none
    assert "42" in tr("case_list.count_cases", count=42, extra_dummy="ignored")


def test_every_tr_key_in_views_and_widgets_exists_in_all_locales():
    locales = {lang: json.loads((REPO / "locales" / f"{lang}.json").read_text(encoding="utf-8")) for lang in LANGS}

    def lookup(d, key):
        for part in key.split("."):
            if not isinstance(d, dict) or part not in d:
                return None
            d = d[part]
        return d

    missing = []
    for f in (REPO / "src" / "ui").rglob("*.py"):
        if "dialogs" in f.parts:
            continue
        for node in ast.walk(ast.parse(f.read_text(encoding="utf-8"))):
            if not isinstance(node, ast.Call):
                continue
            name = getattr(node.func, "id", None) or getattr(node.func, "attr", None)
            if name == "tr" and node.args and isinstance(node.args[0], ast.Constant) and isinstance(node.args[0].value, str):
                key = node.args[0].value
                missing += [f"{lang}: {key} ({f.name}:{node.lineno})" for lang in LANGS if lookup(locales[lang], key) is None]
    assert not missing, missing[:20]


# --- full app (kept minimal; end-to-end flows live elsewhere) -----------------

def test_app_language_and_layout_switching(config):
    from ui.app import SupportCockpitApp

    app = SupportCockpitApp(config)
    app.withdraw()
    try:
        # The last two switches hit already built views, so their debounced profile saves overlap.
        layouts = ("COCKPIT", "BOARD", "TABLE", "ANALYTICS", "COCKPIT", "BOARD")
        for lang, layout in zip(("en", "sv", "de") * 2, layouts):
            get_i18n().current_language = lang  # the app listens and rebuilds its menu bar
            assert get_i18n().current_language == lang
            assert app.title() == tr("app.window_title")
            assert app.menu_frame.winfo_exists() and app.stammdaten_combo.winfo_exists()
            app.switch_layout(get_layout_display(layout))
            assert app.profile.ui_settings.default_layout == layout
        app.on_language_changed("de")

        # The debounced profile save reaches disk on its own timer.
        deadline = time.monotonic() + 3
        while time.monotonic() < deadline:
            try:
                if json.loads(config.app_profile_path.read_text(encoding="utf-8"))["ui_settings"]["default_layout"] == "BOARD":
                    break
            except (OSError, ValueError, KeyError):
                pass
            time.sleep(0.05)
        assert json.loads(config.app_profile_path.read_text(encoding="utf-8"))["ui_settings"]["default_layout"] == "BOARD"
        app.on_closing()
        app._on_restore_from_tray()
    finally:
        try:
            if hasattr(app, "tray_service"):
                app.tray_service.stop()
            app.destroy()
        except Exception:
            pass
