import pytest # type: ignore
from pathlib import Path
from config import AppConfig
from services.storage_service import StorageService
from services.seed_service import SeedService
from services.export_service import ExportService
from services.scoring_service import ScoringService
from enums import UrgencyLevel


def test_ui_service_workflow_integration(tmp_path: Path):
    config = AppConfig(workspace_dir=tmp_path, username="test_agent")
    storage = StorageService(config)
    seed_service = SeedService(storage)
    seed_service.run_seed(force=True)

    # 1. Load cases and schemas
    cases = storage.load_cases()
    schemas = storage.load_schemas()
    templates = storage.load_templates()

    assert len(cases) == 12
    target_case = cases[0]
    schema = next(s for s in schemas if s.schema_id == target_case.classification.schema_id)

    # 2. Update form data in case
    target_case.form_data["database_dump_provided"] = True
    target_case.missing_required_fields.clear()
    target_case.workflow_status.is_data_complete = True

    storage.save_cases(cases)

    # 3. Export service check
    export_service = ExportService(storage)
    template = templates[0]
    success, missing, text = export_service.render_template(target_case, template, schema)

    assert success is True
    assert "Gemeinschaftspraxis" in text

    # 4. Archiving case
    storage.archive_single_case(target_case.case_id)
    remaining_cases = storage.load_cases()
    archived_cases = storage.load_archive()

    assert len(remaining_cases) == 11
    assert len(archived_cases) == 1
    assert archived_cases[0].case_id == target_case.case_id


def test_handover_dialog_formatting():
    from enums import Actor, get_actor_display

    def format_handover_text(person_val: str, note_val: str) -> str:
        new_actor_val = Actor.DEVELOPMENT.value
        channel = "Slacknachricht / Chat"
        person_str = f" ({person_val})" if len(person_val) > 0 else ""
        note_str = f" | Details: {note_val}" if len(note_val) > 0 else ""
        return f"Zuständigkeit übergeben an: {get_actor_display(new_actor_val)}{person_str} via {channel}{note_str}"

    note_text1 = format_handover_text("Max Mustermann", "Bitte um Prüfung")
    assert "Zuständigkeit übergeben an: Entwicklung (Max Mustermann) via Slacknachricht / Chat | Details: Bitte um Prüfung" in note_text1

    note_text2 = format_handover_text("", "")
    assert "Zuständigkeit übergeben an: Entwicklung via Slacknachricht / Chat" in note_text2



def test_followup_flyout_case_selection():
    from models.case import Case, Classification
    from ui.dialogs.followup_flyout_dialog import FollowupFlyoutDialog

    c1 = Case(case_id="T-9999", classification=Classification(title="Test Case"))
    selected_cases = []

    def mock_on_case_selected(case):
        selected_cases.append(case)

    flyout = FollowupFlyoutDialog.__new__(FollowupFlyoutDialog)
    flyout.on_case_selected = mock_on_case_selected
    flyout.destroy = lambda: None

    flyout.select_case(c1)

    assert len(selected_cases) == 1
    assert selected_cases[0].case_id == "T-9999"


def test_toast_notification_open_callback():
    from ui.widgets.toast_notification import ToastNotification
    from models.case import Case

    opened_cases = []
    c1 = Case(case_id="T-8888")

    def mock_open():
        opened_cases.append(c1)

    toast = ToastNotification.__new__(ToastNotification)
    toast.on_open = mock_open
    toast.safe_destroy = lambda: None

    toast.handle_open()

    assert len(opened_cases) == 1
    assert opened_cases[0].case_id == "T-8888"

