"""Tests for src/ui/dialogs/customer_form_builders.py (CustomerFormBuilderMixin).

This mixin is baked into every CustomerManagementDialog instance and so
already runs indirectly whenever a test constructs that dialog (e.g.
test_dialogs_comprehensive.py's test_customer_management_dialog_full_crud).
However that existing test only round-trips a handful of the ~25 fields this
mixin builds (name, VIP flag, one contact). This file specifically covers
the extended fields nothing else touches: old practice name, salutation,
first/last name, address, the secondary phone/mobile/email fields, website,
VM/instance number, DSC/DSCNEU, additional contacts, general notes, and
custom AI rules - verifying they round-trip through save -> reselect, and
that "+ Neue Praxis anlegen" actually clears all of them (not just the ones
covered elsewhere).
"""

from pathlib import Path
import customtkinter as ctk
import pytest

from config import AppConfig
from models.customer import Customer
from services.storage_service import StorageService
from services.customer_service import CustomerService
from ui.dialogs.customer_management_dialog import CustomerManagementDialog


@pytest.fixture
def app_and_dialog(tmp_path: Path):
    config = AppConfig(workspace_dir=tmp_path)
    storage = StorageService(config)
    cust_service = CustomerService(storage)

    app = ctk.CTk()
    app.withdraw()

    dialog = CustomerManagementDialog(app, customer_service=cust_service, on_customers_updated=lambda: None)
    dialog.update_idletasks()

    yield app, dialog, cust_service

    try:
        dialog.destroy()
    except Exception:
        pass
    try:
        app.destroy()
    except Exception:
        pass


def _fill_extended_fields(dialog):
    def set_entry(entry, value):
        entry.delete(0, "end")
        entry.insert(0, value)

    set_entry(dialog.cust_id_entry, "CUST-9001")
    set_entry(dialog.name_entry, "Praxis Extended")
    set_entry(dialog.name_old_entry, "Alte Praxis GmbH")
    set_entry(dialog.salut_entry, "Frau")
    set_entry(dialog.fname_entry, "Erika")
    set_entry(dialog.lname_entry, "Musterfrau")
    set_entry(dialog.street_entry, "Hauptstraße 42")
    set_entry(dialog.zip_entry, "70173")
    set_entry(dialog.city_entry, "Stuttgart")
    set_entry(dialog.phone_m_entry, "0711-111111")
    set_entry(dialog.phone_dir_entry, "0711-222222")
    set_entry(dialog.phone_priv_entry, "0711-333333")
    set_entry(dialog.phone2_entry, "0711-444444")
    set_entry(dialog.phone3_entry, "0711-555555")
    set_entry(dialog.mobile_entry, "0171-666666")
    set_entry(dialog.mobile_priv_entry, "0171-777777")
    set_entry(dialog.email2_entry, "zweite@praxis.de")
    set_entry(dialog.email3_entry, "dritte@praxis.de")
    set_entry(dialog.website_entry, "https://praxis-extended.de")
    set_entry(dialog.vm_entry, "104")
    set_entry(dialog.instance_entry, "2")
    set_entry(dialog.dsc_entry, "DSC-ABC")
    set_entry(dialog.dsc_neu_entry, "DSCNEU-XYZ")
    set_entry(dialog.notes_entry, "Erreichbar nur vormittags")

    dialog.additional_contacts_txt.delete("1.0", "end")
    dialog.additional_contacts_txt.insert("1.0", "Herr Meier\nFrau Schulz")

    dialog.custom_ai_rules_txt.delete("1.0", "end")
    dialog.custom_ai_rules_txt.insert("1.0", "Duzen erwünscht\nBetreff mit [EXT] beginnen")

    dialog.vip_var.set(True)


