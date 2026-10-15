"""I18nService (fallback chain, formatting, listeners, locales dir), LocalizedDict, localized constants and language persistence."""

import json
import sys
from pathlib import Path

import pytest

import services.i18n_service as i18n_module
from constants import DIALOG_TITLES, STATUS_MESSAGES, UI_BUTTON_TEXTS, get_localized_menu_options_stammdaten
from enums import Actor, Channel, UrgencyLevel, get_actor_display, get_channel_display, get_layout_display
from models.profile import UISettings
from services.i18n_service import I18nService, LocalizedDict, get_i18n, tr

REPO = Path(__file__).resolve().parents[2]


def _service(locales: Path, **langs: dict) -> I18nService:
    locales.mkdir(parents=True, exist_ok=True)
    for lang in ("de", "en", "sv"):
        (locales / f"{lang}.json").write_text(json.dumps(langs.get(lang, {}), ensure_ascii=False), encoding="utf-8")
    return I18nService(locales_dir=locales)


@pytest.fixture
def isolated_singleton():
    """Lets a test point the global singleton (used by module-level tr()) at its own service."""
    previous = i18n_module._i18n_instance
    yield
    i18n_module._i18n_instance = previous


# --- I18nService ---------------------------------------------------------------

def test_tr_fallback_chain_current_then_german_then_default_then_key(tmp_path):
    svc = _service(
        tmp_path / "locales",
        de={"greeting": "Grüße {name} 🩺", "only_de": {"x": "Nur Deutsch"}},
        en={"greeting": "Hello {name} 🩺"},
        sv={"greeting": "Hälsningar {name} å, ä, ö"},
    )
    assert svc.current_language == "de"
    assert svc.tr("greeting", name="Anna") == "Grüße Anna 🩺"
    svc.current_language = "en"
    assert svc.tr("greeting", name="Anna") == "Hello Anna 🩺"
    svc.current_language = "sv"
    assert svc.tr("greeting", name="Anna") == "Hälsningar Anna å, ä, ö"
    assert svc.tr("only_de.x") == "Nur Deutsch"  # missing in sv -> German
    assert svc.tr("only_de.missing", default="Default") == "Default"
    assert svc.tr("unknown.system.path") == "unknown.system.path"


def test_tr_format_ignores_extra_kwargs_and_survives_missing_ones(tmp_path):
    svc = _service(tmp_path / "locales", de={"msg": "Hallo {user}, Fall #{case_id}!"})
    assert svc.tr("msg", user="Bob", case_id=99, extra="ignored") == "Hallo Bob, Fall #99!"
    # Missing kwarg -> .format() raises internally, tr() returns the unformatted string.
    assert svc.tr("msg", user="Charlie") == "Hallo {user}, Fall #{case_id}!"


def test_language_setter_notifies_listeners_only_on_real_change(tmp_path):
    svc = I18nService(locales_dir=tmp_path)
    received: list[str] = []
    svc.register_listener(received.append)

    svc.current_language = "de"  # same value -> no-op
    svc.current_language = "fr"  # unsupported -> ignored
    assert svc.current_language == "de" and received == []

    svc.current_language = "en"
    svc.current_language = "sv"
    assert received == ["en", "sv"]

    svc.unregister_listener(received.append)
    svc.current_language = "de"
    assert received == ["en", "sv"]


def test_real_locales_resolve_in_all_languages():
    i18n = get_i18n()
    expected = {"de": "💾 Speichern", "en": "💾 Save", "sv": "💾 Spara"}
    for lang, save in expected.items():
        i18n.current_language = lang
        assert tr("cockpit.save") == save
        assert tr("dialog_titles.followup") != "dialog_titles.followup"
    i18n.current_language = "sv"
    assert tr("cockpit.archive") == "📦 Arkivera"
    assert tr("cockpit.complete") == "✓ Klar"


@pytest.mark.parametrize("lang,expected", [
    ("de", "💻 Entwickler (1)"), ("en", "💻 Developer (1)"), ("sv", "💻 Utvecklare (1)"),
])
def test_real_locale_counter_placeholder_is_formatted(lang, expected):
    get_i18n().current_language = lang
    assert tr("board.col_dev", count=1) == expected


def test_default_locales_dir_in_source_checkout(monkeypatch):
    monkeypatch.setattr(sys, "frozen", False, raising=False)
    monkeypatch.delattr(sys, "_MEIPASS", raising=False)
    svc = I18nService()
    assert svc.locales_dir == REPO / "locales"
    assert all((svc.locales_dir / f"{lang}.json").exists() for lang in ("de", "en", "sv"))


