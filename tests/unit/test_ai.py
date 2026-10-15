"""AiService (Ollama/Gemini/rule-based fallback), AI settings persistence and the AI assistant dialog."""
import json
import time
from unittest.mock import MagicMock, patch

import pytest

from models.case import Case, CaseCustomer, Classification, TimelineEntry, WorkflowStatus
from models.customer import Contact, Customer
from models.profile import AiSettings, UserProfile
from services.ai_service import AiService


def _make_case(
    case_id="FALL-2026-TV01",
    practice_name="Praxis Dr. Meier",
    customer_id="KD-1234",
    contact_person="Frau Müller",
    title="Drucker druckt nicht",
    form_data=None,
    timeline=None,
    followup_at="",
    followup_note="",
    is_completed=False,
    current_actor="SUPPORT",
) -> Case:
    return Case(
        case_id=case_id,
        customer=CaseCustomer(customer_id=customer_id, practice_name=practice_name, contact_person=contact_person),
        classification=Classification(title=title, schema_id="DEFAULT_SCHEMA"),
        workflow_status=WorkflowStatus(
            board_column="IN_PROGRESS",
            current_actor=current_actor,
            followup_at=followup_at,
            followup_note=followup_note,
            is_completed=is_completed,
        ),
        form_data=form_data or {},
        timeline=timeline or [],
    )


@pytest.fixture
def offline_service() -> AiService:
    """AiService whose LLM never answers, so every call takes the rule-based fallback."""
    svc = AiService(ollama_url="http://127.0.0.1:1", model_name="test-model")
    svc._query_ollama = lambda *args, **kwargs: None
    return svc


def _urlopen_ctx(body: bytes = b"{}", status: int = 200) -> MagicMock:
    resp = MagicMock()
    resp.status = status
    resp.read.return_value = body
    ctx = MagicMock()
    ctx.__enter__.return_value = resp
    return ctx


# --- settings persistence ---------------------------------------------------

def test_ai_settings_and_customer_rules_survive_round_trip():
    settings = AiSettings(
        ollama_url="http://192.168.1.100:11434",
        model_name="mistral:7b",
        enable_ai=False,
        base_rules=["Immer im Sie-Stil antworten", "Regel 2"],
    )
    restored = AiSettings.from_dict(settings.to_dict())
    assert (restored.ollama_url, restored.model_name, restored.enable_ai) == ("http://192.168.1.100:11434", "mistral:7b", False)
    assert restored.base_rules == ["Immer im Sie-Stil antworten", "Regel 2"]

    profile = UserProfile()
    assert profile.ai_settings.enable_ai is True
    assert profile.ai_settings.use_modelfile_rules_for_gemini is False
    assert profile.ai_settings.ollama_url == "http://localhost:11434"
    profile.ai_settings.enable_ai = False
    profile.ai_settings.use_modelfile_rules_for_gemini = True
    reloaded = UserProfile.from_dict(profile.to_dict())
    assert reloaded.ai_settings.enable_ai is False
    assert reloaded.ai_settings.use_modelfile_rules_for_gemini is True

    rules = ["VORRANG: Duzen erwünscht (Herr Schmidt)", "Immer Betreff mit [DR-SCHMIDT] kennzeichnen"]
    cust = Customer(customer_id="KD-9912", practice_name="Praxis Dr. Schmidt", custom_ai_rules=rules,
                    contacts=[Contact(name="Herr Schmidt", email="schmidt@praxis.de")])
    restored_cust = Customer.from_dict(cust.to_dict())
    assert restored_cust.customer_id == "KD-9912"
    assert restored_cust.custom_ai_rules == rules


# --- system prompt ----------------------------------------------------------

