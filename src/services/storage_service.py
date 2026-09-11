import json
import logging
import shutil
import threading
from logging.handlers import RotatingFileHandler
from pathlib import Path
from typing import Any
from collections.abc import Callable
from datetime import datetime

from config import AppConfig
from models.case import Case
from models.customer import Customer
from models.profile import UserProfile, Colleague
from models.schema import QuestionSchema
from models.export_template import ExportTemplate
from utils.datetime_utils import calculate_idle_days

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
        with open(target_path, encoding="utf-8") as f:
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
                with open(target_path, encoding="utf-8") as f:
                    return json.load(f)
            except Exception as fallback_err:
                # Both the user file AND the example template failed - without this
                # log line the user silently starts with empty data and there is no
                # trace in the log explaining why.
                logger.error(f"Fallback from example template {example_path} failed for {target_path}: {fallback_err}")

        default_val = default_factory() if default_factory else []
        atomic_save_json(target_path, default_val)
        return default_val


class DebouncedSaver:
    """Buffers and debounces background disk save operations per target file path."""
    def __init__(self):
        self._timers: dict[Path, threading.Timer] = {}
        self._data: dict[Path, Any] = {}
        self._lock = threading.Lock()

    def save_debounced(self, target_path: Path, data_or_producer: Any, delay_seconds: float = 0.15):
        with self._lock:
            self._data[target_path] = data_or_producer
            if target_path in self._timers:
                self._timers[target_path].cancel()

            def flush():
                with self._lock:
                    val = self._data.pop(target_path, None)
                    self._timers.pop(target_path, None)
                if val is not None:
                    try:
                        data = val() if callable(val) else val
                        atomic_save_json(target_path, data)
                    except Exception as e:
                        logger.error(f"Debounced background save failed for {target_path}: {e}")

            timer = threading.Timer(delay_seconds, flush)
            timer.daemon = True
            self._timers[target_path] = timer
            timer.start()

    def flush_all(self):
        """Immediately flushes all pending debounced saves synchronously (used on app exit)."""
        with self._lock:
            pending_data = dict(self._data)
            for timer in self._timers.values():
                timer.cancel()
            self._timers.clear()
            self._data.clear()

        for path, val in pending_data.items():
            try:
                data = val() if callable(val) else val
                atomic_save_json(path, data)
            except Exception as e:
                logger.error(f"Flush save failed for {path}: {e}")


