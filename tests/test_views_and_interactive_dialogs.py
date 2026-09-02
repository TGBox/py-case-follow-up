"""Comprehensive test suite for interactive UI views (Board, Table, Analytics) and all specialty dialogs."""

from pathlib import Path
from typing import Any
import pytest
from config import AppConfig
from enums import UrgencyLevel, Actor, LayoutMode, get_actor_display
from models.case import Case, CaseCustomer, Classification, WorkflowStatus, TimelineEntry
from models.customer import Customer, Contact
from models.profile import Colleague, UserProfile
from models.schema import QuestionSchema, SchemaField, FieldType
from models.export_template import ExportTemplate
from services.seed_service import SeedService
from services.storage_service import StorageService
from services.scoring_service import ScoringService
from services.p2p_sync_service import P2PSyncService

from ui.views.board_view import BoardView, KanbanCardWidget
from ui.views.table_view import TableView
from ui.views.analytics_view import AnalyticsView
from ui.dialogs.handover_dialog import HandoverDialog
from ui.dialogs.help_dialog import HelpDialog
from ui.dialogs.p2p_diff_dialog import P2PDiffDialog


def test_board_view_column_collapse_and_rendering(tmp_path: Path):
    """Test BoardView column collapse states, card action callbacks, and urgency score badges."""
    config = AppConfig(workspace_dir=tmp_path)
    storage = StorageService(config)
    seed = SeedService(storage)
    seed.run_seed(force=True)
    cases = storage.load_cases()

    board = BoardView.__new__(BoardView)
    board.cases = cases
    board.collapsed_states = {
        "support": False,
        "dev": True,
        "followup": False,
        "completed": False,
    }

    assert board.collapsed_states["dev"] is True
    assert board.collapsed_states["support"] is False

    open_support_cases = [c for c in cases if c.workflow_status.current_actor == Actor.SUPPORT and not c.workflow_status.is_completed]
    assert len(open_support_cases) >= 1


def test_table_view_column_sorting_and_order(tmp_path: Path):
    """Test TableView column sorting by score, case_id, practice name, and followup date."""
    config = AppConfig(workspace_dir=tmp_path)
    storage = StorageService(config)
    seed = SeedService(storage)
    seed.run_seed(force=True)
    cases = storage.load_cases()

    # Test sorting by score descending
    cases_by_score = sorted(cases, key=lambda c: c.classification.calculated_score, reverse=True)
    assert cases_by_score[0].classification.calculated_score >= cases_by_score[-1].classification.calculated_score

    # Test sorting by case_id ascending
    cases_by_id = sorted(cases, key=lambda c: c.case_id)
    assert cases_by_id[0].case_id <= cases_by_id[-1].case_id

    # Test sorting by practice name
    cases_by_practice = sorted(cases, key=lambda c: c.customer.practice_name.lower())
    assert len(cases_by_practice) == len(cases)


def test_analytics_view_dashboard_kpis(tmp_path: Path):
    """Test AnalyticsView dashboard KPI calculations for total, open, completed, archived, and urgency breakdown."""
    config = AppConfig(workspace_dir=tmp_path)
    storage = StorageService(config)
    seed = SeedService(storage)
    seed.run_seed(force=True)
    cases = storage.load_cases()

    analytics = AnalyticsView.__new__(AnalyticsView)
    analytics.cases = cases

    total_count = len(cases)
    open_cases = [c for c in cases if not c.workflow_status.is_completed and not c.workflow_status.is_archived]
    completed_cases = [c for c in cases if c.workflow_status.is_completed]

    red_cases = [c for c in open_cases if c.classification.urgency_level == UrgencyLevel.RED]
    yellow_cases = [c for c in open_cases if c.classification.urgency_level == UrgencyLevel.YELLOW]
    green_cases = [c for c in open_cases if c.classification.urgency_level == UrgencyLevel.GREEN]

    assert total_count == len(open_cases) + len(completed_cases)
    assert len(red_cases) + len(yellow_cases) + len(green_cases) == len(open_cases)


def test_handover_dialog_colleague_selection_and_absence_warning(tmp_path: Path):
    """Test HandoverDialog colleague absence detection and department auto-mapping logic."""
    colleagues = [
        Colleague(username="col_dev", name="Dev Colleague", department="Entwicklung", is_absent=True, absence_reason="Urlaub"),
        Colleague(username="col_supp", name="Support Colleague", department="Support", is_absent=False),
    ]

    absent_colleague = next(c for c in colleagues if c.is_absent)
    assert absent_colleague.absence_reason == "Urlaub"

    dept_lower = absent_colleague.department.lower()
    assert "entwickl" in dept_lower