def test_default_locales_dir_in_frozen_bundle(tmp_path, monkeypatch):
    """Regression: a PyInstaller build looked outside sys._MEIPASS and was pinned to German defaults."""
    bundle = tmp_path / "mei_bundle"
    _service(
        bundle / "locales",
        de={"common": {"ok": "OK_DE"}}, en={"common": {"ok": "OK_EN"}}, sv={"common": {"ok": "OK_SV"}},
    )
    monkeypatch.setattr(sys, "frozen", True, raising=False)
    monkeypatch.setattr(sys, "_MEIPASS", str(bundle), raising=False)

    svc = I18nService(locales_dir=None)
    assert svc.locales_dir == bundle / "locales"
    for lang in ("de", "en", "sv"):
        svc.current_language = lang
        assert svc.tr("common.ok") == f"OK_{lang.upper()}"


# --- LocalizedDict and localized constants -----------------------------------

def test_localized_dict_resolves_dynamically_and_falls_back_to_initial_value(tmp_path, isolated_singleton):
    i18n_module._i18n_instance = _service(
        tmp_path / "locales", de={"widgets": {"save": "Speichern"}}, en={"widgets": {"save": "Save"}},
    )
    texts = LocalizedDict("widgets", {"save": "Save (fallback)", "cancel": "Cancel (fallback)"})

    assert texts["save"] == "Speichern"
    assert texts["cancel"] == "Cancel (fallback)"  # untranslated -> initial value, not raw key

    i18n_module._i18n_instance.current_language = "en"
    assert texts["save"] == "Save"
    assert texts.values() == ["Save", "Cancel (fallback)"]
    assert texts.items() == [("save", "Save"), ("cancel", "Cancel (fallback)")]


LOCALIZED_EXPECTATIONS = {
    "de": dict(new_case="Neuen Support-Fall anlegen", profile="Profil", save="Speichern", cancel="Abbrechen",
               delete=("Löschen",), saved=("gespeichert",), phone=("Telefon",), dev="Entwicklung",
               board=("Kanban",), practices="Praxen", colleagues=("Mitarbeiter",)),
    "en": dict(new_case="Create New Support Case", profile="Profile", save="Save", cancel="Cancel",
               delete=("Delete",), saved=("saved",), phone=("Phone", "Telephone"), dev="Development",
               board=("Board", "Kanban"), practices="Practices", colleagues=("Colleagues",)),
    "sv": dict(new_case="Skapa nytt supportärende", profile="Profil", save="Spara", cancel="Avbryt",
               delete=("Ta bort", "Radera"), saved=("sparad", "sparats"), phone=("Telefon",), dev="Utveckling",
               board=("Tavla", "Kanban"), practices="Mottagningar", colleagues=("Kolleger", "Medarbetare")),
}


@pytest.mark.parametrize("lang", ["de", "en", "sv"])
def test_localized_constants_and_enum_helpers_follow_language(lang):
    """Module-level LocalizedDicts and display helpers re-resolve without re-import."""
    exp = LOCALIZED_EXPECTATIONS[lang]
    get_i18n().current_language = lang

    assert DIALOG_TITLES["new_case"] == exp["new_case"]
    assert exp["profile"] in DIALOG_TITLES["profile_settings"]
    assert UI_BUTTON_TEXTS["save"] == exp["save"]
    assert UI_BUTTON_TEXTS["cancel"] == exp["cancel"]
    assert UI_BUTTON_TEXTS["delete"] in exp["delete"]
    assert any(s in STATUS_MESSAGES["profile_saved"] for s in exp["saved"])
    assert any(s in get_channel_display("PHONE_INBOUND") for s in exp["phone"])
    assert any(s in get_channel_display(Channel.PHONE_INBOUND) for s in exp["phone"])
    assert "Hotline" in get_actor_display("SUPPORT")
    assert exp["dev"] in get_actor_display("DEVELOPMENT")
    assert "Cockpit" in get_layout_display("COCKPIT")
    assert any(s in get_layout_display("BOARD") for s in exp["board"])
    menu = get_localized_menu_options_stammdaten()
    assert any(exp["practices"] in opt for opt in menu)
    assert any(word in opt for opt in menu for word in exp["colleagues"])
    if lang == "de":
        assert "E-Mail" in get_channel_display("EMAIL")
    if lang == "en":
        assert "saved" in STATUS_MESSAGES["customer_saved"]


# --- Language persistence and non-ASCII content ------------------------------

def test_ui_settings_language_round_trip_and_invalid_fallback():
    assert UISettings.from_dict(UISettings(language="en").to_dict()).language == "en"
    assert UISettings.from_dict({"language": "invalid_lang"}).language == "de"


