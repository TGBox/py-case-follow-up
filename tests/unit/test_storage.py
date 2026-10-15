"""StorageService persistence, corruption recovery, debounced saving, duplicates, plus small service/UI leftovers."""

import json
import sqlite3
import threading
import time
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any

import pytest

import services.storage_service as storage_service
from config import AppConfig
from enums import Actor, BoardColumn, TargetType, UrgencyLevel
from models.case import Case, CaseCustomer, Classification, TimelineEntry, WorkflowStatus
from models.customer import Contact, Customer
from models.export_template import ExportTemplate
from models.profile import DEFAULT_COLUMN_WIDTHS, Colleague, UISettings, UserInfo, UserProfile
from services.storage_service import DebouncedSaver, StorageService, atomic_save_json, safe_read_json
from utils.datetime_utils import format_iso


def _case(case_id: str, title: str = "Fall", followup: str | None = None) -> Case:
    return Case(
        case_id=case_id,
        customer=CaseCustomer(customer_id="K-1", practice_name="Praxis"),
        classification=Classification(title=title),
        workflow_status=WorkflowStatus(board_column=BoardColumn.WAITING, followup_at=followup),
    )


# --- JSON primitives ---------------------------------------------------------


def test_atomic_save_and_safe_read_json(tmp_path: Path):
    target = tmp_path / "test.json"
    atomic_save_json(target, {"key": "value", "number": 42})
    assert json.loads(target.read_text(encoding="utf-8")) == {"key": "value", "number": 42}
    assert not list(tmp_path.glob("*.tmp.json"))

    missing = tmp_path / "nonexistent.json"
    assert safe_read_json(missing, default_factory=list) == []
    assert missing.exists()

    corrupted = tmp_path / "corrupted.json"
    corrupted.write_text("INVALID JSON {{{", encoding="utf-8")
    assert safe_read_json(corrupted, default_factory=dict) == {}
    assert corrupted.exists()
    assert len(list(tmp_path.glob("corrupted.corrupted_*.json"))) == 1


# --- Corruption recovery -----------------------------------------------------


@pytest.mark.parametrize(
    ("path_attr", "load"),
    [
        ("cases_path", lambda s: s.load_cases()),
        ("customers_path", lambda s: s.load_customers()),
        ("question_schemas_path", lambda s: s.load_schemas()),
        ("export_templates_path", lambda s: s.load_templates()),
        ("colleagues_path", lambda s: s.load_colleagues()),
    ],
)
def test_corrupted_workspace_file_loads_as_empty(storage, config, path_attr, load):
    path = getattr(config, path_attr)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("{ MALFORMED JSON ...", encoding="utf-8")
    assert load(storage) == []


def test_corrupted_profile_falls_back_to_default(storage, config):
    config.app_profile_path.parent.mkdir(parents=True, exist_ok=True)
    config.app_profile_path.write_text("{ INVALID JSON BROKEN ... ", encoding="utf-8")
    profile = storage.load_profile()
    assert isinstance(profile, UserProfile)
    assert profile.ui_settings.theme.lower() in ("system", "dark", "light")


def test_corrupted_snippets_fall_back_to_seeded_defaults(config, tmp_path: Path):
    from services.snippet_service import SnippetService

    snip_file = config.data_dir / "snippets.json"
    snip_file.parent.mkdir(parents=True, exist_ok=True)
    snip_file.write_text("[INVALID_ARRAY_ENTRY...", encoding="utf-8")
    assert len(SnippetService(workspace_dir=tmp_path).load_snippets()) > 0


def test_cases_with_wrong_field_types_are_coerced(storage, config):
    config.cases_path.parent.mkdir(parents=True, exist_ok=True)
    config.cases_path.write_text(json.dumps([{
        "case_id": "CASE-999",
        "customer": {"customer_id": "C-1", "practice_name": "Test Praxis"},
        "classification": {"schema_id": "general", "title": "Bad Types", "tags": "not_a_list"},
        "timeline": "not_a_list",
    }]), encoding="utf-8")
    cases = storage.load_cases()
    assert [c.case_id for c in cases] == ["CASE-999"]
    assert isinstance(cases[0].classification.tags, list)
    assert isinstance(cases[0].timeline, list)


