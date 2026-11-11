import argparse
import logging
import os
import sys
from pathlib import Path

# Ensure src/ directory is in sys.path
src_dir = Path(__file__).parent.resolve() / "src"
if str(src_dir) not in sys.path:
    sys.path.insert(0, str(src_dir))

import tkinter  # noqa: E402 - sys.path must be extended before src/ imports
import traceback  # noqa: E402 - sys.path must be extended before src/ imports

from utils.ui_utils import patch_ctk_scrollable_frame, patch_ctk_rendering  # noqa: E402 - sys.path must be extended before src/ imports

patch_ctk_scrollable_frame()
patch_ctk_rendering()

logger = logging.getLogger("SupportCockpit")

_seen_exceptions: set[str] = set()
_crash_log_dir_override: Path | None = None


def set_crash_log_dir(path: Path | str) -> None:
    """Points the crash log at the resolved workspace, once the config is known."""
    global _crash_log_dir_override
    _crash_log_dir_override = Path(path)


def _crash_log_dir() -> Path:
    """Absolute directory for the crash log.

    A bare Path("logs") resolves against the current working directory, which
    for a packaged .exe is wherever the shortcut happened to point - frequently
    somewhere unwritable, where the write fails and the crash log silently
    disappears. That is exactly the situation in which the log matters most.
    """
    if _crash_log_dir_override is not None:
        return _crash_log_dir_override
    try:
        from config import get_default_workspace_dir
        return get_default_workspace_dir() / "logs"
    except Exception:
        return Path(__file__).resolve().parent / "logs"


def _report_tkinter_exception(*args) -> None:
    if len(args) == 4:
        _, exc, val, tb = args
    elif len(args) == 3:
        exc, val, tb = args
    elif len(args) == 1 and isinstance(args[0], tuple) and len(args[0]) == 3:
        exc, val, tb = args[0]
    else:
        exc_type, exc_val, exc_tb = sys.exc_info()
        exc, val, tb = exc_type, exc_val, exc_tb

    if exc is None:
        return

    tb_lines = traceback.format_exception(exc, val, tb)
    tb_str = "".join(tb_lines)

    # 1. Log to file with immediate sync to disk
    try:
        log_dir = _crash_log_dir()
        log_dir.mkdir(parents=True, exist_ok=True)
        with open(log_dir / "tkinter_error.log", "a", encoding="utf-8") as f:
            f.write(f"\n--- [Exception] ---\n{tb_str}\n")
            f.flush()
            os.fsync(f.fileno())
    except Exception:
        pass

    # 2. Deduplicate on terminal so it only prints once per unique error location
    if tb:
        extracted = traceback.extract_tb(tb)
        last_frame = extracted[-1] if extracted else None
        err_key = f"{exc.__name__}:{last_frame.filename if last_frame else ''}:{last_frame.lineno if last_frame else ''}"
    else:
        err_key = f"{exc.__name__}:{val}"

    if err_key not in _seen_exceptions:
        _seen_exceptions.add(err_key)
        # A windowed PyInstaller build (console=False) has sys.stderr AND
        # sys.stdout set to None. print() tolerates that silently, but the
        # flush() below used to raise AttributeError *inside* the error
        # reporter, so in the packaged app every Tk callback exception turned
        # into a second, misleading crash.
        stream = sys.stderr if sys.stderr is not None else sys.stdout
        if stream is not None:
            try:
                print("\n=================== [TKINTER CALLBACK EXCEPTION] ===================", file=stream)
                print(tb_str.strip(), file=stream)
                print(f"--> Ausführlicher Log gespeichert in: {_crash_log_dir() / 'tkinter_error.log'}", file=stream)
                print("====================================================================\n", file=stream)
                stream.flush()
            except Exception:
                pass


tkinter.Tk.report_callback_exception = _report_tkinter_exception

from config import AppConfig  # noqa: E402 - sys.path must be extended before src/ imports
from services.storage_service import StorageService  # noqa: E402 - sys.path must be extended before src/ imports
from services.seed_service import SeedService  # noqa: E402 - sys.path must be extended before src/ imports


def parse_args():
    parser = argparse.ArgumentParser(description="Support Follow-Up & Ticket-Cockpit Desktop App")
    parser.add_argument(
        "--workspace", "-w",
        type=str,
        default=None,
        help="Path to workspace directory containing cases.json, etc."
    )
    parser.add_argument(
        "--seed",
        action="store_true",
        help="Generates seed test data (5 customers, 8 cases, schemas, templates, wiki DB) and exits. "
             "Refuses if the workspace holds real data, unless --force is given."
    )
    parser.add_argument(
        "--demo",
        action="store_true",
        help="Generates seed test data and launches the GUI in demo mode. "
             "Refuses if the workspace holds real data, unless --force is given."
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="With --seed/--demo: overwrite real data anyway. Every data file is first "
             "copied to data/backups/pre_seed_<timestamp>/."
    )
    parser.add_argument(
        "--open-case",
        type=str,
        default=None,
        metavar="CASE_OR_URI",
        help="Opens the given case in the cockpit. Accepts a case id or a "
             "supportcockpit://case/<id> URI - this is what a clicked Windows "
             "notification passes in."
    )
    return parser.parse_args()


EXIT_STARTUP_ERROR = 1
EXIT_SEED_REFUSED = 2