def test_system_prompt_orders_base_practice_and_custom_rules_by_priority():
    custom = "Antworte ausschließlich in Form von 3 Stichpunkten und beende mit 'Viele Grüße'."
    prompt = AiService.build_system_prompt(
        base_rules=["Immer höflich antworten", "  Verwende Siezen als Anrede  ", "   "],
        practice_rules=["Duzen erwünscht für Ansprechpartner Dr. Schmidt", "Immer Kopie an den Praxismanager senden"],
        custom_instruction=custom,
    )
    assert "IT-Support-Assistent" in prompt
    assert "--- GLOBALE BASIS-REGELN ---" in prompt
    assert "1. Immer höflich antworten" in prompt
    assert "2. Verwende Siezen als Anrede" in prompt
    assert "3. " not in prompt.split("--- PRAXIS")[0], "whitespace-only rule was numbered"
    assert "--- PRAXIS-SPEZIFISCHE REGELN (VORRANGIG UND BINDEND!) ---" in prompt
    assert "Die folgenden Praxis-Regeln haben IMMER Vorrang vor den globalen Basis-Regeln" in prompt
    assert "2. Immer Kopie an den Praxismanager senden" in prompt
    assert "--- BENUTZERDEFINIERTE SONDERANWEISUNG (ALLERHÖCHSTE PRIORITÄT!) ---" in prompt
    assert "ALLERHÖCHSTE PRIORITÄT und übersteuert im Konfliktfall" in prompt
    assert prompt.find("Immer höflich") < prompt.find("Duzen erwünscht") < prompt.find(custom)


def test_system_prompt_without_rules_is_just_the_role():
    prompt = AiService.build_system_prompt(base_rules=[], practice_rules=[])
    assert "BASIS-REGELN" not in prompt and "PRAXIS-SPEZIFISCHE" not in prompt
    custom_role = "Du bist ein Abrechnungsexperte."
    assert AiService.build_system_prompt(default_role=custom_role) == custom_role


# --- rule-based summary -----------------------------------------------------

_TIMELINE_20 = [
    TimelineEntry(timestamp=f"2026-08-{i:02d}T10:00:00", author="Support", channel="PHONE_INBOUND",
                  note=f"Zeitleisten-Eintrag Nummer {i:02d}")
    for i in range(1, 21)
]


@pytest.mark.parametrize(
    "case_kwargs, expected, absent",
    [
        pytest.param(
            dict(case_id="FALL-2026-S01", practice_name="Orthopädie Zentrum Nord", customer_id="KD-9988",
                 title="eGK Kartenleser offline am Empfang"),
            ["FALL-2026-S01", "Orthopädie Zentrum Nord", "KD-9988", "eGK Kartenleser offline am Empfang",
             "1. PROBLEM-ÜBERSICHT:", "2. ZEITLEISTE & MASSNAHMEN:", "3. NÄCHSTER SCHRITT:",
             "Keine bisherigen Zeitleisten-Einträge", "ausstehend"],
            [],
            id="header-and-sections",
        ),
        pytest.param(
            dict(form_data={"unformatted_description": 'KTR-402: "Ungültige Zeichen" <script>x</script> ' + "A" * 500}),
            ["KTR-402", "Ungültige Zeichen", "..."], ["A" * 300], id="description-truncated",
        ),
        pytest.param(dict(timeline=_TIMELINE_20), ["Nummer 20", "Nummer 18"], ["Nummer 17", "Nummer 05"],
                     id="only-last-three-timeline-entries"),
        pytest.param(dict(is_completed=True), ["✓ Fall abgeschlossen"], [], id="completed"),
        pytest.param(dict(followup_at="2026-09-01T10:00:00", followup_note="Rückruf wegen Update"),
                     ["Geplante Wiedervorlage", "Rückruf wegen Update"], [], id="followup"),
        pytest.param(dict(title="Ärztliches Übergabe-Formular — Ñoño", practice_name="Praxis für Orthopädie & Rheumatologie"),
                     ["Ärztliches Übergabe-Formular — Ñoño", "Orthopädie & Rheumatologie"], [], id="unicode"),
        pytest.param(dict(title="", practice_name="", customer_id="", contact_person=""),
                     ["📌 FALL-ZUSAMMENFASSUNG"], [], id="empty-case"),
    ],
)
def test_rule_based_summary(offline_service, case_kwargs, expected, absent):
    summary = offline_service._generate_rule_based_summary(_make_case(**case_kwargs))
    assert summary.startswith("📌 FALL-ZUSAMMENFASSUNG")
    for text in expected:
        assert text in summary
    for text in absent:
        assert text not in summary