# --- Round trips -------------------------------------------------------------


def test_cases_roundtrip(storage):
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
        attachment_directory="data/attachments/T-2026-0001_Praxis_A",
        timeline=[TimelineEntry(timestamp="2026-08-23T09:15:00", author="Daniel", note="Initial note")],
        is_demo_data=True,
    )
    case.workflow_status.followup_at = "2026-08-25T09:00:00"
    case.workflow_status.followup_note = "Beim Entwickler nachfragen"
    storage.save_cases([case, Case(case_id="USER-1", is_demo_data=False)])

    loaded, user = storage.load_cases()
    assert loaded.customer.practice_name == "Praxis A"
    assert loaded.customer.is_vip is True
    assert loaded.classification.urgency_level == UrgencyLevel.RED
    assert loaded.timeline[0].note == "Initial note"
    assert loaded.workflow_status.followup_at == "2026-08-25T09:00:00"
    assert loaded.workflow_status.followup_note == "Beim Entwickler nachfragen"
    assert (loaded.is_demo_data, user.is_demo_data) == (True, False)


def test_custom_cases_path_with_debounced_save(tmp_path: Path):
    custom_ws = tmp_path / "custom_data_dir"
    custom_cases = tmp_path / "external_cases.json"
    config = AppConfig(workspace_dir=custom_ws, custom_cases_path=custom_cases)
    config.ensure_directories()
    assert config.cases_path == custom_cases
    assert config.customers_path == custom_ws / "data" / "customers.json"

    storage = StorageService(config)
    storage.save_cases([Case(case_id="T-999")], sync=False)
    storage.flush_all_saves()
    assert custom_cases.exists()
    assert [c.case_id for c in storage.load_cases(use_cache=False)] == ["T-999"]


def test_templates_and_colleagues_roundtrip(storage):
    storage.save_templates([ExportTemplate(
        template_id="custom_test_tmpl",
        display_name="Custom Test",
        target_type=TargetType.FILE_EXPORT.value,
        required_schema_fields=["billing_quarter"],
        template_string="Hello {{ form_data.billing_quarter }}",
    )])
    tmpl = next(t for t in storage.load_templates() if t.template_id == "custom_test_tmpl")
    assert tmpl.display_name == "Custom Test"
    assert tmpl.required_schema_fields == ["billing_quarter"]

    colleague = Colleague(
        username="mbecker", name="Markus Becker", department="Entwicklung", extension="4022",
        email="m.becker@praxis.de", mobile="0171 99988877", notes="Spezialist für PVS-Imports",
    )
    assert colleague.validate() == []
    storage.save_colleagues([colleague])
    found = next(c for c in storage.load_colleagues() if c.username == "mbecker")
    assert (found.name, found.department, found.notes) == ("Markus Becker", "Entwicklung", "Spezialist für PVS-Imports")


def test_multiple_user_profiles(storage):
    storage.save_profile(UserProfile(user=UserInfo(name="Anna Schmidt", department="Support Team", email="anna@support.de")))
    storage.save_profile(UserProfile(user=UserInfo(name="Ben Becker", department="Entwicklung", email="ben@support.de")))
    profiles = storage.list_profiles()
    assert "Anna Schmidt" in profiles or "Ben Becker" in profiles
    ben = storage.load_profile_by_name("Ben Becker")
    assert (ben.user.name, ben.user.department, ben.user.email) == ("Ben Becker", "Entwicklung", "ben@support.de")


def test_column_widths_persist_in_user_config(tmp_path: Path, monkeypatch):
    monkeypatch.setattr("config.get_global_config_file", lambda: tmp_path / "user_config.json")
    config = AppConfig(workspace_dir=tmp_path)
    config.column_widths = {"cockpit_left": 350, "cockpit_center": 500, "cockpit_right": 300, "board_column": 320}
    config.save_user_config()
    loaded = AppConfig.load_user_config()
    assert loaded.column_widths["cockpit_left"] == 350
    assert loaded.column_widths["board_column"] == 320


