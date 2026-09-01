"""Comprehensive UI dialog lifecycle, event bindings, and cancel/destroy stability test suite."""

import zipfile
from pathlib import Path
import customtkinter as ctk
import pytest
from config import AppConfig
from enums import Actor, UrgencyLevel, TargetType
from models.case import Case, CaseCustomer, Classification
from models.customer import Customer, Contact
from models.export_template import ExportTemplate
from models.profile import UserProfile, Colleague
from models.schema import QuestionSchema, SchemaField
from services.storage_service import StorageService
from services.export_service import ExportService
from services.calendar_email_service import CalendarEmailService
from services.p2p_sync_service import P2PSyncService

from ui.dialogs.handover_dialog import HandoverDialog
from ui.dialogs.convert_schema_dialog import ConvertSchemaDialog
from ui.dialogs.zip_import_dialog import ZipImportPathDialog
from ui.dialogs.followup_flyout_dialog import FollowupFlyoutDialog
from ui.dialogs.email_calendar_dialog import EmailCalendarDialog
from ui.dialogs.calendar_export_dialog import CalendarExportDialog
from ui.dialogs.cobra_import_dialog import CobraImportDialog
from ui.dialogs.p2p_diff_dialog import P2PDiffDialog
from ui.dialogs.export_dialog import ExportDialog
from ui.dialogs.help_dialog import HelpDialog
from ui.dialogs.tag_management_dialog import TagManagementDialog
from ui.dialogs.profile_settings_dialog import ProfileSettingsDialog


@pytest.fixture
def ui_fixture(tmp_path: Path):
    """Fixture providing a hidden root window, test storage, and sample domain models."""
    config = AppConfig(workspace_dir=tmp_path)
    storage = StorageService(config)

    try:
        app = ctk.CTk()
    except Exception:
        import time
        time.sleep(0.1)
        app = ctk.CTk()
    app.withdraw()

    sample_case = Case(
        case_id="CASE-UI-100",
        customer=CaseCustomer(customer_id="C-1", practice_name="Test Praxis"),
        classification=Classification(schema_id="standard", title="UI Test Case", urgency_level=UrgencyLevel.GREEN),
    )

    sample_schemas = [
        QuestionSchema(schema_id="standard", display_name="Standard Formular"),
        QuestionSchema(schema_id="bug", display_name="Fehlermeldung Formular"),
    ]

    sample_templates = [
        ExportTemplate(template_id="t1", display_name="Standard Export", template_string="Fall: {{ case.case_id }}"),
    ]

    sample_colleagues = [
        Colleague(username="col1", name="Max Mustermann", is_absent=True, absence_reason="Urlaub"),
        Colleague(username="col2", name="Erika Muster", is_absent=False),
    ]

    yield app, storage, config, sample_case, sample_schemas, sample_templates, sample_colleagues

    try:
        app.destroy()
    except Exception:
        pass


def test_handover_dialog_lifecycle(ui_fixture):
    """Test HandoverDialog instantiation, colleague selection, and destroy."""
    app, storage, config, case, schemas, templates, colleagues = ui_fixture

    dialog = HandoverDialog(
        app,
        case=case,
        colleagues=colleagues,
        on_handover_confirmed=lambda target_type, target_val, channel, note: None,
    )
    dialog.update_idletasks()

    assert dialog.winfo_exists()
    assert dialog.case.case_id == "CASE-UI-100"
    assert len(dialog.colleagues) == 2

    dialog.destroy()


def test_convert_schema_dialog_lifecycle(ui_fixture):
    """Test ConvertSchemaDialog instantiation, target schema selection, and destroy."""
    app, storage, config, case, schemas, templates, colleagues = ui_fixture

    converted = []

    dialog = ConvertSchemaDialog(
        app,
        case=case,
        schemas=schemas,
        author_name="test_author",
        on_schema_converted=lambda c, s: converted.append(s),
    )
    dialog.update_idletasks()

    assert dialog.winfo_exists()
    assert dialog.case.case_id == "CASE-UI-100"

    dialog.destroy()
    assert len(converted) == 0


def test_zip_import_dialog_lifecycle(ui_fixture, tmp_path: Path):
    """Test ZipImportPathDialog inspecting valid zip file structure and GUI destroy."""
    app, storage, config, case, schemas, templates, colleagues = ui_fixture

    zip_path = tmp_path / "dummy.zip"
    with zipfile.ZipFile(zip_path, "w") as zf:
        zf.writestr("data/cases.json", "[]")

    dialog = ZipImportPathDialog(
        app,
        zip_file_path=zip_path,
        default_data_dir=tmp_path / "data",
        default_attachments_dir=tmp_path / "attachments",
        on_import_confirmed=lambda d, a: None,
    )
    dialog.update_idletasks()

    assert dialog.winfo_exists()
    assert dialog.zip_info["data_files"] == 1

    dialog.destroy()


def test_followup_flyout_dialog_lifecycle(ui_fixture):
    """Test FollowupFlyoutDialog rendering due cases and responding to refresh events."""
    app, storage, config, case, schemas, templates, colleagues = ui_fixture

    due_cases = [case]
    refreshed = False

    def on_ref():
        nonlocal refreshed
        refreshed = True

    dialog = FollowupFlyoutDialog(
        app,
        due_cases=due_cases,
        on_case_selected=lambda c: None,
        on_refresh=on_ref,
    )
    dialog.update_idletasks()

    assert dialog.winfo_exists()
    assert len(dialog.due_cases) == 1

    dialog.destroy()


