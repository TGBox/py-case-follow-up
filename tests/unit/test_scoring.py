"""Urgency scoring (ScoringService) and the analytics report built on case metrics."""

from datetime import datetime, timedelta

import pytest

from enums import UrgencyLevel
from models.case import Case, CaseCustomer, Classification, WorkflowStatus
from models.profile import ScoringMatrix
from services.scoring_service import ScoringService
from utils.datetime_utils import format_iso

NOW = datetime(2026, 8, 23, 14, 0, 0)
G, Y, R = UrgencyLevel.GREEN, UrgencyLevel.YELLOW, UrgencyLevel.RED


@pytest.fixture
def scoring_service():
    return ScoringService(ScoringMatrix(
        vip_bonus_points=50, points_per_idle_day=15, deadline_close_hours=2, deadline_close_bonus=40,
        deadline_overdue_bonus=100, threshold_yellow=50, threshold_red=100,
    ))


NOW_ISO = format_iso(NOW)


def _case(vip=False, deadline="", actor_since=NOW_ISO, completed=False, archived=False, **kw):
    return Case(
        case_id="T-001",
        customer=CaseCustomer(is_vip=vip),
        classification=Classification(deadline_callback=deadline),
        workflow_status=WorkflowStatus(actor_since=actor_since, is_completed=completed, is_archived=archived),
        **kw,
    )


@pytest.mark.parametrize("case, score, level", [
    (_case(created_at=format_iso(NOW), updated_at=format_iso(NOW)), 0.0, G),
    (_case(vip=True), 50.0, Y),
    (_case(actor_since=format_iso(NOW - timedelta(days=3, hours=5))), 45.0, G),  # 3 full idle days
    (_case(deadline=format_iso(NOW + timedelta(hours=1, minutes=30))), 40.0, G),  # deadline close
    (_case(deadline=format_iso(NOW - timedelta(minutes=10))), 100.0, R),  # overdue
    (_case(actor_since=format_iso(NOW + timedelta(days=2))), 0.0, G),  # future -> idle clamped to 0
    (_case(deadline="INVALID_DATE_STRING", actor_since=""), 0.0, G),
    (_case(vip=True, deadline=format_iso(NOW - timedelta(days=2)),
           actor_since=format_iso(NOW - timedelta(days=5)), completed=True), 0.0, G),
    (_case(vip=True, completed=True, archived=True), 0.0, G),
], ids=["base", "vip", "idle", "deadline-close", "overdue", "future-actor", "invalid-dates", "completed", "archived"])
def test_calculate_score(scoring_service, case, score, level):
    assert scoring_service.calculate_score(case, NOW) == score
    assert scoring_service.determine_urgency_level(score) == level


def test_update_case_scoring_writes_score_and_level(scoring_service):
    case = _case(vip=True, deadline=format_iso(NOW - timedelta(minutes=10)))
    assert scoring_service.update_case_scoring(case, NOW) == 150.0
    assert case.classification.calculated_score == 150.0
    assert case.classification.urgency_level == R


def test_completing_a_case_drops_its_score_to_zero():
    case = _case(vip=True)
    service = ScoringService()
    assert service.calculate_score(case) > 0
    case.workflow_status.is_completed = True
    assert service.calculate_score(case) == 0.0


def test_analytics_report_counts(root):
    from ui.views.analytics_view import AnalyticsView

    view = AnalyticsView(root)
    c1 = Case(case_id="T-01", customer=CaseCustomer(practice_name="Praxis Alpha", is_vip=True),
              classification=Classification(schema_id="schema_zuzahlungsnachforderung"),
              workflow_status=WorkflowStatus(followup_at="2020-01-01T12:00:00"))
    c2 = Case(case_id="T-02", customer=CaseCustomer(practice_name="Praxis Beta"),
              workflow_status=WorkflowStatus(is_completed=True),
              created_at="2026-08-01T10:00:00", updated_at="2026-08-02T10:00:00")
    view.set_cases([c1, c2])

    report = view.generate_report_markdown()
    for line in ("**Fälle Gesamt:** 2", "**Offene Fälle:** 1", "**Erledigte Fälle:** 1",
                 "**Überfällige Wiedervorlagen:** 1"):
        assert line in report
