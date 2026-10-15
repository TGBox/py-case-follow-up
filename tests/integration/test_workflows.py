"""Integration chains: real services wired together on a real workspace on disk, checked through a fresh StorageService."""
import time
import zipfile
from datetime import timedelta
from pathlib import Path
from types import SimpleNamespace
from typing import Any

import pytest

from config import AppConfig
from enums import Actor, Channel, FieldType, LayoutMode, UrgencyLevel, get_layout_display
from models.case import Case, CaseCustomer, Classification, TimelineEntry, WorkflowStatus
from models.customer import Contact, Customer
from models.profile import Colleague
from models.snippet import Snippet
from services.attachment_service import AttachmentService
from services.cobra_crm_import_service import CobraCrmImportService as Cobra
from services.customer_service import CustomerService
from services.deep_search_service import DeepSearchService
from services.export_service import ExportService
from services.p2p_sync_service import P2PSyncService
from services.scoring_service import ScoringService
from services.search_service import SearchService
from services.seed_service import SeedService
from services.snippet_service import SnippetService
from services.storage_service import StorageService
from services.tray_service import TrayService
from services.zip_backup_service import ZipBackupService
from utils.datetime_utils import get_local_now, now_iso, parse_german_date


# --- helpers -----------------------------------------------------------------

class KnownBug(AssertionError):
    """Raised only by the bug check of an xfail test, so unrelated errors still fail."""


def _reopen(storage: StorageService, **config_kw) -> StorageService:
    """Flushes pending writes and opens the workspace again, as after an app restart."""
    storage.flush_all_saves()
    return StorageService(AppConfig(workspace_dir=storage.config.workspace_dir, username="test_agent", **config_kw))


def _seeded(workspace: Path) -> StorageService:
    storage = StorageService(AppConfig(workspace_dir=workspace, username="test_agent"))
    SeedService(storage).run_seed(force=True)
    return storage


def _iso(dt) -> str:
    return dt.strftime("%Y-%m-%dT%H:%M:%S")


class _Field:
    """Stands in for an entry/combo/picker/textbox: whatever the user typed or picked."""

    def __init__(self, val: Any = "", values: list[str] | None = None):
        self.val = val
        self.values = values or [val]

    def get(self, *args):
        return self.val

    def get_iso(self):
        return parse_german_date(self.val) if self.val else ""

    def set(self, val):
        self.val = val

    def configure(self, **kwargs):
        if "text" in kwargs:
            self.val = kwargs["text"]
        self.fg_color = kwargs.get("fg_color", getattr(self, "fg_color", ""))

    def cget(self, attr):
        return self.values


class _View:
    """A layout view that records what the app pushes into it."""

    def __init__(self):
        self.cases: list[Case] = []
        self.deep_results: dict = {}
        self.current_case: Case | None = None
        self.selected: list[str] = []
        self.left_frame = SimpleNamespace(is_deep_search_active=False)

    def set_cases(self, cases, **kwargs):
        self.cases = list(cases)
        self.deep_results = kwargs.get("deep_results", {})

    def set_schemas(self, schemas):
        pass

    def pack(self, **kwargs):
        pass

    def pack_forget(self):
        pass

    def on_select_case_from_list(self, case):
        self.current_case = case
        self.selected.append(case.case_id)


def _headless_app(storage: StorageService):
    """SupportCockpitApp without a window: real services and handlers, recording views."""
    from ui.app import SupportCockpitApp

    app: Any = SupportCockpitApp.__new__(SupportCockpitApp)
    app.storage_service = storage
    app.profile = storage.load_profile()
    app.scoring_service = ScoringService(app.profile.scoring_matrix)
    app.customer_service = CustomerService(storage)
    app.deep_search_service = DeepSearchService(storage.config.workspace_dir)
    app.tray_service = TrayService()
    app.search_query = ""
    app.active_case = None
    app.bell_btn = _Field()
    app._last_notified_due_count = None  # Tk's __getattr__ recurses on unset attributes without a window
    app.after = lambda delay, func: "timer"
    app.after_cancel = lambda timer_id: None
    app.cockpit_view, app.board_view, app.table_view, app.analytics_view = _View(), _View(), _View(), _View()
    app.active_view = app.board_view
    app._active_layout = LayoutMode.BOARD.value
    app.layout_combo = _Field(get_layout_display(LayoutMode.BOARD.value))
    app.load_all_data()
    return app


