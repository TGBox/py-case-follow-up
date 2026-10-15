"""Cobra CRM import: file parsing, column auto-mapping, extended Customer fields, duplicate detection and merging."""
from pathlib import Path

import pytest

from models.customer import Contact, Customer
from services.cobra_crm_import_service import CobraCrmImportService as Cobra


def _import(tmp_path: Path, content: str):
    csv_file = tmp_path / "cobra_export.csv"
    csv_file.write_text(content, encoding="utf-8")
    rows, headers = Cobra.parse_file(csv_file)
    mapping = Cobra.auto_detect_mapping(headers)
    return rows, headers, mapping, Cobra.map_rows_to_customers(rows, mapping)


def test_classic_export_with_contact_and_vip(tmp_path):
    rows, headers, mapping, customers = _import(tmp_path, (
        "Kunden-Nr;Firma;Ansprechpartner;Telefon;E-Mail;VIP;Version;VM-Nr;Instanz\n"
        "K-9001;Praxisklinik Sonnenhügel;Dr. Martin Frank;089-112233;frank@sonnenhuegel.de;Ja;v2026.1;109;1\n"
        "K-9002;Zahnzentrum Nord;Sabine Meyer;040-445566;info@zahnzentrum-nord.de;Nein;v2025.4;101;2\n"
    ))
    assert len(rows) == 2 and "Firma" in headers
    assert {k: mapping[k] for k in ("customer_id", "practice_name", "contact_person", "email", "is_vip")} == {
        "customer_id": "Kunden-Nr", "practice_name": "Firma", "contact_person": "Ansprechpartner",
        "email": "E-Mail", "is_vip": "VIP",
    }
    c1, c2 = customers
    assert (c1.customer_id, c1.practice_name, c1.is_vip) == ("K-9001", "Praxisklinik Sonnenhügel", True)
    assert (c1.contacts[0].name, c1.contacts[0].email) == ("Dr. Martin Frank", "frank@sonnenhuegel.de")
    assert c2.is_vip is False


_EXPECTED_18 = {
    # field: (header, value)
    "salutation": ("Anrede", "Frau"), "last_name": ("Nachname", "Dr. Müller"), "first_name": ("Vorname", "Sabine"),
    "street": ("Straße", "Bahnhofstraße 5"), "zip_code": ("PLZ", "10115"), "city": ("Ort", "Berlin"),
    "vnum1": ("VNUM1", "9001"), "dsc": ("DSC", "OLD_AL"), "dsc_neu": ("DSCNEU", "NEW_AL"),
    "practice_name": ("Praxisname", "Praxis Dr. Müller"), "practice_name_old": ("Praxisname_alt", "Praxis Dr. Alt"),
    "phone_main": ("Telefon", "030-111"), "phone_direct": ("Telefon direkt", "030-112"),
    "phone_private": ("Telefon privat", "030-113"), "phone2": ("Telefon2", "030-114"), "phone3": ("Telefon3", "030-115"),
    "mobile": ("Mobil", "0160-999"), "mobile_private": ("Mobil privat", "0160-888"),
}


def test_full_18_column_export_maps_every_field(tmp_path):
    header = ";".join(h for h, _ in _EXPECTED_18.values())
    values = ";".join(v for _, v in _EXPECTED_18.values())
    rows, headers, mapping, customers = _import(tmp_path, f"{header}\n{values}\n")

    assert len(rows) == 1 and len(headers) == 18
    (c,) = customers
    for field, (col, value) in _EXPECTED_18.items():
        assert mapping[field] == col
        assert getattr(c, field) == value
    assert c.customer_id == "9001", "VNUM1 doubles as customer id"
    assert c.contact_person == "Frau Sabine Dr. Müller"


