import pytest # type: ignore
import customtkinter as ctk
from models.case import Case, CaseCustomer, WorkflowStatus, Classification
from models.profile import UserProfile, AiSettings
from services.ai_service import AiService
from ui.dialogs.ai_assistant_dialog import AiAssistantDialog


def create_sample_case():
    return Case(
        case_id="FALL-2026-AI01",
        customer=CaseCustomer(
            customer_id="KD-8812",
            practice_name="Gemeinschaftspraxis Dr. Med. Schneider",
            contact_person="Frau Dr. Schneider",
        ),
        classification=Classification(
            title="eRezept Signaturfehler beim Kartenleser",
            schema_id="DEFAULT_SCHEMA",
        ),
        workflow_status=WorkflowStatus(
            board_column="IN_PROGRESS",
            current_actor="USER",
        ),
        form_data={
            "unformatted_description": "Der eRezept Signaturvorgang schlägt am Kartenterminal 3 mit Fehlercode KTR-402 ab.",
        },
    )


def test_ai_settings_serialization():
    settings = AiSettings(ollama_url="http://localhost:11434", model_name="llama3", enable_ai=True)
    d = settings.to_dict()
    assert d["ollama_url"] == "http://localhost:11434"
    assert d["model_name"] == "llama3"
    assert d["enable_ai"] is True

    restored = AiSettings.from_dict(d)
    assert restored.ollama_url == "http://localhost:11434"
    assert restored.model_name == "llama3"
    assert restored.enable_ai is True

    profile = UserProfile()
    p_dict = profile.to_dict()
    assert "ai_settings" in p_dict
    p_restored = UserProfile.from_dict(p_dict)
    assert p_restored.ai_settings.ollama_url == "http://localhost:11434"


def test_ai_service_rule_based_fallback():
    case = create_sample_case()
    service = AiService()

    # Rule-Based NLP Summary
    summary = service._generate_rule_based_summary(case)
    assert "📌 FALL-ZUSAMMENFASSUNG [FALL-2026-AI01]" in summary
    assert "Gemeinschaftspraxis Dr. Med. Schneider" in summary
    assert "eRezept Signaturfehler" in summary

    # Solution Suggestion Matching
    wiki_arts = [
        {"title": "eRezept Fehlerbehebung", "content": "Bei eRezept Fehlern SMC-B Karte prüfen."}
    ]
    solutions = service.suggest_solutions(case, wiki_articles=wiki_arts)
    assert len(solutions) >= 1
    assert any("eRezept" in s["title"] for s in solutions)

    # Response Drafting
    draft = service.generate_customer_response(case, user_name="Max Mustermann")
    assert "Frau Dr. Schneider" in draft
    assert "FALL-2026-AI01" in draft or "eRezept" in draft
    assert "Max Mustermann" in draft


def test_ai_assistant_dialog_lifecycle():
    import time
    root = ctk.CTk()
    root.withdraw()

    case = create_sample_case()
    profile = UserProfile()
    updated_cases = []

    def on_updated(c):
        updated_cases.append(c)

    dlg = AiAssistantDialog(
        root,
        case=case,
        profile=profile,
        on_case_updated=on_updated,
        wiki_articles=[{"title": "eRezept Hilfe", "content": "Kartenleser neustarten"}],
    )

    # Wait for async background worker to finish
    time.sleep(0.2)
    root.update()

    # Manually trigger summary and draft check
    dlg.summary_textbox.delete("1.0", "end")
    dlg.summary_textbox.insert("1.0", "Test Summary")

    # Test copy and timeline insertion
    dlg.append_summary_to_timeline()
    assert len(updated_cases) == 1
    assert len(case.timeline) == 1
    assert "🤖 KI-Zusammefassung" in case.timeline[0].note

    dlg.destroy()
    root.destroy()