def test_ui_settings_serialization():
    profile = UserProfile()
    profile.ui_settings.column_widths = {"table_col_id": 500, "board_column": 900}
    profile.ui_settings.reset_column_widths()
    assert profile.ui_settings.column_widths == DEFAULT_COLUMN_WIDTHS
    assert profile.ui_settings.column_widths["board_column"] == 280

    assert UISettings.from_dict(UISettings(show_demo_data=False).to_dict()).show_demo_data is False

    s = UISettings()
    s.board_collapsed["tech"] = True
    again = UISettings.from_dict(json.loads(json.dumps(s.to_dict())))
    assert again.board_collapsed["tech"] is True
    assert set(again.board_collapsed) == {"hotline", "tech", "dev", "customer", "followup", "completed"}


@pytest.mark.parametrize(
    ("stored", "expected_hotline"),
    [
        ({"support": True}, True),  # legacy key migrated
        ({"support": False, "hotline": True, "followup": True}, True),  # stale legacy key must not win
    ],
)
def test_board_collapsed_legacy_support_key(stored, expected_hotline):
    s = UISettings.from_dict({"board_collapsed": stored})
    assert s.board_collapsed["hotline"] is expected_hotline
    assert "support" not in s.board_collapsed


# --- Archive -----------------------------------------------------------------


def test_archive_single_case(storage):
    storage.save_cases([Case(case_id="T-001"), Case(case_id="T-002")])
    assert storage.archive_single_case("T-001") is True
    assert [c.case_id for c in storage.load_cases()] == ["T-002"]
    archived = storage.load_archive()
    assert [c.case_id for c in archived] == ["T-001"]
    assert archived[0].workflow_status.is_archived is True


def test_auto_archive_respects_threshold(storage):
    now = datetime.now()
    storage.save_cases([
        Case(case_id="T-OLD", updated_at=format_iso(now - timedelta(days=31)),
             workflow_status=WorkflowStatus(is_completed=True, is_archived=False)),
        Case(case_id="T-RECENT", updated_at=format_iso(now - timedelta(days=5)),
             workflow_status=WorkflowStatus(is_completed=True, is_archived=False)),
    ])
    assert storage.auto_archive_completed_cases(threshold_days=30) == 1
    assert [c.case_id for c in storage.load_cases()] == ["T-RECENT"]
    assert [c.case_id for c in storage.load_archive()] == ["T-OLD"]


# --- DebouncedSaver ----------------------------------------------------------


def test_flush_all_returns_and_writes_when_background_save_is_stuck(tmp_path, monkeypatch):
    """Regression: exit hang when a Tk finalizer blocked the save thread and flush_all waited forever."""
    target = tmp_path / "profile.json"
    release = threading.Event()
    entered = threading.Event()
    real_save = storage_service.atomic_save_json

    def save(path, data, temp_tag=""):
        if threading.current_thread() is not threading.main_thread():
            entered.set()
            release.wait(10)  # stands in for the blocked Tcl call
            return
        real_save(path, data, temp_tag=temp_tag)

    monkeypatch.setattr(storage_service, "atomic_save_json", save)
    saver = DebouncedSaver()
    saver.save_debounced(target, {"v": 1}, delay_seconds=0)
    assert entered.wait(2), "background save did not start"

    start = time.monotonic()
    saver.flush_all(timeout=0.3)
    elapsed = time.monotonic() - start
    release.set()

    assert elapsed < 2, f"flush_all blocked for {elapsed:.1f}s"
    assert json.loads(target.read_text(encoding="utf-8")) == {"v": 1}
    assert not list(tmp_path.glob("*.tmp.json"))


def test_flush_all_waits_for_a_normal_background_save(tmp_path):
    target = tmp_path / "cases.json"
    saver = DebouncedSaver()
    saver.save_debounced(target, [1, 2, 3], delay_seconds=0)
    saver.flush_all()
    assert json.loads(target.read_text(encoding="utf-8")) == [1, 2, 3]


# --- Duplicate case ids ------------------------------------------------------


