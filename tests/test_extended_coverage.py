"""Extended unit and UI tests for NewCaseDialog, P2PDiffDialog, TemplateManagerDialog, ZipImportPathDialog, and WikiWidget."""

from pathlib import Path
import customtkinter as ctk
import pytest
from config import AppConfig
from enums import Actor, UrgencyLevel, BoardColumn, TargetType
from models.case import Case, CaseCustomer, Classification, WorkflowStatus, TimelineEntry
from models.customer import Customer, Contact
from models.profile import Colleague
from models.export_template import ExportTemplate
from models.schema import QuestionSchema, SchemaField
from services.storage_service import StorageService
from services.p2p_sync_service import P2PSyncService
from services.export_service import ExportService
from services.wiki_sync_service import WikiSyncService


@pytest.fixture
def ext_env(tmp_path: Path):
    config = AppConfig(workspace_dir=tmp_path)
    storage = StorageService(config)
    export_svc = ExportService(config)
    p2p_svc = P2PSyncService(storage)
    wiki_svc = WikiSyncService(config)

    app = ctk.CTk()
    app.withdraw()

    yield app, storage, export_svc, p2p_svc, wiki_svc, config, tmp_path

    try:
        app.destroy()
    except Exception:
        pass


def test_new_case_dialog_and_quick_customer(ext_env):
    """Test QuickAddCustomerDialog and NewCaseDialog case submission."""
    app, storage, export_svc, p2p_svc, wiki_svc, config, tmp_path = ext_env
    from ui.dialogs.new_case_dialog import QuickAddCustomerDialog, NewCaseDialog

    customers = [
        Customer(
            customer_id="K-555",
            practice_name="Praxis Dr. Quick",
            contacts=[Contact(name="Frau Quick", email="quick@praxis.de")],
        )
    ]
    schemas = storage.load_schemas()

    # 1. Test QuickAddCustomerDialog
    created_cust = None

    def on_cust(c):
        nonlocal created_cust
        created_cust = c

    q_diag = QuickAddCustomerDialog(app, on_customer_created=on_cust)
    q_diag.update_idletasks()
    q_diag.name_entry.insert(0, "Praxis Schnell")
    q_diag.contact_entry.insert(0, "Herr Schnell")
    q_diag.on_save()

    assert created_cust is not None
    assert created_cust.practice_name == "Praxis Schnell"

    # 2. Test NewCaseDialog
    created_case = None

    def on_case(c):
        nonlocal created_case
        created_case = c

    diag = NewCaseDialog(
        app,
        customers=customers,
        schemas=schemas,
        created_by="DaniBani",
        on_case_created=on_case,
    )
    diag.update_idletasks()

    diag.customer_combo.set("Praxis Dr. Quick (K-555)")
    diag.title_entry.insert(0, "Rezeptdrucker reagiert nicht")
    diag.note_textbox.insert("1.0", "Druckauftrag bleibt in Warteschlange hängen.")
    diag.on_save()

    assert created_case is not None
    assert created_case.classification.title == "Rezeptdrucker reagiert nicht"
    assert created_case.created_by == "DaniBani"

    diag.destroy()


def test_p2p_diff_dialog(ext_env, tmp_path: Path):
    """Test P2PDiffDialog peer cases comparison and selective import."""
    app, storage, export_svc, p2p_svc, wiki_svc, config, _ = ext_env
    from ui.dialogs.p2p_diff_dialog import P2PDiffDialog

    colleague_dir = tmp_path / "colleague_share"
    colleague_dir.mkdir(exist_ok=True)
    colleague_file = colleague_dir / "cases.json"

    remote_case = Case(
        case_id="T-P2P-01",
        customer=CaseCustomer(customer_id="K-1", practice_name="Praxis P2P"),
        classification=Classification(schema_id="schema_standard", title="P2P Fall"),
        updated_at="2026-08-25T12:00:00",
    )
    import json
    with open(colleague_file, "w", encoding="utf-8") as f:
        json.dump([remote_case.to_dict()], f)

    colleagues = [
        Colleague(
            name="Max Kollege",
            username="mkollege",
            cases_path=str(colleague_file),
        )
    ]

    synced = False

    def on_sync():
        nonlocal synced
        synced = True

    dialog = P2PDiffDialog(
        app,
        colleagues=colleagues,
        p2p_service=p2p_svc,
        on_sync_completed=on_sync,
    )
    dialog.update_idletasks()

    assert len(dialog.diff_items) == 1
    assert dialog.diff_items[0].case_id == "T-P2P-01"

    # Select and import
    dialog.on_import_selected()
    assert synced is True
    assert len(storage.load_cases()) == 1

    dialog.destroy()


