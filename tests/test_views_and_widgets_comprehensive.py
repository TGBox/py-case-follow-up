"""Comprehensive tests for views (BoardView, TableView, AnalyticsView) and interactive widgets."""

from pathlib import Path
import customtkinter as ctk
import pytest
from config import AppConfig
from enums import Actor, UrgencyLevel, BoardColumn, FieldType
from models.case import Case, CaseCustomer, Classification, WorkflowStatus
from models.schema import QuestionSchema, SchemaField
from services.storage_service import StorageService
from services.scoring_service import ScoringService
from services.attachment_service import AttachmentService
from services.wiki_sync_service import WikiSyncService


@pytest.fixture
def test_env(tmp_path: Path):
    config = AppConfig(workspace_dir=tmp_path)
    storage = StorageService(config)
    scoring = ScoringService()
    attachment_svc = AttachmentService(config)
    wiki_svc = WikiSyncService(config)

    app = ctk.CTk()
    app.withdraw()

    yield app, storage, scoring, attachment_svc, wiki_svc, config

    try:
        app.destroy()
    except Exception:
        pass


def test_board_view_rendering_and_interactions(test_env):
    """Test BoardView (Kanban) rendering, card creation, and quick actions."""
    app, storage, scoring, attachment_svc, wiki_svc, config = test_env
    from ui.views.board_view import BoardView

    cases = [
        Case(
            case_id="T-BV-01",
            customer=CaseCustomer(customer_id="K-1", practice_name="Praxis Alpha"),
            classification=Classification(title="Offener Fall", urgency_level=UrgencyLevel.GREEN),
            workflow_status=WorkflowStatus(board_column=BoardColumn.NEW, current_actor=Actor.SUPPORT),
        ),
        Case(
            case_id="T-BV-02",
            customer=CaseCustomer(customer_id="K-2", practice_name="Praxis Beta"),
            classification=Classification(title="Entwicklungsfall", urgency_level=UrgencyLevel.RED),
            workflow_status=WorkflowStatus(board_column=BoardColumn.IN_PROGRESS, current_actor=Actor.DEVELOPMENT),
        ),
        Case(
            case_id="T-BV-03",
            customer=CaseCustomer(customer_id="K-3", practice_name="Praxis Gamma"),
            classification=Classification(title="Wiedervorlage Fall", urgency_level=UrgencyLevel.YELLOW),
            workflow_status=WorkflowStatus(board_column=BoardColumn.WAITING, followup_at="2026-08-30T10:00:00"),
        ),
        Case(
            case_id="T-BV-04",
            customer=CaseCustomer(customer_id="K-4", practice_name="Praxis Delta"),
            classification=Classification(title="Erledigter Fall"),
            workflow_status=WorkflowStatus(board_column=BoardColumn.DONE, is_completed=True),
        ),
    ]

    selected_case = None
    cockpit_case = None

    def on_select(c):
        nonlocal selected_case
        selected_case = c

    def on_cockpit(c):
        nonlocal cockpit_case
        cockpit_case = c

    board = BoardView(
        app,
        on_select_case=on_select,
        on_switch_to_cockpit=on_cockpit,
        on_open_followup=lambda c: None,
        on_toggle_complete=lambda c: None,
        on_change_actor=lambda c: None,
        app_config=config,
    )
    board.pack(fill="both", expand=True)
    board.set_cases(cases)
    board.update_idletasks()

    assert len(board.cases) == 4

    # Test column toggling
    board.toggle_column_collapse("support")
    board.update_idletasks()
    assert board.collapsed_states["support"]
    board.toggle_column_collapse("support")
    board.update_idletasks()
    assert not board.collapsed_states["support"]

    board.destroy()