def test_update_single_case_does_not_overwrite_other_case_with_same_id(storage):
    """Regression: two cases sharing a case_id got merged into one on update."""
    a, b = _case("T-2026-2627", "A"), _case("T-2026-2627", "B")
    storage.save_cases([a, b], sync=True)
    b.classification.title = "B geaendert"
    storage.update_single_case(b)
    cases = storage.load_cases()
    assert [c.classification.title for c in cases] == ["A", "B geaendert"]
    assert cases[0] is a and cases[1] is b


def test_load_cases_drops_exact_duplicates_only(storage, config):
    """Regression: duplicated cases on the board; only byte-identical entries are removed."""
    dup = _case("T-2026-2627", "Ergo", "2026-10-07T11:27:00").to_dict()
    other_same_id = _case("T-2026-2627", "Anderer Fall").to_dict()
    config.cases_path.parent.mkdir(parents=True, exist_ok=True)
    config.cases_path.write_text(json.dumps([dup, dict(dup), other_same_id]), encoding="utf-8")

    cases = storage.load_cases(use_cache=False)
    assert [c.classification.title for c in cases] == ["Ergo", "Anderer Fall"]
    assert len(json.loads(config.cases_path.read_text(encoding="utf-8"))) == 2


def _bare_new_case_dialog(existing: set[str], created: list[Case]) -> Any:
    from models.schema import QuestionSchema
    from ui.dialogs.new_case_dialog import NewCaseDialog

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


def test_new_case_is_created_only_once():
    """Regression: double Enter/click created the case twice; the app also ignores a re-delivered case."""
    from ui.app_dialogs import DialogLaunchersMixin

    created: list[Case] = []
    d = _bare_new_case_dialog(set(), created)
    d.on_save()
    d.on_save()
    assert len(created) == 1

    class Host(DialogLaunchersMixin):
        pass

    host: Any = Host.__new__(Host)
    existing = _case("T-2026-2627")
    host.cases = [existing]
    host.scoring_service = type("S", (), {"update_case_scoring": lambda self, c: None})()
    host.storage_service = type("St", (), {"save_cases": lambda self, c: None})()
    host.refresh_views = lambda: None
    host.cockpit_view = type("C", (), {"on_select_case_from_list": lambda self, c: None})()
    DialogLaunchersMixin.on_case_created(host, existing)
    DialogLaunchersMixin.on_case_created(host, _case("T-2026-2627"))
    assert host.cases == [existing]


# --- Board collapse persistence ---------------------------------------------


def test_board_collapse_is_reported_and_restored(root):
    from ui.views.board_view import BoardView

    noop = lambda c: None  # noqa: E731
    saved: list[dict] = []
    board = BoardView(root, noop, noop, noop, noop, noop, collapsed_states={}, on_collapsed_changed=saved.append)
    board.toggle_column_collapse("followup")
    assert saved and saved[-1]["followup"] is True

    board2 = BoardView(root, noop, noop, noop, noop, noop, collapsed_states=saved[-1])
    assert board2.collapsed_states["followup"] is True
    assert "followup" not in board2.col_scrolls  # built collapsed


def test_app_collapse_callback_writes_profile_and_saves():
    from ui.app import SupportCockpitApp

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


# --- Other services touched by the old grab-bag files ------------------------


def test_german_date_formatting_and_parsing():
    from utils.datetime_utils import format_german_date, format_german_datetime, parse_german_date

    iso_str = "2026-08-23T16:30:00"
    assert format_german_date(iso_str) == "23.08.2026"
    assert format_german_datetime(iso_str) == "23.08.2026 16:30 Uhr"
    assert format_german_datetime(iso_str, with_uhr=False) == "23.08.2026 16:30"
    assert format_german_datetime(iso_str, include_seconds=True) == "23.08.2026 16:30:00 Uhr"
    assert parse_german_date("23.08.2026 16:30") == "2026-08-23T16:30:00"
    assert parse_german_date("23.08.2026") == "2026-08-23T00:00:00"