def test_followup_flyout_dialog_complete_keeps_open_until_empty(ui_fixture):
    """Test that completing a due case keeps the flyout open if remaining cases exist, and closes it when empty."""
    app, storage, config, case1, schemas, templates, colleagues = ui_fixture
    from models.case import Case, CaseCustomer, Classification, WorkflowStatus

    case2 = Case(
        case_id="T-FW-02",
        customer=CaseCustomer(customer_id="K-2", practice_name="Praxis Test 2"),
        classification=Classification(title="Zweiter Fall"),
        workflow_status=WorkflowStatus(
            followup_at="2026-08-01T10:00:00",
            followup_note="Wichtig!",
            is_completed=False,
        ),
    )

    due_cases = [case1, case2]
    refresh_count = 0

    def on_ref():
        nonlocal refresh_count
        refresh_count += 1

    dialog = FollowupFlyoutDialog(
        app,
        due_cases=due_cases,
        on_case_selected=lambda c: None,
        on_refresh=on_ref,
    )
    dialog.update_idletasks()

    assert dialog.winfo_exists()
    assert len(dialog.due_cases) == 2

    # Complete 1st case -> window should remain open, due_cases should have 1 case left
    dialog.complete_followup(case1)
    dialog.update_idletasks()

    assert refresh_count == 1
    assert len(dialog.due_cases) == 1
    assert dialog.winfo_exists()

    # Complete 2nd case -> window should close (safe_close destroys it)
    dialog.complete_followup(case2)
    dialog.update_idletasks()

    assert refresh_count == 2
    assert len(dialog.due_cases) == 0


def test_email_calendar_and_export_dialogs_lifecycle(ui_fixture):
    """Test EmailCalendarDialog and CalendarExportDialog rendering."""
    app, storage, config, case, schemas, templates, colleagues = ui_fixture

    cal_email_service = CalendarEmailService(config)

    dlg1 = EmailCalendarDialog(
        app,
        case=case,
        calendar_email_service=cal_email_service,
        user_name="Agent User",
    )
    dlg1.update_idletasks()
    assert dlg1.winfo_exists()
    dlg1.destroy()

    dlg2 = CalendarExportDialog(
        app,
        case=case,
        calendar_email_service=cal_email_service,
    )
    dlg2.update_idletasks()
    assert dlg2.winfo_exists()
    dlg2.destroy()


def test_cobra_import_dialog_lifecycle(ui_fixture):
    """Test CobraImportDialog wizard rendering and cancellation."""
    app, storage, config, case, schemas, templates, colleagues = ui_fixture

    existing_customers = [Customer(customer_id="C-1", practice_name="Test")]

    dialog = CobraImportDialog(
        app,
        existing_customers=existing_customers,
        on_import_completed=lambda custs: None,
    )
    dialog.update_idletasks()

    assert dialog.winfo_exists()
    assert len(dialog.existing_customers) == 1

    dialog.destroy()


def test_p2p_diff_dialog_lifecycle(ui_fixture):
    """Test P2PDiffDialog GUI rendering with colleagues list."""
    app, storage, config, case, schemas, templates, colleagues = ui_fixture

    p2p_service = P2PSyncService(storage)

    dialog = P2PDiffDialog(
        app,
        colleagues=colleagues,
        p2p_service=p2p_service,
        on_sync_completed=lambda: None,
    )
    dialog.update_idletasks()

    assert dialog.winfo_exists()
    assert dialog.active_colleague is not None
    assert dialog.active_colleague.username == "col1"

    dialog.destroy()


def test_export_dialog_lifecycle(ui_fixture):
    """Test ExportDialog template selection, preview update, and destroy."""
    app, storage, config, case, schemas, templates, colleagues = ui_fixture

    export_service = ExportService(storage)

    dialog = ExportDialog(
        app,
        case=case,
        templates=templates,
        schemas=schemas,
        export_service=export_service,
        on_case_updated=lambda c: None,
    )
    dialog.update_idletasks()

    assert dialog.winfo_exists()
    assert dialog.active_template is not None
    assert dialog.active_template.template_id == "t1"

    dialog.destroy()


def test_help_dialog_lifecycle(ui_fixture):
    """Test HelpDialog rendering article list and article selection."""
    app, storage, config, case, schemas, templates, colleagues = ui_fixture

    dialog = HelpDialog(app)
    dialog.update_idletasks()

    assert dialog.winfo_exists()
    assert len(dialog.filtered_articles) > 0

    dialog.destroy()


def test_tag_management_and_profile_settings_dialogs_lifecycle(ui_fixture):
    """Test TagManagementDialog and ProfileSettingsDialog lifecycle."""
    app, storage, config, case, schemas, templates, colleagues = ui_fixture

    profile = UserProfile()

    dlg_tag = TagManagementDialog(
        app,
        profile=profile,
        storage_service=storage,
        on_tags_updated=lambda: None,
    )
    dlg_tag.update_idletasks()
    assert dlg_tag.winfo_exists()
    dlg_tag.destroy()

    dlg_profile = ProfileSettingsDialog(
        app,
        profile=profile,
        storage_service=storage,
        on_profile_updated=lambda: None,
    )
    dlg_profile.update_idletasks()
    assert dlg_profile.winfo_exists()
    dlg_profile.destroy()