def test_three_email_columns(tmp_path):
    _rows, _headers, mapping, (c,) = _import(tmp_path, (
        "VNUM1;Praxisname;E-Mail;E-Mail 2;E-Mail 3\n"
        "9002;Zahnzentrum;zahn@nord.de;info@nord.de;empfang@nord.de\n"
    ))
    assert (mapping["email_address"], mapping["email2"], mapping["email3"]) == ("E-Mail", "E-Mail 2", "E-Mail 3")
    assert c.all_emails == ["zahn@nord.de", "info@nord.de", "empfang@nord.de"]


def test_customer_extended_fields_round_trip_and_derived_properties():
    c = Customer(
        customer_id="K-1001", vnum1="9988", practice_name="Gemeinschaftspraxis Dr. Muster",
        practice_name_old="Praxis Muster alt", salutation="Dr. med.", first_name="Max", last_name="Mustermann",
        street="Hauptstraße 12", zip_code="70173", city="Stuttgart", phone_main="0711-123456",
        email_address="max@musterpraxis.de", email2="info@musterpraxis.de", email3="rezeption@musterpraxis.de",
        website="https://musterpraxis.de", system_version="2026.2", dsc="DSC-DATA-AL", dsc_neu="DSCNEU-2026",
        is_vip=True, additional_contacts=["Dr. Anna Schmidt", "Sabine Helfer"],
    )
    for cust in (c, Customer.from_dict(c.to_dict())):
        assert cust.contact_person == "Dr. med. Max Mustermann"
        assert cust.email == "max@musterpraxis.de"
        assert cust.all_emails == ["max@musterpraxis.de", "info@musterpraxis.de", "rezeption@musterpraxis.de"]
        assert cust.phone == "0711-123456"
        assert cust.full_address == "Hauptstraße 12, 70173 Stuttgart"
        assert (cust.vnum1, cust.practice_name_old, cust.dsc, cust.dsc_neu) == ("9988", "Praxis Muster alt", "DSC-DATA-AL", "DSCNEU-2026")
        assert cust.additional_contacts == ["Dr. Anna Schmidt", "Sabine Helfer"]


def test_compare_with_existing_splits_new_and_duplicates():
    existing = [Customer(customer_id="K-9001", practice_name="Alt")]
    imported = [Customer(customer_id="K-9001", practice_name="Neu"), Customer(customer_id="K-9003", practice_name="Berg")]
    diff = Cobra.compare_with_existing(imported, existing)
    assert [c.customer_id for c in diff["new"]] == ["K-9003"]
    assert [d["imported"].customer_id for d in diff["duplicates"]] == ["K-9001"]


@pytest.mark.parametrize("mode, expected_name, expected_email", [
    ("update", "Praxisklinik Sonnenhügel (Neu)", "frank@sonnenhuegel.de"),
    ("skip", "Praxisklinik Sonnenhügel (Alt)", "old@sonnenhuegel.de"),
])
def test_merge_modes(mode, expected_name, expected_email):
    existing = [Customer(customer_id="K-9001", practice_name="Praxisklinik Sonnenhügel (Alt)", phone_main="000",
                         contacts=[Contact(name="Dr. Frank Alt", email="old@sonnenhuegel.de")])]
    imported = [
        Customer(customer_id="K-9001", practice_name="Praxisklinik Sonnenhügel (Neu)", phone_main="030-111",
                 phone_direct="030-112", dsc_neu="NEW_AL",
                 contacts=[Contact(name="Dr. Martin Frank", email="frank@sonnenhuegel.de")]),
        Customer(customer_id="K-9003", practice_name="Hausarztpraxis Dr. Berg"),
    ]
    merged = {c.customer_id: c for c in Cobra.merge_customers(existing, imported, mode=mode)}
    assert set(merged) == {"K-9001", "K-9003"}
    m = merged["K-9001"]
    assert m.practice_name == expected_name
    assert m.contacts[0].email == expected_email
    if mode == "update":
        assert (m.phone_main, m.phone_direct, m.dsc_neu) == ("030-111", "030-112", "NEW_AL")
