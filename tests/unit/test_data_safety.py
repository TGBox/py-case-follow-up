"""Guards against losing data: unreadable files, seeding over real data, a second instance, a missing workspace, silent start failures."""

import importlib
import json
import os
import sys
from datetime import date, datetime, timedelta
from pathlib import Path

import pytest

import services.storage_service as storage_service
from config import AppConfig, get_os_username
from models.case import Case, CaseCustomer, Classification, WorkflowStatus
from models.customer import Customer
from services.instance_service import InstanceService
from services.seed_service import SeedRefusedError, SeedService
from services.storage_service import StorageReadError, StorageService, read_json_readonly, safe_read_json

_REPO_ROOT = str(Path(__file__).resolve().parents[2])


def _main_module():
    if _REPO_ROOT not in sys.path:
        sys.path.insert(0, _REPO_ROOT)
    return importlib.import_module("main")


def _real_case(case_id: str = "T-2026-0001", **workflow) -> Case:
    return Case(
        case_id=case_id,
        customer=CaseCustomer(customer_id="K-1", practice_name="Praxis Echt"),
        classification=Classification(title="Echter Fall"),
        workflow_status=WorkflowStatus(**workflow),
    )


def _files(folder: Path) -> list[str]:
    return sorted(f.name for f in folder.iterdir())


# --- reading: an I/O error is not corruption ----------------------------------


@pytest.mark.parametrize("error", [PermissionError(13, "locked"), OSError(64, "network name no longer available")])
def test_unreadable_file_is_never_renamed_or_replaced(tmp_path: Path, monkeypatch, error):
    """A share that drops out or a lock that outlasts the retries used to cost the file: renamed, then replaced by the example."""
    folder = tmp_path / "ablage"
    folder.mkdir()
    target = folder / "cases.json"
    target.write_text('[{"case_id": "T-1"}]', encoding="utf-8")
    example = folder / "example.json"
    example.write_text('[{"case_id": "DEMO"}]', encoding="utf-8")

    def failing(path):
        raise error

    monkeypatch.setattr(storage_service, "_read_json_with_retry", failing)
    with pytest.raises(StorageReadError):
        safe_read_json(target, default_factory=list, example_path=example)
    assert target.read_text(encoding="utf-8") == '[{"case_id": "T-1"}]'
    assert _files(folder) == ["cases.json", "example.json"]


def test_corrupted_file_that_cannot_be_set_aside_is_not_overwritten(tmp_path: Path, monkeypatch):
    folder = tmp_path / "ablage"
    folder.mkdir()
    target = folder / "cases.json"
    target.write_text("{ half written", encoding="utf-8")

    def locked_rename(self, new_name):
        raise PermissionError(13, "in use")

    monkeypatch.setattr(Path, "rename", locked_rename)
    with pytest.raises(StorageReadError):
        safe_read_json(target, default_factory=list)
    assert target.read_text(encoding="utf-8") == "{ half written"
    assert _files(folder) == ["cases.json"]


def test_read_json_readonly_changes_nothing(tmp_path: Path):
    folder = tmp_path / "ablage"
    folder.mkdir()
    good = folder / "good.json"
    good.write_text('{"a": 1}', encoding="utf-8")
    assert read_json_readonly(good) == {"a": 1}

    bad = folder / "bad.json"
    bad.write_text("nope", encoding="utf-8")
    with pytest.raises(ValueError):
        read_json_readonly(bad)
    with pytest.raises(OSError):
        read_json_readonly(folder / "missing.json")
    assert _files(folder) == ["bad.json", "good.json"]
    assert bad.read_text(encoding="utf-8") == "nope"


def test_storage_error_on_load_reaches_the_caller(storage, config, monkeypatch):
    storage.save_cases([_real_case()], sync=True)
    storage.invalidate_cache()

    def failing(path):
        raise OSError(5, "I/O error")

    monkeypatch.setattr(storage_service, "_read_json_with_retry", failing)
    with pytest.raises(StorageReadError):
        storage.load_cases()
    monkeypatch.undo()
    assert [c.case_id for c in StorageService(config).load_cases()] == ["T-2026-0001"]


# --- seeding --------------------------------------------------------------------


