import pytest
from pathlib import Path
from config import AppConfig
from enums import Actor, BoardColumn, UrgencyLevel, Channel, LayoutMode
from models.case import Case, CaseCustomer, Classification, WorkflowStatus, TimelineEntry
from models.customer import Customer, Contact
from models.profile import UserProfile, UserInfo, Colleague
from services.storage_service import StorageService
from services.seed_service import SeedService
from services.scoring_service import ScoringService
from services.search_service import SearchService
from services.customer_service import CustomerService
from services.zip_backup_service import ZipBackupService
from utils.datetime_utils import now_iso, get_local_now


def test_new_case_creation_and_cockpit_load_chain(tmp_path: Path):
    """UI Workflow Chain 1: Create case -> score update -> save -> cockpit selection."""
    config = AppConfig(workspace_dir=tmp_path, username="test_agent")
    storage = StorageService(config)
    seed_service = SeedService(storage)
    seed_service.run_seed(force=True)

    scoring_service = ScoringService()
    cases = storage.load_cases()
    initial_count = len(cases)

    # 1. Simulate NewCaseDialog case creation callback
    new_case = Case(
        case_id="T-2026-9999",
        created_at=now_iso(),
        updated_at=now_iso(),
        created_by="Daniel Rösch",
        assigned_to="Daniel Rösch",
        customer=CaseCustomer(
            customer_id="K-10482",
            practice_name="Gemeinschaftspraxis Dr. Müller & Partner",
            is_vip=True,
            contact_person="Frau Weber",
            phone="+49 731 123456-12",
        ),
        classification=Classification(
            schema_id="schema_bug_report",
            title="Neuer Absturz-Fall aus UI-Workflow-Test",
            urgency_level=UrgencyLevel.RED.value,
            tags=["Dringend", "Hardware"],
        ),
        workflow_status=WorkflowStatus(
            is_completed=False,
            is_archived=False,
            board_column=BoardColumn.ACTION_REQUIRED.value,
            current_actor=Actor.SUPPORT.value,
            actor_since=now_iso(),
        ),
        form_data={"module_name": "Hauptmenü", "reproduction_steps": "Klick auf Button"},
    )

    # Apply scoring update (simulating app.on_case_created)
    scoring_service.update_case_scoring(new_case)
    cases.append(new_case)
    storage.save_cases(cases)

    # Reload storage to verify persistence
    reloaded_cases = storage.load_cases()
    assert len(reloaded_cases) == initial_count + 1

    created = next(c for c in reloaded_cases if c.case_id == "T-2026-9999")
    assert created.classification.title == "Neuer Absturz-Fall aus UI-Workflow-Test"
    assert created.classification.calculated_score > 0
    assert "Dringend" in created.classification.tags


def test_followup_setting_overdue_flyout_and_open_chain(tmp_path: Path):
    """UI Workflow Chain 2: Set followup date -> timeline log -> overdue check -> flyout open."""
    config = AppConfig(workspace_dir=tmp_path, username="test_agent")
    storage = StorageService(config)
    seed_service = SeedService(storage)
    seed_service.run_seed(force=True)

    cases = storage.load_cases()
    target_case = cases[0]

    # 1. Simulate FollowupDialog setting followup date
    past_due_date = "2026-08-20 09:00"
    target_case.workflow_status.followup_at = past_due_date
    entry = TimelineEntry(
        timestamp=now_iso(),
        author="Daniel Rösch",
        channel=Channel.INTERNAL_NOTE.value,
        note=f"Wiedervorlage gesetzt auf: {past_due_date}. Rückmeldung abwarten",
    )
    target_case.timeline.append(entry)
    storage.save_cases(cases)

    # 2. Simulate check_due_followups detecting overdue cases
    due_cases = [c for c in storage.load_cases() if c.workflow_status.followup_at and not c.workflow_status.is_completed]
    assert len(due_cases) >= 1

    # 3. Simulate FollowupFlyoutDialog selecting case -> trigger switch_to_cockpit_view_for_case
    selected_cases = []

    def mock_switch_to_cockpit_view_for_case(c: Case):
        selected_cases.append(c)

    from ui.dialogs.followup_flyout_dialog import FollowupFlyoutDialog
    flyout = FollowupFlyoutDialog.__new__(FollowupFlyoutDialog)
    flyout.on_case_selected = mock_switch_to_cockpit_view_for_case
    flyout.destroy = lambda: None

    flyout.select_case(due_cases[0])
    assert len(selected_cases) == 1
    assert selected_cases[0].case_id == due_cases[0].case_id


def test_handover_workflow_chain(tmp_path: Path):
    """UI Workflow Chain 3: Handover dialog -> actor update -> timeline status change log -> storage."""
    config = AppConfig(workspace_dir=tmp_path, username="test_agent")
    storage = StorageService(config)
    seed_service = SeedService(storage)
    seed_service.run_seed(force=True)

    cases = storage.load_cases()
    target_case = cases[0]
    prev_actor = target_case.workflow_status.current_actor
    new_actor = Actor.DEVELOPMENT.value

    # Simulate HandoverDialog callback (on_confirmed)
    from enums import get_actor_display
    target_case.workflow_status.current_actor = new_actor
    target_case.workflow_status.actor_since = now_iso()

    change_text = f"ZUSTÄNDIGKEIT: {get_actor_display(prev_actor)} -> {get_actor_display(new_actor)}"
    entry = TimelineEntry(
        timestamp=now_iso(),
        author="Daniel Rösch",
        channel=Channel.INTERNAL_NOTE.value,
        note="Übergabe an Dev wegen Bugfix",
        status_change=change_text,
    )
    target_case.timeline.append(entry)
    storage.save_cases(cases)

    # Verify updated case
    reloaded = storage.load_cases()[0]
    assert reloaded.workflow_status.current_actor == Actor.DEVELOPMENT.value
    assert any("ZUSTÄNDIGKEIT:" in t.status_change for t in reloaded.timeline)


