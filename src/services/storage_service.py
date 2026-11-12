import filecmp
import json
import logging
import os
import re
import shutil
import threading
import time
from logging.handlers import RotatingFileHandler
from pathlib import Path
from typing import Any
from collections.abc import Callable
from datetime import datetime, date

from config import AppConfig
from constants import (
    ATOMIC_REPLACE_RETRIES,
    ATOMIC_REPLACE_RETRY_DELAY_SECONDS,
    ATTACHMENTS_DIRNAME,
    BACKUP_SERIES_CASES,
    DAYS_PER_MONTH,
    DAYS_PER_WEEK,
    DEBOUNCE_DELAY_STORAGE_SAVE,
    DEFAULT_AUTO_ARCHIVE_THRESHOLD_DAYS,
    JSON_INDENT,
    LOG_BACKUP_COUNT,
    LOG_MAX_BYTES,
    REGEX_DATA_BACKUP,
    SAFETY_SNAPSHOT_TIMESTAMP_FORMAT,
    SNIPPETS_BACKUP_SOURCE_FILENAME,
    STALE_TEMP_FILE_MAX_AGE_SECONDS,
    TEMP_JSON_GLOB,
    REL_ATTACHMENTS_DIR,
    TIMEOUT_STORAGE_FLUSH_ALL,
    TIMEOUT_STORAGE_WRITE_COND,
)
from models.case import Case
from models.customer import Customer
from models.profile import UserProfile, Colleague, BackupSettings
from models.schema import QuestionSchema
from models.export_template import ExportTemplate
from utils.datetime_utils import calculate_idle_days

logger = logging.getLogger("SupportCockpit")

# The path overrides a profile carries, named identically on PathSettings and on
# AppConfig. Seeding (load_profile) and applying (apply_profile_paths) both walk
# this tuple so the two can no longer cover different sets of fields.
PROFILE_PATH_OVERRIDES: tuple[str, ...] = (
    "custom_cases_path",
    "custom_archive_path",
    "custom_customers_path",
    "custom_app_profile_path",
    "custom_colleagues_path",
    "custom_question_schemas_path",
    "custom_export_templates_path",
    "custom_wiki_db_path",
)


def setup_logging(log_path: Path) -> None:
    """Sets up rotating file logging.

    The handler sits on the "SupportCockpit" logger. Modules log either to it
    directly or to a child such as "SupportCockpit.transit", which propagates
    here and keeps its own name in the log line. A logger outside that tree
    (e.g. getLogger(__name__)) never reaches app.log.
    """
    log_path.parent.mkdir(parents=True, exist_ok=True)
    logger.setLevel(logging.INFO)
    if not logger.handlers:
        handler = RotatingFileHandler(
            log_path, maxBytes=LOG_MAX_BYTES, backupCount=LOG_BACKUP_COUNT, encoding="utf-8"
        )
        formatter = logging.Formatter(
            "%(asctime)s [%(levelname)s] %(name)s - %(message)s"
        )
        handler.setFormatter(formatter)
        logger.addHandler(handler)


def _replace_with_retry(source: Path, target: Path) -> None:
    """Path.replace that survives a target briefly held open by another handle.

    On Windows os.replace() raises PermissionError while any other handle has
    the target file open without FILE_SHARE_DELETE - which is how Python (and
    most readers) open files. A concurrent read of the same JSON, a virus
    scanner or a sync client is enough, and without a retry the save was lost.
    """
    for attempt in range(ATOMIC_REPLACE_RETRIES):
        try:
            source.replace(target)
            return
        except PermissionError:
            if attempt == ATOMIC_REPLACE_RETRIES - 1:
                raise
            time.sleep(ATOMIC_REPLACE_RETRY_DELAY_SECONDS)


def _read_json_with_retry(path: Path) -> Any:
    """json.load that survives the file being replaced at that very moment.

    The mirror image of _replace_with_retry: while atomic_save_json swaps the
    file in, Windows answers a concurrent open() with PermissionError. Without
    the retry that transient error was taken for a corrupted file, and an
    intact app_profile.json was renamed away as .corrupted_*.
    """
    for attempt in range(ATOMIC_REPLACE_RETRIES):
        try:
            with open(path, encoding="utf-8") as f:
                return json.load(f)
        except PermissionError:
            if attempt == ATOMIC_REPLACE_RETRIES - 1:
                raise
            time.sleep(ATOMIC_REPLACE_RETRY_DELAY_SECONDS)


#: Serialises the final "move the temp file over the target" step of every
#: writer in this process, so the order of commits is well defined.
_COMMIT_LOCK = threading.Lock()


