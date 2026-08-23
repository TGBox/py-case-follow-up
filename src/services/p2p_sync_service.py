import logging
from dataclasses import dataclass
from pathlib import Path
from src.models.case import Case
from src.models.profile import Colleague
from src.services.storage_service import StorageService, safe_read_json
from src.utils.datetime_utils import parse_iso

logger = logging.getLogger("SupportCockpit")


@dataclass
class CaseDiffItem:
    case_id: str
    remote_case: Case
    local_case: Case | None
    status: str  # "NEW", "REMOTE_NEWER", "LOCAL_NEWER", "IDENTICAL"
    remote_updated_at: str
    local_updated_at: str


class P2PSyncService:
    def __init__(self, storage_service: StorageService):
        self.storage = storage_service

    def read_colleague_cases(self, colleague: Colleague) -> tuple[bool, str, list[Case]]:
        """Reads and validates remote cases.json from colleague path."""
        if not colleague.cases_path:
            return False, "Colleague cases path is empty.", []

        cases_path = Path(colleague.cases_path)
        if not cases_path.exists():
            return False, f"Colleague cases file does not exist at: {cases_path}", []

        try:
            data = safe_read_json(cases_path, default_factory=list)
            if not isinstance(data, list):
                return False, "Invalid cases data format in colleague file.", []

            remote_cases = [Case.from_dict(item) for item in data if isinstance(item, dict)]
            valid_cases = []
            for c in remote_cases:
                errors = c.validate()
                if not errors:
                    valid_cases.append(c)
                else:
                    logger.warning(f"Skipping invalid remote case {c.case_id}: {errors}")

            return True, f"Loaded {len(valid_cases)} cases from {colleague.name}.", valid_cases

        except Exception as e:
            logger.error(f"Error reading colleague cases file: {e}")
            return False, f"Error accessing colleague file: {e}", []

    def compute_diff(self, remote_cases: list[Case]) -> list[CaseDiffItem]:
        """Compares remote cases with local cases based on case_id and updated_at."""
        local_cases = {c.case_id: c for c in self.storage.load_cases()}
        diff_items = []

        for r_case in remote_cases:
            l_case = local_cases.get(r_case.case_id)
            if not l_case:
                diff_items.append(CaseDiffItem(
                    case_id=r_case.case_id,
                    remote_case=r_case,
                    local_case=None,
                    status="NEW",
                    remote_updated_at=r_case.updated_at,
                    local_updated_at="",
                ))
            else:
                r_dt = parse_iso(r_case.updated_at) if r_case.updated_at else None
                l_dt = parse_iso(l_case.updated_at) if l_case.updated_at else None

                if r_dt and l_dt:
                    if r_dt > l_dt:
                        status = "REMOTE_NEWER"
                    elif r_dt < l_dt:
                        status = "LOCAL_NEWER"
                    else:
                        status = "IDENTICAL"
                elif r_case.updated_at != l_case.updated_at:
                    status = "REMOTE_NEWER"
                else:
                    status = "IDENTICAL"

                diff_items.append(CaseDiffItem(
                    case_id=r_case.case_id,
                    remote_case=r_case,
                    local_case=l_case,
                    status=status,
                    remote_updated_at=r_case.updated_at,
                    local_updated_at=l_case.updated_at,
                ))

        return diff_items

    def import_selected_cases(self, selected_remote_cases: list[Case]) -> int:
        """Imports selected remote cases into local cases atomically."""
        local_cases = self.storage.load_cases()
        local_map = {c.case_id: i for i, c in enumerate(local_cases)}

        imported_count = 0
        for r_case in selected_remote_cases:
            if r_case.case_id in local_map:
                idx = local_map[r_case.case_id]
                local_cases[idx] = r_case
            else:
                local_cases.append(r_case)
            imported_count += 1

        self.storage.save_cases(local_cases)
        logger.info(f"Imported {imported_count} cases from P2P sync.")
        return imported_count
