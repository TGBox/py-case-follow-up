import pytest
from pathlib import Path
from src.config import AppConfig
from src.models.case import Case, CaseCustomer, Classification, WorkflowStatus
from src.models.profile import Colleague
from src.services.storage_service import StorageService, atomic_save_json
from src.services.p2p_sync_service import P2PSyncService


def test_p2p_diff_computation(tmp_path: Path):
    config = AppConfig(workspace_dir=tmp_path)
    storage = StorageService(config)
    p2p_service = P2PSyncService(storage)

    # Local cases
    c_local_older = Case(case_id="T-100", updated_at="2026-08-23T10:00:00")
    c_local_newer = Case(case_id="T-200", updated_at="2026-08-23T14:00:00")
    c_local_identical = Case(case_id="T-300", updated_at="2026-08-23T12:00:00")
    storage.save_cases([c_local_older, c_local_newer, c_local_identical])

    # Remote cases from colleague
    c_remote_newer = Case(case_id="T-100", updated_at="2026-08-23T12:00:00")  # REMOTE_NEWER
    c_remote_older = Case(case_id="T-200", updated_at="2026-08-23T10:00:00")  # LOCAL_NEWER
    c_remote_identical = Case(case_id="T-300", updated_at="2026-08-23T12:00:00")  # IDENTICAL
    c_remote_brand_new = Case(case_id="T-400", updated_at="2026-08-23T15:00:00")  # NEW

    remote_cases = [c_remote_newer, c_remote_older, c_remote_identical, c_remote_brand_new]
    diff = p2p_service.compute_diff(remote_cases)

    assert len(diff) == 4
    diff_map = {item.case_id: item.status for item in diff}

    assert diff_map["T-100"] == "REMOTE_NEWER"
    assert diff_map["T-200"] == "LOCAL_NEWER"
    assert diff_map["T-300"] == "IDENTICAL"
    assert diff_map["T-400"] == "NEW"


def test_p2p_selective_import(tmp_path: Path):
    config = AppConfig(workspace_dir=tmp_path)
    storage = StorageService(config)
    p2p_service = P2PSyncService(storage)

    c_local = Case(case_id="T-100", updated_at="2026-08-23T10:00:00")
    storage.save_cases([c_local])

    c_remote_100 = Case(case_id="T-100", updated_at="2026-08-23T12:00:00", created_by="Colleague")
    c_remote_400 = Case(case_id="T-400", updated_at="2026-08-23T15:00:00", created_by="Colleague")

    count = p2p_service.import_selected_cases([c_remote_100, c_remote_400])
    assert count == 2

    updated_local = storage.load_cases()
    assert len(updated_local) == 2
    local_map = {c.case_id: c for c in updated_local}
    assert local_map["T-100"].updated_at == "2026-08-23T12:00:00"
    assert local_map["T-400"].created_by == "Colleague"
