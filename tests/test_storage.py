import json
import pytest
from pathlib import Path
from config import AppConfig
from services.storage_service import StorageService, atomic_save_json, safe_read_json
from models.case import Case, CaseCustomer, Classification, WorkflowStatus, TimelineEntry
from enums import UrgencyLevel, BoardColumn, Actor


@pytest.fixture
def tmp_config(tmp_path: Path) -> AppConfig:
    return AppConfig(workspace_dir=tmp_path, username="test_user")


def test_atomic_save_json(tmp_path: Path):
    target = tmp_path / "test.json"
    data = {"key": "value", "number": 42}
    atomic_save_json(target, data)

    assert target.exists()
    with open(target, "r", encoding="utf-8") as f:
        loaded = json.load(f)
    assert loaded == data
    # Temporary file should no longer exist
    assert not (tmp_path / "test.json.tmp.json").exists()


def test_safe_read_json_missing(tmp_path: Path):
    target = tmp_path / "nonexistent.json"
    result = safe_read_json(target, default_factory=list)
    assert result == []
    assert target.exists()


def test_safe_read_json_corrupted(tmp_path: Path):
    target = tmp_path / "corrupted.json"
    target.write_text("INVALID JSON {{{", encoding="utf-8")
    
    result = safe_read_json(target, default_factory=dict)
    assert result == {}
    assert target.exists()
    # Check that corrupted file backup was created
    corrupted_files = list(tmp_path.glob("corrupted.corrupted_*.json"))
    assert len(corrupted_files) == 1


def test_storage_service_cases_roundtrip(tmp_config: AppConfig):
    storage = StorageService(tmp_config)
    case = Case(
        case_id="T-2026-0001",
        created_at="2026-08-23T09:15:00",
        updated_at="2026-08-23T14:30:00",
        created_by="Daniel Rösch",
        assigned_to="Daniel Rösch",
        customer=CaseCustomer(customer_id="K-10482", practice_name="Praxis A", is_vip=True),
        classification=Classification(schema_id="s1", title="Test Case", urgency_level=UrgencyLevel.RED),
        workflow_status=WorkflowStatus(board_column=BoardColumn.ACTION_REQUIRED, current_actor=Actor.DEVELOPMENT),
        form_data={"field1": "val1"},
        missing_required_fields=["field2"],
        attachment_directory="attachments/T-2026-0001_Praxis_A",
        timeline=[TimelineEntry(timestamp="2026-08-23T09:15:00", author="Daniel", note="Initial note")],
    )

    storage.save_cases([case])
    loaded_cases = storage.load_cases()

    assert len(loaded_cases) == 1
    assert loaded_cases[0].case_id == "T-2026-0001"
    assert loaded_cases[0].customer.practice_name == "Praxis A"
    assert loaded_cases[0].customer.is_vip is True
    assert loaded_cases[0].classification.urgency_level == UrgencyLevel.RED
    assert loaded_cases[0].timeline[0].note == "Initial note"


def test_daily_backup(tmp_config: AppConfig):
    storage = StorageService(tmp_config)
    case = Case(case_id="T-2026-0001")
    storage.save_cases([case])

    backup_path = storage.perform_daily_backup("2026-08-23")
    assert backup_path is not None
    assert backup_path.exists()
    assert backup_path.name == "cases_2026-08-23.json"


def test_archive_single_case(tmp_config: AppConfig):
    storage = StorageService(tmp_config)
    case1 = Case(case_id="T-001")
    case2 = Case(case_id="T-002")
    storage.save_cases([case1, case2])

    success = storage.archive_single_case("T-001")
    assert success is True

    remaining = storage.load_cases()
    archived = storage.load_archive()

    assert len(remaining) == 1
    assert remaining[0].case_id == "T-002"
    assert len(archived) == 1
    assert archived[0].case_id == "T-001"
    assert archived[0].workflow_status.is_archived is True