def test_seed_refuses_to_overwrite_real_cases(storage):
    storage.save_cases([_real_case()], sync=True)
    with pytest.raises(SeedRefusedError) as refused:
        SeedService(storage).run_seed()
    assert refused.value.user_data == {"cases": 1}
    assert [c.case_id for c in storage.load_cases(use_cache=False)] == ["T-2026-0001"]


def test_seed_refuses_when_only_the_archive_or_the_customers_are_real(storage):
    storage.save_cases([], sync=True)
    storage.save_archive([_real_case("T-2025-0009")], sync=True)
    assert SeedService(storage).find_user_data() == {"archived cases": 1}

    storage.save_archive([], sync=True)
    storage.save_customers([Customer(customer_id="K-77001", practice_name="Praxis Echt")], sync=True)
    assert SeedService(storage).find_user_data() == {"customers": 1}
    with pytest.raises(SeedRefusedError):
        SeedService(storage).run_seed()
    assert [c.customer_id for c in storage.load_customers(use_cache=False)] == ["K-77001"]


def test_seed_runs_on_a_fresh_and_on_an_already_seeded_workspace(storage, config):
    assert SeedService(storage).find_user_data() == {}
    SeedService(storage).run_seed()
    assert SeedService(storage).find_user_data() == {}
    summary = SeedService(storage).run_seed()
    assert summary["cases"] > 0
    assert not list(config.backups_dir.glob("pre_seed_*")), "nothing real was overwritten, so no snapshot"


def test_forced_seed_saves_the_previous_state_first(storage, config):
    storage.save_cases([_real_case()], sync=True)
    storage.save_customers([Customer(customer_id="K-77001", practice_name="Praxis Echt")], sync=True)

    SeedService(storage).run_seed(force=True)

    assert all(c.is_demo_data for c in storage.load_cases(use_cache=False))
    snapshots = list(config.backups_dir.glob("pre_seed_*"))
    assert len(snapshots) == 1 and snapshots[0].is_dir()
    saved_cases = json.loads((snapshots[0] / "cases.json").read_text(encoding="utf-8"))
    assert [c["case_id"] for c in saved_cases] == ["T-2026-0001"]
    saved_customers = json.loads((snapshots[0] / "customers.json").read_text(encoding="utf-8"))
    assert [c["customer_id"] for c in saved_customers] == ["K-77001"]


# --- daily backup covers every data file ----------------------------------------


def test_daily_backup_covers_all_data_files(storage, config):
    storage.save_cases([_real_case()], sync=True)
    storage.save_archive([_real_case("T-2025-0009")], sync=True)
    storage.save_customers([Customer(customer_id="K-77001", practice_name="Praxis Echt")], sync=True)
    storage.save_profile(storage.load_profile(), sync=True)
    storage.load_schemas()
    storage.load_templates()
    storage.load_colleagues()

    storage.perform_daily_backup("2026-09-11")

    names = {f.name for f in config.backups_dir.iterdir() if f.is_file()}
    for series in ("cases", "archive", "customers", "app_profile", "colleagues", "question_schemas", "export_templates"):
        assert f"{series}_2026-09-11.json" in names
    assert "T-2025-0009" in (config.backups_dir / "archive_2026-09-11.json").read_text(encoding="utf-8")
    assert "K-77001" in (config.backups_dir / "customers_2026-09-11.json").read_text(encoding="utf-8")

    # Once per day: a later change the same day does not replace the morning copy.
    storage.save_customers([], sync=True)
    storage.perform_daily_backup("2026-09-11")
    assert "K-77001" in (config.backups_dir / "customers_2026-09-11.json").read_text(encoding="utf-8")


def test_retention_is_applied_per_series_and_keeps_the_newest_of_each(storage, config):
    config.ensure_directories()
    ref = date(2026, 9, 11)
    for series in ("cases", "customers"):
        for age in (0, 1, 400, 500):
            (config.backups_dir / f"{series}_{(ref - timedelta(days=age)).isoformat()}.json").write_text("[]", encoding="utf-8")
    lonely = config.backups_dir / "archive_2020-01-01.json"
    lonely.write_text("[]", encoding="utf-8")

    pruned = {p.name for p in storage.prune_old_backups(reference_date=ref)}

    assert pruned == {
        f"{series}_{(ref - timedelta(days=age)).isoformat()}.json" for series in ("cases", "customers") for age in (400, 500)
    }
    assert lonely.exists(), "the only archive backup is its newest and stays, however old"