@pytest.mark.parametrize(
    ("template_string", "expected"),
    [
        ("Fall-ID: {{ case.case_id }} | Praxis: {{ case.customer.practice_name }}",
         ["Fall-ID: T-EXP-99", "Praxis: Praxis Sonnenschein"]),
        ("[FALL {{ case.case_id }}] Praxis: {{ customer.practice_name }} | {{ case.classification.urgency_level }}",
         ["[FALL T-EXP-99]", "Praxis Sonnenschein", "RED"]),
    ],
)
def test_export_service_renders_template(storage, template_string, expected):
    from services.export_service import ExportService

    case = Case(
        case_id="T-EXP-99",
        customer=CaseCustomer(customer_id="K-99", practice_name="Praxis Sonnenschein"),
        classification=Classification(schema_id="standard", title="Fehler", urgency_level=UrgencyLevel.RED),
    )
    tmpl = ExportTemplate(template_id="tpl_test", display_name="Test", template_string=template_string)
    ok, _missing, rendered = ExportService(storage).render_template(case, tmpl)
    assert ok is True
    for part in expected:
        assert part in rendered


def test_cobra_import_reads_latin1_file(tmp_path: Path):
    from services.cobra_crm_import_service import CobraCrmImportService

    csv_file = tmp_path / "cobra_export_latin1.csv"
    csv_file.write_bytes("Kunden_Nr;Firma;Ansprechpartner;Telefon\nK-101;Praxis Dr. Müller & Co.;Bärbel Schütz;030-123456".encode("latin-1"))
    raw_rows, headers = CobraCrmImportService.parse_file(csv_file)
    customers = CobraCrmImportService.map_rows_to_customers(raw_rows, CobraCrmImportService.auto_detect_mapping(headers))
    assert [c.customer_id for c in customers] == ["K-101"]


def test_outlook_email_to_case_and_timeline():
    from services.outlook_integration_service import OutlookIntegrationService

    case = OutlookIntegrationService.parse_outlook_email_to_case(
        subject="Fehler beim Starten des PVS (K-12345)",
        sender_email="weber@praxis-weber.de",
        sender_name="Dr. Hans Weber",
        body="Sehr geehrtes Team,\nwir können das PVS nicht starten.\nViele Grüße,\nDr. Hans Weber",
    )
    assert case.customer.customer_id == "K-12345"
    assert case.customer.practice_name == "Dr. Hans Weber"
    assert "E-Mail empfangen von Dr. Hans Weber" in case.timeline[0].note

    entry = OutlookIntegrationService.append_outlook_email_to_case_timeline(
        case=case, sender_name="Dr. Hans Weber", sender_email="weber@praxis-weber.de",
        subject="Re: Fehler", body="Zusatzinfo: Fehlercode 404.",
    )
    assert len(case.timeline) == 2
    assert "Zusatzinfo: Fehlercode 404" in entry.note

    assert OutlookIntegrationService.transfer_to_outlook(
        to_email="support@medico.de", subject="Ticket #1234", body_text="Hallo Welt",
    ) in (True, False)


def test_deep_search_attachments_and_wiki_cache(tmp_path: Path):
    from services.deep_search_service import DeepSearchService

    deep_search = DeepSearchService(workspace_dir=tmp_path)
    att_dir = tmp_path / "data" / "attachments" / "T-SEARCH-01"
    att_dir.mkdir(parents=True)
    (att_dir / "system_error.log").write_text(
        "2026-08-25 10:15:00 [ERROR] Database connection timed out on port 5432\n2026-08-25 10:15:05 [INFO] Retry 1...",
        encoding="utf-8",
    )
    case = Case(case_id="T-SEARCH-01", attachment_directory=str(att_dir.relative_to(tmp_path)))
    matches = deep_search.search_case_attachments(case, "Database connection")
    assert [(m["file_name"], m["line_number"]) for m in matches] == [("system_error.log", 1)]
    assert "Database connection timed out" in matches[0]["snippet"]

    cache_file = tmp_path / "wiki_cache.json"
    cache_file.write_text(json.dumps([{
        "article_id": "art_1", "title": "PVS Konfiguration",
        "content": "Für den GKV-Export muss Zertifikat X509 installiert sein.", "tags": ["PVS", "Export"],
    }]), encoding="utf-8")
    wiki = deep_search.search_wiki_cache("Zertifikat X509", wiki_cache_file=cache_file)
    assert [w["title"] for w in wiki] == ["PVS Konfiguration"]