def test_language_choice_survives_app_restart(config):
    from services.storage_service import StorageService

    storage = StorageService(config)
    profile = storage.load_profile()
    assert profile.ui_settings.language in ("de", "")
    profile.user.name = "Sven Svensson"

    # Two quick changes: the pending debounced save is replaced, the last choice wins.
    for lang in ("sv", "en"):
        profile.ui_settings.language = lang
        storage.save_profile(profile)
    assert storage.load_profile().ui_settings.language == "en"
    storage.flush_all_saves()
    assert StorageService(config).load_profile(use_cache=False).ui_settings.language == "en"

    profile.ui_settings.language = "sv"
    storage.save_profile(profile, sync=True)
    reloaded = StorageService(config).load_profile(use_cache=False)  # simulated restart
    assert (reloaded.ui_settings.language, reloaded.user.name) == ("sv", "Sven Svensson")


def test_swedish_case_survives_storage_export_and_ics(storage, config, tmp_path):
    """Non-ASCII (å, ä, ö) case data must round-trip through storage, export rendering and .ics files."""
    from enums import TargetType
    from models.case import Case, CaseCustomer, Classification, TimelineEntry, WorkflowStatus
    from models.export_template import ExportTemplate
    from services.calendar_email_service import CalendarEmailService
    from services.export_service import ExportService
    from services.scoring_service import ScoringService

    get_i18n().current_language = "sv"
    case = Case(
        case_id="T-2026-SE-001",
        created_at="2026-09-02T10:00:00",
        updated_at="2026-09-02T10:00:00",
        customer=CaseCustomer(customer_id="KUND-8801", practice_name="Göteborgs Vårdcentral",
                              contact_person="Dr. Astrid Lind", is_vip=True),
        classification=Classification(schema_id="standard_support", title="Databaslåsning vid fakturering",
                                      urgency_level=UrgencyLevel.RED, tags=["Databas"]),
        workflow_status=WorkflowStatus(current_actor=Actor.SUPPORT, followup_at="2026-09-03T09:00:00",
                                       followup_note="Ring upp Dr. Lind för fjärrsupport"),
        timeline=[TimelineEntry(timestamp="2026-09-02T10:30:00", author="agent_sv",
                                channel=Channel.PHONE_INBOUND, note="Tog emot felrapport per telefon.")],
    )
    assert ScoringService(storage.load_profile().scoring_matrix).update_case_scoring(case) > 0

    storage.save_cases([case], sync=True)
    loaded = storage.load_cases()
    assert [c.customer.practice_name for c in loaded] == ["Göteborgs Vårdcentral"]
    assert loaded[0].timeline[0].note == "Tog emot felrapport per telefon."

    template = ExportTemplate(
        template_id="TPL-SV", display_name="Svensk Ärenderapport", target_type=TargetType.CLIPBOARD_TEXT,
        template_string="# Ärenderapport: {{ case.case_id }}\n**Mottagning:** {{ customer.practice_name }}",
    )
    success, _missing, output = ExportService(storage).render_template(case, template)
    assert success is True
    assert output == "# Ärenderapport: T-2026-SE-001\n**Mottagning:** Göteborgs Vårdcentral"

    ics_path = CalendarEmailService(tmp_path).generate_ics_file(case=case, target_dir=tmp_path)
    ics_text = ics_path.read_text(encoding="utf-8")
    assert "BEGIN:VEVENT" in ics_text and "Göteborgs Vårdcentral" in ics_text


def test_seeded_workspace_under_english_ui_supports_customers_and_snippets(seeded_storage, config):
    """Demo seed + customer search + snippet storage work while the UI runs in English."""
    from models.customer import Contact, Customer
    from models.snippet import Snippet
    from services.customer_service import CustomerService
    from services.snippet_service import SnippetService

    get_i18n().current_language = "en"
    customers = CustomerService(seeded_storage)
    seeded_count = len(customers.get_all_customers())
    customers.save_customer(Customer(
        customer_id="PRAC-901", practice_name="Central Health Clinic London", city="London",
        contacts=[Contact(name="Dr. James Wilson", role="Senior Doctor")],
    ))
    assert [c.customer_id for c in customers.search_customers("Wilson")] == ["PRAC-901"]
    assert len(customers.get_all_customers()) == seeded_count + 1

    snippets = SnippetService(config.workspace_dir)
    assert snippets.load_snippets()
    snippets.add_or_update_snippet(Snippet(snippet_id="SNIP-ENG-01", title="Backup Request", shortcut="#reqdump",
                                           content="Dear {contact_person}"))
    reloaded = SnippetService(config.workspace_dir).load_snippets()
    assert any(s.snippet_id == "SNIP-ENG-01" and s.content == "Dear {contact_person}" for s in reloaded)