class StorageService:
    def __init__(self, config: AppConfig):
        self.config = config
        self.config.ensure_directories()
        setup_logging(self.config.log_file_path)

        self._cases_cache: list[Case] | None = None
        self._archive_cache: list[Case] | None = None
        self._profile_cache: UserProfile | None = None
        self._customers_cache: list[Customer] | None = None
        self._schemas_cache: list[QuestionSchema] | None = None
        self._templates_cache: list[ExportTemplate] | None = None
        self._colleagues_cache: list[Colleague] | None = None
        self.saver = DebouncedSaver()

    def flush_all_saves(self) -> None:
        """Flushes all pending background saves to disk synchronously."""
        self.saver.flush_all()

    def invalidate_cache(self) -> None:
        """Clears all in-memory caches and flushes pending writes to force fresh disk reads."""
        self.flush_all_saves()
        self._cases_cache = None
        self._archive_cache = None
        self._profile_cache = None
        self._customers_cache = None
        self._schemas_cache = None
        self._templates_cache = None
        self._colleagues_cache = None

    # --- Cases & Archive ---
    def load_cases(self, use_cache: bool = True) -> list[Case]:
        if use_cache and self._cases_cache is not None:
            return self._cases_cache

        data = safe_read_json(
            self.config.cases_path,
            default_factory=list,
            example_path=self.config.get_example_path("cases.json")
        )
        if isinstance(data, list):
            self._cases_cache = [Case.from_dict(item) for item in data if isinstance(item, dict)]
        else:
            self._cases_cache = []
        return self._cases_cache

    def save_cases(self, cases: list[Case], sync: bool = False) -> None:
        self._cases_cache = cases
        if sync:
            data = [case.to_dict() for case in cases]
            atomic_save_json(self.config.cases_path, data)
        else:
            cases_snapshot = list(cases)
            self.saver.save_debounced(
                self.config.cases_path,
                lambda: [c.to_dict() for c in cases_snapshot]
            )

    def update_single_case(self, case: Case) -> None:
        """Updates or adds a single case in the cache and persists the cases file."""
        cases = self.load_cases(use_cache=True)
        updated = False
        for idx, existing in enumerate(cases):
            if existing.case_id == case.case_id:
                cases[idx] = case
                updated = True
                break
        if not updated:
            cases.append(case)
        self.save_cases(cases)

    def load_archive(self, use_cache: bool = True) -> list[Case]:
        if use_cache and self._archive_cache is not None:
            return self._archive_cache

        data = safe_read_json(
            self.config.archive_path,
            default_factory=list,
            example_path=self.config.get_example_path("archive.json")
        )
        if isinstance(data, list):
            self._archive_cache = [Case.from_dict(item) for item in data if isinstance(item, dict)]
        else:
            self._archive_cache = []
        return self._archive_cache

    def save_archive(self, cases: list[Case], sync: bool = False) -> None:
        self._archive_cache = cases
        if sync:
            data = [case.to_dict() for case in cases]
            atomic_save_json(self.config.archive_path, data)
        else:
            cases_snapshot = list(cases)
            self.saver.save_debounced(
                self.config.archive_path,
                lambda: [c.to_dict() for c in cases_snapshot]
            )

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

        # Index the archive by case_id once instead of rebuilding the whole
        # archive list per archived case (that was O(archived x archive size)
        # and runs on every app start).
        archive_by_id: dict[str, Case] = {}
        archive_order: list[str] = []
        for existing in archive:
            if existing.case_id not in archive_by_id:
                archive_order.append(existing.case_id)
            archive_by_id[existing.case_id] = existing

        for c in cases:
            if c.workflow_status.is_completed:
                idle_days = calculate_idle_days(c.updated_at)
                if idle_days >= threshold_days:
                    c.workflow_status.is_archived = True
                    if c.case_id not in archive_by_id:
                        archive_order.append(c.case_id)
                    archive_by_id[c.case_id] = c
                    archived_count += 1
                    logger.info(f"Auto-archived case {c.case_id} (idle {idle_days:.1f} days)")
                    continue
            remaining_cases.append(c)

        if archived_count > 0:
            archive = [archive_by_id[cid] for cid in archive_order]
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
    def load_customers(self, use_cache: bool = True) -> list[Customer]:
        if use_cache and self._customers_cache is not None:
            return self._customers_cache

        data = safe_read_json(
            self.config.customers_path,
            default_factory=list,
            example_path=self.config.get_example_path("customers.json")
        )
        if isinstance(data, list):
            self._customers_cache = [Customer.from_dict(item) for item in data if isinstance(item, dict)]
        else:
            self._customers_cache = []
        return self._customers_cache

    def save_customers(self, customers: list[Customer], sync: bool = False) -> None:
        self._customers_cache = customers
        if sync:
            data = [c.to_dict() for c in customers]
            atomic_save_json(self.config.customers_path, data)
        else:
            customers_snapshot = list(customers)
            self.saver.save_debounced(
                self.config.customers_path,
                lambda: [c.to_dict() for c in customers_snapshot]
            )

    # --- Profile ---
    @property
    def profiles_dir(self) -> Path:
        p_dir = self.config.data_dir / "profiles"
        p_dir.mkdir(parents=True, exist_ok=True)
        return p_dir

    def list_profiles(self) -> list[str]:
        """Lists available user profile usernames."""
        curr_profile = self.load_profile()
        profiles = [curr_profile.user.name]
        if self.profiles_dir.exists():
            for f in self.profiles_dir.glob("*.json"):
                try:
                    with open(f, encoding="utf-8") as file:
                        data = json.load(file)
                    name = data.get("user", {}).get("name")
                    if name and name not in profiles:
                        profiles.append(name)
                except Exception as profile_err:
                    logger.warning(f"Skipping unreadable profile file {f}: {profile_err}")
        return profiles

    def load_profile(self, use_cache: bool = True) -> UserProfile:
        if use_cache and self._profile_cache is not None:
            return self._profile_cache

        data = safe_read_json(
            self.config.app_profile_path,
            default_factory=dict,
            example_path=self.config.get_example_path("app_profile.json")
        )
        if isinstance(data, dict):
            self._profile_cache = UserProfile.from_dict(data)
        else:
            self._profile_cache = UserProfile()
        return self._profile_cache

    def load_profile_by_name(self, profile_name: str) -> UserProfile:
        """Loads UserProfile by user name from profiles_dir or falls back to active profile."""
        safe_filename = "".join(c for c in profile_name if c.isalnum() or c in (" ", "_", "-")).strip().replace(" ", "_")
        target_path = self.profiles_dir / f"profile_{safe_filename}.json"

        if target_path.exists():
            data = safe_read_json(target_path, default_factory=dict)
            if isinstance(data, dict):
                return UserProfile.from_dict(data)

        return self.load_profile()

    def save_profile(self, profile: UserProfile, sync: bool = False) -> None:
        self._profile_cache = profile
        p_dict: dict[str, Any] | None = None
        if sync:
            p_dict = profile.to_dict()
            atomic_save_json(self.config.app_profile_path, p_dict)
        else:
            self.saver.save_debounced(self.config.app_profile_path, lambda: profile.to_dict())
        safe_filename = "".join(c for c in profile.user.name if c.isalnum() or c in (" ", "_", "-")).strip().replace(" ", "_")
        if safe_filename:
            target_path = self.profiles_dir / f"profile_{safe_filename}.json"
            if sync:
                if p_dict is None:
                    p_dict = profile.to_dict()
                atomic_save_json(target_path, p_dict)
            else:
                self.saver.save_debounced(target_path, lambda: profile.to_dict())

    # --- Schemas ---
    def load_schemas(self, use_cache: bool = True) -> list[QuestionSchema]:
        if use_cache and self._schemas_cache is not None:
            return self._schemas_cache

        data = safe_read_json(
            self.config.question_schemas_path,
            default_factory=lambda: {"schemas": []},
            example_path=self.config.get_example_path("question_schemas.json")
        )
        schemas_raw = data.get("schemas", []) if isinstance(data, dict) else []
        loaded_schemas = [QuestionSchema.from_dict(s) for s in schemas_raw if isinstance(s, dict)]
        self._schemas_cache = loaded_schemas
        return self._schemas_cache

    def _create_safety_backup(self, path: Path) -> None:
        """Creates a safety backup (.bak) of the given file before destructive or modifying operations."""
        if path.exists():
            try:
                bak_path = path.with_suffix(path.suffix + ".bak")
                shutil.copy2(path, bak_path)
                logger.info(f"Created safety backup at {bak_path}")
            except Exception as e:
                logger.warning(f"Failed to create safety backup for {path}: {e}")

    def get_default_schemas(self) -> list[QuestionSchema]:
        """Loads and returns default schemas from data_examples/question_schemas.json."""
        example_path = self.config.get_example_path("question_schemas.json")
        if example_path and example_path.exists():
            try:
                with open(example_path, encoding="utf-8") as f:
                    ex_data = json.load(f)
                ex_raw = ex_data.get("schemas", []) if isinstance(ex_data, dict) else []
                return [QuestionSchema.from_dict(s) for s in ex_raw if isinstance(s, dict)]
            except Exception as e:
                logger.warning(f"Failed to load default schemas from {example_path}: {e}")
        return []

    def has_default_schemas(self) -> bool:
        """Returns True if all default schemas are present in the current schema list."""
        defaults = self.get_default_schemas()
        if not defaults:
            return False
        curr_ids = {s.schema_id for s in self.load_schemas()}
        return all(d.schema_id in curr_ids for d in defaults)

    def toggle_default_schemas(self) -> tuple[list[QuestionSchema], bool]:
        """Toggles default schemas: adds them if missing, or removes only defaults if present.
        Existing custom schemas created by the user are never deleted.
        Automatically creates a safety backup.
        Returns: (updated_schemas_list, is_added: bool)
        """
        self._create_safety_backup(self.config.question_schemas_path)
        curr = list(self.load_schemas(use_cache=False))
        defaults = self.get_default_schemas()
        default_ids = {d.schema_id for d in defaults}

        if self.has_default_schemas():
            # Remove ONLY default schemas; keep all custom user schemas!
            updated = [s for s in curr if s.schema_id not in default_ids]
            is_added = False
        else:
            # Add missing default schemas; keep all existing custom user schemas!
            existing_ids = {s.schema_id for s in curr}
            to_add = [d for d in defaults if d.schema_id not in existing_ids]
            updated = curr + to_add
            is_added = True

        self.save_schemas(updated, sync=True)
        return updated, is_added

    def save_schemas(self, schemas: list[QuestionSchema], sync: bool = False) -> None:
        self._schemas_cache = schemas
        if sync:
            data = {"schemas": [s.to_dict() for s in schemas]}
            atomic_save_json(self.config.question_schemas_path, data)
        else:
            schemas_snapshot = list(schemas)
            self.saver.save_debounced(
                self.config.question_schemas_path,
                lambda: {"schemas": [s.to_dict() for s in schemas_snapshot]}
            )

    def reset_schemas_to_defaults(self) -> list[QuestionSchema]:
        """Overwrites working schemas with data_examples/question_schemas.json with safety backup."""
        self._create_safety_backup(self.config.question_schemas_path)
        self._schemas_cache = None
        example_path = self.config.get_example_path("question_schemas.json")
        if example_path and example_path.exists():
            shutil.copy2(example_path, self.config.question_schemas_path)
            logger.info(f"Reset {self.config.question_schemas_path.name} from example template.")
        return self.load_schemas(use_cache=False)

    # --- Templates ---
    def load_templates(self, use_cache: bool = True) -> list[ExportTemplate]:
        if use_cache and self._templates_cache is not None:
            return self._templates_cache

        data = safe_read_json(
            self.config.export_templates_path,
            default_factory=lambda: {"templates": []},
            example_path=self.config.get_example_path("export_templates.json")
        )
        templates_raw = data.get("templates", []) if isinstance(data, dict) else []
        loaded_templates = [ExportTemplate.from_dict(t) for t in templates_raw if isinstance(t, dict)]
        self._templates_cache = loaded_templates
        return self._templates_cache

    def get_default_templates(self) -> list[ExportTemplate]:
        """Loads and returns default templates from data_examples/export_templates.json."""
        example_path = self.config.get_example_path("export_templates.json")
        if example_path and example_path.exists():
            try:
                with open(example_path, encoding="utf-8") as f:
                    ex_data = json.load(f)
                ex_raw = ex_data.get("templates", []) if isinstance(ex_data, dict) else []
                return [ExportTemplate.from_dict(t) for t in ex_raw if isinstance(t, dict)]
            except Exception as e:
                logger.warning(f"Failed to load default templates from {example_path}: {e}")
        return []

    def has_default_templates(self) -> bool:
        """Returns True if all default templates are present in the current template list."""
        defaults = self.get_default_templates()
        if not defaults:
            return False
        curr_ids = {t.template_id for t in self.load_templates()}
        return all(d.template_id in curr_ids for d in defaults)

    def toggle_default_templates(self) -> tuple[list[ExportTemplate], bool]:
        """Toggles default templates: adds them if missing, or removes only defaults if present.
        Existing custom templates created by the user are never deleted.
        Automatically creates a safety backup.
        Returns: (updated_templates_list, is_added: bool)
        """
        self._create_safety_backup(self.config.export_templates_path)
        curr = list(self.load_templates(use_cache=False))
        defaults = self.get_default_templates()
        default_ids = {d.template_id for d in defaults}

        if self.has_default_templates():
            # Remove ONLY default templates; keep all custom user templates!
            updated = [t for t in curr if t.template_id not in default_ids]
            is_added = False
        else:
            # Add missing default templates; keep all existing custom user templates!
            existing_ids = {t.template_id for t in curr}
            to_add = [d for d in defaults if d.template_id not in existing_ids]
            updated = curr + to_add
            is_added = True

        self.save_templates(updated, sync=True)
        return updated, is_added

    def save_templates(self, templates: list[ExportTemplate], sync: bool = False) -> None:
        self._templates_cache = templates
        data = {"templates": [t.to_dict() for t in templates]}
        if sync:
            atomic_save_json(self.config.export_templates_path, data)
        else:
            self.saver.save_debounced(self.config.export_templates_path, data)

    def reset_templates_to_defaults(self) -> list[ExportTemplate]:
        """Overwrites working templates with data_examples/export_templates.json with safety backup."""
        self._create_safety_backup(self.config.export_templates_path)
        self._templates_cache = None
        example_path = self.config.get_example_path("export_templates.json")
        if example_path and example_path.exists():
            shutil.copy2(example_path, self.config.export_templates_path)
            logger.info(f"Reset {self.config.export_templates_path.name} from example template.")
        return self.load_templates(use_cache=False)

    # --- Colleagues ---
    def load_colleagues(self, use_cache: bool = True) -> list[Colleague]:
        if use_cache and self._colleagues_cache is not None:
            return self._colleagues_cache

        data = safe_read_json(
            self.config.colleagues_path,
            default_factory=list,
            example_path=self.config.get_example_path("colleagues.json")
        )
        if isinstance(data, list):
            self._colleagues_cache = [Colleague.from_dict(item) for item in data if isinstance(item, dict)]
        else:
            self._colleagues_cache = []
        return self._colleagues_cache

    def save_colleagues(self, colleagues: list[Colleague], sync: bool = False) -> None:
        self._colleagues_cache = colleagues
        data = [c.to_dict() for c in colleagues]
        if sync:
            atomic_save_json(self.config.colleagues_path, data)
        else:
            self.saver.save_debounced(self.config.colleagues_path, data)
