from datetime import datetime, timedelta
import pytest
from models.case import Case, CaseCustomer, Classification, WorkflowStatus
from models.profile import ScoringMatrix
from services.scoring_service import ScoringService
from enums import UrgencyLevel
from utils.datetime_utils import format_iso


@pytest.fixture
def scoring_service():
    matrix = ScoringMatrix(
        vip_bonus_points=50,
        points_per_idle_day=15,
        deadline_close_hours=2,
        deadline_close_bonus=40,
        deadline_overdue_bonus=100,
        threshold_yellow=50,
        threshold_red=100,
    )
    return ScoringService(matrix)


def test_base_case_score(scoring_service):
    now = datetime(2026, 8, 23, 14, 0, 0)
    case = Case(
        case_id="T-001",
        created_at=format_iso(now),
        updated_at=format_iso(now),
        customer=CaseCustomer(is_vip=False),
        classification=Classification(deadline_callback=""),
        workflow_status=WorkflowStatus(actor_since=format_iso(now)),
    )
    score = scoring_service.calculate_score(case, now)
    assert score == 0.0
    assert scoring_service.determine_urgency_level(score) == UrgencyLevel.GREEN


def test_vip_case_score(scoring_service):
    now = datetime(2026, 8, 23, 14, 0, 0)
    case = Case(
        case_id="T-001",
        customer=CaseCustomer(is_vip=True),
        workflow_status=WorkflowStatus(actor_since=format_iso(now)),
    )
    score = scoring_service.calculate_score(case, now)
    assert score == 50.0
    assert scoring_service.determine_urgency_level(score) == UrgencyLevel.YELLOW


def test_idle_days_score(scoring_service):
    now = datetime(2026, 8, 23, 14, 0, 0)
    actor_time = now - timedelta(days=3, hours=5)
    case = Case(
        case_id="T-001",
        customer=CaseCustomer(is_vip=False),
        workflow_status=WorkflowStatus(actor_since=format_iso(actor_time)),
    )
    # 3 full days * 15 = 45 points
    score = scoring_service.calculate_score(case, now)
    assert score == 45.0
    assert scoring_service.determine_urgency_level(score) == UrgencyLevel.GREEN


def test_deadline_close_score(scoring_service):
    now = datetime(2026, 8, 23, 14, 0, 0)
    deadline = now + timedelta(hours=1, minutes=30)  # within 2 hours
    case = Case(
        case_id="T-001",
        classification=Classification(deadline_callback=format_iso(deadline)),
        workflow_status=WorkflowStatus(actor_since=format_iso(now)),
    )
    score = scoring_service.calculate_score(case, now)
    assert score == 40.0


def test_deadline_overdue_score(scoring_service):
    now = datetime(2026, 8, 23, 14, 0, 0)
    deadline = now - timedelta(minutes=10)  # overdue
    case = Case(
        case_id="T-001",
        classification=Classification(deadline_callback=format_iso(deadline)),
        workflow_status=WorkflowStatus(actor_since=format_iso(now)),
    )
    score = scoring_service.calculate_score(case, now)
    assert score == 100.0
    assert scoring_service.determine_urgency_level(score) == UrgencyLevel.RED


def test_update_case_scoring(scoring_service):
    now = datetime(2026, 8, 23, 14, 0, 0)
    deadline = now - timedelta(minutes=10)
    case = Case(
        case_id="T-001",
        customer=CaseCustomer(is_vip=True),  # 50
        classification=Classification(deadline_callback=format_iso(deadline)),  # 100
        workflow_status=WorkflowStatus(actor_since=format_iso(now)),
    )
    score = scoring_service.update_case_scoring(case, now)
    assert score == 150.0
    assert case.classification.calculated_score == 150.0
    assert case.classification.urgency_level == UrgencyLevel.RED


def test_completed_case_score_zero(scoring_service):
    now = datetime(2026, 8, 23, 14, 0, 0)
    case = Case(
        case_id="T-001",
        customer=CaseCustomer(is_vip=True),
        classification=Classification(deadline_callback=format_iso(now - timedelta(days=2))),
        workflow_status=WorkflowStatus(is_completed=True, actor_since=format_iso(now - timedelta(days=5))),
    )
    score = scoring_service.calculate_score(case, now)
    assert score == 0.0
    assert scoring_service.determine_urgency_level(score) == UrgencyLevel.GREEN


def test_archived_case_score_zero(scoring_service):
    now = datetime(2026, 8, 23, 14, 0, 0)
    case = Case(
        case_id="T-001",
        customer=CaseCustomer(is_vip=True),
        workflow_status=WorkflowStatus(is_archived=True, is_completed=True),
    )
    score = scoring_service.calculate_score(case, now)
    assert score == 0.0
    assert scoring_service.determine_urgency_level(score) == UrgencyLevel.GREEN


def test_negative_idle_days_clamped(scoring_service):
    now = datetime(2026, 8, 23, 14, 0, 0)
    future_actor = now + timedelta(days=2)  # Future date
    case = Case(
        case_id="T-001",
        customer=CaseCustomer(is_vip=False),
        workflow_status=WorkflowStatus(actor_since=format_iso(future_actor)),
    )
    score = scoring_service.calculate_score(case, now)
    assert score == 0.0


def test_scoring_with_missing_dates(scoring_service):
    now = datetime(2026, 8, 23, 14, 0, 0)
    case = Case(
        case_id="T-001",
        customer=CaseCustomer(is_vip=False),
        classification=Classification(deadline_callback="INVALID_DATE_STRING"),
        workflow_status=WorkflowStatus(actor_since=""),
    )
    score = scoring_service.calculate_score(case, now)
    assert score == 0.0
