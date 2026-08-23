import math
from datetime import datetime
from src.models.case import Case
from src.models.profile import ScoringMatrix
from src.enums import UrgencyLevel
from src.utils.datetime_utils import get_local_now, calculate_idle_days, hours_until_deadline


class ScoringService:
    def __init__(self, matrix: ScoringMatrix | None = None):
        self.matrix = matrix or ScoringMatrix()

    def update_matrix(self, matrix: ScoringMatrix) -> None:
        self.matrix = matrix

    def calculate_score(self, case: Case, now: datetime | None = None) -> float:
        """Calculates urgency score according to SRS formula."""
        ref_now = now or get_local_now()

        # 1. VIP Bonus
        vip_points = self.matrix.vip_bonus_points if case.customer.is_vip else 0

        # 2. Idle Days (floor(idle_days) * points_per_idle_day)
        actor_time = case.workflow_status.actor_since or case.updated_at or case.created_at
        idle_days = calculate_idle_days(actor_time, ref_now)
        full_idle_days = math.floor(idle_days)
        idle_points = full_idle_days * self.matrix.points_per_idle_day

        # 3. Deadline Bonus
        deadline_points = 0
        if case.classification.deadline_callback:
            h_until_deadline = hours_until_deadline(case.classification.deadline_callback, ref_now)
            if h_until_deadline < 0:
                # Overdue
                deadline_points = self.matrix.deadline_overdue_bonus
            elif h_until_deadline <= self.matrix.deadline_close_hours:
                # Close to deadline
                deadline_points = self.matrix.deadline_close_bonus

        total_score = float(vip_points + idle_points + deadline_points)
        return total_score

    def determine_urgency_level(self, score: float) -> UrgencyLevel:
        """Assigns GREEN, YELLOW, or RED urgency level based on thresholds."""
        if score >= self.matrix.threshold_red:
            return UrgencyLevel.RED
        elif score >= self.matrix.threshold_yellow:
            return UrgencyLevel.YELLOW
        else:
            return UrgencyLevel.GREEN

    def update_case_scoring(self, case: Case, now: datetime | None = None) -> float:
        """Calculates score, updates classification fields on the case, and returns score."""
        score = self.calculate_score(case, now)
        urgency = self.determine_urgency_level(score)
        case.classification.calculated_score = score
        case.classification.urgency_level = urgency
        return score