def _new_case_dialog(customers, schemas, on_case_created, existing_ids=lambda: set()):
    from ui.dialogs.new_case_dialog import NewCaseDialog

    dialog: Any = NewCaseDialog.__new__(NewCaseDialog)
    dialog.customers = customers
    dialog.schemas = schemas
    dialog.created_by = "Daniel Rösch"
    dialog.on_case_created = on_case_created
    dialog.existing_case_ids = existing_ids
    dialog.destroy = lambda: None
    dialog.error_label = _Field()
    dialog.is_internal_var = _Field(False)
    dialog.deadline_picker = _Field("")
    dialog.note_textbox = _Field("Kunde meldet Kartenleser-Ausfall")
    displays = [f"{s.display_name} [{s.schema_id}]" for s in schemas]
    dialog.schema_combo = _Field(displays[0], values=displays)
    dialog.selected_tags_vars = {}
    return dialog


def _fill_new_case(dialog, title: str, customer: str, created_at: str, schema_display: str, tags=()):
    dialog._case_submitted = False
    dialog.title_entry = _Field(title)
    dialog.customer_combo = _Field(customer)
    dialog.created_at_picker = _Field(created_at)
    dialog.schema_combo.set(schema_display)
    dialog.selected_tags_vars = {t: _Field(True) for t in tags}
    dialog.on_save()


def _cobra_customers(tmp_path: Path, csv_text: str) -> list[Customer]:
    csv_file = tmp_path / "cobra_export.csv"
    csv_file.write_text(csv_text, encoding="utf-8")
    rows, headers = Cobra.parse_file(csv_file)
    return Cobra.map_rows_to_customers(rows, Cobra.auto_detect_mapping(headers))


# --- customer master data -> case -> search -----------------------------------

def test_cobra_import_feeds_new_case_board_redirect_and_search(seeded_storage, tmp_path: Path):
    """Cobra CSV -> merged customer master data -> NewCaseDialog -> app persists, scores, selects -> search finds it."""
    imported = _cobra_customers(tmp_path, (
        "Kunden-Nr;Firma;Ansprechpartner;Telefon;E-Mail;VIP\n"
        "K-10482;Gemeinschaftspraxis Dr. Müller & Partner;Frau Weber;0731-999;weber@mueller.de;Ja\n"
        "K-9100;Orthopädie Zentrum Süd;Dr. Bernd Becker;089-112233;becker@ortho-sued.de;Ja\n"
    ))
    existing = seeded_storage.load_customers()
    diff = Cobra.compare_with_existing(imported, existing)
    assert [c.customer_id for c in diff["new"]] == ["K-9100"]
    assert [d["existing"].customer_id for d in diff["duplicates"]] == ["K-10482"]
    seeded_storage.save_customers(Cobra.merge_customers(existing, imported, mode="update"))

    storage = _reopen(seeded_storage)
    customer_service = CustomerService(storage)
    assert len(customer_service.get_all_customers()) == 6
    assert customer_service.get_customer_by_id("K-10482").phone_main == "0731-999"
    ortho = customer_service.get_customer_by_id("K-9100")
    assert (ortho.is_vip, ortho.contact_person) == (True, "Dr. Bernd Becker")

    app = _headless_app(storage)
    profile = storage.load_profile()
    profile.available_tags.append("Kartenleser")
    storage.save_profile(profile)
    # Quick-add from inside the dialog goes through the same customer master data.
    app.on_quick_customer_added(Customer(customer_id="K-9200", practice_name="Praxis Schnellanlage",
                                         contacts=[Contact(name="Fr. Quick")]))
    assert app.customer_service.get_customer_by_id("K-9200").contact_person == "Fr. Quick"

    bug_schema = next(s for s in app.schemas if s.schema_id == "schema_bug_report")
    dialog = _new_case_dialog(app.customers, app.schemas, app.on_case_created, app._all_known_case_ids)
    bug_display = f"{bug_schema.display_name} [{bug_schema.schema_id}]"

    future = (get_local_now() + timedelta(days=30)).strftime("%d.%m.%Y %H:%M")
    _fill_new_case(dialog, "Kartenleser defekt", "Orthopädie Zentrum Süd (K-9100)", future, bug_display)
    assert "Zukunft" in dialog.error_label.val
    assert len(app.cases) == 12

    _fill_new_case(dialog, "Kartenleser defekt", "Orthopädie Zentrum Süd (K-9100)", "20.08.2026 10:00",
                   bug_display, tags=["Kartenleser"])
    new_case = app.cases[-1]
    assert new_case.created_at.startswith("2026-08-20T10:00")
    assert new_case.workflow_status.actor_since == new_case.timeline[0].timestamp == new_case.created_at
    assert app.cockpit_view.selected == [new_case.case_id]
    # A double submit must not add the case twice.
    app.on_case_created(new_case)
    assert [c.case_id for c in app.cases].count(new_case.case_id) == 1

    # Clicking the case on the board redirects to the cockpit exactly once and remembers the layout.
    app.on_case_selected(new_case)
    app.on_case_selected(new_case)
    assert app.cockpit_view.selected == [new_case.case_id, new_case.case_id]
    assert app.active_view is app.cockpit_view
    assert app.layout_combo.get() == get_layout_display(LayoutMode.COCKPIT.value)

    reopened = _reopen(storage)
    assert reopened.load_profile().ui_settings.default_layout == LayoutMode.COCKPIT.value
    stored = next(c for c in reopened.load_cases() if c.case_id == new_case.case_id)
    assert (stored.customer.customer_id, stored.customer.practice_name, stored.customer.is_vip,
            stored.customer.contact_person, stored.customer.phone) == (
        "K-9100", "Orthopädie Zentrum Süd", True, "Dr. Bernd Becker", "089-112233")
    assert stored.classification.schema_id == "schema_bug_report"
    assert stored.classification.calculated_score > 0
    assert stored.attachment_directory.endswith(f"{stored.case_id}_Orthopädie_Zentrum_Süd")
    for query in ("K-9100", "Orthopädie", "tag:Kartenleser", "089-112233"):
        assert [c.case_id for c in SearchService.filter_cases(reopened.load_cases(), query)] == [stored.case_id], query