def test_table_view_rendering_and_sorting(test_env):
    """Test TableView Treeview column rendering, sorting, and row selection."""
    app, storage, scoring, attachment_svc, wiki_svc, config = test_env
    from ui.views.table_view import TableView

    cases = [
        Case(
            case_id="T-TV-01",
            customer=CaseCustomer(customer_id="K-1", practice_name="Praxis Alpha"),
            classification=Classification(title="Erster Fall"),
            workflow_status=WorkflowStatus(board_column=BoardColumn.NEW),
        ),
        Case(
            case_id="T-TV-02",
            customer=CaseCustomer(customer_id="K-2", practice_name="Praxis Beta"),
            classification=Classification(title="Zweiter Fall"),
            workflow_status=WorkflowStatus(board_column=BoardColumn.IN_PROGRESS),
        ),
    ]

    selected_case = None

    def on_select(c):
        nonlocal selected_case
        selected_case = c

    table = TableView(
        app,
        author_name="DaniBani",
        scoring_service=scoring,
        attachment_service=attachment_svc,
        on_case_updated=lambda c: None,
        on_case_selected=on_select,
        app_config=config,
    )
    table.pack(fill="both", expand=True)
    table.set_cases(cases)
    table.update_idletasks()

    assert len(table.cases) == 2

    # Test sorting column
    table.on_header_click("case_id")
    table.update_idletasks()
    table.on_header_click("score")
    table.update_idletasks()

    table.destroy()


def test_analytics_view_dashboard_kpis(test_env):
    """Test AnalyticsView KPI calculations and dashboard cards."""
    app, storage, scoring, attachment_svc, wiki_svc, config = test_env
    from ui.views.analytics_view import AnalyticsView

    cases = [
        Case(
            case_id="T-AN-01",
            customer=CaseCustomer(customer_id="K-1", practice_name="Praxis Alpha"),
            classification=Classification(title="Fall 1", urgency_level=UrgencyLevel.GREEN),
            workflow_status=WorkflowStatus(current_actor=Actor.SUPPORT, is_completed=False),
        ),
        Case(
            case_id="T-AN-02",
            customer=CaseCustomer(customer_id="K-2", practice_name="Praxis Beta"),
            classification=Classification(title="Fall 2", urgency_level=UrgencyLevel.RED),
            workflow_status=WorkflowStatus(current_actor=Actor.DEVELOPMENT, is_completed=True),
        ),
    ]

    analytics = AnalyticsView(app)
    analytics.pack(fill="both", expand=True)
    analytics.set_cases(cases)
    analytics.update_idletasks()

    assert len(analytics.cases) == 2
    assert len(analytics.scroll_frame.winfo_children()) >= 1

    analytics.destroy()


def test_dynamic_form_widget_fields_and_validation(test_env):
    """Test DynamicFormWidget rendering various field types and form data extraction."""
    app, storage, scoring, attachment_svc, wiki_svc, config = test_env
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
        ],
    )

    form = DynamicFormWidget(
        app,
        profile=storage.load_profile(),
        storage_service=storage,
        attachment_service=attachment_svc,
    )
    form.pack(fill="both", expand=True)

    initial_data = {
        "f_text": "Hallo Welt",
        "f_drop": "Option A",
        "f_num": 42,
        "f_bool": True,
        "f_date": "2026-08-25",
    }
    form.load_schema(schema, initial_data)
    form.update_idletasks()

    extracted = form.get_form_data()
    assert extracted.get("f_text") == "Hallo Welt"
    assert extracted.get("f_drop") == "Option A"
    assert extracted.get("f_num") == 42
    assert extracted.get("f_bool") is True

    form.destroy()


def test_attachment_widget_and_service(test_env, tmp_path: Path):
    """Test AttachmentWidget loading and AttachmentService file handling."""
    app, storage, scoring, attachment_svc, wiki_svc, config = test_env
    from ui.widgets.attachment_widget import AttachmentWidget

    # Create dummy attachment file
    dummy_file = tmp_path / "screenshot.png"
    dummy_file.write_text("dummy binary content", encoding="utf-8")

    case = Case(
        case_id="T-ATT-01",
        customer=CaseCustomer(customer_id="K-1", practice_name="Praxis Attachment"),
    )

    widget = AttachmentWidget(
        app,
        attachment_service=attachment_svc,
    )
    widget.pack(fill="both", expand=True)
    widget.load_attachments(case)
    widget.update_idletasks()

    files = attachment_svc.list_attachments(case)
    assert len(files) == 0

    # Add attachment via service
    saved_path = attachment_svc.copy_attachment(case, dummy_file)
    assert saved_path.exists()

    widget.load_attachments(case)
    widget.update_idletasks()
    assert len(attachment_svc.list_attachments(case)) == 1

    # Delete attachment
    saved_path.unlink()
    widget.load_attachments(case)
    widget.update_idletasks()
    assert len(attachment_svc.list_attachments(case)) == 0

    widget.destroy()