def test_wiki_sync_offline_search(seeded_storage, config):
    from services.wiki_sync_service import WikiSyncService

    wiki_svc = WikiSyncService(config)
    assert isinstance(wiki_svc.search("PVS"), list)

    conn = sqlite3.connect(wiki_svc.db_path)
    conn.execute(
        "INSERT INTO wiki_pages (page_id, book_id, title, slug, url, updated_at, content_markdown) "
        "VALUES (101, 1, 'Kartenleser Einrichtung', 'kartenleser', 'https://wiki.intern/kartenleser', "
        "'2026-08-25', 'CT-Kartenleser im Gerätemanager konfigurieren')"
    )
    if wiki_svc.is_fts5_available():
        conn.execute(
            "INSERT INTO wiki_fts (page_id, title, content) "
            "VALUES (101, 'Kartenleser Einrichtung', 'CT-Kartenleser im Gerätemanager konfigurieren')"
        )
    conn.commit()
    conn.close()
    assert any(item["title"] == "Kartenleser Einrichtung" for item in wiki_svc.search("Kartenleser"))


def test_new_case_and_quick_customer_dialogs(root, storage):
    from ui.dialogs.new_case_dialog import NewCaseDialog, QuickAddCustomerDialog

    created_cust: list[Customer] = []
    q_diag = QuickAddCustomerDialog(root, on_customer_created=created_cust.append)
    q_diag.update_idletasks()
    q_diag.name_entry.insert(0, "Praxis Schnell")
    q_diag.contact_entry.insert(0, "Herr Schnell")
    q_diag.on_save()
    assert created_cust[0].practice_name == "Praxis Schnell"

    created: list[Case] = []
    diag = NewCaseDialog(
        root,
        customers=[Customer(customer_id="K-555", practice_name="Praxis Dr. Quick",
                            contacts=[Contact(name="Frau Quick", email="quick@praxis.de")])],
        schemas=storage.load_schemas(),
        created_by="DaniBani",
        on_case_created=created.append,
    )
    diag.update_idletasks()
    diag.customer_combo.set("Praxis Dr. Quick (K-555)")
    diag.title_entry.insert(0, "Rezeptdrucker reagiert nicht")
    diag.note_textbox.insert("1.0", "Druckauftrag bleibt in Warteschlange hängen.")
    diag.on_save()
    assert created[0].classification.title == "Rezeptdrucker reagiert nicht"
    assert created[0].created_by == "DaniBani"
    diag.destroy()


def test_template_manager_and_edit_dialog(root, storage):
    from services.export_service import ExportService
    from ui.dialogs.template_manager_dialog import EditTemplateDialog, TemplateManagerDialog

    export_svc = ExportService(storage)
    schemas = storage.load_schemas()
    saved: list[ExportTemplate] = []
    edit_diag = EditTemplateDialog(root, template=None, schemas=schemas, export_service=export_svc, on_save=saved.append)
    edit_diag.update_idletasks()
    edit_diag.id_entry.insert(0, "tpl_custom")
    edit_diag.name_entry.insert(0, "Custom Ticket")
    edit_diag.template_textbox.insert("1.0", "Fall {{ case.case_id }} - {{ customer.practice_name }}")
    edit_diag.save()
    assert saved[0].template_id == "tpl_custom"

    dialog = TemplateManagerDialog(
        root,
        templates=[ExportTemplate(template_id="tpl_dev", display_name="Dev Ticket", template_string="Fall {{ case.case_id }}")],
        schemas=schemas,
        storage_service=storage,
        export_service=export_svc,
    )
    dialog.update_idletasks()
    assert [t.template_id for t in dialog.templates] == ["tpl_dev"]
    dialog.destroy()


def test_wiki_widget_offline_search(root, config):
    from services.wiki_sync_service import WikiSyncService
    from ui.widgets.wiki_widget import WikiWidget

    widget = WikiWidget(root, wiki_service=WikiSyncService(config))
    widget.pack(fill="both", expand=True)
    widget.update_idletasks()
    widget.search_entry.insert(0, "Setup")
    widget.on_search()
    widget.update_idletasks()
    widget.destroy()