@pytest.mark.xfail(strict=True, raises=KnownBug, reason="NewCaseDialog.on_save matches the chosen customer with "
                   "'customer_id in selected_str', so id '100' wins for 'Praxis Zwei (1001)'")
def test_new_case_links_the_selected_cobra_customer_even_when_ids_share_a_prefix(seeded_storage, tmp_path: Path):
    imported = _cobra_customers(tmp_path, (
        "Kunden-Nr;Firma;Ansprechpartner\n"
        "100;Praxis Eins;Dr. Anna Alt\n"
        "1001;Praxis Zwei;Dr. Bernd Berg\n"
    ))
    seeded_storage.save_customers(Cobra.merge_customers(seeded_storage.load_customers(), imported))
    storage = _reopen(seeded_storage)
    created: list[Case] = []
    dialog = _new_case_dialog(storage.load_customers(), storage.load_schemas(), created.append)
    _fill_new_case(dialog, "Rückfrage", "Praxis Zwei (1001)", "20.08.2026 10:00", dialog.schema_combo.get())
    assert len(created) == 1
    if created[0].customer.customer_id != "1001":
        raise KnownBug(f"case linked to customer {created[0].customer.customer_id!r} instead of '1001'")


# --- attachments -> deep search -> delete ------------------------------------

def test_attachments_found_by_deep_search_after_restart_and_kept_after_delete(seeded_storage, tmp_path: Path):
    """Files attached to a case are found by the cockpit deep search; deleting the case keeps the folder."""
    case = next(c for c in seeded_storage.load_cases() if c.case_id == "T-2026-0005")
    attachments = AttachmentService(seeded_storage.config)
    log = tmp_path / "fehler.log"
    log.write_text("09:14 OK\n09:15 ERR_KARTENLESER_4711 Lesegerät antwortet nicht\n", encoding="utf-8")
    shot = tmp_path / "screen.png"
    shot.write_bytes(b"\x89PNG ERR_KARTENLESER_4711")  # binary: never searched
    first = attachments.copy_attachment(case, log)
    second = attachments.copy_attachment(case, log)  # same name again -> kept side by side
    attachments.copy_attachment(case, shot)
    assert first != second and first.parent == second.parent
    seeded_storage.update_single_case(case)

    storage = _reopen(seeded_storage)
    app = _headless_app(storage)
    app.switch_layout(LayoutMode.COCKPIT.value)
    app.cockpit_view.left_frame.is_deep_search_active = True
    app.search_query = "ERR_KARTENLESER_4711"
    assert SearchService.filter_cases(app.cases, app.search_query) == []

    app.refresh_views()
    assert [c.case_id for c in app.cockpit_view.cases] == ["T-2026-0005"]
    matches = app.cockpit_view.deep_results["T-2026-0005"]["attachment_matches"]
    assert {m["file_name"] for m in matches} == {first.name, second.name}
    assert all(m["line_number"] == 2 and "ERR_KARTENLESER_4711" in m["snippet"] for m in matches)

    att_dir = first.parent
    assert storage.delete_case_permanently("T-2026-0005") is True
    reopened = _reopen(storage)
    assert "T-2026-0005" not in {c.case_id for c in reopened.load_cases() + reopened.load_archive()}
    assert sorted(p.name for p in att_dir.iterdir()) == sorted([first.name, second.name, "screen.png"])
    assert DeepSearchService(reopened.config.workspace_dir).perform_deep_search(
        reopened.load_cases(), "ERR_KARTENLESER_4711") == {}


