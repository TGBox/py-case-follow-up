import pytest # type: ignore
from models.customer import Customer, Contact
from models.profile import UserProfile, AiSettings
from services.ai_service import AiService


def test_ai_settings_base_rules_serialization():
    settings = AiSettings(
        ollama_url="http://localhost:11434",
        model_name="llama3",
        base_rules=["Immer im Sie-Stil antworten", "Keine Fachbegriffe ohne Erläuterung"],
    )
    d = settings.to_dict()
    assert d["base_rules"] == ["Immer im Sie-Stil antworten", "Keine Fachbegriffe ohne Erläuterung"]

    restored = AiSettings.from_dict(d)
    assert len(restored.base_rules) == 2
    assert restored.base_rules[0] == "Immer im Sie-Stil antworten"


def test_customer_custom_ai_rules_serialization():
    cust = Customer(
        customer_id="KD-9912",
        practice_name="Praxis Dr. Schmidt",
        custom_ai_rules=["VORRANG: Duzen erwünscht (Herr Schmidt)", "Immer Betreff mit [DR-SCHMIDT] kennzeichnen"],
        contacts=[Contact(name="Herr Schmidt", email="schmidt@praxis.de")],
    )
    d = cust.to_dict()
    assert "custom_ai_rules" in d
    assert len(d["custom_ai_rules"]) == 2

    restored = Customer.from_dict(d)
    assert restored.customer_id == "KD-9912"
    assert restored.custom_ai_rules == ["VORRANG: Duzen erwünscht (Herr Schmidt)", "Immer Betreff mit [DR-SCHMIDT] kennzeichnen"]


def test_hierarchical_system_prompt_builder():
    base_rules = ["Immer höflich antworten", "Verwende Siezen als Anrede"]
    practice_rules = ["Duzen erwünscht für Ansprechpartner Dr. Schmidt", "Immer Kopie an den Praxismanager senden"]

    sys_prompt = AiService.build_system_prompt(base_rules=base_rules, practice_rules=practice_rules)

    # Check headings
    assert "--- GLOBALE BASIS-REGELN ---" in sys_prompt
    assert "--- PRAXIS-SPEZIFISCHE REGELN (VORRANGIG UND BINDEND!) ---" in sys_prompt

    # Check base rules inclusion
    assert "1. Immer höflich antworten" in sys_prompt
    assert "2. Verwende Siezen als Anrede" in sys_prompt

    # Check practice rules inclusion and override warning
    assert "Die folgenden Praxis-Regeln haben IMMER Vorrang vor den globalen Basis-Regeln" in sys_prompt
    assert "1. Duzen erwünscht für Ansprechpartner Dr. Schmidt" in sys_prompt
    assert "2. Immer Kopie an den Praxismanager senden" in sys_prompt
