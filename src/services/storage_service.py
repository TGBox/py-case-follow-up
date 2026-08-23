import json
import logging
import shutil
from logging.handlers import RotatingFileHandler
from pathlib import Path
from typing import Any, Callable
from datetime import datetime

from config import AppConfig
from models.case import Case
from models.customer import Customer
from models.profile import UserProfile, Colleague
from models.schema import QuestionSchema
from models.export_template import ExportTemplate
from utils.datetime_utils import now_iso, parse_iso, calculate_idle_days

logger = logging.getLogger("SupportCockpit")


def setup_logging(log_path: Path) -> None:
    """Sets up rotating file logging."""
    log_path.parent.mkdir(parents=True, exist_ok=True)
    logger.setLevel(logging.INFO)
    if not logger.handlers:
        handler = RotatingFileHandler(
            log_path, maxBytes=5_000_000, backupCount=3, encoding="utf-8"
        )
        formatter = logging.Formatter(
            "%(asctime)s [%(levelname)s] %(name)s - %(message)s"
        )
        handler.setFormatter(formatter)
        logger.addHandler(handler)


def atomic_save_json(target_path: Path, data: Any) -> None:
    """Atomic JSON save using temporary file and atomic replace."""
    target_path.parent.mkdir(parents=True, exist_ok=True)
    temp_path = target_path.with_name(f"{target_path.name}.tmp.json")
    try:
        with open(temp_path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        temp_path.replace(target_path)
    except Exception as e:
        logger.error(f"Failed atomic save to {target_path}: {e}")
        if temp_path.exists():
            try:
                temp_path.unlink()
            except Exception:
                pass
        raise e


def safe_read_json(
    target_path: Path,
    default_factory: Callable[[], Any] | None = None,
    example_path: Path | None = None,
) -> Any:
    """Reads JSON from target path.
    1. If target_path exists: read and return.
    2. If target_path is missing:
       a. Copy example_path if available.
       b. Otherwise save and return default_factory() value.
    3. If corrupted: backup corrupted file and try example_path or default.
    """
    if not target_path.exists():
        if example_path and example_path.exists():
            try:
                target_path.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(example_path, target_path)
                logger.info(f"Initialized {target_path.name} from example template {example_path}")
            except Exception as copy_err:
                logger.error(f"Could not copy example file {example_path} to {target_path}: {copy_err}")

        if not target_path.exists():
            default_val = default_factory() if default_factory else []
            atomic_save_json(target_path, default_val)
            return default_val

    try:
        with open(target_path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        logger.error(f"Corrupted or unreadable JSON file {target_path}: {e}")
        # Backup corrupted file
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        corrupted_path = target_path.with_suffix(f".corrupted_{timestamp}.json")
        try:
            target_path.rename(corrupted_path)
            logger.info(f"Renamed corrupted file to {corrupted_path}")
        except Exception as rename_err:
            logger.error(f"Could not rename corrupted file: {rename_err}")

        if example_path and example_path.exists():
            try:
                shutil.copy2(example_path, target_path)
                with open(target_path, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception:
                pass

        default_val = default_factory() if default_factory else []
        atomic_save_json(target_path, default_val)
        return default_val


class StorageService:
    def __init__(self, config: AppConfig):
        self.config = config
        self.config.ensure_directories()
        setup_logging(self.config.log_file_path)

    # --- Cases & Archive ---
    def load_cases(self) -> list[Case]:
        data = safe_read_json(
            self.config.cases_path,
            default_factory=list,
            example_path=self.config.get_example_path("cases.json")
        )
        if isinstance(data, list):
            return [Case.from_dict(item) for item in data if isinstance(item, dict)]
        return []

    def save_cases(self, cases: list[Case]) -> None:
        data = [case.to_dict() for case in cases]
        atomic_save_json(self.config.cases_path, data)

    def load_archive(self) -> list[Case]:
        data = safe_read_json(
            self.config.archive_path,
            default_factory=list,
            example_path=self.config.get_example_path("archive.json")
        )
        if isinstance(data, list):
            return [Case.from_dict(item) for item in data if isinstance(item, dict)]
        return []

    def save_archive(self, cases: list[Case]) -> None:
        data = [case.to_dict() for case in cases]
        atomic_save_json(self.config.archive_path, data)

    def archive_single_case(self, case_id: str) -> bool:
        cases = self.load_cases()
        archive = self.load_archive()
        
        target_case = None
        remaining_cases = []
        for c in cases:
            if c.case_id == case_id:
                target_case = c
            else:
                remaining_cases.append(c)
                
        if not target_case:
            return False

        target_case.workflow_status.is_archived = True
        target_case.workflow_status.is_completed = True

        # Avoid duplicates in archive
        archive = [c for c in archive if c.case_id != case_id]
        archive.append(target_case)

        self.save_cases(remaining_cases)
        self.save_archive(archive)
        logger.info(f"Archived case {case_id}")
        return True

    def auto_archive_completed_cases(self, threshold_days: int = 30) -> int:
        """Automatically archives cases completed >= threshold_days ago."""
        cases = self.load_cases()
        archive = self.load_archive()
        
        archived_count = 0
        remaining_cases = []
        
        for c in cases:
            if c.workflow_status.is_completed:
                idle_days = calculate_idle_days(c.updated_at)
                if idle_days >= threshold_days:
                    c.workflow_status.is_archived = True
                    archive = [existing for existing in archive if existing.case_id != c.case_id]
                    archive.append(c)
                    archived_count += 1
                    logger.info(f"Auto-archived case {c.case_id} (idle {idle_days:.1f} days)")
                    continue
            remaining_cases.append(c)

        if archived_count > 0:
            self.save_cases(remaining_cases)
            self.save_archive(archive)
        return archived_count

    def perform_daily_backup(self, date_str: str | None = None) -> Path | None:
        """Performs daily backup of cases.json to backups/cases_YYYY-MM-DD.json."""
        if not date_str:
            date_str = datetime.now().strftime("%Y-%m-%d")
        
        backup_filename = f"cases_{date_str}.json"
        backup_path = self.config.backups_dir / backup_filename
        
        if backup_path.exists():
            return backup_path

        cases = self.load_cases()
        if cases:
            atomic_save_json(backup_path, [c.to_dict() for c in cases])
            logger.info(f"Created daily backup: {backup_path}")
            return backup_path
        return None

    # --- Customers ---
    def load_customers(self) -> list[Customer]:
        data = safe_read_json(
            self.config.customers_path,
            default_factory=list,
            example_path=self.config.get_example_path("customers.json")
        )
        if isinstance(data, list):
            return [Customer.from_dict(item) for item in data if isinstance(item, dict)]
        return []

    def save_customers(self, customers: list[Customer]) -> None:
        data = [c.to_dict() for c in customers]
        atomic_save_json(self.config.customers_path, data)

    # --- Profile ---
    def load_profile(self) -> UserProfile:
        data = safe_read_json(
            self.config.app_profile_path,
            default_factory=dict,
            example_path=self.config.get_example_path("app_profile.json")
        )
        if isinstance(data, dict):
            return UserProfile.from_dict(data)
        return UserProfile()

    def save_profile(self, profile: UserProfile) -> None:
        atomic_save_json(self.config.app_profile_path, profile.to_dict())

    # --- Schemas ---
    def load_schemas(self) -> list[QuestionSchema]:
        data = safe_read_json(
            self.config.question_schemas_path,
            default_factory=lambda: {"schemas": []},
            example_path=self.config.get_example_path("question_schemas.json")
        )
        schemas_raw = data.get("schemas", []) if isinstance(data, dict) else []
        return [QuestionSchema.from_dict(s) for s in schemas_raw if isinstance(s, dict)]

    def save_schemas(self, schemas: list[QuestionSchema]) -> None:
        data = {"schemas": [s.to_dict() for s in schemas]}
        atomic_save_json(self.config.question_schemas_path, data)

    # --- Templates ---
    def load_templates(self) -> list[ExportTemplate]:
        data = safe_read_json(
            self.config.export_templates_path,
            default_factory=lambda: {"templates": []},
            example_path=self.config.get_example_path("export_templates.json")
        )
        templates_raw = data.get("templates", []) if isinstance(data, dict) else []
        return [ExportTemplate.from_dict(t) for t in templates_raw if isinstance(t, dict)]

    def save_templates(self, templates: list[ExportTemplate]) -> None:
        data = {"templates": [t.to_dict() for t in templates]}
        atomic_save_json(self.config.export_templates_path, data)

    # --- Colleagues ---
    def load_colleagues(self) -> list[Colleague]:
        data = safe_read_json(
            self.config.colleagues_path,
            default_factory=list,
            example_path=self.config.get_example_path("colleagues.json")
        )
        if isinstance(data, list):
            return [Colleague.from_dict(item) for item in data if isinstance(item, dict)]
        return []

    def save_colleagues(self, colleagues: list[Colleague]) -> None:
        data = [c.to_dict() for c in colleagues]
        atomic_save_json(self.config.colleagues_path, data)
