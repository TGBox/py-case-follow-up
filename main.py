import argparse
import sys
from pathlib import Path

# Ensure src/ directory is in sys.path
src_dir = Path(__file__).parent.resolve() / "src"
if str(src_dir) not in sys.path:
    sys.path.insert(0, str(src_dir))

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

    workspace_path = Path(args.workspace) if args.workspace else Path.cwd()
    config = AppConfig(workspace_dir=workspace_path)
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