def test_custom_workspace_and_path_overrides(tmp_path: Path):
    custom_ws = tmp_path / "custom_data_dir"
    custom_cases = tmp_path / "external_cases.json"
    
    config = AppConfig(workspace_dir=custom_ws, custom_cases_path=custom_cases)
    config.ensure_directories()
    
    assert config.workspace_dir == custom_ws
    assert config.cases_path == custom_cases
    assert config.customers_path == custom_ws / "data" / "customers.json"
    
    storage = StorageService(config)
    case = Case(case_id="T-999")
    storage.save_cases([case])

    assert custom_cases.exists()
    loaded = storage.load_cases()
    assert len(loaded) == 1
    assert loaded[0].case_id == "T-999"


def test_followup_data_serialization(tmp_config: AppConfig):
    storage = StorageService(tmp_config)
    case = Case(case_id="T-777")
    case.workflow_status.followup_at = "2026-08-25T09:00:00"
    case.workflow_status.followup_note = "Beim Entwickler nachfragen"

    storage.save_cases([case])
    loaded = storage.load_cases()

    assert len(loaded) == 1
    assert loaded[0].workflow_status.followup_at == "2026-08-25T09:00:00"
    assert loaded[0].workflow_status.followup_note == "Beim Entwickler nachfragen"


def test_template_crud_storage(tmp_config: AppConfig):
    storage = StorageService(tmp_config)
    from models.export_template import ExportTemplate
    from enums import TargetType

    tmpl = ExportTemplate(
        template_id="custom_test_tmpl",
        display_name="Custom Test",
        target_type=TargetType.FILE_EXPORT.value,
        required_schema_fields=["billing_quarter"],
        template_string="Hello {{ form_data.billing_quarter }}"
    )

    storage.save_templates([tmpl])
    loaded = storage.load_templates()

    assert any(t.template_id == "custom_test_tmpl" for t in loaded)
    found = next(t for t in loaded if t.template_id == "custom_test_tmpl")
    assert found.display_name == "Custom Test"
    assert found.required_schema_fields == ["billing_quarter"]


from datetime import datetime, timedelta
from utils.datetime_utils import format_iso


def test_corrupt_json_file_recovery(tmp_path: Path):
    corrupt_file = tmp_path / "corrupt_cases.json"
    with open(corrupt_file, "w", encoding="utf-8") as f:
        f.write("{ INVALID JSON DATA }}}")

    data = safe_read_json(corrupt_file, default_factory=list)
    assert data == []
    # Verify backup file created
    bak_files = [f for f in tmp_path.iterdir() if f.name.startswith("corrupt_cases.corrupted_")]
    assert len(bak_files) == 1


def test_auto_archive_threshold_boundary(tmp_config: AppConfig):
    storage = StorageService(tmp_config)
    now = datetime.now()

    old_completed_case = Case(
        case_id="T-OLD",
        updated_at=format_iso(now - timedelta(days=31)),
        workflow_status=WorkflowStatus(is_completed=True, is_archived=False)
    )
    recent_completed_case = Case(
        case_id="T-RECENT",
        updated_at=format_iso(now - timedelta(days=5)),
        workflow_status=WorkflowStatus(is_completed=True, is_archived=False)
    )

    storage.save_cases([old_completed_case, recent_completed_case])

    count = storage.auto_archive_completed_cases(threshold_days=30)
    assert count == 1

    remaining = storage.load_cases()
    archived = storage.load_archive()

    assert len(remaining) == 1
    assert remaining[0].case_id == "T-RECENT"
    assert len(archived) == 1
    assert archived[0].case_id == "T-OLD"


def test_german_date_formatting_and_parsing():
    from utils.datetime_utils import format_german_date, format_german_datetime, parse_german_date

    iso_str = "2026-08-23T16:30:00"
    assert format_german_date(iso_str) == "23.08.2026"
    assert format_german_datetime(iso_str) == "23.08.2026 16:30"
    assert format_german_datetime(iso_str, include_seconds=True) == "23.08.2026 16:30:00"

    parsed = parse_german_date("23.08.2026 16:30")
    assert parsed == "2026-08-23T16:30:00"

    parsed_date_only = parse_german_date("23.08.2026")
    assert parsed_date_only == "2026-08-23T00:00:00"


