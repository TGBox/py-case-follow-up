"""Tests for 18-column Cobra CRM import, extended Customer fields, and merge logic."""

import pytest
from pathlib import Path
from models.customer import Customer
from services.cobra_crm_import_service import CobraCrmImportService


def test_customer_model_extended_fields():
    """Verify Customer model serializes and deserializes all 18 Cobra fields properly."""
    c = Customer(
        customer_id="K-1001",
        vnum1="9988",
        practice_name="Gemeinschaftspraxis Dr. Muster",
        practice_name_old="Praxis Muster alt",
        salutation="Dr. med.",
        first_name="Max",
        last_name="Mustermann",
        street="Hauptstraße 12",
        zip_code="70173",
        city="Stuttgart",
        phone_main="0711-123456",
        phone_direct="0711-123457",
        phone_private="0170-1111111",
        phone2="0711-123458",
        phone3="0711-123459",
        mobile="0171-2222222",
        mobile_private="0172-3333333",
        email_address="max@musterpraxis.de",
        email2="info@musterpraxis.de",
        email3="rezeption@musterpraxis.de",
        website="https://musterpraxis.de",
        system_version="2026.2",
        dsc="DSC-DATA-AL",
        dsc_neu="DSCNEU-2026",
        is_vip=True,
        additional_contacts=["Dr. Anna Schmidt", "Sabine Helfer"],
    )

    # Test properties
    assert c.contact_person == "Dr. med. Max Mustermann"
    assert c.email == "max@musterpraxis.de"
    assert c.all_emails == ["max@musterpraxis.de", "info@musterpraxis.de", "rezeption@musterpraxis.de"]
    assert c.phone == "0711-123456"
    assert c.full_address == "Hauptstraße 12, 70173 Stuttgart"

    # Test dict conversion
    data = c.to_dict()
    assert data["customer_id"] == "K-1001"
    assert data["vnum1"] == "9988"
    assert data["practice_name_old"] == "Praxis Muster alt"
    assert data["street"] == "Hauptstraße 12"
    assert data["dsc"] == "DSC-DATA-AL"
    assert data["dsc_neu"] == "DSCNEU-2026"
    assert len(data["additional_contacts"]) == 2

    # Reconstruct
    c2 = Customer.from_dict(data)
    assert c2.customer_id == "K-1001"
    assert c2.contact_person == "Dr. med. Max Mustermann"
    assert c2.full_address == "Hauptstraße 12, 70173 Stuttgart"
    assert c2.dsc_neu == "DSCNEU-2026"


def test_cobra_import_service_18_column_parsing(tmp_path: Path):
    """Test importing a CSV file with all 18 Cobra export columns."""
    csv_file = tmp_path / "cobra_export.csv"
    csv_file.write_text(
        "Anrede;Nachname;Vorname;Straße;PLZ;Ort;VNUM1;DSC;DSCNEU;Praxisname;Praxisname_alt;Telefon;Telefon direkt;Telefon privat;Telefon2;Telefon3;Mobil;Mobil privat\n"
        "Frau;Dr. Müller;Sabine;Bahnhofstraße 5;10115;Berlin;9001;OLD_AL;NEW_AL;Praxis Dr. Müller;Praxis Dr. Alt;030-111;030-112;030-113;030-114;030-115;0160-999;0160-888\n",
        encoding="utf-8",
    )

    rows, headers = CobraCrmImportService.parse_file(csv_file)
    assert len(rows) == 1
    assert len(headers) == 18

    mapping = CobraCrmImportService.auto_detect_mapping(headers)
    assert mapping["vnum1"] == "VNUM1"
    assert mapping["practice_name"] == "Praxisname"
    assert mapping["practice_name_old"] == "Praxisname_alt"
    assert mapping["salutation"] == "Anrede"
    assert mapping["first_name"] == "Vorname"
    assert mapping["last_name"] == "Nachname"
    assert mapping["street"] == "Straße"
    assert mapping["zip_code"] == "PLZ"
    assert mapping["city"] == "Ort"
    assert mapping["phone_main"] == "Telefon"
    assert mapping["phone_direct"] == "Telefon direkt"
    assert mapping["phone_private"] == "Telefon privat"
    assert mapping["phone2"] == "Telefon2"
    assert mapping["phone3"] == "Telefon3"
    assert mapping["mobile"] == "Mobil"
    assert mapping["mobile_private"] == "Mobil privat"
    assert mapping["dsc"] == "DSC"
    assert mapping["dsc_neu"] == "DSCNEU"

    customers = CobraCrmImportService.map_rows_to_customers(rows, mapping)
    assert len(customers) == 1
    c = customers[0]
    assert c.customer_id == "9001"
    assert c.vnum1 == "9001"
    assert c.practice_name == "Praxis Dr. Müller"
    assert c.practice_name_old == "Praxis Dr. Alt"
    assert c.contact_person == "Frau Sabine Dr. Müller"
    assert c.street == "Bahnhofstraße 5"
    assert c.zip_code == "10115"
    assert c.city == "Berlin"
    assert c.phone_main == "030-111"
    assert c.phone_direct == "030-112"
    assert c.phone_private == "030-113"
    assert c.phone2 == "030-114"
    assert c.phone3 == "030-115"
    assert c.mobile == "0160-999"
    assert c.mobile_private == "0160-888"
    assert c.dsc == "OLD_AL"
    assert c.dsc_neu == "NEW_AL"


def test_cobra_import_service_merge():
    """Verify update merge mode correctly updates existing practice fields."""
    existing = [
        Customer(
            customer_id="9001",
            practice_name="Alte Praxis",
            phone_main="000",
        )
    ]
    imported = [
        Customer(
            customer_id="9001",
            vnum1="9001",
            practice_name="Praxis Dr. Müller",
            phone_main="030-111",
            phone_direct="030-112",
            dsc_neu="NEW_AL",
        )
    ]

    merged = CobraCrmImportService.merge_customers(existing, imported, mode="update")
    assert len(merged) == 1
    m = merged[0]
    assert m.practice_name == "Praxis Dr. Müller"
    assert m.phone_main == "030-111"
    assert m.phone_direct == "030-112"
    assert m.dsc_neu == "NEW_AL"


def test_cobra_import_service_email_column_mapping(tmp_path: Path):
    """Test importing CSV with E-Mail, E-Mail 2, and E-Mail 3 columns."""
    csv_file = tmp_path / "cobra_emails.csv"
    csv_file.write_text(
        "VNUM1;Praxisname;E-Mail;E-Mail 2;E-Mail 3\n"
        "9002;Zahnzentrum;zahn@nord.de;info@nord.de;empfang@nord.de\n",
        encoding="utf-8",
    )

    rows, headers = CobraCrmImportService.parse_file(csv_file)
    mapping = CobraCrmImportService.auto_detect_mapping(headers)
    assert mapping["email_address"] == "E-Mail"
    assert mapping["email2"] == "E-Mail 2"
    assert mapping["email3"] == "E-Mail 3"

    customers = CobraCrmImportService.map_rows_to_customers(rows, mapping)
    assert len(customers) == 1
    c = customers[0]
    assert c.email_address == "zahn@nord.de"
    assert c.email2 == "info@nord.de"
    assert c.email3 == "empfang@nord.de"
    assert c.all_emails == ["zahn@nord.de", "info@nord.de", "empfang@nord.de"]
