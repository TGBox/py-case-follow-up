import argparse
import os
import sys
from pathlib import Path

# Ensure src/ directory is in sys.path
src_dir = Path(__file__).parent.resolve() / "src"
if str(src_dir) not in sys.path:
    sys.path.insert(0, str(src_dir))

import tkinter
import traceback
from types import TracebackType


_seen_exceptions: set[str] = set()


def _report_tkinter_exception(exc: type[BaseException], val: BaseException, tb: TracebackType | None) -> None:
    tb_lines = traceback.format_exception(exc, val, tb)
    tb_str = "".join(tb_lines)

    # 1. Log to file with immediate sync to disk
    try:
        log_dir = Path("logs")
        log_dir.mkdir(exist_ok=True)
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
        print("\n=================== [TKINTER CALLBACK EXCEPTION] ===================", file=sys.stderr)
        print(tb_str.strip(), file=sys.stderr)
        print(f"--> Ausführlicher Log gespeichert in: logs/tkinter_error.log", file=sys.stderr)
        print("====================================================================\n", file=sys.stderr)
        sys.stderr.flush()


tkinter.Tk.report_callback_exception = _report_tkinter_exception

from config import AppConfig
from services.storage_service import StorageService
from services.seed_service import SeedService


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
    storage = StorageService(config)

    if args.seed:
        print(f"[*] Seeding test data in workspace: {config.workspace_dir}")
        seed_service = SeedService(storage)
        summary = seed_service.run_seed(force=True)
        print(f"[+] Seeding complete! Created: {summary}")
        sys.exit(0)

    if args.demo:
        print(f"[*] Starting Support Cockpit in DEMO mode...")
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
    except Exception as e:
        print(f"[-] Application execution error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
