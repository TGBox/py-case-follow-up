"""Customer management form (extended fields, validation) and the Cobra CSV import dialog."""

from pathlib import Path
from tkinter import filedialog

import pytest

from models.customer import Contact, Customer

EXTENDED_ENTRIES = {
    "name_old_entry": "Alte Praxis GmbH",
    "salut_entry": "Frau",
    "fname_entry": "Erika",
    "lname_entry": "Musterfrau",
    "street_entry": "Hauptstraße 42",
    "zip_entry": "70173",
    "city_entry": "Stuttgart",
    "phone_m_entry": "0711-111111",
    "phone_dir_entry": "0711-222222",
    "phone_priv_entry": "0711-333333",
    "phone2_entry": "0711-444444",
    "phone3_entry": "0711-555555",
    "mobile_entry": "0171-666666",
    "mobile_priv_entry": "0171-777777",
    "email2_entry": "zweite@praxis.de",
    "email3_entry": "dritte@praxis.de",
    "website_entry": "https://praxis-extended.de",
    "vm_entry": "104",
    "instance_entry": "2",
    "dsc_entry": "DSC-ABC",
    "dsc_neu_entry": "DSCNEU-XYZ",
    "notes_entry": "Erreichbar nur vormittags",
}
EXTENDED_TEXTS = {
    "additional_contacts_txt": "Herr Meier\nFrau Schulz",
    "custom_ai_rules_txt": "Duzen erwünscht\nBetreff mit [EXT] beginnen",
}


def _set(entry, value: str):
    entry.configure(state="normal")
    entry.delete(0, "end")
    entry.insert(0, value)


@pytest.fixture
def cust_dialog(root, storage):
    from services.customer_service import CustomerService
    from ui.dialogs.customer_management_dialog import CustomerManagementDialog

    service = CustomerService(storage)
    dialog = CustomerManagementDialog(root, customer_service=service, on_customers_updated=lambda: None)
    dialog.update_idletasks()
    return dialog, service


def test_extended_fields_round_trip_and_new_customer_clears_them(cust_dialog):
    dialog, service = cust_dialog
    _set(dialog.cust_id_entry, "CUST-9001")
    _set(dialog.name_entry, "Praxis Extended")
    for attr, value in EXTENDED_ENTRIES.items():
        _set(getattr(dialog, attr), value)
    for attr, value in EXTENDED_TEXTS.items():
        getattr(dialog, attr).delete("1.0", "end")
        getattr(dialog, attr).insert("1.0", value)
    dialog.vip_var.set(True)
    dialog.save_current_customer()

    saved = service.get_customer_by_id("CUST-9001")
    assert (saved.vm_number, saved.instance_number, saved.is_vip) == (104, 2, True)
    assert saved.additional_contacts == ["Herr Meier", "Frau Schulz"]
    assert saved.custom_ai_rules == ["Duzen erwünscht", "Betreff mit [EXT] beginnen"]

    # "+ Neue Praxis anlegen" must clear every field, reselecting must reload them from the model.
    dialog.on_click_new_customer()
    assert all(getattr(dialog, a).get() == "" for a in EXTENDED_ENTRIES)
    assert all(getattr(dialog, a).get("1.0", "end-1c") == "" for a in EXTENDED_TEXTS)
    assert dialog.vip_var.get() is False

    dialog.select_customer("CUST-9001")
    assert {a: getattr(dialog, a).get() for a in EXTENDED_ENTRIES} == EXTENDED_ENTRIES
    assert {a: getattr(dialog, a).get("1.0", "end-1c") for a in EXTENDED_TEXTS} == EXTENDED_TEXTS
    assert dialog.vip_var.get() is True


def test_save_validates_id_and_numeric_fields(cust_dialog):
    dialog, service = cust_dialog

    dialog.on_click_new_customer()
    _set(dialog.cust_id_entry, "")
    _set(dialog.name_entry, "Praxis Ohne ID")
    dialog.save_current_customer()
    assert service.get_all_customers() == []
    assert dialog.status_lbl.cget("text") != ""

    _set(dialog.cust_id_entry, "CUST-9002")
    _set(dialog.vm_entry, "nicht-numerisch")
    _set(dialog.instance_entry, "")
    dialog.save_current_customer()
    saved = service.get_customer_by_id("CUST-9002")
    assert (saved.vm_number, saved.instance_number) == (None, None)


@pytest.fixture
def cobra_csv(tmp_path: Path) -> Path:
    csv_file = tmp_path / "cobra_export.csv"
    csv_file.write_text(
        "Kunden-Nr;Firma;Ansprechpartner;Telefon;E-Mail;VIP\n"
        "K-1001;Praxis Dr. Alpha;Dr. Alpha;01234;alpha@praxis.de;Ja\n"
        "K-1002;Zentrum Beta;Fr. Beta;05678;beta@praxis.de;Nein\n",
        encoding="utf-8",
    )
    return csv_file


def test_cobra_import_dialog_load_map_preview_and_import(root, cobra_csv, monkeypatch):
    from ui.dialogs.cobra_import_dialog import CobraImportDialog

    existing = [Customer(customer_id="K-1001", practice_name="Praxis Dr. Alpha (Alt)",
                         contacts=[Contact(name="Dr. Alpha Alt", email="old@praxis.de")])]
    imported = []
    dialog = CobraImportDialog(root, existing_customers=existing, on_import_completed=imported.append)

    dialog.on_click_import()  # nothing loaded yet
    assert imported == []

    monkeypatch.setattr(filedialog, "askopenfilename", lambda **k: str(cobra_csv))
    dialog.on_browse_file()
    assert dialog.file_path == str(cobra_csv)
    assert len(dialog.raw_rows) == 2
    assert dialog.mapping["practice_name"] == "Firma"
    summary = dialog.summary_lbl.cget("text")
    assert "1 neue" in summary and "1 bereits vorhandene" in summary

    monkeypatch.setattr(filedialog, "askopenfilename", lambda **k: "")
    dialog.on_browse_file()  # cancelled browse keeps the loaded file
    assert dialog.file_path == str(cobra_csv)

    dialog.on_mapping_changed("practice_name", "(Keine Zuordnung)")
    assert dialog.mapping["practice_name"] == ""
    dialog.on_mapping_changed("practice_name", "Firma")

    modes = dialog.mode_combo.cget("values")
    for mode in (modes[1], modes[2], modes[0]):  # skip, all new, update
        dialog.mode_combo.set(mode)
        dialog.update_preview()
    dialog.on_click_import()

    assert len(imported) == 1 and len(imported[0]) == 2
    alpha = next(c for c in imported[0] if c.customer_id == "K-1001")
    assert alpha.practice_name == "Praxis Dr. Alpha"
    assert alpha.is_vip is True