def test_summarize_case_falls_back_to_rules_when_llm_is_offline(offline_service):
    summary = offline_service.summarize_case(_make_case(title="Terminkalender-Ansicht eingefroren", current_actor="USER"))
    assert "FALL-ZUSAMMENFASSUNG" in summary
    assert "Terminkalender-Ansicht eingefroren" in summary
    assert "Zuständig: USER" in summary, "an unknown actor is shown verbatim"


# --- customer response draft ------------------------------------------------

@pytest.mark.parametrize(
    "contact, practice, greeting",
    [
        ("Dr. med. Müller-Lüdenscheidt", "Praxis X", "Sehr geehrte/r Dr. med. Müller-Lüdenscheidt,"),
        ("", "Gemeinschaftspraxis Linden", "Sehr geehrte/r Gemeinschaftspraxis Linden,"),
        ("", "", "Sehr geehrte Damen und Herren,"),
    ],
)
def test_response_draft_greets_the_most_specific_name(offline_service, contact, practice, greeting):
    response = offline_service.generate_customer_response(_make_case(contact_person=contact, practice_name=practice))
    assert response.startswith(greeting)
    assert "Mit freundlichen Grüßen" in response
    assert response.rstrip().endswith("Ihr Support-Team")


def test_response_draft_carries_title_intent_and_sender(offline_service):
    response = offline_service.generate_customer_response(
        _make_case(title="Abrechnungslauf Q3 bricht ab"), intent="Wir haben das Problem behoben.", user_name="Support-Team Süd",
    )
    assert "Abrechnungslauf Q3 bricht ab" in response
    assert "Wir haben das Problem behoben." in response
    assert response.rstrip().endswith("Support-Team Süd")


# --- solution suggestions ---------------------------------------------------

@pytest.mark.parametrize(
    "title, description, wiki, expected_titles",
    [
        ("Import", "Cobra CRM Schnittstelle meldet Fehler beim Import", None, ["COBRA"]),
        ("eRezept Signaturfehler", "", None, ["eRezept"]),
        ("LDT Laborbefund kommt nicht an", "", None, ["LDT"]),
        ("cobra import", "Nach cobra Import funktioniert das eRezept nicht mehr", None, ["COBRA", "eRezept"]),
        ("Drucker offline seit heute morgen", "",
         [{"title": "Drucker Fehlerbehebung", "content": "Drucker-Spooler Dienst neu starten."}], ["Wiki: Drucker"]),
        ("Allgemeine Anfrage", "Allgemeines Problem", None, ["Standard-Diagnose"]),
    ],
)
def test_suggest_solutions_matches_keywords_and_wiki(offline_service, title, description, wiki, expected_titles):
    case = _make_case(title=title, form_data={"unformatted_description": description})
    solutions = offline_service.suggest_solutions(case, wiki_articles=wiki)
    titles = " ".join(s["title"] for s in solutions)
    for fragment in expected_titles:
        assert fragment in titles
    for sol in solutions:
        assert set(sol) == {"title", "snippet", "confidence", "source"}
        assert sol["confidence"].endswith("%")


# --- providers ---------------------------------------------------------------

