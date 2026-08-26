import pytest # type: ignore
from pathlib import Path
import customtkinter as ctk
from unittest.mock import MagicMock

from config import AppConfig
from services.storage_service import StorageService
from services.search_service import SearchService, parse_search_query
from services.deep_search_service import DeepSearchService
from models.case import Case, Classification, WorkflowStatus, CaseCustomer
from models.customer import Customer
from enums import UrgencyLevel, Actor


def test_storage_service_caching_and_update_single(tmp_path: Path):
    config = AppConfig(workspace_dir=tmp_path)
    storage = StorageService(config)

    c1 = Case(case_id="FALL-001", customer=CaseCustomer(customer_id="C1", practice_name="Praxis A"))
    storage.save_cases([c1])

    # First load populates cache
    loaded1 = storage.load_cases(use_cache=True)
    assert len(loaded1) == 1
    assert loaded1[0].case_id == "FALL-001"

    # Second load uses cache (same instance)
    loaded2 = storage.load_cases(use_cache=True)
    assert loaded1 is loaded2

    # Update single case
    c1.classification.title = "Updated Title"
    storage.update_single_case(c1)

    loaded_after = storage.load_cases(use_cache=True)
    assert len(loaded_after) == 1
    assert loaded_after[0].classification.title == "Updated Title"

    # Verify invalidation
    storage.invalidate_cache()
    fresh_loaded = storage.load_cases(use_cache=True)
    assert fresh_loaded is not loaded2
    assert fresh_loaded[0].classification.title == "Updated Title"


def test_search_query_lru_cache():
    q1 = parse_search_query("vip:true status:open")
    q2 = parse_search_query("vip:true status:open")
    assert q1 is q2


def test_deep_search_file_lines_cache(tmp_path: Path):
    att_dir = tmp_path / "data" / "attachments" / "FALL-001"
    att_dir.mkdir(parents=True)
    test_file = att_dir / "log.txt"
    test_file.write_text("Line 1: Error occurred\nLine 2: Fixed\n", encoding="utf-8")

    deep_svc = DeepSearchService(workspace_dir=tmp_path)
    c = Case(case_id="FALL-001", attachment_directory=str(att_dir))

    res1 = deep_svc.search_case_attachments(c, "Error")
    assert len(res1) == 1
    assert "Line 1" in res1[0]["snippet"]
    assert str(test_file) in deep_svc._file_lines_cache

    # Second search hits cache
    res2 = deep_svc.search_case_attachments(c, "Error")
    assert len(res2) == 1

    # Modify file mtime/content
    test_file.write_text("Line 1: No issue\nLine 2: Critical Error\n", encoding="utf-8")
    res3 = deep_svc.search_case_attachments(c, "Critical")
    assert len(res3) == 1
    assert "Line 2" in res3[0]["snippet"]