def test_ctk_tooltip_lifecycle(test_env):
    """Test CTkTooltip creation, enter, leave, and destroy."""
    app, storage, scoring, attachment_svc, wiki_svc, config = test_env
    from ui.widgets.ctk_tooltip import CTkTooltip

    btn = ctk.CTkButton(app, text="Tooltip Button")
    btn.pack(padx=20, pady=20)
    app.update_idletasks()

    tooltip = CTkTooltip(btn, "Hilfetext für Button")
    assert tooltip.text_or_func == "Hilfetext für Button"

    # Simulate enter and leave
    event = type("Event", (), {"x": 10, "y": 10})()
    tooltip.on_enter(event)
    tooltip.on_leave(event)
    tooltip.on_destroy(event)


# --- Collapsing one board column must not rebuild the other three ---

def _board(root, case_count: int = 12):
    from ui.views.board_view import BoardView

    board = BoardView(
        root,
        on_select_case=lambda c: None,
        on_switch_to_cockpit=lambda c: None,
        on_open_followup=lambda c: None,
        on_toggle_complete=lambda c: None,
        on_change_actor=lambda c, a: None,
    )
    board.pack(fill="both", expand=True)
    cases = []
    for i in range(case_count):
        case = Case(
            case_id=f"T-{i:04d}",
            customer=CaseCustomer(customer_id=f"K-{i}", practice_name=f"Praxis {i}"),
            classification=Classification(title=f"Fall {i}"),
            workflow_status=WorkflowStatus(
                current_actor=Actor.DEVELOPMENT if i % 2 else Actor.SUPPORT,
                is_completed=False,
            ),
        )
        cases.append(case)
    board.set_cases(cases)
    return board


def test_collapsing_one_column_replaces_only_that_column():
    root = ctk.CTk()
    root.geometry("1200x700")
    root.withdraw()
    try:
        board = _board(root)
        root.update()

        before = {key: str(frame) for key, frame in board.col_frames.items()}
        assert len(before) == 4

        board.toggle_column_collapse("dev")
        root.update()

        after = {key: str(frame) for key, frame in board.col_frames.items()}
        replaced = [key for key in before if before[key] != after[key]]

        assert replaced == ["dev"], f"Es wurden zu viele Spalten neu gebaut: {replaced}"
        assert set(after) == {"support", "dev", "followup", "completed"}
        assert board.collapsed_states["dev"] is True
        assert "dev" not in board.col_scrolls, "eingeklappte Spalte braucht keinen Scrollbereich"
    finally:
        root.destroy()


def test_collapsing_keeps_the_other_columns_cards_alive():
    """The cached card signatures of untouched columns must survive a toggle."""
    from ui.views.board_view import KanbanCardWidget

    root = ctk.CTk()
    root.geometry("1200x700")
    root.withdraw()
    try:
        board = _board(root)
        root.update()

        support_scroll = board.col_scrolls["support"]
        cards_before = [str(w) for w in support_scroll.winfo_children() if isinstance(w, KanbanCardWidget)]
        assert cards_before, "Testaufbau ohne Karten in 'support'"
        signatures_before = dict(board._col_signatures)

        board.toggle_column_collapse("dev")
        root.update()

        cards_after = [str(w) for w in board.col_scrolls["support"].winfo_children() if isinstance(w, KanbanCardWidget)]
        assert cards_after == cards_before, "Karten fremder Spalten wurden neu gebaut"
        assert board._col_signatures.get("support") == signatures_before.get("support")
    finally:
        root.destroy()


def test_expanding_restores_the_column():
    root = ctk.CTk()
    root.geometry("1200x700")
    root.withdraw()
    try:
        board = _board(root)
        root.update()

        board.toggle_column_collapse("dev")
        root.update()
        assert "dev" not in board.col_scrolls

        board.toggle_column_collapse("dev")
        root.update()

        assert board.collapsed_states["dev"] is False
        assert "dev" in board.col_scrolls
        assert "dev" in board.col_headers
        assert len(board.col_frames) == 4
    finally:
        root.destroy()