# --- ZIP backup -> restore into another workspace -----------------------------

def test_zip_backup_restores_complete_workspace_elsewhere(seeded_storage, tmp_path: Path):
    """Seeded + edited workspace -> ZIP -> empty workspace: every store, snippet and attachment comes back."""
    source = seeded_storage
    profile = source.load_profile()
    profile.ui_settings.column_widths["cockpit_left"] = 380
    profile.available_tags.append("Backup-Tag")
    source.save_profile(profile)
    assert source.archive_single_case("T-2026-0007") is True
    snippets = SnippetService(source.config.workspace_dir)
    snippets.add_or_update_snippet(Snippet(title="Rückruf Kartenleser", content="Bitte Lesegerät neu starten",
                                           category="Hardware", tags=["kartenleser"]))
    case = next(c for c in source.load_cases() if c.case_id == "T-2026-0001")
    att_dir = AttachmentService(source.config).get_case_attachment_dir(case)
    (att_dir / "zuzahlung.csv").write_text("Patient;Betrag\nMuster;10,00 BACKUP_MARKER\n", encoding="utf-8")

    zip_path = tmp_path / "SupportBackup.zip"
    exported = ZipBackupService.export_backup_zip(source, zip_path)
    assert ZipBackupService.inspect_backup_zip(zip_path)["total_files"] == exported["file_count"]

    target_ws = tmp_path / "restored"
    target_cfg = AppConfig(workspace_dir=target_ws, username="test_agent")
    result = ZipBackupService.import_backup_zip(zip_path, target_cfg.data_dir, target_cfg.attachments_dir)
    assert result["extracted_data_files"] > 0 and result["extracted_attachment_files"] > 0

    # Opened explicitly via --workspace: the restored profile must not pull the app back to the source.
    restored = StorageService(AppConfig(workspace_dir=target_ws, username="test_agent", workspace_from_cli=True))
    restored.apply_profile_paths(restored.load_profile())
    assert restored.config.workspace_dir == target_ws

    original = _reopen(source)
    for loader in ("load_cases", "load_archive", "load_customers", "load_templates", "load_schemas", "load_colleagues"):
        expected = [x.to_dict() for x in getattr(original, loader)()]
        assert [x.to_dict() for x in getattr(restored, loader)()] == expected, loader
    assert [c.case_id for c in restored.load_archive()] == ["T-2026-0007"]
    restored_profile = restored.load_profile()
    assert restored_profile.ui_settings.column_widths["cockpit_left"] == 380
    assert "Backup-Tag" in restored_profile.available_tags
    assert restored_profile.user.name == "Daniel Rösch"
    restored_snippets = SnippetService(target_ws)
    assert len(restored_snippets.get_all_snippets()) == len(snippets.get_all_snippets())
    assert [s.title for s in restored_snippets.search_snippets("kartenleser")] == ["Rückruf Kartenleser"]

    restored_case = next(c for c in restored.load_cases() if c.case_id == "T-2026-0001")
    hits = DeepSearchService(target_ws).perform_deep_search([restored_case], "BACKUP_MARKER")
    assert hits["T-2026-0001"]["attachment_matches"][0]["file_name"] == "zuzahlung.csv"


