import pytest
from pathlib import Path
from models.case import Case
from models.profile import Colleague
from services.p2p_sync_service import P2PSyncService, CaseDiffItem
from services.storage_service import StorageService, AppConfig


def test_p2p_sync_compares_cases_and_detects_conflicts(tmp_path: Path):
    config = AppConfig(workspace_dir=tmp_path)
    storage = StorageService(config)

    # Local cases
    c_local1 = Case(case_id="T-2026-0001", updated_at="2026-08-20T10:00:00")
    c_local1.classification.title = "Lokale Version"
    c_local2 = Case(case_id="T-2026-0002", updated_at="2026-08-21T12:00:00")
    c_local2.classification.title = "Identischer Fall"

    storage.save_cases([c_local1, c_local2])

    p2p = P2PSyncService(storage)

    # Remote payload from colleague
    c_remote1 = Case(case_id="T-2026-0001", updated_at="2026-08-22T14:00:00")
    c_remote1.classification.title = "Remote Version (Neuere Änderung)"
    c_remote2 = Case(case_id="T-2026-0002", updated_at="2026-08-21T12:00:00")
    c_remote2.classification.title = "Identischer Fall"
    c_remote3 = Case(case_id="T-2026-0003", updated_at="2026-08-23T09:00:00")
    c_remote3.classification.title = "Neuer Remote-Fall"

    diff_items = p2p.compute_diff([c_remote1, c_remote2, c_remote3])

    assert len(diff_items) == 3

    statuses = {item.case_id: item.status for item in diff_items}
    assert statuses["T-2026-0001"] == "REMOTE_NEWER"
    assert statuses["T-2026-0002"] == "IDENTICAL"
    assert statuses["T-2026-0003"] == "NEW"


def test_p2p_sync_merges_remote_cases(tmp_path: Path):
    config = AppConfig(workspace_dir=tmp_path)
    storage = StorageService(config)

    c_local = Case(case_id="T-001", updated_at="2026-08-01T10:00:00")
    c_local.classification.title = "Alt"
    storage.save_cases([c_local])

    p2p = P2PSyncService(storage)

    c_remote = Case(case_id="T-001", updated_at="2026-08-02T10:00:00")
    c_remote.classification.title = "Neu von Kollegin"
    c_new_remote = Case(case_id="T-002", updated_at="2026-08-02T11:00:00")
    c_new_remote.classification.title = "Vollkommen neu"

    p2p.import_selected_cases([c_remote, c_new_remote])

    updated_cases = storage.load_cases()
    assert len(updated_cases) == 2
    merged_ids = [c.case_id for c in updated_cases]
    assert "T-001" in merged_ids
    assert "T-002" in merged_ids

    found_001 = next(c for c in updated_cases if c.case_id == "T-001")
    assert found_001.classification.title == "Neu von Kollegin"
