from pathlib import Path
from models.customer import Customer, Contact
from services.cobra_crm_import_service import CobraCrmImportService


def test_cobra_csv_parsing_and_mapping(tmp_path: Path):
    csv_content = (
        "Kunden-Nr;Firma;Ansprechpartner;Telefon;E-Mail;VIP;Version;VM-Nr;Instanz\n"
        "K-9001;Praxisklinik Sonnenhügel;Dr. Martin Frank;089-112233;frank@sonnenhuegel.de;Ja;v2026.1;109;1\n"
        "K-9002;Zahnzentrum Nord;Sabine Meyer;040-445566;info@zahnzentrum-nord.de;Nein;v2025.4;101;2\n"
    )
    csv_file = tmp_path / "cobra_export.csv"
    csv_file.write_text(csv_content, encoding="utf-8")

    rows, headers = CobraCrmImportService.parse_file(csv_file)
    assert len(rows) == 2
    assert "Firma" in headers

    mapping = CobraCrmImportService.auto_detect_mapping(headers)
    assert mapping["customer_id"] == "Kunden-Nr"
    assert mapping["practice_name"] == "Firma"
    assert mapping["contact_person"] == "Ansprechpartner"
    assert mapping["email"] == "E-Mail"
    assert mapping["is_vip"] == "VIP"

    customers = CobraCrmImportService.map_rows_to_customers(rows, mapping)
    assert len(customers) == 2
    c1 = customers[0]
    assert c1.customer_id == "K-9001"
    assert c1.practice_name == "Praxisklinik Sonnenhügel"
    assert c1.is_vip is True
    assert c1.contacts[0].name == "Dr. Martin Frank"
    assert c1.contacts[0].email == "frank@sonnenhuegel.de"


def test_cobra_duplicate_detection_and_merging(tmp_path: Path):
    existing = [
        Customer(
            customer_id="K-9001",
            practice_name="Praxisklinik Sonnenhügel (Alt)",
            contacts=[Contact(name="Dr. Frank Alt", email="old@sonnenhuegel.de")],
        )
    ]

    imported = [
        Customer(
            customer_id="K-9001",
            practice_name="Praxisklinik Sonnenhügel (Neu)",
            contacts=[Contact(name="Dr. Martin Frank", email="frank@sonnenhuegel.de")],
        ),
        Customer(
            customer_id="K-9003",
            practice_name="Hausarztpraxis Dr. Berg",
            contacts=[Contact(name="Dr. Berg", email="berg@hausarzt.de")],
        ),
    ]

    diff = CobraCrmImportService.compare_with_existing(imported, existing)
    assert len(diff["new"]) == 1
    assert diff["new"][0].customer_id == "K-9003"
    assert len(diff["duplicates"]) == 1
    assert diff["duplicates"][0]["imported"].customer_id == "K-9001"

    # Merge with update mode
    merged_update = CobraCrmImportService.merge_customers(existing, imported, mode="update")
    assert len(merged_update) == 2
    c1 = next(c for c in merged_update if c.customer_id == "K-9001")
    assert c1.practice_name == "Praxisklinik Sonnenhügel (Neu)"
    assert c1.contacts[0].email == "frank@sonnenhuegel.de"

    # Merge with skip mode
    merged_skip = CobraCrmImportService.merge_customers(existing, imported, mode="skip")
    assert len(merged_skip) == 2
    c1_skip = next(c for c in merged_skip if c.customer_id == "K-9001")
    assert c1_skip.practice_name == "Praxisklinik Sonnenhügel (Alt)"