@pytest.mark.xfail(strict=True, raises=KnownBug, reason="export_backup_zip walks data_dir and attachments_dir, but attachments_dir "
                   "is data/attachments, so every attachment is written into the ZIP twice")
def test_zip_backup_stores_each_attachment_once(seeded_storage, tmp_path: Path):
    att_dir = seeded_storage.config.attachments_dir / "T-2026-0001_Gemeinschaftspraxis_Dr_Mueller"
    att_dir.mkdir(parents=True, exist_ok=True)
    (att_dir / "sample_log.txt").write_text("Log content", encoding="utf-8")
    zip_path = tmp_path / "SupportBackup.zip"
    ZipBackupService.export_backup_zip(seeded_storage, zip_path)
    with zipfile.ZipFile(zip_path) as zf:
        copies = [n for n in zf.namelist() if n.replace("\\", "/").endswith("/sample_log.txt")]
    assert copies, "attachment missing from the backup"
    if len(copies) != 1:
        raise KnownBug(f"attachment stored {len(copies)}x in the ZIP: {copies}")


# --- two colleagues -> P2P sync -> local rescoring ----------------------------

def test_p2p_import_from_colleague_workspace_is_rescored_with_local_matrix(tmp_path: Path):
    """Colleague edits and adds cases in her workspace -> diff/import -> restart rescoring uses the local matrix."""
    mine = _seeded(tmp_path / "daniel")
    theirs = _seeded(tmp_path / "max")

    remote_cases = theirs.load_cases()
    edited = next(c for c in remote_cases if c.case_id == "T-2026-0003")
    edited.updated_at = now_iso()
    edited.classification.deadline_callback = "2026-08-01T10:00:00"
    edited.workflow_status.current_actor = Actor.DEVELOPMENT.value
    edited.timeline.append(TimelineEntry(timestamp=now_iso(), author="Max Müller", note="An Dev übergeben",
                                         channel=Channel.INTERNAL_NOTE.value))
    added = Case(case_id="T-2026-0100", created_at=now_iso(), updated_at=now_iso(), created_by="Max Müller",
                 customer=CaseCustomer(customer_id="K-10211", practice_name="Zahnarztpraxis Dr. Schmidt"),
                 classification=Classification(schema_id="schema_bug_report", title="Neuer Fall von Max"))
    remote_cases.append(added)
    colleague_scoring = ScoringService(theirs.load_profile().scoring_matrix)
    for c in remote_cases:
        colleague_scoring.update_case_scoring(c)
    theirs.save_cases(remote_cases)
    theirs.flush_all_saves()
    assert edited.classification.urgency_level == UrgencyLevel.RED

    mine.save_colleagues([Colleague(username="max", name="Max Müller", department="Support",
                                    cases_path=str(theirs.config.cases_path))])
    profile = mine.load_profile()
    profile.scoring_matrix.threshold_yellow = 1
    profile.scoring_matrix.threshold_red = 200_000
    mine.save_profile(profile)

    mine = _reopen(mine)
    p2p = P2PSyncService(mine)
    ok, _msg, remote = p2p.read_colleague_cases(mine.load_colleagues()[0])
    assert ok is True
    statuses = {d.case_id: d.status for d in p2p.compute_diff(remote)}
    assert statuses.pop("T-2026-0003") == "REMOTE_NEWER"
    assert statuses.pop("T-2026-0100") == "NEW"
    assert set(statuses.values()) == {"IDENTICAL"}
    assert p2p.import_selected_cases([c for c in remote if c.case_id in ("T-2026-0003", "T-2026-0100")]) == 2

    app = _headless_app(_reopen(mine))  # restart: load_all_data rescoring with the local profile
    by_id = {c.case_id: c for c in app.cases}
    assert len(by_id) == 13
    assert by_id["T-2026-0003"].workflow_status.current_actor == Actor.DEVELOPMENT.value
    assert by_id["T-2026-0003"].timeline[-1].note == "An Dev übergeben"
    open_cases = [c for c in app.cases if not c.workflow_status.is_completed and c.case_id != "T-2026-0100"]
    assert {c.classification.urgency_level for c in open_cases} == {UrgencyLevel.YELLOW}  # RED at the colleague's
    assert by_id["T-2026-0100"].classification.urgency_level == UrgencyLevel.GREEN  # brand new: score 0
    assert by_id["T-2026-0003"].classification.calculated_score >= 100  # overdue deadline bonus
    app.storage_service.save_cases(app.cases)
    persisted = _reopen(app.storage_service).load_cases()
    assert next(c for c in persisted if c.case_id == "T-2026-0003").classification.urgency_level == UrgencyLevel.YELLOW
    assert [c.case_id for c in SearchService.filter_cases(persisted, "actor:dev Schmidt")] == ["T-2026-0003"]