def test_gemini_query_sends_anonymized_text_and_restores_real_names():
    svc = AiService(provider="GEMINI", gemini_api_key="test_fake_key_123", gemini_model="gemini-1.5-flash",
                    enable_anonymization=True)
    case = Case(case_id="FALL-2026-10", customer=CaseCustomer(
        customer_id="KD-55", practice_name="Praxis Dr. Med. Hoffmann",
        contact_person="Herr Klaus Hoffmann", email="hoffmann@praxis.de"))
    answer = {"candidates": [{"content": {"parts": [
        {"text": "Sehr geehrte Damen und Herren,\n\nwir haben das Problem für [PRAXIS_1] bezüglich [CASE_ID_1] analysiert."}
    ]}}]}

    with patch("urllib.request.urlopen", return_value=_urlopen_ctx(json.dumps(answer).encode())) as urlopen:
        result = svc.summarize_case(case)

    req = urlopen.call_args[0][0]
    assert "generativelanguage.googleapis.com" in req.full_url and "test_fake_key_123" in req.full_url
    body = req.data.decode("utf-8")
    assert "Praxis Dr. Med. Hoffmann" not in body and "[PRAXIS_1]" in body
    assert "Praxis Dr. Med. Hoffmann" in result and "FALL-2026-10" in result
    assert "[PRAXIS_1]" not in result


def test_gemini_status_accepts_a_valid_key():
    svc = AiService(provider="GEMINI", gemini_api_key="valid_key")
    with patch("urllib.request.urlopen", return_value=_urlopen_ctx()):
        ok, msg = svc.check_gemini_status()
    assert ok is True and "gültig" in msg


def test_ollama_model_management():
    svc = AiService(ollama_url="http://localhost:11434", model_name="qwen3.5:9b")

    with patch.object(svc, "check_ollama_status", return_value=(True, ["qwen3.5:9b", "llama3:latest"])):
        assert svc.get_available_models() == ["qwen3.5:9b", "llama3:latest"]

    with patch("urllib.request.urlopen", return_value=_urlopen_ctx(b'{"models": [{"name": "qwen3.5:9b"}]}')):
        assert svc.get_running_models() == ["qwen3.5:9b"]

    with patch("urllib.request.urlopen", return_value=_urlopen_ctx(b'{"done": true}')):
        ok, msg = svc.preload_model("qwen3.5:9b")
        assert ok is True and "geladen" in msg
        ok, msg = svc.unload_model("qwen3.5:9b")
        assert ok is True and "entladen" in msg

    with patch("shutil.which", return_value="C:\\Program Files\\Ollama\\ollama.exe"), patch("subprocess.Popen") as popen:
        ok, msg = svc.start_ollama_server()
    assert ok is True and "gestartet" in msg
    popen.assert_called_once()

    with patch("subprocess.run") as run:
        ok, msg = svc.stop_ollama_server()
    assert ok is True and "beendet" in msg and run.called


def test_create_pvs_support_model_switches_to_the_new_model(tmp_path):
    modelfile = tmp_path / "Modelfile"
    modelfile.write_text('FROM qwen3.5:9b\nSYSTEM "You are a support assistant."', encoding="utf-8")
    svc = AiService(ollama_url="http://localhost:11434")

    with patch.object(svc, "get_available_models", return_value=["qwen3.5:9b"]), \
            patch("urllib.request.urlopen", return_value=_urlopen_ctx(b'{"status": "success"}')):
        ok, msg = svc.create_pvs_support_model(str(modelfile))

    assert ok is True and "erfolgreich erstellt" in msg
    assert svc.model_name == "pvs-support"


# --- assistant dialog --------------------------------------------------------

def test_assistant_dialog_appends_summary_to_timeline(root):
    from ui.dialogs.ai_assistant_dialog import AiAssistantDialog

    case = _make_case(case_id="FALL-2026-AI01", title="eRezept Signaturfehler beim Kartenleser",
                      form_data={"unformatted_description": "Signaturvorgang schlägt mit KTR-402 fehl."})
    updated = []
    dlg = AiAssistantDialog(root, case=case, profile=UserProfile(), on_case_updated=updated.append,
                            wiki_articles=[{"title": "eRezept Hilfe", "content": "Kartenleser neustarten"}])
    time.sleep(0.2)  # let the status/solution worker threads report back
    root.update()

    dlg.summary_textbox.delete("1.0", "end")
    dlg.summary_textbox.insert("1.0", "Test Summary")
    dlg.append_summary_to_timeline()

    assert updated == [case]
    assert len(case.timeline) == 1
    assert "🤖 KI-Zusammefassung" in case.timeline[0].note
    dlg.destroy()
