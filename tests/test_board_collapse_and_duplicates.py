"""Kanban: collapsed columns persist in the profile; cases never appear twice."""

import json
from pathlib import Path
from typing import Any

import customtkinter as ctk
import pytest

from config import AppConfig
from enums import BoardColumn
from models.case import Case, CaseCustomer, Classification, WorkflowStatus
from models.profile import UISettings
from services.storage_service import StorageService


def _case(case_id: str, title: str = "Fall", followup: str | None = None) -> Case:
    return Case(
        case_id=case_id,
        customer=CaseCustomer(customer_id="K-1", practice_name="Praxis"),
        classification=Classification(title=title),
        workflow_status=WorkflowStatus(board_column=BoardColumn.WAITING, followup_at=followup),
    )


# --- Collapsed columns ---


def test_profile_keeps_collapsed_hotline_over_stale_support_key():
    s = UISettings.from_dict({"board_collapsed": {"support": False, "hotline": True, "followup": True}})
    assert s.board_collapsed["hotline"] is True
    assert s.board_collapsed["followup"] is True
    assert "support" not in s.board_collapsed


def test_profile_migrates_legacy_support_key():
    s = UISettings.from_dict({"board_collapsed": {"support": True}})
    assert s.board_collapsed["hotline"] is True
    assert "support" not in s.board_collapsed


def test_profile_roundtrip_of_board_collapsed():
    s = UISettings()
    s.board_collapsed["tech"] = True
    again = UISettings.from_dict(json.loads(json.dumps(s.to_dict())))
    assert again.board_collapsed["tech"] is True
    assert set(again.board_collapsed) == {"hotline", "tech", "dev", "customer", "followup", "completed"}


@pytest.fixture
def root():
    app = ctk.CTk()
    app.withdraw()
    yield app
    try:
        app.destroy()
    except Exception:
        pass


def _board(root: Any, **kwargs) -> Any:
    from ui.views.board_view import BoardView

    noop = lambda c: None  # noqa: E731
    return BoardView(root, noop, noop, noop, noop, noop, **kwargs)


def test_board_reports_toggle_and_restores_it(root):
    saved: list[dict] = []
    board = _board(root, collapsed_states={}, on_collapsed_changed=saved.append)
    board.toggle_column_collapse("followup")
    assert saved and saved[-1]["followup"] is True

    # A new board (restart / rebuilt view) starts from what was saved.
    board2 = _board(root, collapsed_states=saved[-1])
    assert board2.collapsed_states["followup"] is True
    assert "followup" not in board2.col_scrolls  # built collapsed


def test_app_callback_writes_into_profile_and_saves():
    from ui.app import SupportCockpitApp
    from models.profile import UserProfile

    calls: list[Any] = []

    class FakeStorage:
        def save_profile(self, profile):
            calls.append(profile)

    host: Any = SupportCockpitApp.__new__(SupportCockpitApp)
    host.__dict__["profile"] = UserProfile()
    host.__dict__["storage_service"] = FakeStorage()
    SupportCockpitApp._on_board_collapsed_changed(host, {"hotline": True, "dev": False})
    assert host.profile.ui_settings.board_collapsed == {"hotline": True, "dev": False}
    assert calls == [host.profile]


# --- Duplicates ---


def test_update_single_case_does_not_overwrite_other_case_with_same_id(tmp_path: Path):
    storage = StorageService(AppConfig(workspace_dir=tmp_path, username="test_agent"))
    a, b = _case("T-2026-2627", "A"), _case("T-2026-2627", "B")
    storage.save_cases([a, b], sync=True)
    b.classification.title = "B geaendert"
    storage.update_single_case(b)
    cases = storage.load_cases()
    assert [c.classification.title for c in cases] == ["A", "B geaendert"]
    assert cases[0] is a and cases[1] is b


def test_load_cases_drops_exact_duplicates_only(tmp_path: Path):
    config = AppConfig(workspace_dir=tmp_path, username="test_agent")
    storage = StorageService(config)
    dup = _case("T-2026-2627", "Ergo", "2026-10-07T11:27:00").to_dict()
    other_same_id = _case("T-2026-2627", "Anderer Fall").to_dict()
    config.cases_path.parent.mkdir(parents=True, exist_ok=True)
    config.cases_path.write_text(json.dumps([dup, dict(dup), other_same_id]), encoding="utf-8")

    cases = storage.load_cases(use_cache=False)
    assert [c.classification.title for c in cases] == ["Ergo", "Anderer Fall"]
    # The cleaned list is written back.
    on_disk = json.loads(config.cases_path.read_text(encoding="utf-8"))
    assert len(on_disk) == 2


def _bare_new_case_dialog(existing: set[str], created: list[Case]) -> Any:
    from ui.dialogs.new_case_dialog import NewCaseDialog
    from models.customer import Customer
    from models.schema import QuestionSchema

    class W:
        def __init__(self, val: Any = ""):
            self.val = val

        def get(self, *a):
            return self.val

        def get_iso(self):
            return ""

        def configure(self, **kw):
            self.val = kw.get("text", self.val)

        def cget(self, attr):
            return [self.val]

    d: Any = NewCaseDialog.__new__(NewCaseDialog)
    d.customers = [Customer(customer_id="K-1", practice_name="Praxis")]
    d.schemas = [QuestionSchema(schema_id="default", display_name="Default")]
    d.created_by = "Tester"
    d.on_case_created = created.append
    d.existing_case_ids = lambda: existing
    d.destroy = lambda: None
    d.mark_clean = lambda: None
    d.title_entry = W("Neuer Fall")
    d.created_at_picker = W("")
    d.error_label = W()
    d.is_internal_var = W(False)
    d.customer_combo = W("Praxis (K-1)")
    d.schema_combo = W("Default")
    d.selected_tags_vars = {}
    d.note_textbox = W("")
    d.deadline_picker = W("")
    return d


def test_generate_case_id_avoids_taken_ids(monkeypatch):
    import ui.dialogs.new_case_dialog as mod

    class FixedDT(mod.datetime):  # type: ignore[misc, valid-type]
        @classmethod
        def now(cls, tz=None):
            return mod.datetime(2026, 10, 7, 11, 26, 27)

    monkeypatch.setattr(mod, "datetime", FixedDT)
    d = _bare_new_case_dialog({"T-2026-2627", "T-2026-2627-2"}, [])
    assert d.generate_case_id(2026) == "T-2026-2627-3"
    d.existing_case_ids = lambda: set()
    assert d.generate_case_id(2026) == "T-2026-2627"


def test_new_case_dialog_creates_the_case_only_once():
    created: list[Case] = []
    d = _bare_new_case_dialog(set(), created)
    d.on_save()
    d.on_save()  # second Enter / click before the dialog is gone
    assert len(created) == 1


def test_on_case_created_ignores_a_case_already_in_the_list():
    from ui.app_dialogs import DialogLaunchersMixin

    refreshed: list[bool] = []

    class Host(DialogLaunchersMixin):
        pass

    host: Any = Host.__new__(Host)
    existing = _case("T-2026-2627")
    host.cases = [existing]
    host.scoring_service = type("S", (), {"update_case_scoring": lambda self, c: None})()
    host.storage_service = type("St", (), {"save_cases": lambda self, c: None})()
    host.refresh_views = lambda: refreshed.append(True)
    host.cockpit_view = type("C", (), {"on_select_case_from_list": lambda self, c: None})()
    DialogLaunchersMixin.on_case_created(host, existing)
    DialogLaunchersMixin.on_case_created(host, _case("T-2026-2627"))
    assert host.cases == [existing]