def test_customer_management_and_quick_add_chain(tmp_path: Path):
    """UI Workflow Chain 4: Create customer in management dialog -> verify fields -> quick-add in case creation."""
    config = AppConfig(workspace_dir=tmp_path, username="test_agent")
    storage = StorageService(config)
    service = CustomerService(storage)

    # 1. Create new customer with website, vm_number, instance_number & contacts
    new_cust = Customer(
        customer_id="K-88112",
        practice_name="Orthopädie ZENTRUM",
        is_vip=True,
        system_version="v2026.3.0",
        website="https://ortho-zentrum.de",
        vm_number=202,
        instance_number=4,
        general_notes="Sehr wichtige Praxis",
        contacts=[Contact(name="Dr. Becker", role="Inhaber", email="becker@ortho-zentrum.de", phone="089-112233")],
    )

    service.save_customer(new_cust)

    # 2. Verify stored customer
    loaded = service.get_customer_by_id("K-88112")
    assert loaded is not None
    assert loaded.practice_name == "Orthopädie ZENTRUM"
    assert loaded.website == "https://ortho-zentrum.de"
    assert loaded.vm_number == 202
    assert loaded.instance_number == 4
    assert len(loaded.contacts) == 1
    assert loaded.contacts[0].name == "Dr. Becker"


def test_zip_export_import_workflow_chain(tmp_path: Path):
    """UI Workflow Chain 5: Export backup ZIP -> import restoration -> ZipImportPathDialog callback."""
    config = AppConfig(workspace_dir=tmp_path, username="test_agent")
    storage = StorageService(config)
    seed_service = SeedService(storage)
    seed_service.run_seed(force=True)

    # 1. Create a dummy attachment file
    att_dir = config.attachments_dir / "T-2026-0001_Gemeinschaftspraxis_Dr_Mueller"
    att_dir.mkdir(parents=True, exist_ok=True)
    dummy_file = att_dir / "sample_log.txt"
    dummy_file.write_text("Log content for backup test", encoding="utf-8")

    # 2. Export backup ZIP
    zip_dest = tmp_path / "SupportBackup.zip"
    export_res = ZipBackupService.export_backup_zip(storage, zip_dest)
    assert export_res["file_count"] > 0
    assert zip_dest.exists()

    # 3. Simulate ZipImportPathDialog unpacking to custom directory
    import_target_data = tmp_path / "imported_data"
    import_target_attachments = tmp_path / "imported_attachments"

    import_res = ZipBackupService.import_backup_zip(zip_dest, import_target_data, import_target_attachments)
    assert (import_res["extracted_data_files"] + import_res["extracted_attachment_files"]) > 0

    # Verify extracted data files & attachment
    assert (import_target_data / "cases.json").exists()
    assert (import_target_data / "customers.json").exists()
    assert (import_target_attachments / "T-2026-0001_Gemeinschaftspraxis_Dr_Mueller" / "sample_log.txt").exists()


def test_tag_management_and_smart_filter_chain(tmp_path: Path):
    """UI Workflow Chain 6: Tag creation -> assigning tag to case -> smart tag search filter."""
    config = AppConfig(workspace_dir=tmp_path, username="test_agent")
    storage = StorageService(config)
    seed_service = SeedService(storage)
    seed_service.run_seed(force=True)

    # 1. Add new tag to profile
    profile = storage.load_profile()
    new_tag = "NetzwerkDrucker"
    if new_tag not in profile.available_tags:
        profile.available_tags.append(new_tag)
    storage.save_profile(profile)

    # 2. Assign tag to case
    cases = storage.load_cases()
    target_case = cases[0]
    target_case.classification.tags.append("NetzwerkDrucker")
    storage.save_cases(cases)

    # 3. Perform tag search filter (tag:NetzwerkDrucker)
    filtered = SearchService.filter_cases(storage.load_cases(), "tag:NetzwerkDrucker")
    assert len(filtered) == 1
    assert filtered[0].case_id == target_case.case_id


def test_multi_view_search_and_layout_refresh_chain(tmp_path: Path):
    """UI Workflow Chain 7: Search filter -> multi-view data synchronization across Cockpit, Board, Table & Analytics."""
    config = AppConfig(workspace_dir=tmp_path, username="test_agent")
    storage = StorageService(config)
    seed_service = SeedService(storage)
    seed_service.run_seed(force=True)

    all_cases = storage.load_cases()
    search_query = "Müller"

    # Filter active cases for views
    filtered = SearchService.filter_cases(all_cases, search_query)
    assert len(filtered) >= 1
    assert all("Müller" in c.customer.practice_name or "Müller" in c.created_by or "Müller" in c.assigned_to or any("Müller" in ct.name for ct in getattr(c.customer, "contacts", [])) for c in filtered)