def test_template_manager_and_edit_dialog(ext_env):
    """Test TemplateManagerDialog and EditTemplateDialog CRUD."""
    app, storage, export_svc, p2p_svc, wiki_svc, config, tmp_path = ext_env
    from ui.dialogs.template_manager_dialog import TemplateManagerDialog, EditTemplateDialog

    templates = [
        ExportTemplate(
            template_id="tpl_dev",
            display_name="Dev Ticket",
            template_string="Fall {{ case.case_id }}",
        )
    ]
    schemas = storage.load_schemas()

    # 1. Test EditTemplateDialog
    saved_tpl = None

    def on_save_tpl(t):
        nonlocal saved_tpl
        saved_tpl = t

    edit_diag = EditTemplateDialog(
        app,
        template=None,
        schemas=schemas,
        export_service=export_svc,
        on_save=on_save_tpl,
    )
    edit_diag.update_idletasks()
    edit_diag.id_entry.insert(0, "tpl_custom")
    edit_diag.name_entry.insert(0, "Custom Ticket")
    edit_diag.template_textbox.insert("1.0", "Fall {{ case.case_id }} - {{ customer.practice_name }}")
    edit_diag.save()

    assert saved_tpl is not None
    assert saved_tpl.template_id == "tpl_custom"

    # 2. Test TemplateManagerDialog
    dialog = TemplateManagerDialog(
        app,
        templates=templates,
        schemas=schemas,
        storage_service=storage,
        export_service=export_svc,
    )
    dialog.update_idletasks()

    assert len(dialog.templates) == 1
    dialog.destroy()


def test_zip_import_path_dialog(ext_env, tmp_path: Path):
    """Test ZipImportPathDialog inspection and path confirmation."""
    app, storage, export_svc, p2p_svc, wiki_svc, config, _ = ext_env
    from ui.dialogs.zip_import_dialog import ZipImportPathDialog
    import zipfile

    # Create dummy zip backup
    zip_path = tmp_path / "backup_test.zip"
    with zipfile.ZipFile(zip_path, "w") as zf:
        zf.writestr("data/cases.json", "[]")

    confirmed_paths = None

    def on_confirmed(data_dir, att_dir):
        nonlocal confirmed_paths
        confirmed_paths = (data_dir, att_dir)

    diag = ZipImportPathDialog(
        app,
        zip_file_path=zip_path,
        default_data_dir=config.data_dir,
        default_attachments_dir=config.attachments_dir,
        on_import_confirmed=on_confirmed,
    )
    diag.update_idletasks()

    diag.on_confirm()
    assert confirmed_paths is not None
    assert confirmed_paths[0] == config.data_dir

    diag.destroy()


def test_wiki_widget(ext_env):
    """Test WikiWidget rendering, search entry, and offline search."""
    app, storage, export_svc, p2p_svc, wiki_svc, config, tmp_path = ext_env
    from ui.widgets.wiki_widget import WikiWidget

    widget = WikiWidget(
        app,
        wiki_service=wiki_svc,
    )
    widget.pack(fill="both", expand=True)
    widget.update_idletasks()

    assert widget.search_entry is not None
    widget.search_entry.insert(0, "Setup")
    widget.on_search()
    widget.update_idletasks()

    widget.destroy()
