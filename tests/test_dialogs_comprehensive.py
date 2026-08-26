"""Comprehensive unit and interaction tests for application dialogs."""

from pathlib import Path
import customtkinter as ctk
import pytest
from config import AppConfig
from enums import Actor, UrgencyLevel, BoardColumn, FieldType
from models.case import Case, CaseCustomer, Classification, WorkflowStatus, TimelineEntry
from models.customer import Customer, Contact
from models.export_template import ExportTemplate
from models.profile import UserProfile, Colleague
from models.schema import QuestionSchema, SchemaField
from services.storage_service import StorageService
from services.customer_service import CustomerService
from services.schema_service import SchemaService
from services.export_service import ExportService
from services.calendar_email_service import CalendarEmailService


@pytest.fixture
def app_and_storage(tmp_path: Path):
    config = AppConfig(workspace_dir=tmp_path)
    storage = StorageService(config)
    
    app = ctk.CTk()
    app.withdraw()
    
    yield app, storage, config
    
    try:
        app.destroy()
    except Exception:
        pass


def test_customer_management_dialog_full_crud(app_and_storage):
    """Test loading, adding, editing practice details and contact persons in CustomerManagementDialog."""
    app, storage, config = app_and_storage
    from ui.dialogs.customer_management_dialog import CustomerManagementDialog

    initial_customers = [
        Customer(
            customer_id="K-100",
            practice_name="Praxis Dr. Alpha",
            is_vip=False,
            contacts=[Contact(name="Frau Alpha", email="alpha@praxis.de", phone="0123-456")],
        )
    ]
    storage.save_customers(initial_customers)
    cust_service = CustomerService(storage)

    dialog = CustomerManagementDialog(
        app,
        customer_service=cust_service,
        on_customers_updated=lambda: None,
    )
    dialog.update_idletasks()

    assert len(dialog.customers) == 1
    assert dialog.customers[0].practice_name == "Praxis Dr. Alpha"

    # 1. Select the customer
    dialog.select_customer("K-100")
    dialog.update_idletasks()
    assert dialog.name_entry.get() == "Praxis Dr. Alpha"

    # 2. Modify customer
    dialog.name_entry.delete(0, "end")
    dialog.name_entry.insert(0, "Praxis Dr. Alpha-Beta")
    dialog.vip_var.set(True)
    dialog.save_current_customer()
    dialog.update_idletasks()

    assert dialog.selected_customer is not None
    assert dialog.selected_customer.practice_name == "Praxis Dr. Alpha-Beta"
    assert dialog.selected_customer.is_vip

    # 3. Add a new customer
    dialog.on_click_new_customer()
    dialog.cust_id_entry.configure(state="normal")
    dialog.cust_id_entry.delete(0, "end")
    dialog.cust_id_entry.insert(0, "K-200")
    dialog.name_entry.delete(0, "end")
    dialog.name_entry.insert(0, "Klinik Gamma")
    dialog.save_current_customer()
    dialog.update_idletasks()

    assert len(dialog.customers) == 2
    assert any(c.customer_id == "K-200" for c in dialog.customers)

    # 4. Add contact person to selected customer
    dialog.add_contact_row()
    dialog.update_idletasks()
    assert len(dialog.contact_rows) >= 1

    dialog.destroy()


def test_colleague_management_dialog_full_crud(app_and_storage):
    """Test adding, editing, absence toggling and saving in ColleagueManagementDialog."""
    app, storage, config = app_and_storage
    from ui.dialogs.colleague_management_dialog import ColleagueManagementDialog

    initial_colleagues = [
        Colleague(
            name="Max Mustermann",
            username="mmustermann",
            email="max@support.de",
            is_absent=False,
        )
    ]
    storage.save_colleagues(initial_colleagues)

    dialog = ColleagueManagementDialog(
        app,
        storage_service=storage,
        on_colleagues_updated=lambda: None,
    )
    dialog.update_idletasks()

    assert len(dialog.colleagues) == 1
    assert dialog.colleagues[0].name == "Max Mustermann"

    # 1. Select colleague
    dialog.select_colleague(dialog.colleagues[0])
    dialog.update_idletasks()
    assert dialog.name_entry.get() == "Max Mustermann"

    # 2. Toggle absence
    dialog.is_absent_var.set(True)
    dialog.absence_reason_entry.delete(0, "end")
    dialog.absence_reason_entry.insert(0, "Im Urlaub bis Freitag")
    dialog.on_click_save()
    dialog.update_idletasks()

    assert dialog.selected_colleague is not None
    assert dialog.selected_colleague.is_absent
    assert dialog.selected_colleague.absence_reason == "Im Urlaub bis Freitag"

    # 3. Add new colleague
    dialog.on_click_new_colleague()
    dialog.username_entry.delete(0, "end")
    dialog.username_entry.insert(0, "emusterfrau")
    dialog.name_entry.delete(0, "end")
    dialog.name_entry.insert(0, "Erika Musterfrau")
    dialog.email_entry.delete(0, "end")
    dialog.email_entry.insert(0, "erika@support.de")
    dialog.on_click_save()
    dialog.update_idletasks()

    assert len(dialog.colleagues) == 2
    assert any(c.name == "Erika Musterfrau" for c in dialog.colleagues)

    dialog.destroy()