def test_auto_archive_skips_a_case_with_an_unreadable_timestamp(storage):
    """It runs on every start: one damaged updated_at used to keep the app from opening at all."""
    broken = _real_case("T-BROKEN", is_completed=True)
    broken.updated_at = "kein datum"
    old = _real_case("T-OLD", is_completed=True)
    old.updated_at = "2020-01-01T10:00:00"
    storage.save_cases([broken, old], sync=True)

    assert storage.auto_archive_completed_cases(threshold_days=30) == 1
    assert [c.case_id for c in storage.load_cases()] == ["T-BROKEN"]
    assert [c.case_id for c in storage.load_archive()] == ["T-OLD"]


# --- one instance per workspace --------------------------------------------------


def test_a_fresh_lock_of_a_dead_process_does_not_block_a_restart(tmp_path, monkeypatch):
    """After a crash the lock is still fresh; without the PID check a refused second start would lock the user out for minutes."""
    import services.instance_service as instance_service

    crashed = InstanceService(tmp_path)
    crashed.acquire()
    crashed.lock_path.write_text("424242", encoding="utf-8")
    monkeypatch.setattr(instance_service, "pid_is_alive", lambda pid: False)

    restarted = InstanceService(tmp_path)
    assert restarted.is_running() is False
    assert restarted.handoff_or_claim(None) is False
    assert restarted.owns_lock and not restarted.is_blocked_by_other_instance()


def test_pid_probe_knows_this_process_and_rejects_nonsense():
    from services.instance_service import pid_is_alive

    assert pid_is_alive(os.getpid()) is True
    assert pid_is_alive(0) is False
    assert pid_is_alive(-5) is False


def test_pid_probe_tells_a_running_process_from_a_finished_one():
    """The real OS probe (on Windows the OpenProcess path) - and it must not harm the process it looks at."""
    import subprocess

    from services.instance_service import pid_is_alive

    child = subprocess.Popen([sys.executable, "-c", "import time; time.sleep(60)"])
    try:
        assert pid_is_alive(child.pid) is True
        assert child.poll() is None, "probing must not terminate the process"
    finally:
        child.kill()
        child.wait(timeout=10)
    assert pid_is_alive(child.pid) is False


def test_a_live_instance_blocks_a_second_one_but_not_itself(tmp_path):
    first = InstanceService(tmp_path)
    assert first.handoff_or_claim(None) is False
    assert not first.is_blocked_by_other_instance()

    second = InstanceService(tmp_path)
    assert second.handoff_or_claim(None) is False
    assert second.is_blocked_by_other_instance()

    first.release()
    assert not InstanceService(tmp_path).is_blocked_by_other_instance()


@pytest.fixture
def main_mod(monkeypatch):
    """main.py with the registry untouched and the window replaced by a marker."""
    module = _main_module()
    monkeypatch.setattr(module, "_crash_log_dir_override", None)  # main() sets it globally
    monkeypatch.setattr("services.instance_service.register_uri_scheme", lambda: False)
    started: list = []

    class _App:
        def __init__(self, config):
            started.append(config)

        def request_open_case(self, case_id):
            pass

        def mainloop(self):
            pass

    monkeypatch.setattr("ui.app.SupportCockpitApp", _App)
    module.started_apps = started
    return module


def test_second_start_on_a_running_workspace_is_refused_before_touching_data(tmp_path, monkeypatch, main_mod, startup_dialog_log):
    running = InstanceService(tmp_path)
    running.acquire()
    opened: list = []
    monkeypatch.setattr(main_mod, "StorageService", lambda config: opened.append(config))
    monkeypatch.setattr(sys, "argv", ["main.py", "--workspace", str(tmp_path)])

    with pytest.raises(SystemExit) as exited:
        main_mod.main()

    assert exited.value.code == main_mod.EXIT_STARTUP_ERROR
    assert opened == [] and main_mod.started_apps == []
    assert [kind for kind, _title, _msg in startup_dialog_log] == ["error"]
    assert str(tmp_path) in startup_dialog_log[0][2]
    assert running.is_running(), "the refused start must not remove the running instance's lock"


def test_a_normal_start_opens_the_window_and_releases_the_lock(tmp_path, monkeypatch, main_mod, startup_dialog_log):
    monkeypatch.setattr(sys, "argv", ["main.py", "--workspace", str(tmp_path)])
    main_mod.main()
    assert len(main_mod.started_apps) == 1
    assert startup_dialog_log == []
    assert InstanceService(tmp_path).is_running() is False


