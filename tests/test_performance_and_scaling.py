"""Performance benchmarks, scaling verification, and high-volume dataset resilience test suite."""

import time
from pathlib import Path
import pytest
from config import AppConfig
from enums import UrgencyLevel, BoardColumn, Actor
from models.case import Case, CaseCustomer, Classification, WorkflowStatus, TimelineEntry
from models.customer import Customer, Contact
from services.storage_service import StorageService
from services.customer_service import CustomerService
from services.scoring_service import ScoringService
from services.search_service import parse_search_query, SearchService
from services.p2p_sync_service import P2PSyncService
from services.zip_backup_service import ZipBackupService


def generate_bulk_cases(count: int = 1000) -> list[Case]:
    """Helper to generate a large list of valid sample cases."""
    cases = []
    urgencies = [UrgencyLevel.GREEN, UrgencyLevel.YELLOW, UrgencyLevel.RED]
    columns = [BoardColumn.NEW, BoardColumn.ACTION_REQUIRED, BoardColumn.WAITING, BoardColumn.IN_PROGRESS, BoardColumn.DONE]
    actors = [Actor.SUPPORT, Actor.DEVELOPMENT, Actor.TECH, Actor.CUSTOMER]

    for i in range(1, count + 1):
        cust_id = "INTERNAL" if (i % 7 == 0) else f"CUST-{(i % 500) + 1:03d}"
        c = Case(
            case_id=f"BULK-CASE-{i:04d}",
            customer=CaseCustomer(
                customer_id=cust_id,
                practice_name=f"Praxis Dr. Benchmark {i % 100}",
                is_vip=(i % 10 == 0),
            ),
            classification=Classification(
                schema_id="standard",
                title=f"Performance Test Case Title {i}",
                urgency_level=urgencies[i % 3],
                calculated_score=float(i % 120),
                tags=["Abrechnung", "System"] if i % 2 == 0 else ["Hardware"],
            ),
            workflow_status=WorkflowStatus(
                board_column=columns[i % 5],
                current_actor=actors[i % 4],
            ),
            timeline=[
                TimelineEntry(timestamp="2026-08-20T10:00:00", author="agent1", note=f"Initial note {i}"),
                TimelineEntry(timestamp="2026-08-21T11:30:00", author="agent2", note=f"Followup note {i}"),
            ],
        )
        cases.append(c)
    return cases


def generate_bulk_customers(count: int = 500) -> list[Customer]:
    """Helper to generate a large list of sample customers."""
    customers = []
    for i in range(1, count + 1):
        c = Customer(
            customer_id=f"CUST-{i:03d}",
            practice_name=f"Praxis Dr. Benchmark {i}",
            is_vip=(i % 5 == 0),
            system_version=f"v2.4.{i % 10}",
            contacts=[
                Contact(name=f"Dr. Contact {i}", email=f"contact{i}@praxis.de", phone=f"030-100{i}"),
            ],
        )
        customers.append(c)
    return customers


def test_large_cases_dataset_load_and_save_performance(tmp_path: Path):
    """Test saving and loading 1,000 cases finishes within benchmark threshold."""
    config = AppConfig(workspace_dir=tmp_path, username="bench_user")
    storage = StorageService(config)

    bulk_cases = generate_bulk_cases(1000)

    # Measure Save Performance
    start_save = time.perf_counter()
    storage.save_cases(bulk_cases)
    save_duration = time.perf_counter() - start_save

    assert save_duration < 2.0, f"Saving 1000 cases took too long: {save_duration:.3f}s"

    # Measure Load Performance
    start_load = time.perf_counter()
    loaded_cases = storage.load_cases()
    load_duration = time.perf_counter() - start_load

    assert len(loaded_cases) == 1000
    assert load_duration < 1.0, f"Loading 1000 cases took too long: {load_duration:.3f}s"


def test_large_customers_search_performance(tmp_path: Path):
    """Test searching through 500 customers finishes under 200 ms."""
    config = AppConfig(workspace_dir=tmp_path, username="bench_user")
    storage = StorageService(config)
    storage.save_customers(generate_bulk_customers(500))

    cust_service = CustomerService(storage)

    start_time = time.perf_counter()
    results = cust_service.search_customers("Benchmark 42")
    duration = time.perf_counter() - start_time

    assert len(results) >= 1
    assert duration < 0.2, f"Customer search took too long: {duration:.3f}s"