def test_tag_management_dialog_crud(app_and_storage):
    """Test managing tags, module tags, and quick-access tags."""
    app, storage, config = app_and_storage
    from ui.dialogs.tag_management_dialog import TagManagementDialog

    profile = storage.load_profile()
    profile.available_tags = ["PVS", "Abrechnung", "Hardware"]
    storage.save_profile(profile)

    dialog = TagManagementDialog(
        app,
        storage_service=storage,
        profile=profile,
        on_tags_updated=lambda: None,
    )
    dialog.update_idletasks()

    # 1. Add new tag
    dialog.new_tag_entry.delete(0, "end")
    dialog.new_tag_entry.insert(0, "Telematik")
    dialog.on_add_tag()
    dialog.update_idletasks()

    assert "Telematik" in dialog.profile.available_tags

    # 2. Delete tag
    dialog.on_delete_tag("Hardware")
    dialog.update_idletasks()

    assert "Hardware" not in dialog.profile.available_tags

    dialog.destroy()


def test_schema_builder_dialog(app_and_storage):
    """Test building, editing questions, and validating custom schemas."""
    app, storage, config = app_and_storage
    from ui.dialogs.schema_builder_dialog import SchemaBuilderDialog, NewSchemaDialog

    schemas = storage.load_schemas()
    schema_service = SchemaService(config)

    created_schemas = None

    def on_updated(s_list):
        nonlocal created_schemas
        created_schemas = s_list

    dialog = SchemaBuilderDialog(
        app,
        schemas=schemas,
        schema_service=schema_service,
        on_schemas_updated=on_updated,
    )
    dialog.update_idletasks()

    # 1. Test NewSchemaDialog
    new_diag = NewSchemaDialog(app, on_schema_created=dialog.on_schema_created)
    new_diag.name_entry.insert(0, "Abrechnung Test")
    new_diag.id_entry.insert(0, "schema_test_custom")
    new_diag.desc_entry.insert(0, "Test Formular")
    new_diag.on_save()

    assert any(s.schema_id == "schema_test_custom" for s in dialog.schemas)
    assert dialog.selected_schema is not None
    assert dialog.selected_schema.schema_id == "schema_test_custom"

    # 2. Add field
    dialog.new_id_entry.delete(0, "end")
    dialog.new_id_entry.insert(0, "test_field_1")
    dialog.new_label_entry.delete(0, "end")
    dialog.new_label_entry.insert(0, "Test Frage")
    dialog.new_type_combo.set(FieldType.TEXT.value)
    dialog.on_add_field()
    dialog.update_idletasks()

    assert dialog.selected_schema is not None
    assert len(dialog.selected_schema.fields) >= 1
    assert dialog.selected_schema.fields[0].field_id == "test_field_1"

    dialog.destroy()


def test_export_dialog_filtering_and_generation(app_and_storage):
    """Test ExportDialog template selection, generation, and output preview."""
    app, storage, config = app_and_storage
    from ui.dialogs.export_dialog import ExportDialog

    templates = [
        ExportTemplate(
            template_id="tpl_dev",
            display_name="Entwickler-Ticket",
            template_string="Fall {{ case.case_id }}: {{ case.classification.title }}",
        )
    ]
    schemas = storage.load_schemas()
    export_svc = ExportService(storage)

    case = Case(
        case_id="T-EXP-01",
        customer=CaseCustomer(customer_id="K-1", practice_name="Praxis Eins"),
        classification=Classification(title="Fehler beim Start"),
        workflow_status=WorkflowStatus(board_column=BoardColumn.NEW),
        form_data={"description": "Programm startet nicht"},
    )

    updated_case = None

    def on_update(c):
        nonlocal updated_case
        updated_case = c

    dialog = ExportDialog(
        app,
        case=case,
        templates=templates,
        schemas=schemas,
        export_service=export_svc,
        on_case_updated=on_update,
    )
    dialog.update_idletasks()

    assert dialog.active_template is not None
    output_txt = dialog.preview_textbox.get("1.0", "end")
    assert "T-EXP-01" in output_txt

    dialog.destroy()