# --- app start: daily backup + auto-archive -----------------------------------

def test_startup_daily_backup_then_auto_archive(seeded_storage):
    """main.py start sequence: backup of all cases first, then completed cases idle >= 30 days move to the archive."""
    cases = seeded_storage.load_cases()
    recent_done = Case(case_id="T-2026-0200", created_at=now_iso(), updated_at=now_iso(),
                       workflow_status=WorkflowStatus(is_completed=True))
    old_done = Case(case_id="T-2026-OLD1", created_at="2026-06-01T10:00:00", updated_at="2026-06-01T10:00:00",
                    classification=Classification(title="Old Case"), workflow_status=WorkflowStatus(is_completed=True))
    seeded_storage.save_cases(cases + [recent_done, old_done])
    expected_archived = {"T-2026-0006", "T-2026-0007", "T-2026-0011", "T-2026-OLD1"}

    backup = seeded_storage.perform_daily_backup()
    today = get_local_now().strftime("%Y-%m-%d")
    assert seeded_storage.auto_archive_completed_cases(threshold_days=30) == 4

    storage = _reopen(seeded_storage)
    assert backup is not None and backup.name == f"cases_{today}.json"
    backed_up = backup.read_text(encoding="utf-8")
    assert all(cid in backed_up for cid in expected_archived)
    active = {c.case_id for c in storage.load_cases()}
    assert len(active) == 10 and "T-2026-0200" in active and not active & expected_archived
    archive = storage.load_archive()
    assert {c.case_id for c in archive} == expected_archived
    assert all(c.workflow_status.is_archived for c in archive)

    # Second start the same day: backup is not overwritten, nothing more to archive.
    snapshot = backup.read_text(encoding="utf-8")
    assert storage.perform_daily_backup(today) == backup
    assert backup.read_text(encoding="utf-8") == snapshot
    assert storage.auto_archive_completed_cases(threshold_days=30) == 0


# --- quick case -> schema conversion -> form edit -> export -------------------