def _seed_workspace(storage: StorageService, force: bool) -> dict[str, int]:
    """Runs the seed, or tells the user why not and exits.

    --seed and --demo replace cases, customers, profile and colleagues. Pointed
    at the real workspace (the default without --workspace) that used to wipe
    it without a question.
    """
    from services.i18n_service import tr
    from services.seed_service import SeedRefusedError
    from utils import startup_dialogs

    try:
        return SeedService(storage).run_seed(force=force)
    except SeedRefusedError as refused:
        found = ", ".join(f"{count} {kind}" for kind, count in refused.user_data.items())
        startup_dialogs.show_error(
            tr("startup.seed_refused_title", "Demo-Daten nicht erzeugt"),
            tr(
                "startup.seed_refused_message",
                "Der Workspace enthält echte Daten ({found}):\n{workspace}\n\n"
                "--seed und --demo würden sie überschreiben. Bitte mit --workspace einen "
                "anderen Ordner angeben, oder mit --force bestätigen (dann wird vorher "
                "eine Sicherung unter data/backups/pre_seed_... angelegt).",
                found=found,
                workspace=refused.workspace_dir,
            ),
        )
        sys.exit(EXIT_SEED_REFUSED)


def _run(args: argparse.Namespace) -> None:
    from services.i18n_service import tr
    from utils import startup_dialogs

    config = AppConfig.load_user_config(cli_workspace=args.workspace)

    # The configured workspace is gone (network drive not connected, folder
    # moved). Quietly starting on the default folder shows an empty app - which
    # looks like data loss - and the next save makes that folder permanent.
    if config.missing_workspace_dir is not None:
        go_on = startup_dialogs.ask_yes_no(
            tr("startup.workspace_missing_title", "Workspace nicht erreichbar"),
            tr(
                "startup.workspace_missing_message",
                "Der eingestellte Workspace ist nicht erreichbar:\n{missing}\n\n"
                "Stattdessen mit dem Standard-Workspace starten?\n{fallback}\n\n"
                "Bei „Nein“ wird die Anwendung beendet und die Einstellung bleibt unverändert.",
                missing=config.missing_workspace_dir,
                fallback=config.workspace_dir,
            ),
        )
        if not go_on:
            sys.exit(EXIT_STARTUP_ERROR)

    set_crash_log_dir(config.workspace_dir / "logs")

    # A clicked Windows notification starts a *second* process with the toast's
    # launch URI. If the app is already running, that process must only hand the
    # case over and exit - otherwise every click opens another copy.
    from services.instance_service import InstanceService, parse_case_uri, register_uri_scheme
    requested_case = parse_case_uri(args.open_case)
    instance = InstanceService(config.workspace_dir)
    if instance.handoff_or_claim(requested_case):
        print(f"[*] Case {requested_case} handed to the running instance.")
        sys.exit(0)

    # Nothing was handed over and the lock belongs to a live instance: a second
    # window on the same workspace would overwrite the first one's saves (and
    # the other way round), so this start ends here - before anything is read,
    # seeded, backed up or archived.
    if instance.is_blocked_by_other_instance():
        startup_dialogs.show_error(
            tr("startup.already_running_title", "Support Cockpit läuft bereits"),
            tr(
                "startup.already_running_message",
                "Support Cockpit ist mit diesem Workspace bereits geöffnet:\n{workspace}\n\n"
                "Bitte das laufende Fenster verwenden (ggf. über das Symbol im Infobereich).",
                workspace=config.workspace_dir,
            ),
        )
        sys.exit(EXIT_STARTUP_ERROR)

    try:
        register_uri_scheme()

        storage = StorageService(config)

        if args.seed:
            print(f"[*] Seeding test data in workspace: {config.workspace_dir}")
            summary = _seed_workspace(storage, force=args.force)
            print(f"[+] Seeding complete! Created: {summary}")
            sys.exit(0)

        if args.demo:
            print("[*] Starting Support Cockpit in DEMO mode...")
            _seed_workspace(storage, force=args.force)

        # Daily backup and auto-archiving are housekeeping: if one of them
        # fails, the app still starts - the failure is in the log.
        try:
            storage.perform_daily_backup()
        except Exception as err:
            logger.error(f"Daily backup failed: {err}", exc_info=True)
        try:
            archived_count = storage.auto_archive_completed_cases(threshold_days=30)
            if archived_count > 0:
                print(f"[*] Auto-archived {archived_count} completed cases (>= 30 days).")
        except Exception as err:
            logger.error(f"Auto-archiving failed: {err}", exc_info=True)

        # Import UI app and run
        from ui.app import SupportCockpitApp
        app = SupportCockpitApp(config)
        app.instance_service = instance
        if requested_case:
            app.request_open_case(requested_case)
        app.mainloop()
    finally:
        instance.release()


def main():
    args = parse_args()
    try:
        _run(args)
    except KeyboardInterrupt:
        print("[*] Application interrupted by user.")
    except Exception as e:
        # Everything up to and including the window build used to fail without
        # a trace: the Tk error hook only covers callbacks of the running
        # program, and in the packaged .exe stdout is None. An unreadable data
        # file, a failed directory or a crash in the window build all looked
        # like "the app just does not start". Now it is in the crash log and
        # in front of the user.
        _report_tkinter_exception(*sys.exc_info())
        print(f"[-] Application execution error: {e}")
        try:
            from services.i18n_service import tr
            from utils import startup_dialogs

            startup_dialogs.show_error(
                tr("startup.error_title", "Support Cockpit konnte nicht gestartet werden"),
                tr(
                    "startup.error_message",
                    "Beim Start ist ein Fehler aufgetreten:\n\n{error}\n\nDetails stehen in:\n{log}",
                    error=f"{type(e).__name__}: {e}",
                    log=_crash_log_dir() / "tkinter_error.log",
                ),
            )
        except Exception:
            pass
        sys.exit(EXIT_STARTUP_ERROR)


if __name__ == "__main__":
    main()