def atomic_save_json(
    target_path: Path,
    data: Any,
    temp_tag: str = "",
    should_commit: Callable[[], bool] | None = None,
) -> bool:
    """Atomic JSON save using a temporary file and an atomic replace.

    Every writer gets a temp file of its own (process id + thread id, plus the
    optional temp_tag). They used to share "<name>.tmp.json": when a debounced
    background save and a flush on the main thread hit the same target at the
    same moment, both wrote into that one file. The result was interleaved
    JSON moved into place by whoever finished first - a corrupted cases.json -
    and a "file not found" for the other one.

    should_commit is asked under the commit lock, immediately before the
    replace. Returning False drops this write (the temp file is removed) - that
    is how a save that was overtaken by a newer one is kept from landing last.
    Returns True if the target was replaced.
    """
    target_path.parent.mkdir(parents=True, exist_ok=True)
    writer = f"{os.getpid()}-{threading.get_ident()}"
    tag = f".{temp_tag}" if temp_tag else ""
    temp_path = target_path.with_name(f"{target_path.name}.{writer}{tag}.tmp.json")
    try:
        with open(temp_path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=JSON_INDENT, ensure_ascii=False)
        with _COMMIT_LOCK:
            if should_commit is not None and not should_commit():
                temp_path.unlink(missing_ok=True)
                return False
            _replace_with_retry(temp_path, target_path)
        return True
    except Exception as e:
        logger.error(f"Failed atomic save to {target_path}: {e}")
        if temp_path.exists():
            try:
                temp_path.unlink()
            except Exception:
                pass
        raise e


class StorageReadError(OSError):
    """A data file exists but could not be read (or safely set aside).

    Raised instead of quietly replacing the file: an unreachable network
    share, a lock that outlasts the retries or a failed rename say nothing
    about the content, and treating them as corruption overwrote intact data
    with the example template or an empty list.
    """


