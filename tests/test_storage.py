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