def test_scoring_matrix_bulk_computation():
    """Test computing urgency scores for 1,000 cases finishes under 200 ms."""
    bulk_cases = generate_bulk_cases(1000)
    scoring_service = ScoringService()

    start_time = time.perf_counter()
    for case in bulk_cases:
        score = scoring_service.calculate_score(case)
        level = scoring_service.determine_urgency_level(score)
        assert isinstance(score, float)
        assert level in [UrgencyLevel.GREEN, UrgencyLevel.YELLOW, UrgencyLevel.RED]
    duration = time.perf_counter() - start_time

    assert duration < 0.2, f"Bulk scoring calculation took too long: {duration:.3f}s"


def test_deep_search_token_filtering_scaling():
    """Test token search filtering across 1,000 cases completes rapidly."""
    bulk_cases = generate_bulk_cases(1000)

    query_str = "is:internal vip:true status:open Benchmark"
    query_obj = parse_search_query(query_str)

    start_time = time.perf_counter()
    matching_cases = [c for c in bulk_cases if SearchService.matches_query(c, query_obj)]
    duration = time.perf_counter() - start_time

    assert duration < 0.3, f"Token filtering 1000 cases took too long: {duration:.3f}s"


def test_p2p_large_diff_computation_speed(tmp_path: Path):
    """Test P2P sync diff computation across 500 remote cases finishes under 200 ms."""
    config = AppConfig(workspace_dir=tmp_path, username="bench_user")
    storage = StorageService(config)
    storage.save_cases(generate_bulk_cases(500))

    remote_cases = generate_bulk_cases(500)
    remote_cases[0].updated_at = "2026-08-25T12:00:00"

    p2p_service = P2PSyncService(storage)

    start_time = time.perf_counter()
    diff_items = p2p_service.compute_diff(remote_cases)
    duration = time.perf_counter() - start_time

    assert len(diff_items) == 500
    assert duration < 0.2, f"P2P diff computation took too long: {duration:.3f}s"


def test_analytics_metrics_large_dataset_aggregation(tmp_path: Path):
    """Test analytics KPI aggregation over 1,000 cases completes under 250 ms."""
    config = AppConfig(workspace_dir=tmp_path, username="bench_user")
    storage = StorageService(config)
    bulk_cases = generate_bulk_cases(1000)
    storage.save_cases(bulk_cases)

    start_time = time.perf_counter()
    open_cases = [c for c in bulk_cases if not c.workflow_status.is_completed]
    red_count = sum(1 for c in open_cases if c.classification.urgency_level == UrgencyLevel.RED)
    yellow_count = sum(1 for c in open_cases if c.classification.urgency_level == UrgencyLevel.YELLOW)
    green_count = sum(1 for c in open_cases if c.classification.urgency_level == UrgencyLevel.GREEN)

    practice_counts: dict[str, int] = {}
    for c in bulk_cases:
        p = c.customer.practice_name
        practice_counts[p] = practice_counts.get(p, 0) + 1

    duration = time.perf_counter() - start_time

    assert len(open_cases) > 0
    assert (red_count + yellow_count + green_count) == len(open_cases)
    assert duration < 0.25, f"Analytics calculation took too long: {duration:.3f}s"


def test_zip_backup_compression_speed(tmp_path: Path):
    """Test creating a ZIP backup archive of 500 cases completes within performance bounds."""
    config = AppConfig(workspace_dir=tmp_path, username="bench_user")
    storage = StorageService(config)
    storage.save_cases(generate_bulk_cases(500))

    output_zip = tmp_path / "bench_backup.zip"

    start_time = time.perf_counter()
    result = ZipBackupService.export_backup_zip(storage, output_zip)
    duration = time.perf_counter() - start_time

    assert output_zip.exists()
    assert result["file_count"] >= 1
    assert duration < 2.5, f"ZIP backup creation took too long: {duration:.3f}s"