def read_json_readonly(path: Path) -> Any:
    """Reads a JSON file without ever creating, renaming or rewriting it.

    For files this app does not own - above all a colleague's cases.json on a
    share. Raises OSError if the file cannot be read and ValueError if it is
    not valid JSON; the file is left exactly as it was either way.
    """
    return _read_json_with_retry(path)


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
    3. If the content is not valid JSON: set the file aside as .corrupted_*
       and try example_path or default. If it cannot be set aside, nothing is
       overwritten and StorageReadError is raised.
    4. If the file cannot be read at all (I/O error): StorageReadError, the
       file stays untouched.
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
        return _read_json_with_retry(target_path)
    except OSError as e:
        # Not a statement about the content: the file may be perfectly fine.
        logger.error(f"Could not read {target_path} (left untouched): {e}")
        raise StorageReadError(f"Could not read {target_path}: {e}") from e
    except ValueError as e:
        # json.JSONDecodeError and UnicodeDecodeError: the content itself is broken.
        logger.error(f"Corrupted JSON file {target_path}: {e}")
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        corrupted_path = target_path.with_suffix(f".corrupted_{timestamp}.json")
        try:
            target_path.rename(corrupted_path)
            logger.info(f"Renamed corrupted file to {corrupted_path}")
        except OSError as rename_err:
            # Without the rename the fallback below would overwrite the only
            # copy of whatever is still recoverable from the file.
            logger.error(f"Could not set corrupted file {target_path} aside: {rename_err}")
            raise StorageReadError(
                f"{target_path} is corrupted and could not be set aside: {rename_err}"
            ) from rename_err

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
    """Buffers and debounces background disk save operations per target file path.

    Every save gets a generation number when it is handed in. Whatever thread
    ends up writing it - the debounce timer, flush_all() or save_now() - the
    write is only moved into place if no newer generation of that file is on
    disk already. Writers can therefore overlap freely: the newest data wins,
    never the writer that happened to finish last.
    """
    def __init__(self):
        self._timers: dict[Path, threading.Timer] = {}
        #: Saves waiting for their debounce timer: path -> (generation, data or producer).
        self._data: dict[Path, tuple[int, Any]] = {}
        self._lock = threading.Lock()
        #: Background writes that are running right now: path -> {generation: data or producer},
        #: so flush_all can write them itself if one never finishes.
        self._active: dict[Path, dict[int, Any]] = {}
        self._write_cond = threading.Condition(self._lock)
        self._next_generation = 0
        #: Newest generation that reached the disk, per path.
        self._committed: dict[Path, int] = {}
        #: Saves older than this were discarded (discard_pending) and must not land any more.
        self._discard_floor = 0

    def _new_generation(self) -> int:
        """Call with self._lock held."""
        self._next_generation += 1
        return self._next_generation

    def _write(self, target_path: Path, generation: int, val: Any, temp_tag: str = "") -> bool:
        """Serialises and saves one generation; False if a newer one made it obsolete."""
        def still_newest() -> bool:
            with self._lock:
                if generation < self._discard_floor or generation < self._committed.get(target_path, 0):
                    return False
                self._committed[target_path] = generation
                return True

        data = val() if callable(val) else val
        return atomic_save_json(target_path, data, temp_tag=temp_tag, should_commit=still_newest)

    def save_debounced(self, target_path: Path, data_or_producer: Any, delay_seconds: float = DEBOUNCE_DELAY_STORAGE_SAVE):
        with self._lock:
            self._data[target_path] = (self._new_generation(), data_or_producer)
            if target_path in self._timers:
                self._timers[target_path].cancel()

            def flush():
                with self._lock:
                    pending = self._data.pop(target_path, None)
                    self._timers.pop(target_path, None)
                    if pending is None:
                        return
                    generation, val = pending
                    self._active.setdefault(target_path, {})[generation] = val
                try:
                    self._write(target_path, generation, val)
                except Exception as e:
                    logger.error(f"Debounced background save failed for {target_path}: {e}")
                finally:
                    with self._lock:
                        running = self._active.get(target_path, {})
                        running.pop(generation, None)
                        if not running:
                            self._active.pop(target_path, None)
                        self._write_cond.notify_all()

            timer = threading.Timer(delay_seconds, flush)
            timer.daemon = True
            self._timers[target_path] = timer
            timer.start()

    def save_now(self, target_path: Path, data: Any) -> None:
        """Writes synchronously and makes every earlier save of this file obsolete.

        A synchronous save used to bypass the debouncer altogether: an older
        save still waiting for its timer (or just being written) then landed
        afterwards and put the previous state back - a permanently deleted
        case could reappear on disk that way. Raises if the write fails.
        """
        with self._lock:
            generation = self._new_generation()
            self._data.pop(target_path, None)
            timer = self._timers.pop(target_path, None)
            if timer is not None:
                timer.cancel()
        self._write(target_path, generation, data)

    def discard_pending(self) -> int:
        """Drops every save that is still waiting for its debounce timer, without writing it.

        For the moment the files on disk were replaced from outside (a ZIP
        import): a waiting save still holds the data from before and would
        write it right over the new files. Returns how many were dropped. A
        write that is already running is not interrupted, but it will not be
        moved into place any more.
        """
        with self._lock:
            dropped = len(self._data)
            for timer in self._timers.values():
                timer.cancel()
            self._timers.clear()
            self._data.clear()
            self._discard_floor = self._new_generation()
        return dropped

    def flush_all(self, timeout: float = TIMEOUT_STORAGE_FLUSH_ALL):
        """Immediately flushes all pending debounced saves synchronously (used on app exit).

        Waits at most ``timeout`` seconds for background writes that are
        already running. A background write can block for good: if the garbage
        collector happens to run there and finalises a Tk object (a CTkFont's
        __del__ calls into Tcl), Tcl hands that call to the main thread and
        waits - while the main thread sits here waiting for the write. Without
        the deadline the app hung on exit. A write still running at the
        deadline is done here on the main thread instead, so nothing is lost.
        """
        with self._lock:
            pending_data = dict(self._data)
            for timer in self._timers.values():
                timer.cancel()
            self._timers.clear()
            self._data.clear()

        for path, (generation, val) in pending_data.items():
            try:
                self._write(path, generation, val)
            except Exception as e:
                logger.error(f"Flush save failed for {path}: {e}")

        deadline = time.monotonic() + timeout
        stuck: list[tuple[Path, int, Any]] = []
        with self._lock:
            while self._active:
                remaining = deadline - time.monotonic()
                if remaining <= 0:
                    stuck = [(p, g, v) for p, running in self._active.items() for g, v in running.items()]
                    break
                self._write_cond.wait(timeout=min(remaining, TIMEOUT_STORAGE_WRITE_COND))

        for path, generation, val in sorted(stuck, key=lambda item: item[1]):
            logger.warning(f"Background save for {path} did not finish in {timeout}s - writing it from the main thread.")
            try:
                self._write(path, generation, val, temp_tag="flush")
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
        #: Counts reload_from_disk() calls, so the UI can tell "the data was
        #: replaced" from an ordinary settings save and close what it has open.
        self.reload_generation = 0
        self._remove_stale_temp_files()
        self.migrate_legacy_attachments()

    def _remove_stale_temp_files(self) -> None:
        """Removes temp files that an interrupted save (crash, power loss) left next to the data files.

        Each writer has a temp file name of its own, so unlike the single
        shared name before, a leftover is no longer overwritten by the next
        save. Only files older than an hour are touched - nothing that a save
        of this very moment could still be working on.
        """
        folders = {self.config.data_dir, self.config.data_dir / "profiles"}
        for attr in PROFILE_PATH_OVERRIDES:
            custom = getattr(self.config, attr, None)
            if isinstance(custom, Path):
                folders.add(custom.parent)
        cutoff = time.time() - STALE_TEMP_FILE_MAX_AGE_SECONDS
        for folder in folders:
            try:
                leftovers = [f for f in folder.glob(TEMP_JSON_GLOB) if f.is_file() and f.stat().st_mtime < cutoff]
            except OSError:
                continue
            for leftover in leftovers:
                try:
                    leftover.unlink()
                    logger.info(f"Removed stale temp file {leftover}")
                except OSError as e:
                    logger.warning(f"Could not remove stale temp file {leftover}: {e}")

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

    def reload_from_disk(self) -> None:
        """Forgets the cached data lists after the files were replaced from outside.

        A ZIP import unpacks new cases.json, customers.json, ... underneath
        the running app. The caches still held the old lists, so the app kept
        showing them - and its next save wrote them over the imported files
        (import nine cases into an empty workspace, create one case, and
        cases.json held exactly that one).

        Unlike invalidate_cache() this does NOT flush first: a pending save
        carries the pre-import data and is dropped instead of written. The
        profile cache stays, because the profile object is shared with the
        open settings dialog and is not something an import swaps mid-session.
        """
        dropped = self.saver.discard_pending()
        if dropped:
            logger.warning(f"Dropped {dropped} pending save(s) that predate the reload from disk")
        self._cases_cache = None
        self._archive_cache = None
        self._customers_cache = None
        self._schemas_cache = None
        self._templates_cache = None
        self._colleagues_cache = None
        self.reload_generation += 1

    def migrate_legacy_attachments(self) -> None:
        """Migrates legacy attachments folder (workspace_dir/attachments) into data/attachments.
        Also migrates attachment_directory in active cases and archive from 'attachments/...' to 'data/attachments/...'.
        """
        workspace_dir = getattr(self.config, "workspace_dir", None)
        target_att_dir = getattr(self.config, "attachments_dir", None)
        if not isinstance(workspace_dir, Path) or not isinstance(target_att_dir, Path):
            return

        legacy_dir = workspace_dir / ATTACHMENTS_DIRNAME

        if legacy_dir.exists() and legacy_dir.is_dir() and legacy_dir.resolve() != target_att_dir.resolve():
            target_att_dir.mkdir(parents=True, exist_ok=True)
            for item in list(legacy_dir.iterdir()):
                self._merge_move(item, target_att_dir / item.name)

            # Only an empty legacy folder is removed - nothing is ever deleted recursively.
            try:
                legacy_dir.rmdir()
                logger.info(f"Removed legacy attachments directory: {legacy_dir}")
            except OSError as e:
                logger.warning(f"Legacy attachments directory not empty, left in place: {legacy_dir} ({e})")

        # Check and migrate cases.json & archive.json files on disk
        cases_path = getattr(self.config, "cases_path", None)
        if isinstance(cases_path, Path) and cases_path.exists():
            self.load_cases(use_cache=False)

        archive_path = getattr(self.config, "archive_path", None)
        if isinstance(archive_path, Path) and archive_path.exists():
            self.load_archive(use_cache=False)

    @staticmethod
    def _merge_move(src: Path, dest: Path) -> None:
        """Moves src to dest without ever losing data.

        - dest missing: plain move.
        - both directories: merge recursively, then remove src only if empty.
        - identical files: the legacy duplicate is dropped.
        - any other collision: src is moved next to dest under a '_legacy' name.
        """
        try:
            if not dest.exists():
                shutil.move(str(src), str(dest))
                return

            if src.is_dir() and dest.is_dir():
                for child in list(src.iterdir()):
                    StorageService._merge_move(child, dest / child.name)
                try:
                    src.rmdir()
                except OSError:
                    logger.warning(f"Legacy attachment folder not empty after merge, left in place: {src}")
                return

            if src.is_file() and dest.is_file() and filecmp.cmp(src, dest, shallow=False):
                src.unlink()
                return

            counter = 1
            alt = dest.with_name(f"{dest.stem}_legacy{dest.suffix}")
            while alt.exists():
                counter += 1
                alt = dest.with_name(f"{dest.stem}_legacy{counter}{dest.suffix}")
            shutil.move(str(src), str(alt))
            logger.warning(f"Attachment name collision during migration: {src} kept as {alt}")
        except Exception as e:
            logger.warning(f"Error migrating legacy attachment item {src} to {dest}: {e}")

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
            migrated = False
            self._cases_cache = []
            seen_items: dict[str, list[dict]] = {}
            for item in data:
                if isinstance(item, dict):
                    # Exact copies of an entry (same id, same content) are left
                    # over from the duplicate-case bug and are dropped. Entries
                    # that only share the id are kept - both are real data.
                    item_id = str(item.get("case_id", ""))
                    if item_id and item in seen_items.get(item_id, []):
                        logger.warning(f"Dropped exact duplicate of case {item_id} from cases.json")
                        migrated = True
                        continue
                    seen_items.setdefault(item_id, []).append(dict(item))
                    att = str(item.get("attachment_directory") or "").replace("\\", "/")
                    if att.startswith("attachments/"):
                        item["attachment_directory"] = f"data/{att}"
                        migrated = True
                    elif att == "attachments":
                        item["attachment_directory"] = REL_ATTACHMENTS_DIR
                        migrated = True
                    self._cases_cache.append(Case.from_dict(item))
            if migrated:
                try:
                    atomic_save_json(self.config.cases_path, [c.to_dict() for c in self._cases_cache])
                    logger.info("Persisted migrated attachment directories in cases.json")
                except Exception as e:
                    logger.warning(f"Could not persist migrated attachment directories in cases: {e}")
        else:
            self._cases_cache = []
        return self._cases_cache

    def save_cases(self, cases: list[Case], sync: bool = False) -> None:
        # Bulk save paths (scoring run, follow-up flyout, P2P sync, seeding) mutate
        # cases in place without going through update_single_case, so the cached
        # searchable text would keep matching the pre-edit content until restart.
        # Recomputing is lazy, so this costs nothing until the next search.
        for c in cases:
            c.invalidate_search_cache()
        self._cases_cache = cases
        if sync:
            data = [case.to_dict() for case in cases]
            self.saver.save_now(self.config.cases_path, data)
        else:
            cases_snapshot = list(cases)
            self.saver.save_debounced(
                self.config.cases_path,
                lambda: [c.to_dict() for c in cases_snapshot]
            )

    def update_single_case(self, case: Case) -> None:
        """Updates or adds a single case in the cache and persists the cases file."""
        case.invalidate_search_cache()
        cases = self.load_cases(use_cache=True)
        # The very object first: if two cases ever share an id, matching by id
        # alone overwrote the other one with this case - one case lost, this
        # one listed twice.
        idx = next((i for i, existing in enumerate(cases) if existing is case), None)
        if idx is None:
            idx = next((i for i, existing in enumerate(cases) if existing.case_id == case.case_id), None)
        if idx is None:
            cases.append(case)
        else:
            cases[idx] = case
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
            migrated = False
            self._archive_cache = []
            for item in data:
                if isinstance(item, dict):
                    att = str(item.get("attachment_directory") or "").replace("\\", "/")
                    if att.startswith("attachments/"):
                        item["attachment_directory"] = f"data/{att}"
                        migrated = True
                    elif att == "attachments":
                        item["attachment_directory"] = REL_ATTACHMENTS_DIR
                        migrated = True
                    self._archive_cache.append(Case.from_dict(item))
            if migrated:
                try:
                    atomic_save_json(self.config.archive_path, [c.to_dict() for c in self._archive_cache])
                    logger.info("Persisted migrated attachment directories in archive.json")
                except Exception as e:
                    logger.warning(f"Could not persist migrated attachment directories in archive: {e}")
        else:
            self._archive_cache = []
        return self._archive_cache

    def save_archive(self, cases: list[Case], sync: bool = False) -> None:
        self._archive_cache = cases
        if sync:
            data = [case.to_dict() for case in cases]
            self.saver.save_now(self.config.archive_path, data)
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

    def delete_case_permanently(self, case_id: str) -> bool:
        """Removes a case permanently from both the active cases list and the archive.

        Writes both files synchronously (sync=True) so the deletion is on disk
        immediately before the caller removes the case from the app's in-memory list.
        Returns True if the case was found in at least one of the two lists.
        """
        cases = self.load_cases()
        archive = self.load_archive()

        remaining_cases = [c for c in cases if c.case_id != case_id]
        remaining_archive = [c for c in archive if c.case_id != case_id]

        found = len(remaining_cases) < len(cases) or len(remaining_archive) < len(archive)

        if not found:
            logger.warning(f"delete_case_permanently: case {case_id} not found in cases or archive")
            return False

        self._cases_cache = remaining_cases
        self._archive_cache = remaining_archive
        self.save_cases(remaining_cases, sync=True)
        self.save_archive(remaining_archive, sync=True)
        logger.info(f"Permanently deleted case {case_id}")
        return True

    def auto_archive_completed_cases(self, threshold_days: int = DEFAULT_AUTO_ARCHIVE_THRESHOLD_DAYS) -> int:
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
                try:
                    idle_days = calculate_idle_days(c.updated_at)
                except ValueError as e:
                    # Runs on every start: one unreadable timestamp must not
                    # keep the whole app from opening. The case simply stays.
                    logger.warning(f"Auto-archive skipped case {c.case_id}: unreadable updated_at {c.updated_at!r} ({e})")
                    idle_days = 0.0
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

    def prune_old_backups(
        self,
        reference_date: date | None = None,
        settings: BackupSettings | None = None,
    ) -> list[Path]:
        """Prunes old backup files in backups/ according to grandfather-father-son retention rules.

        Rules, applied to each backup series (cases, archive, customers, ...) on its own:
        - Only files matching '<series>_YYYY-MM-DD.json' are evaluated.
        - The newest backup file of a series is never deleted under any circumstances (safety guard).
        - Files within 'daily_days' are all kept.
        - Files between 'daily_days' and weekly cutoff keep the latest backup per ISO calendar week.
        - Files between weekly cutoff and monthly cutoff keep the latest backup per calendar month.
        - Files older than monthly cutoff are deleted.
        """
        backups_dir = self.config.backups_dir
        if not backups_dir.exists():
            return []

        if settings is None:
            try:
                profile = self.load_profile()
                settings = profile.backup_settings
            except Exception as e:
                logger.warning(f"Could not load backup settings, using defaults: {e}")
                settings = BackupSettings()

        pattern = re.compile(REGEX_DATA_BACKUP)
        series_files: dict[str, list[tuple[Path, date]]] = {}

        for p in backups_dir.iterdir():
            if not p.is_file():
                continue
            m = pattern.match(p.name)
            if not m:
                continue
            try:
                d = date.fromisoformat(m.group(2))
            except ValueError:
                continue
            series_files.setdefault(m.group(1), []).append((p, d))

        if not series_files:
            return []

        ref_date = reference_date if reference_date is not None else datetime.now().date()

        deleted_files: list[Path] = []
        # Cases first, so the returned list starts with the series callers know.
        for series in sorted(series_files, key=lambda name: (name != BACKUP_SERIES_CASES, name)):
            backup_files = sorted(series_files[series], key=lambda item: item[1])
            keep_paths = self._backups_to_keep(backup_files, ref_date, settings)
            for path, _ in backup_files:
                if path not in keep_paths:
                    try:
                        path.unlink()
                        deleted_files.append(path)
                        logger.info(f"Pruned old backup: {path.name}")
                    except Exception as e:
                        logger.warning(f"Failed to prune backup file {path}: {e}")

        return deleted_files

    @staticmethod
    def _backups_to_keep(
        backup_files: list[tuple[Path, date]],
        ref_date: date,
        settings: BackupSettings,
    ) -> set[Path]:
        """Retention decision for one backup series, given ascending (path, date) pairs."""
        daily_days = max(1, settings.daily_days)
        weekly_weeks = max(0, settings.weekly_weeks)
        monthly_months = max(0, settings.monthly_months)

        weekly_cutoff_days = max(daily_days, weekly_weeks * DAYS_PER_WEEK)
        monthly_cutoff_days = max(weekly_cutoff_days, monthly_months * DAYS_PER_MONTH)

        # Unconditional safety: keep the single newest backup
        newest_file, _ = backup_files[-1]
        keep_paths: set[Path] = {newest_file}

        weekly_buckets: dict[tuple[int, int], tuple[Path, date]] = {}
        monthly_buckets: dict[tuple[int, int], tuple[Path, date]] = {}

        for path, d in backup_files:
            age_days = (ref_date - d).days

            if age_days < daily_days:
                # Daily tier: keep all
                keep_paths.add(path)
            elif age_days < weekly_cutoff_days:
                # Weekly tier: group by (iso_year, iso_week), keep latest
                iso_key = d.isocalendar()[:2]
                if iso_key not in weekly_buckets or d > weekly_buckets[iso_key][1]:
                    weekly_buckets[iso_key] = (path, d)
            elif age_days < monthly_cutoff_days:
                # Monthly tier: group by (year, month), keep latest
                month_key = (d.year, d.month)
                if month_key not in monthly_buckets or d > monthly_buckets[month_key][1]:
                    monthly_buckets[month_key] = (path, d)
            # Older than the monthly cutoff: eligible for deletion

        keep_paths.update(p for p, _ in weekly_buckets.values())
        keep_paths.update(p for p, _ in monthly_buckets.values())
        return keep_paths

    def _backup_sources(self) -> dict[str, Path]:
        """The data files besides cases.json that belong in a backup, by series name."""
        return {
            "archive": self.config.archive_path,
            "customers": self.config.customers_path,
            "app_profile": self.config.app_profile_path,
            "colleagues": self.config.colleagues_path,
            "question_schemas": self.config.question_schemas_path,
            "export_templates": self.config.export_templates_path,
            "snippets": self.config.data_dir / SNIPPETS_BACKUP_SOURCE_FILENAME,
        }

    def create_safety_snapshot(self, label: str) -> Path | None:
        """Copies every data file into backups/<label>_<timestamp>/ before a destructive operation.

        Returns the snapshot folder, or None if there was nothing to copy. A
        file that cannot be copied raises: the caller is about to overwrite it,
        so going ahead without the copy would defeat the purpose.
        """
        self.flush_all_saves()
        sources = {BACKUP_SERIES_CASES: self.config.cases_path, **self._backup_sources()}
        existing = {name: path for name, path in sources.items() if path.exists()}
        if not existing:
            return None

        stamp = datetime.now().strftime(SAFETY_SNAPSHOT_TIMESTAMP_FORMAT)
        snapshot_dir = self.config.backups_dir / f"{label}_{stamp}"
        counter = 2
        while snapshot_dir.exists():
            snapshot_dir = self.config.backups_dir / f"{label}_{stamp}_{counter}"
            counter += 1
        snapshot_dir.mkdir(parents=True)
        for name, path in existing.items():
            shutil.copy2(path, snapshot_dir / f"{name}.json")
        logger.info(f"Created safety snapshot of {len(existing)} data files in {snapshot_dir}")
        return snapshot_dir

    def perform_daily_backup(self, date_str: str | None = None, settings: BackupSettings | None = None) -> Path | None:
        """Performs the daily backup of cases.json and the other data files to backups/<series>_YYYY-MM-DD.json and prunes old backups."""
        if not date_str:
            date_str = datetime.now().strftime("%Y-%m-%d")

        backup_filename = f"cases_{date_str}.json"
        backup_path = self.config.backups_dir / backup_filename

        ref_date: date | None = None
        try:
            ref_date = date.fromisoformat(date_str)
        except ValueError:
            pass

        created_or_existing: Path | None = None
        if backup_path.exists():
            created_or_existing = backup_path
        else:
            cases = self.load_cases()
            if cases:
                atomic_save_json(backup_path, [c.to_dict() for c in cases])
                logger.info(f"Created daily backup: {backup_path}")
                created_or_existing = backup_path

        # The other data files are just as hard to recreate as the cases
        # (customers, archive, profile, schemas, templates, snippets). They are
        # copied as they are on disk, once per day like the cases.
        for series, source in self._backup_sources().items():
            series_backup = self.config.backups_dir / f"{series}_{date_str}.json"
            if series_backup.exists() or not source.exists():
                continue
            try:
                shutil.copy2(source, series_backup)
            except OSError as e:
                logger.warning(f"Could not back up {source} to {series_backup}: {e}")

        try:
            self.prune_old_backups(reference_date=ref_date, settings=settings)
        except Exception as e:
            logger.error(f"Error during backup pruning: {e}")

        return created_or_existing

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
            self.saver.save_now(self.config.customers_path, data)
        else:
            customers_snapshot = list(customers)
            self.saver.save_debounced(
                self.config.customers_path,
                lambda: [c.to_dict() for c in customers_snapshot]
            )

    # --- Profile ---
    @property
    def global_profiles_dir(self) -> Path:
        from config import get_global_config_dir
        p_dir = get_global_config_dir() / "profiles"
        p_dir.mkdir(parents=True, exist_ok=True)
        return p_dir

    @property
    def profiles_dir(self) -> Path:
        p_dir = self.config.data_dir / "profiles"
        p_dir.mkdir(parents=True, exist_ok=True)
        return p_dir

    def list_profiles(self) -> list[str]:
        """Lists available user profile usernames from both workspace and global profiles directory."""
        curr_profile = self.load_profile()
        profiles = [curr_profile.user.name]
        for dir_path in (self.global_profiles_dir, self.profiles_dir):
            if dir_path.exists():
                for f in dir_path.glob("*.json"):
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

        loaded_profile: UserProfile | None = None
        prof_name = getattr(self.config, "active_profile_name", None)
        if prof_name:
            safe_filename = "".join(c for c in prof_name if c.isalnum() or c in (" ", "_", "-")).strip().replace(" ", "_")
            for dir_path in (self.global_profiles_dir, self.profiles_dir):
                target_path = dir_path / f"profile_{safe_filename}.json"
                if target_path.exists():
                    data = safe_read_json(target_path, default_factory=dict)
                    if isinstance(data, dict) and data:
                        loaded_profile = UserProfile.from_dict(data)
                        break

        if loaded_profile is None:
            data = safe_read_json(
                self.config.app_profile_path,
                default_factory=dict,
                example_path=self.config.get_example_path("app_profile.json")
            )
            if isinstance(data, dict) and data:
                loaded_profile = UserProfile.from_dict(data)
            else:
                loaded_profile = UserProfile()

        # Seed missing path_settings from the active config. This has to cover
        # every override, not just the four the dialog shows: apply_profile_paths
        # writes all of them back, so a path that is never seeded here is set to
        # None there and then persisted - which silently deleted an existing
        # archive, colleagues, schema or template path on the first start.
        if not loaded_profile.path_settings.workspace_dir:
            loaded_profile.path_settings.workspace_dir = str(self.config.workspace_dir)
        for attr in PROFILE_PATH_OVERRIDES:
            config_value = getattr(self.config, attr, None)
            if config_value and not getattr(loaded_profile.path_settings, attr, ""):
                setattr(loaded_profile.path_settings, attr, str(config_value))

        self._profile_cache = loaded_profile
        return self._profile_cache

    def load_profile_by_name(self, profile_name: str) -> UserProfile:
        """Loads UserProfile by user name from global or workspace profiles_dir or falls back to active profile."""
        safe_filename = "".join(c for c in profile_name if c.isalnum() or c in (" ", "_", "-")).strip().replace(" ", "_")
        for dir_path in (self.global_profiles_dir, self.profiles_dir):
            target_path = dir_path / f"profile_{safe_filename}.json"
            if target_path.exists():
                data = safe_read_json(target_path, default_factory=dict)
                if isinstance(data, dict) and data:
                    loaded = UserProfile.from_dict(data)
                    if not loaded.path_settings.workspace_dir:
                        loaded.path_settings.workspace_dir = str(self.config.workspace_dir)
                    return loaded

        return self.load_profile()

    def save_profile(self, profile: UserProfile, sync: bool = False) -> None:
        self._profile_cache = profile
        p_dict: dict[str, Any] | None = None
        if sync:
            p_dict = profile.to_dict()
            self.saver.save_now(self.config.app_profile_path, p_dict)
        else:
            self.saver.save_debounced(self.config.app_profile_path, lambda: profile.to_dict())

        safe_filename = "".join(c for c in profile.user.name if c.isalnum() or c in (" ", "_", "-")).strip().replace(" ", "_")
        if safe_filename:
            for dir_path in (self.global_profiles_dir, self.profiles_dir):
                target_path = dir_path / f"profile_{safe_filename}.json"
                if sync:
                    if p_dict is None:
                        p_dict = profile.to_dict()
                    self.saver.save_now(target_path, p_dict)
                else:
                    self.saver.save_debounced(target_path, lambda: profile.to_dict())

        self.config.active_profile_name = profile.user.name
        self.config.save_user_config()

    def apply_profile_paths(self, profile: UserProfile) -> None:
        """Applies PathSettings from profile to storage config, ensures directories, and invalidates data caches.

        Never leaves the app pointing at a location it cannot use: if the
        directories cannot be created - a drive letter that only exists on the
        machine the workspace was copied from, a folder without write access -
        the previous paths are restored and the app keeps running on them. The
        alternative was an exception out of SupportCockpitApp.__init__, which in
        a windowed build means the program simply does not start, with no
        message anywhere.
        """
        if not hasattr(profile, "path_settings") or profile.path_settings is None:
            return

        previous = self._current_path_config()

        ws_str = profile.path_settings.workspace_dir.strip()
        # An explicitly requested workspace (--workspace) outranks the one stored
        # in the profile; otherwise a copied data folder would quietly redirect
        # the app back to the path it was copied from.
        if ws_str and not getattr(self.config, "workspace_from_cli", False):
            self.config.workspace_dir = Path(ws_str)

        for attr in PROFILE_PATH_OVERRIDES:
            value = getattr(profile.path_settings, attr, "").strip()
            setattr(self.config, attr, Path(value) if value else None)

        try:
            self.config.ensure_directories()
        except OSError as err:
            self._restore_path_config(previous)
            logger.error(
                f"Profile paths point to an unusable location ({err}); "
                f"staying on {self.config.workspace_dir}"
            )
            return

        self.flush_all_saves()
        self._cases_cache = None
        self._archive_cache = None
        self._customers_cache = None
        self._schemas_cache = None
        self._templates_cache = None
        self._colleagues_cache = None
        self._profile_cache = profile
        self.config.save_user_config()

    def _current_path_config(self) -> dict[str, Any]:
        snapshot: dict[str, Any] = {"workspace_dir": self.config.workspace_dir}
        for attr in PROFILE_PATH_OVERRIDES:
            snapshot[attr] = getattr(self.config, attr, None)
        return snapshot

    def _restore_path_config(self, snapshot: dict[str, Any]) -> None:
        for attr, value in snapshot.items():
            setattr(self.config, attr, value)

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
            self.saver.save_now(self.config.question_schemas_path, data)
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
            self.saver.save_now(self.config.export_templates_path, data)
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
            self.saver.save_now(self.config.colleagues_path, data)
        else:
            self.saver.save_debounced(self.config.colleagues_path, data)