def test_quick_case_converted_filled_in_cockpit_and_exported(seeded_storage):
    """Quick case -> ConvertSchemaDialog -> cockpit form save -> persisted -> export template renders."""
    from ui.dialogs.convert_schema_dialog import ConvertSchemaDialog
    from ui.views.cockpit_view import CockpitView
    from ui.widgets.dynamic_form_widget import DynamicFormWidget

    app = _headless_app(seeded_storage)
    quick_schema = next(s for s in app.schemas if s.schema_id == "schema_quick")
    bug_schema = next(s for s in app.schemas if s.schema_id == "schema_bug_report")
    template = next(t for t in app.templates if t.template_id == "gitlab_dev_bug")
    quick = Case(case_id="T-2026-8888", created_at=now_iso(), updated_at=now_iso(), created_by="Daniel Rösch",
                 customer=CaseCustomer(customer_id="K-10777", practice_name="Hausarztpraxis Dipl.-Med. Fischer"),
                 classification=Classification(schema_id="schema_quick", title="Rezeptdruck-Störung"),
                 attachment_directory="data/attachments/T-2026-8888_Fischer",
                 form_data={"module_name": "Rezeptdruck", "short_description": "Drucker druckt nicht",
                            "unformatted_description": "Leere Seiten seit Update v2026.2."})
    app.on_case_created(quick)

    cockpit: Any = CockpitView.__new__(CockpitView)
    cockpit.scoring_service = app.scoring_service
    cockpit.on_case_updated = app.on_case_updated
    cockpit.on_select_case_from_list = lambda c: setattr(cockpit, "current_case", c)
    cockpit.schemas = app.schemas

    dialog: Any = ConvertSchemaDialog.__new__(ConvertSchemaDialog)
    dialog.case, dialog.schemas, dialog.current_schema = quick, app.schemas, quick_schema
    dialog.author_name = "Daniel Rösch"
    dialog.on_schema_converted = cockpit.on_schema_converted
    dialog.destroy = lambda: None
    dialog.error_label = _Field()
    dialog.schema_combo = _Field(f"{quick_schema.display_name} [schema_quick]")
    dialog.on_convert()
    assert dialog.error_label.val  # converting to the schema already in use is refused
    dialog.schema_combo = _Field(f"{bug_schema.display_name} [schema_bug_report]")
    dialog.on_convert()

    storage = _reopen(seeded_storage)
    converted = next(c for c in storage.load_cases() if c.case_id == "T-2026-8888")
    assert converted.classification.schema_id == "schema_bug_report"
    assert converted.form_data == {"module_name": "Rezeptdruck"}
    assert "Formular umgewandelt" in converted.timeline[-1].note
    assert "Leere Seiten seit Update v2026.2." in converted.timeline[-1].note
    assert set(converted.missing_required_fields) == {"error_message", "reproduction_steps", "database_dump_provided"}
    ok, missing, _ = ExportService(storage).render_template(converted, template, bug_schema)
    assert (ok, set(missing)) == (False, set(converted.missing_required_fields))

    form: Any = DynamicFormWidget.__new__(DynamicFormWidget)
    form.schema = bug_schema
    form.apply_missing_field_highlight = lambda missing: None
    form.field_widgets = {
        "module_name": (FieldType.TEXT, _Field("Rezeptdruck ")),
        "error_message": (FieldType.TEXT, _Field("ERR_PRINT_17")),
        "reproduction_steps": ("textbox", _Field("Rezept öffnen, Drucken klicken")),
        "database_dump_provided": (FieldType.BOOLEAN, _Field(True)),
        "tested_browsers": ("browser_pills", {"Firefox": _Field(True), "Edge": _Field(False), "Chrome": _Field(True)}),
    }
    cockpit.form_widget = form
    cockpit.current_case = next(c for c in app.cases if c.case_id == "T-2026-8888")
    cockpit.on_click_save()

    storage = _reopen(app.storage_service)
    saved = next(c for c in storage.load_cases() if c.case_id == "T-2026-8888")
    assert saved.form_data["tested_browsers"] == "Firefox, Chrome"
    assert saved.missing_required_fields == [] and saved.workflow_status.is_data_complete is True
    ok, missing, text = ExportService(storage).render_template(saved, template, bug_schema)
    assert ok is True and missing == []
    assert "**Praxis:** Hausarztpraxis Dipl.-Med. Fischer (Kundennr: K-10777)" in text
    assert "**Fehlermeldung:** ERR_PRINT_17" in text
    assert "Vorhanden im Ordner data/attachments/T-2026-8888_Fischer" in text


# --- follow-up reminders -> bell / flyout / toast -> handover -----------------