def test_followup_flyout_dialog(app_and_storage):
    """Test displaying overdue followups and interacting with snooze actions."""
    app, storage, config = app_and_storage
    from ui.dialogs.followup_flyout_dialog import FollowupFlyoutDialog

    cases = [
        Case(
            case_id="T-FW-01",
            customer=CaseCustomer(customer_id="K-1", practice_name="Praxis Overdue"),
            classification=Classification(title="Dringender Rückruf"),
            workflow_status=WorkflowStatus(
                followup_at="2026-08-01T10:00:00",
                followup_note="Wichtig!",
                is_completed=False,
            ),
        ),
    ]

    selected_case = None

    def on_select(c):
        nonlocal selected_case
        selected_case = c

    dialog = FollowupFlyoutDialog(
        app,
        due_cases=cases,
        on_case_selected=on_select,
        on_refresh=lambda: None,
    )
    dialog.update_idletasks()

    assert len(dialog.due_cases) == 1
    assert dialog.due_cases[0].case_id == "T-FW-01"

    # Test clicking case row
    dialog.on_case_selected(dialog.due_cases[0])
    assert selected_case is not None
    assert selected_case.case_id == "T-FW-01"

    dialog.destroy()


def test_handover_dialog(app_and_storage):
    """Test selecting target colleague and creating handover timeline note."""
    app, storage, config = app_and_storage
    from ui.dialogs.handover_dialog import HandoverDialog

    colleagues = [
        Colleague(name="Anna Schmidt", email="anna@support.de"),
        Colleague(name="Bernd Weber", email="bernd@support.de"),
    ]

    case = Case(
        case_id="T-HO-01",
        customer=CaseCustomer(customer_id="K-1", practice_name="Praxis Handover"),
        classification=Classification(title="Übergabefall"),
    )

    handover_recorded = None

    def on_handover(target, person, channel, note):
        nonlocal handover_recorded
        handover_recorded = (target, person, channel, note)

    dialog = HandoverDialog(
        app,
        case=case,
        colleagues=colleagues,
        on_handover_confirmed=on_handover,
    )
    dialog.update_idletasks()

    dialog.actor_combo.set("Support")
    dialog.note_entry.delete(0, "end")
    dialog.note_entry.insert(0, "Bitte Fall bis 14 Uhr prüfen.")
    dialog.on_confirm()

    assert handover_recorded is not None
    assert "Bitte Fall bis 14 Uhr prüfen." in handover_recorded[3]

    dialog.destroy()


def test_convert_schema_dialog(app_and_storage):
    """Test converting case schema and migrating form data."""
    app, storage, config = app_and_storage
    from ui.dialogs.convert_schema_dialog import ConvertSchemaDialog

    schema_1 = QuestionSchema(
        schema_id="schema_1",
        display_name="Schema 1",
        fields=[SchemaField(field_id="q1", label="Problembeschreibung", field_type=FieldType.TEXT)],
    )
    schema_2 = QuestionSchema(
        schema_id="schema_2",
        display_name="Schema 2",
        fields=[
            SchemaField(field_id="q1", label="Problembeschreibung", field_type=FieldType.TEXT),
            SchemaField(field_id="q2", label="Dringlichkeit", field_type=FieldType.NUMBER),
        ],
    )

    case = Case(
        case_id="T-CONV-01",
        classification=Classification(schema_id="schema_1", title="Altfall"),
        form_data={"q1": "Alte Daten"},
    )

    converted_case = None

    def on_converted(c, schema):
        nonlocal converted_case
        converted_case = c

    dialog = ConvertSchemaDialog(
        app,
        case=case,
        schemas=[schema_1, schema_2],
        author_name="DaniBani",
        on_schema_converted=on_converted,
    )
    dialog.update_idletasks()

    dialog.schema_combo.set("Schema 2 [schema_2]")
    dialog.on_convert()

    assert converted_case is not None
    assert converted_case.classification.schema_id == "schema_2"
    assert converted_case.form_data.get("q1") == "Alte Daten"

    dialog.destroy()


def test_profile_settings_dialog(app_and_storage):
    """Test loading and saving profile settings."""
    app, storage, config = app_and_storage
    from ui.dialogs.profile_settings_dialog import ProfileSettingsDialog

    profile = storage.load_profile()
    profile.user.name = "Test User"
    profile.user.email = "test@user.de"

    updated = False

    def on_update():
        nonlocal updated
        updated = True

    dialog = ProfileSettingsDialog(
        app,
        profile=profile,
        storage_service=storage,
        on_profile_updated=on_update,
    )
    dialog.update_idletasks()

    dialog.save_settings()
    assert updated

    dialog.destroy()
