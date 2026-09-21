from pathlib import Path
from typing import cast
from unittest.mock import MagicMock, patch

import pytest

from config import AppConfig
from enums import Channel
from models.case import Case, CaseCustomer, Classification, TimelineEntry, WorkflowStatus
from models.customer import Customer
from services.storage_service import StorageService
from ui.app_dialogs import DialogLaunchersMixin


@pytest.fixture
def tmp_config(tmp_path: Path) -> AppConfig:
    return AppConfig(workspace_dir=tmp_path, username="test_user")


def _make_dummy_case(case_id: str, practice_name: str = "Alte Praxis", att_dir: str = "") -> Case:
    return Case(
        case_id=case_id,
        created_at="2026-09-01T10:00:00",
        updated_at="2026-09-01T10:00:00",
        created_by="Tester",
        assigned_to="Tester",
        customer=CaseCustomer(
            customer_id="K-001",
            practice_name=practice_name,
            contact_person="Dr. Alt",
        ),
        classification=Classification(schema_id="s1", title="Testfall"),
        workflow_status=WorkflowStatus(),
        attachment_directory=att_dir,
    )


def test_storage_delete_case_permanently_active_case(tmp_config: AppConfig):
    storage = StorageService(tmp_config)
    case1 = _make_dummy_case("CASE-001")
    case2 = _make_dummy_case("CASE-002")
    storage.save_cases([case1, case2], sync=True)

    assert len(storage.load_cases()) == 2

    # Delete CASE-001
    assert storage.delete_case_permanently("CASE-001") is True

    remaining = storage.load_cases()
    assert len(remaining) == 1
    assert remaining[0].case_id == "CASE-002"

    # Deleting it again should return False
    assert storage.delete_case_permanently("CASE-001") is False


def test_storage_delete_case_permanently_archive(tmp_config: AppConfig):
    storage = StorageService(tmp_config)
    case_archived = _make_dummy_case("CASE-ARCH-001")
    storage.save_archive([case_archived], sync=True)

    assert len(storage.load_archive()) == 1

    # Delete archived case
    assert storage.delete_case_permanently("CASE-ARCH-001") is True

    assert len(storage.load_archive()) == 0
    assert storage.delete_case_permanently("CASE-ARCH-001") is False


def test_storage_delete_case_permanently_nonexistent(tmp_config: AppConfig):
    storage = StorageService(tmp_config)
    storage.save_cases([], sync=True)
    storage.save_archive([], sync=True)

    assert storage.delete_case_permanently("DOES-NOT-EXIST") is False


class DummyApp(DialogLaunchersMixin):
    """Minimal dummy implementing DialogLaunchersMixin for testing on_delete_case and on_change_practice."""

    def __init__(self, tmp_path: Path):
        self.config = AppConfig(workspace_dir=tmp_path, username="Tester")
        self.storage_service = StorageService(self.config)
        self.profile = MagicMock()
        self.profile.user.name = "Tester"
        self.cases = []
        self.customers = [
            Customer(customer_id="K-002", practice_name="Neue Praxis Dr. Neu"),
        ]
        self.active_case = None
        self.refresh_views = MagicMock()
        self.on_case_updated = MagicMock()
        self.on_quick_customer_added = MagicMock()
        self._views = {}

    def is_view_built(self, view_name: str) -> bool:
        return False


def test_on_delete_case_cancelled_stage1(tmp_path: Path):
    app = DummyApp(tmp_path)
    case = _make_dummy_case("DEL-001")
    app.cases = [case]
    app.storage_service.save_cases([case], sync=True)

    with patch("ui.dialogs.confirm_dialog.ask_confirmation", return_value=False):
        app.on_delete_case(case)

    # Not deleted
    assert len(app.cases) == 1
    assert len(app.storage_service.load_cases()) == 1


def test_on_delete_case_confirmed_with_attachments(tmp_path: Path):
    app = DummyApp(tmp_path)
    att_dir = tmp_path / "attachments_case_001"
    att_dir.mkdir(parents=True, exist_ok=True)
    (att_dir / "doc.pdf").write_bytes(b"pdf content")

    case = _make_dummy_case("DEL-002", att_dir=str(att_dir))
    app.cases = [case]
    app.storage_service.save_cases([case], sync=True)

    # Confirm both stage 1 (case deletion) and stage 2 (attachment folder deletion)
    with patch("ui.dialogs.confirm_dialog.ask_confirmation", side_effect=[True, True]), \
         patch("ui.widgets.toast_notification.ToastNotification"):
        app.on_delete_case(case)

    # Case removed from memory and disk
    assert len(app.cases) == 0
    assert len(app.storage_service.load_cases()) == 0
    # Attachment directory removed from disk
    assert not att_dir.exists()
    cast(MagicMock, app.refresh_views).assert_called_once_with(force_all=True)


def test_on_delete_case_confirmed_keep_attachments(tmp_path: Path):
    app = DummyApp(tmp_path)
    att_dir = tmp_path / "attachments_case_002"
    att_dir.mkdir(parents=True, exist_ok=True)
    (att_dir / "doc.pdf").write_bytes(b"pdf content")

    case = _make_dummy_case("DEL-003", att_dir=str(att_dir))
    app.cases = [case]
    app.storage_service.save_cases([case], sync=True)

    # Confirm stage 1 (case deletion), decline stage 2 (keep attachments)
    with patch("ui.dialogs.confirm_dialog.ask_confirmation", side_effect=[True, False]), \
         patch("ui.widgets.toast_notification.ToastNotification"):
        app.on_delete_case(case)

    # Case removed, attachment dir remains intact
    assert len(app.cases) == 0
    assert len(app.storage_service.load_cases()) == 0
    assert att_dir.exists()
    assert (att_dir / "doc.pdf").exists()


def test_on_change_practice_workflow(tmp_path: Path):
    app = DummyApp(tmp_path)
    case = _make_dummy_case("PRACTICE-001", practice_name="Alte Praxis Dr. Alt")
    app.cases = [case]

    new_cust = CaseCustomer(
        customer_id="K-002",
        practice_name="Neue Praxis Dr. Neu",
        contact_person="Dr. Neu",
    )

    captured_callback = None

    def mock_dialog(parent, case, customers, on_practice_changed, on_customer_added):
        nonlocal captured_callback
        captured_callback = on_practice_changed

    with patch("ui.dialogs.change_practice_dialog.ChangePracticeDialog", side_effect=mock_dialog), \
         patch("ui.widgets.toast_notification.ToastNotification"):
        app.on_change_practice(case)
        assert captured_callback is not None

        # Simulate user confirming practice change with a timeline note
        captured_callback(new_cust, "Praxisübernahme zum Quartalsende.")

    # Verify customer updated
    assert case.customer.practice_name == "Neue Praxis Dr. Neu"
    assert case.customer.customer_id == "K-002"

    # Verify timeline entry added
    assert len(case.timeline) == 1
    t_entry = case.timeline[0]
    assert t_entry.author == "Tester"
    assert t_entry.channel == Channel.INTERNAL_NOTE.value
    assert "Alte Praxis Dr. Alt" in t_entry.note
    assert "Neue Praxis Dr. Neu" in t_entry.note
    assert "Praxisübernahme zum Quartalsende." in t_entry.note
    assert "PRAXIS: Alte Praxis Dr. Alt → Neue Praxis Dr. Neu" in t_entry.status_change

    cast(MagicMock, app.on_case_updated).assert_called_once_with(case)
