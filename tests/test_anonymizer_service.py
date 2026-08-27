import pytest
from models.case import Case, CaseCustomer
from services.anonymizer_service import PiiAnonymizer


def test_pii_anonymizer_basic_email_and_phone():
    anonymizer = PiiAnonymizer(enable_anonymization=True)
    text = "Bitte schicken Sie die Info an dr.mueller@praxis-gesund.de oder rufen Sie unter 089-12345678 an."
    
    anonymized, mapping = anonymizer.anonymize(text)
    
    assert "dr.mueller@praxis-gesund.de" not in anonymized
    assert "[EMAIL_1]" in anonymized
    assert mapping.get("[EMAIL_1]") == "dr.mueller@praxis-gesund.de"
    
    restored = anonymizer.deanonymize(anonymized, mapping)
    assert restored == text


def test_pii_anonymizer_case_context():
    anonymizer = PiiAnonymizer(enable_anonymization=True)
    case = Case(
        case_id="FALL-2026-99",
        customer=CaseCustomer(
            customer_id="KD-100",
            practice_name="Gemeinschaftspraxis Dr. Med. Sonnenstein",
            contact_person="Frau Sabine Meyer",
            email="kontakt@sonnenstein.de",
            phone="030-998877"
        )
    )
    
    prompt = (
        "Zusammenfassung für FALL-2026-99 von Gemeinschaftspraxis Dr. Med. Sonnenstein. "
        "Ansprechpartner ist Frau Sabine Meyer (kontakt@sonnenstein.de). "
        "Patient Herr Max Mustermann klagt über Fehler beim PVS-Import."
    )
    
    anonymized, mapping = anonymizer.anonymize(prompt, case=case)
    
    assert "FALL-2026-99" not in anonymized
    assert "Gemeinschaftspraxis Dr. Med. Sonnenstein" not in anonymized
    assert "Frau Sabine Meyer" not in anonymized
    assert "kontakt@sonnenstein.de" not in anonymized
    assert "Max Mustermann" not in anonymized
    
    restored = anonymizer.deanonymize(anonymized, mapping)
    assert restored == prompt


def test_pii_anonymizer_disabled():
    anonymizer = PiiAnonymizer(enable_anonymization=False)
    text = "Hallo dr.test@example.com"
    anonymized, mapping = anonymizer.anonymize(text)
    assert anonymized == text
    assert mapping == {}