@pytest.mark.parametrize("flag", ["--seed", "--demo"])
def test_seed_and_demo_refuse_a_workspace_with_real_data(tmp_path, monkeypatch, main_mod, startup_dialog_log, flag):
    StorageService(AppConfig(workspace_dir=tmp_path, username="t")).save_cases([_real_case()], sync=True)
    monkeypatch.setattr(sys, "argv", ["main.py", flag, "--workspace", str(tmp_path)])

    with pytest.raises(SystemExit) as exited:
        main_mod.main()

    assert exited.value.code == main_mod.EXIT_SEED_REFUSED
    assert main_mod.started_apps == []
    assert len(startup_dialog_log) == 1 and "--force" in startup_dialog_log[0][2]
    cases = json.loads((tmp_path / "data" / "cases.json").read_text(encoding="utf-8"))
    assert [c["case_id"] for c in cases] == ["T-2026-0001"]
    assert InstanceService(tmp_path).is_running() is False


def test_forced_seed_overwrites_after_a_snapshot(tmp_path, monkeypatch, main_mod, startup_dialog_log):
    StorageService(AppConfig(workspace_dir=tmp_path, username="t")).save_cases([_real_case()], sync=True)
    monkeypatch.setattr(sys, "argv", ["main.py", "--seed", "--force", "--workspace", str(tmp_path)])

    with pytest.raises(SystemExit) as exited:
        main_mod.main()

    assert exited.value.code == 0 and startup_dialog_log == []
    cases = json.loads((tmp_path / "data" / "cases.json").read_text(encoding="utf-8"))
    assert cases and all(c["is_demo_data"] for c in cases)
    snapshot = next((tmp_path / "data" / "backups").glob("pre_seed_*"))
    assert "T-2026-0001" in (snapshot / "cases.json").read_text(encoding="utf-8")


def test_a_failure_before_the_window_exists_is_logged_and_shown(tmp_path, monkeypatch, main_mod, startup_dialog_log):
    """Reading the data, not only building the window: in the exe this used to end without any trace."""

    def unreadable(config):
        raise StorageReadError("Could not read cases.json: network drive gone")

    monkeypatch.setattr(main_mod, "StorageService", unreadable)
    monkeypatch.setattr(sys, "argv", ["main.py", "--workspace", str(tmp_path)])

    with pytest.raises(SystemExit) as exited:
        main_mod.main()

    assert exited.value.code == main_mod.EXIT_STARTUP_ERROR
    assert main_mod.started_apps == []
    assert len(startup_dialog_log) == 1 and "network drive gone" in startup_dialog_log[0][2]
    log = (tmp_path / "logs" / "tkinter_error.log").read_text(encoding="utf-8")
    assert "StorageReadError" in log and "network drive gone" in log
    assert InstanceService(tmp_path).is_running() is False


def test_a_failed_daily_backup_does_not_keep_the_app_from_starting(tmp_path, monkeypatch, main_mod, startup_dialog_log):
    def no_space(self, *args, **kwargs):
        raise OSError(28, "No space left on device")

    monkeypatch.setattr(StorageService, "perform_daily_backup", no_space)
    monkeypatch.setattr(sys, "argv", ["main.py", "--workspace", str(tmp_path)])
    main_mod.main()
    assert len(main_mod.started_apps) == 1 and startup_dialog_log == []


# --- a workspace that is not there -----------------------------------------------


def _configure_workspace(path: Path) -> None:
    AppConfig(workspace_dir=path, username="t").save_user_config()


def test_missing_workspace_is_reported_instead_of_silently_replaced(tmp_path):
    gone = tmp_path / "netzlaufwerk" / "cockpit"
    _configure_workspace(gone)
    loaded = AppConfig.load_user_config()
    assert loaded.missing_workspace_dir == gone
    assert loaded.workspace_dir != gone

    there = tmp_path / "da"
    there.mkdir()
    _configure_workspace(there)
    loaded = AppConfig.load_user_config()
    assert loaded.missing_workspace_dir is None and loaded.workspace_dir == there