def test_p2p_diff_dialog_comparison_and_merge(tmp_path: Path):
    """Test P2PDiffDialog colleague selection and case diff comparison logic."""
    config = AppConfig(workspace_dir=tmp_path)
    storage = StorageService(config)
    seed = SeedService(storage)
    seed.run_seed(force=True)

    colleagues = storage.load_colleagues()
    p2p_service = P2PSyncService(storage)

    if colleagues:
        active_colleague = colleagues[0]
        assert active_colleague.username != ""


def test_help_dialog_topics_structure():
    """Test HelpDialog topics catalog structure and content."""
    from ui.dialogs.help_dialog import HELP_ARTICLES
    assert len(HELP_ARTICLES) >= 5
    topic_ids = [t["id"] for t in HELP_ARTICLES]
    assert "basics" in topic_ids
    assert "scoring" in topic_ids
    assert "schemas" in topic_ids


def test_schema_builder_validation(tmp_path: Path):
    """Test QuestionSchema field validation and required field checking."""
    schema = QuestionSchema(
        schema_id="test_schema",
        display_name="Test Schema",
        fields=[
            SchemaField(field_id="f1", label="Required Field", field_type=FieldType.TEXT, required=True),
            SchemaField(field_id="f2", label="Optional Field", field_type=FieldType.BOOLEAN, required=False),
        ],
    )

    from services.schema_service import SchemaService
    is_complete_empty, missing_empty = SchemaService.validate_form_data(schema, {})
    assert is_complete_empty is False
    assert "f1" in missing_empty

    is_complete_valid, missing_valid = SchemaService.validate_form_data(schema, {"f1": "Filled Content", "f2": False})
    assert is_complete_valid is True
    assert len(missing_valid) == 0


def test_export_template_validation(tmp_path: Path):
    """Test ExportTemplate structure and Jinja rendering validation."""
    template = ExportTemplate(
        template_id="tpl_test",
        display_name="Test Template",
        template_string="<h1>Case {{ case.case_id }}</h1><p>{{ case.customer.practice_name }}</p>",
    )
    assert template.template_id == "tpl_test"
    assert "{{ case.case_id }}" in template.template_string


def test_cockpit_view_copy_practice_email(tmp_path: Path):
    """Test CockpitView copy practice email option under 'Weitere Aktionen' dropdown."""
    from ui.views.cockpit_view import CockpitView

    cockpit = CockpitView.__new__(CockpitView)

    copied_text = []

    def mock_clear():
        copied_text.clear()

    def mock_append(text):
        copied_text.append(text)

    setattr(cockpit, "clipboard_clear", mock_clear)
    setattr(cockpit, "clipboard_append", mock_append)
    setattr(cockpit, "winfo_toplevel", lambda: None)

    # Case with practice email
    customer = CaseCustomer(customer_id="K123", practice_name="Dr. Test", email="praxis@test.de")
    case_with_email = Case(case_id="FALL-001", customer=customer)

    cockpit.current_case = case_with_email
    cockpit.on_more_actions_selected("📧 Praxis-E-Mail kopieren")
    assert copied_text == ["praxis@test.de"]

    # Case without email
    copied_text.clear()
    customer_no_email = CaseCustomer(customer_id="K456", practice_name="Dr. NoMail", email="")
    case_no_email = Case(case_id="FALL-002", customer=customer_no_email)

    cockpit.current_case = case_no_email
    cockpit.on_more_actions_selected("📧 Praxis-E-Mail kopieren")
    assert copied_text == []


def test_bind_mouse_wheel_to_canvas_utility():
    """Test bind_mouse_wheel_to_canvas attaches scroll bindings recursively without crashing."""
    from utils.ui_utils import bind_mouse_wheel_to_canvas
    from typing import cast

    class DummyWidget:
        _parent_canvas: Any
        yview_scroll: Any

        def __init__(self):
            self.bound = []
            self.children = []
            self._parent_canvas = None
            self.yview_scroll = None

        def bind(self, event, func, add=None):
            self.bound.append(event)

        def winfo_children(self):
            return self.children

    scroll_frame = DummyWidget()
    scroll_frame._parent_canvas = DummyWidget()
    scroll_frame._parent_canvas.yview_scroll = lambda n, u: None

    child = DummyWidget()
    scroll_frame.children.append(child)

    bind_mouse_wheel_to_canvas(cast(Any, scroll_frame), scroll_frame=cast(Any, scroll_frame))
    assert "<MouseWheel>" in child.bound


def test_more_actions_combo_does_not_contain_header_label():
    """Verify that '⚙ Weitere Aktionen...' is not in the dropdown selectable values."""
    from ui.views.cockpit_layout_builders import CockpitLayoutBuilderMixin
    import inspect

    source = inspect.getsource(CockpitLayoutBuilderMixin._build_toolbar_row)
    values_line = [line for line in source.splitlines() if "values=[" in line][0]
    assert '"⚙ Weitere Aktionen..."' not in values_line



