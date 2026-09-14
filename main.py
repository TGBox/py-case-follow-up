import argparse
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
        help="Generates seed test data (5 customers, 8 cases, schemas, templates, wiki DB) and exits."
    )
    parser.add_argument(
        "--demo",
        action="store_true",
        help="Generates seed test data and launches the GUI in demo mode."
    )
    return parser.parse_args()


def main():
    args = parse_args()

    config = AppConfig.load_user_config(cli_workspace=args.workspace)
    set_crash_log_dir(config.workspace_dir / "logs")
    storage = StorageService(config)

    if args.seed:
        print(f"[*] Seeding test data in workspace: {config.workspace_dir}")
        seed_service = SeedService(storage)
        summary = seed_service.run_seed(force=True)
        print(f"[+] Seeding complete! Created: {summary}")
        sys.exit(0)

    if args.demo:
        print("[*] Starting Support Cockpit in DEMO mode...")
        seed_service = SeedService(storage)
        seed_service.run_seed(force=True)

    # Perform daily backup and auto-archiving
    storage.perform_daily_backup()
    archived_count = storage.auto_archive_completed_cases(threshold_days=30)
    if archived_count > 0:
        print(f"[*] Auto-archived {archived_count} completed cases (>= 30 days).")

    # Import UI app and run
    try:
        from ui.app import SupportCockpitApp
        app = SupportCockpitApp(config)
        app.mainloop()
    except KeyboardInterrupt:
        print("[*] Application interrupted by user.")
    except Exception as e:
        print(f"[-] Application execution error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