def test_extended_fields_round_trip_through_save_and_reselect(app_and_dialog):
    app, dialog, cust_service = app_and_dialog

    _fill_extended_fields(dialog)
    dialog.save_current_customer()
    dialog.update_idletasks()

    # Switch to a different (freshly created) customer to force the form to
    # actually reload from the model rather than just keep showing stale text.
    dialog.on_click_new_customer()
    dialog.update_idletasks()

    dialog.select_customer("CUST-9001")
    dialog.update_idletasks()

    assert dialog.name_old_entry.get() == "Alte Praxis GmbH"
    assert dialog.salut_entry.get() == "Frau"
    assert dialog.fname_entry.get() == "Erika"
    assert dialog.lname_entry.get() == "Musterfrau"
    assert dialog.street_entry.get() == "Hauptstraße 42"
    assert dialog.zip_entry.get() == "70173"
    assert dialog.city_entry.get() == "Stuttgart"
    assert dialog.phone_m_entry.get() == "0711-111111"
    assert dialog.phone_dir_entry.get() == "0711-222222"
    assert dialog.phone_priv_entry.get() == "0711-333333"
    assert dialog.phone2_entry.get() == "0711-444444"
    assert dialog.phone3_entry.get() == "0711-555555"
    assert dialog.mobile_entry.get() == "0171-666666"
    assert dialog.mobile_priv_entry.get() == "0171-777777"
    assert dialog.email2_entry.get() == "zweite@praxis.de"
    assert dialog.email3_entry.get() == "dritte@praxis.de"
    assert dialog.website_entry.get() == "https://praxis-extended.de"
    assert dialog.vm_entry.get() == "104"
    assert dialog.instance_entry.get() == "2"
    assert dialog.dsc_entry.get() == "DSC-ABC"
    assert dialog.dsc_neu_entry.get() == "DSCNEU-XYZ"
    assert dialog.notes_entry.get() == "Erreichbar nur vormittags"
    assert dialog.additional_contacts_txt.get("1.0", "end-1c") == "Herr Meier\nFrau Schulz"
    assert dialog.custom_ai_rules_txt.get("1.0", "end-1c") == "Duzen erwünscht\nBetreff mit [EXT] beginnen"
    assert dialog.vip_var.get() is True

    saved = cust_service.get_customer_by_id("CUST-9001")
    assert saved is not None
    assert saved.vm_number == 104
    assert saved.instance_number == 2
    assert saved.additional_contacts == ["Herr Meier", "Frau Schulz"]
    assert saved.custom_ai_rules == ["Duzen erwünscht", "Betreff mit [EXT] beginnen"]
    assert saved.is_vip is True


def test_vm_and_instance_number_default_to_none_when_not_numeric(app_and_dialog):
    app, dialog, cust_service = app_and_dialog

    dialog.on_click_new_customer()
    dialog.cust_id_entry.configure(state="normal")
    dialog.cust_id_entry.delete(0, "end")
    dialog.cust_id_entry.insert(0, "CUST-9002")
    dialog.name_entry.delete(0, "end")
    dialog.name_entry.insert(0, "Praxis Ohne VM")
    dialog.vm_entry.delete(0, "end")
    dialog.vm_entry.insert(0, "nicht-numerisch")
    dialog.instance_entry.delete(0, "end")

    dialog.save_current_customer()

    saved = cust_service.get_customer_by_id("CUST-9002")
    assert saved.vm_number is None
    assert saved.instance_number is None


def test_new_customer_clears_all_extended_fields(app_and_dialog):
    app, dialog, cust_service = app_and_dialog

    _fill_extended_fields(dialog)
    dialog.save_current_customer()
    dialog.select_customer("CUST-9001")
    dialog.update_idletasks()

    dialog.on_click_new_customer()
    dialog.update_idletasks()

    assert dialog.name_old_entry.get() == ""
    assert dialog.salut_entry.get() == ""
    assert dialog.fname_entry.get() == ""
    assert dialog.lname_entry.get() == ""
    assert dialog.street_entry.get() == ""
    assert dialog.zip_entry.get() == ""
    assert dialog.city_entry.get() == ""
    assert dialog.phone_m_entry.get() == ""
    assert dialog.phone_dir_entry.get() == ""
    assert dialog.phone_priv_entry.get() == ""
    assert dialog.phone2_entry.get() == ""
    assert dialog.phone3_entry.get() == ""
    assert dialog.mobile_entry.get() == ""
    assert dialog.mobile_priv_entry.get() == ""
    assert dialog.email2_entry.get() == ""
    assert dialog.email3_entry.get() == ""
    assert dialog.website_entry.get() == ""
    assert dialog.vm_entry.get() == ""
    assert dialog.instance_entry.get() == ""
    assert dialog.dsc_entry.get() == ""
    assert dialog.dsc_neu_entry.get() == ""
    assert dialog.notes_entry.get() == ""
    assert dialog.additional_contacts_txt.get("1.0", "end-1c") == ""
    assert dialog.custom_ai_rules_txt.get("1.0", "end-1c") == ""
    assert dialog.vip_var.get() is False


def test_save_rejects_missing_id_or_name(app_and_dialog):
    app, dialog, cust_service = app_and_dialog

    dialog.on_click_new_customer()
    dialog.cust_id_entry.configure(state="normal")
    dialog.cust_id_entry.delete(0, "end")  # no ID
    dialog.name_entry.delete(0, "end")
    dialog.name_entry.insert(0, "Praxis Ohne ID")

    before_count = len(cust_service.get_all_customers())
    dialog.save_current_customer()

    assert len(cust_service.get_all_customers()) == before_count
    assert dialog.status_lbl.cget("text") != ""