def test_followup_reminder_bell_flyout_toast_and_handover(seeded_storage):
    """Follow-up set and persisted -> bell and tray count it -> flyout/toast open the case -> handover -> done clears it."""
    from enums import get_actor_display
    from ui.dialogs.followup_flyout_dialog import FollowupFlyoutDialog
    from ui.widgets.ctk_tooltip import CTkTooltip
    from ui.widgets.toast_notification import ToastNotification

    app = _headless_app(seeded_storage)
    app.refresh_views()
    seeded_due = int(app.bell_btn.val)
    assert seeded_due == 2  # T-2026-0009 / -0010 carry past follow-ups in the seed

    case = next(c for c in app.cases if c.case_id == "T-2026-0001")
    case.workflow_status.followup_at = _iso(get_local_now() - timedelta(hours=1))
    case.workflow_status.followup_note = "Entwickler fragen"
    app.on_case_updated(case)
    assert app.bell_btn.val == str(seeded_due + 1) and app.bell_btn.fg_color == "darkred"
    assert app.tray_service._badge_count == seeded_due + 1

    storage = _reopen(seeded_storage)
    app = _headless_app(storage)
    app.check_due_followups()
    assert app.bell_btn.val == str(seeded_due + 1)
    due = next(c for c in app.cases if c.case_id == "T-2026-0001")
    assert [c.case_id for c in SearchService.filter_cases(app.cases, "reminder:due vip:true")] == [
        "T-2026-0001", "T-2026-0009"]

    card = SimpleNamespace(bind=lambda *a, **k: None, winfo_children=lambda: [])
    tooltip = CTkTooltip(card, lambda: f"{due.case_id}: {due.workflow_status.followup_note}")
    assert tooltip.text == "T-2026-0001: Entwickler fragen"

    flyout: Any = FollowupFlyoutDialog.__new__(FollowupFlyoutDialog)
    flyout.on_case_selected = app.on_case_selected
    flyout.destroy = lambda: None
    flyout.select_case(due)
    assert app.active_view is app.cockpit_view and app.cockpit_view.current_case is due

    other = next(c for c in app.cases if c.case_id == "T-2026-0010")
    toast: Any = ToastNotification.__new__(ToastNotification)
    toast.on_open = lambda: app.switch_to_cockpit_view_for_case(other)
    toast.safe_destroy = lambda: None
    toast.handle_open()
    toast.handle_open()  # a second click on a closing toast does nothing
    assert app.cockpit_view.selected == ["T-2026-0001", "T-2026-0010"]

    previous_actor = due.workflow_status.current_actor
    due.workflow_status.current_actor = Actor.DEVELOPMENT.value
    due.workflow_status.actor_since = now_iso()
    due.timeline.append(TimelineEntry(
        timestamp=now_iso(), author="Daniel Rösch", channel=Channel.INTERNAL_NOTE.value, note="Bugfix nötig",
        status_change=f"ZUSTÄNDIGKEIT: {get_actor_display(previous_actor)} -> {get_actor_display(Actor.DEVELOPMENT.value)}"))
    due.workflow_status.followup_at = _iso(get_local_now() + timedelta(days=3))
    app.on_case_updated(due)
    assert app.bell_btn.val == str(seeded_due)

    for c in [c for c in app.cases if c.workflow_status.followup_at]:
        c.workflow_status.is_completed = True
        app.on_case_updated(c)
    assert (app.bell_btn.val, app.bell_btn.fg_color) == ("0", "gray30")
    assert app.tray_service._badge_count == 0

    persisted = {c.case_id: c for c in _reopen(storage).load_cases()}
    handed = persisted["T-2026-0001"]
    assert handed.workflow_status.current_actor == Actor.DEVELOPMENT.value
    assert handed.timeline[-1].status_change.startswith("ZUSTÄNDIGKEIT:")
    assert all(persisted[cid].workflow_status.is_completed for cid in ("T-2026-0001", "T-2026-0009", "T-2026-0010"))
    assert all(persisted[cid].classification.calculated_score == 0 for cid in ("T-2026-0001", "T-2026-0009"))


# --- cockpit column widths -> profile on disk ---------------------------------

def test_cockpit_sash_widths_survive_restart(storage):
    """Regression: the right column was saved 8px too wide (sash width + pads), so it crept on every restore."""
    from ui.views.cockpit_view import CockpitView

    class _Paned:
        pinned: dict[str, int] = {}

        def winfo_exists(self):
            return True

        def winfo_width(self):
            return 1000

        def cget(self, option):
            return {"sashwidth": 6, "sashpad": 1}[option]

        def sash_coord(self, index):
            return (350, 0) if index == 0 else (680, 0)

        def paneconfigure(self, pane, **kwargs):
            self.pinned[pane] = kwargs["width"]

    view: Any = CockpitView.__new__(CockpitView)
    view.profile = storage.load_profile()
    view.storage_service = storage
    view.paned = _Paned()
    view.left_frame, view.right_tabview = "left", "right"
    view.on_paned_sash_released()

    # Pinned as pane options too, or Tk re-derives the sizes and the column snaps back.
    assert view.paned.pinned == {"left": 350, "right": 312}

    # The debounced background save reaches disk on its own, without an explicit flush.
    cfg = AppConfig(workspace_dir=storage.config.workspace_dir, username="test_agent")
    deadline = time.monotonic() + 5
    while time.monotonic() < deadline:
        widths = StorageService(cfg).load_profile().ui_settings.column_widths
        if (widths["cockpit_left"], widths["cockpit_right"]) == (350, 312):
            break
        time.sleep(0.05)
    assert (widths["cockpit_left"], widths["cockpit_right"]) == (350, 312)