def test_column_width_persistence(tmp_path: Path, monkeypatch):
    test_config_file = tmp_path / "user_config.json"
    monkeypatch.setattr("config.get_global_config_file", lambda: test_config_file)

    config = AppConfig(workspace_dir=tmp_path)
    config.column_widths = {"cockpit_left": 350, "cockpit_center": 500, "cockpit_right": 300, "board_column": 320}

    # Save user config
    config.save_user_config()

    # Load back
    loaded_config = AppConfig.load_user_config()
    assert loaded_config.column_widths["cockpit_left"] == 350
    assert loaded_config.column_widths["cockpit_center"] == 500
    assert loaded_config.column_widths["board_column"] == 320


def test_multi_user_profile_management(tmp_path: Path):
    from models.profile import UserInfo, UserProfile
    config = AppConfig(workspace_dir=tmp_path)
    storage = StorageService(config)

    # Save default profile with department
    p1 = UserProfile(user=UserInfo(name="Anna Schmidt", department="Support Team", email="anna@support.de"))
    storage.save_profile(p1)

    # Save second employee profile with department
    p2 = UserProfile(user=UserInfo(name="Ben Becker", department="Entwicklung", email="ben@support.de"))
    storage.save_profile(p2)

    profiles = storage.list_profiles()
    assert "Anna Schmidt" in profiles or "Ben Becker" in profiles

    loaded_p2 = storage.load_profile_by_name("Ben Becker")
    assert loaded_p2.user.name == "Ben Becker"
    assert loaded_p2.user.department == "Entwicklung"
    assert loaded_p2.user.email == "ben@support.de"


def test_reset_column_widths():
    from models.profile import UserProfile, DEFAULT_COLUMN_WIDTHS
    profile = UserProfile()
    profile.ui_settings.column_widths = {"table_col_id": 500, "board_column": 900}
    profile.ui_settings.reset_column_widths()

    assert profile.ui_settings.column_widths == DEFAULT_COLUMN_WIDTHS
    assert profile.ui_settings.column_widths["board_column"] == 280
    assert profile.ui_settings.column_widths["table_col_id"] == 120


def test_colleague_crud_storage(tmp_path: Path):
    from models.profile import Colleague
    config = AppConfig(workspace_dir=tmp_path)
    storage = StorageService(config)

    c1 = Colleague(
        username="mbecker",
        name="Markus Becker",
        department="Entwicklung",
        extension="4022",
        email="m.becker@praxis.de",
        mobile="0171 99988877",
        notes="Spezialist für PVS-Imports",
    )

    assert len(c1.validate()) == 0

    storage.save_colleagues([c1])
    loaded = storage.load_colleagues()

    assert len(loaded) >= 1
    found = next(c for c in loaded if c.username == "mbecker")
    assert found.name == "Markus Becker"
    assert found.department == "Entwicklung"
    assert found.notes == "Spezialist für PVS-Imports"


def test_demo_data_flag_and_ui_settings(tmp_path: Path):
    c_demo = Case(case_id="DEMO-1", is_demo_data=True)
    c_user = Case(case_id="USER-1", is_demo_data=False)

    d_demo = c_demo.to_dict()
    d_user = c_user.to_dict()
    assert d_demo["is_demo_data"] is True
    assert d_user["is_demo_data"] is False

    restored_demo = Case.from_dict(d_demo)
    restored_user = Case.from_dict(d_user)
    assert restored_demo.is_demo_data is True
    assert restored_user.is_demo_data is False

    from models.profile import UISettings
    ui = UISettings(show_demo_data=False)
    ui_dict = ui.to_dict()
    assert ui_dict["show_demo_data"] is False

    ui_restored = UISettings.from_dict(ui_dict)
    assert ui_restored.show_demo_data is False