@pytest.mark.parametrize("answer, starts", [(False, False), (True, True)])
def test_start_with_a_missing_workspace_asks_first(tmp_path, monkeypatch, main_mod, startup_dialog_log, answer, starts):
    gone = tmp_path / "netzlaufwerk" / "cockpit"
    _configure_workspace(gone)
    startup_dialog_log.answer = answer
    monkeypatch.setattr(sys, "argv", ["main.py"])

    if starts:
        main_mod.main()
    else:
        with pytest.raises(SystemExit) as exited:
            main_mod.main()
        assert exited.value.code == main_mod.EXIT_STARTUP_ERROR

    assert startup_dialog_log[0][0] == "question" and str(gone) in startup_dialog_log[0][2]
    assert (len(main_mod.started_apps) == 1) is starts
    if not starts:
        # Declined: nothing was created in the fallback folder, the setting is untouched.
        assert not (tmp_path / "data").exists()
        saved = json.loads((Path(os.environ["SUPPORTCOCKPIT_CONFIG_DIR"]) / "user_config.json").read_text(encoding="utf-8"))
        assert Path(saved["workspace_dir"]) == gone


def test_os_username_never_raises(monkeypatch):
    def no_tty():
        raise OSError(25, "Inappropriate ioctl for device")

    monkeypatch.setattr(os, "getlogin", no_tty)
    monkeypatch.setattr("getpass.getuser", lambda: "droesch")
    assert get_os_username() == "droesch"
    assert AppConfig(workspace_dir=Path(".")).username == "droesch"

    def nothing():
        raise KeyError("no user")

    monkeypatch.setattr("getpass.getuser", nothing)
    assert get_os_username()


# --- startup dialogs ---------------------------------------------------------------


def test_startup_dialogs_never_raise(monkeypatch):
    from utils import startup_dialogs

    def broken(title, message, kind):
        raise RuntimeError("no display")

    monkeypatch.setattr(startup_dialogs, "_show_native", broken)
    monkeypatch.setattr(sys, "stderr", None)
    monkeypatch.setattr(sys, "stdout", None)  # the windowed exe has neither
    startup_dialogs.show_error("Titel", "Text")
    assert startup_dialogs.ask_yes_no("Titel", "Frage?") is False


# --- follow-up dates are data, not display text --------------------------------------


@pytest.mark.parametrize("lang", ["de", "en", "sv"])
def test_quick_capture_stores_the_reminder_as_iso_in_every_language(lang):
    from services.i18n_service import get_i18n
    from services.quick_capture import build_quick_case
    from utils.datetime_utils import parse_followup_datetime

    get_i18n().current_language = lang
    case = build_quick_case(text="Rückruf", person="", reminder=datetime(2026, 10, 29, 16, 30), created_by="Ich",
                            taken_ids=set(), now=datetime(2026, 10, 29, 9, 0))
    assert case.workflow_status.followup_at == "2026-10-29T16:30:00"
    assert parse_followup_datetime(case.workflow_status.followup_at).replace(tzinfo=None) == datetime(2026, 10, 29, 16, 30)


@pytest.mark.parametrize("stored", [
    "29.10.2026 16:30 Uhr",
    "29.10.2026 16:30 o'clock",
    "29.10.2026 16:30 o’clock",
    "29.10.2026 16:30 kl.",
    "29.10.2026 16:30",
])
def test_follow_ups_saved_in_any_languages_display_form_are_still_read(stored):
    """Values written before the fix stay in the data; an unreadable one means the reminder never fires."""
    from utils.datetime_utils import format_german_datetime, parse_followup_datetime

    parsed = parse_followup_datetime(stored)
    assert parsed is not None and parsed.replace(tzinfo=None) == datetime(2026, 10, 29, 16, 30)
    assert format_german_datetime(stored) == "29.10.2026 16:30 Uhr"


@pytest.mark.parametrize("stored, is_due", [
    ("2031-01-01T09:00:00", False),
    ("01.01.2031 09:00 Uhr", False),
    ("01.01.2031 09:00 o'clock", False),
    ("2020-01-01T09:00:00", True),
    ("01.01.2020 09:00 Uhr", True),
    ("nicht lesbar", True),
])
def test_reminder_due_search_reads_every_stored_form(stored, is_due):
    """A future follow-up in display form used to raise inside the filter and count as due."""
    from services.search_service import SearchService

    case = _real_case(followup_at=stored)
    assert (SearchService.filter_cases([case], "reminder:due") == [case]) is is_due
