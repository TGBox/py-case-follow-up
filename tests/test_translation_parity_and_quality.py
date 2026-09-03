"""Comprehensive automated test suite for translation parity, quality, format tokens,

and I18nService resilience across German (de), English (en), and Swedish (sv).
"""

import json
import re
from pathlib import Path
from typing import Any
import pytest

from services.i18n_service import I18nService, tr, SUPPORTED_LANGUAGES


def get_locales_dir() -> Path:
    """Return the absolute path to the project's locales directory."""
    locales_dir = Path(__file__).resolve().parent.parent / "locales"
    assert locales_dir.exists(), f"Locales directory not found at {locales_dir}"
    return locales_dir


def load_locale_json(lang_code: str) -> dict[str, Any]:
    """Load and parse a locale JSON file."""
    locales_dir = get_locales_dir()
    file_path = locales_dir / f"{lang_code}.json"
    assert file_path.exists(), f"Locale file {file_path} does not exist"
    with open(file_path, "r", encoding="utf-8") as f:
        return json.load(f)


def extract_leaf_keys(data: dict[str, Any], prefix: str = "") -> dict[str, str]:
    """Recursively extract all leaf keys (dot-separated) and their string values."""
    leaf_dict: dict[str, str] = {}
    for key, value in data.items():
        full_key = f"{prefix}.{key}" if prefix else key
        if isinstance(value, dict):
            leaf_dict.update(extract_leaf_keys(value, full_key))
        elif isinstance(value, str):
            leaf_dict[full_key] = value
        elif isinstance(value, list):
            for idx, item in enumerate(value):
                if isinstance(item, dict):
                    leaf_dict.update(extract_leaf_keys(item, f"{full_key}[{idx}]"))
                else:
                    leaf_dict[f"{full_key}[{idx}]"] = str(item)
        else:
            leaf_dict[full_key] = str(value)
    return leaf_dict


def extract_format_tokens(text: str) -> set[str]:
    """Extract format placeholder tokens like '{case_id}' or '{name}' from a string."""
    if not isinstance(text, str):
        return set()
    return set(re.findall(r"\{([a-zA-Z0-9_]+)\}", text))


# Keys that are intentionally allowed to be empty (e.g. grammar differences like German 'Uhr' vs English '')
INTENTIONAL_EMPTY_KEYS = {
    "datetime.o_clock",
    "handover_dialog.header_suffix",
}


# ============================================================================
# Tier 1 & Tier 2: Key Parity, Non-Empty, & Structure Validation
# ============================================================================

class TestTranslationParity:
    """Test 100% mutual key parity, structural parity, and non-empty values across locales."""

    def test_all_supported_locale_files_exist(self):
        """Verify that de.json, en.json, and sv.json exist in locales/."""
        locales_dir = get_locales_dir()
        for lang_code in SUPPORTED_LANGUAGES:
            file_path = locales_dir / f"{lang_code}.json"
            assert file_path.is_file(), f"Missing translation file: {file_path}"
            assert file_path.stat().st_size > 0, f"Translation file is empty: {file_path}"

    def test_valid_json_structure_and_top_level_dict(self):
        """Verify that all locale files contain valid JSON and top-level dicts."""
        for lang_code in ("de", "en", "sv"):
            data = load_locale_json(lang_code)
            assert isinstance(data, dict), f"Top-level structure in {lang_code}.json must be a dict"
            assert len(data) > 0, f"{lang_code}.json is an empty dict"

    def test_top_level_section_parity(self):
        """Verify that all top-level sections match 100% across de, en, and sv."""
        de_data = load_locale_json("de")
        en_data = load_locale_json("en")
        sv_data = load_locale_json("sv")

        de_sections = set(de_data.keys())
        en_sections = set(en_data.keys())
        sv_sections = set(sv_data.keys())

        missing_in_en = de_sections - en_sections
        extra_in_en = en_sections - de_sections
        missing_in_sv = de_sections - sv_sections
        extra_in_sv = sv_sections - de_sections

        assert not missing_in_en, f"Top-level sections missing in en.json: {missing_in_en}"
        assert not extra_in_en, f"Unexpected top-level sections in en.json: {extra_in_en}"
        assert not missing_in_sv, f"Top-level sections missing in sv.json: {missing_in_sv}"
        assert not extra_in_sv, f"Unexpected top-level sections in sv.json: {extra_in_sv}"

    def test_100_percent_mutual_leaf_key_parity_de_and_en(self):
        """Verify 100% leaf key parity between de.json and en.json."""
        de_leafs = extract_leaf_keys(load_locale_json("de"))
        en_leafs = extract_leaf_keys(load_locale_json("en"))

        missing_in_en = set(de_leafs.keys()) - set(en_leafs.keys())
        extra_in_en = set(en_leafs.keys()) - set(de_leafs.keys())

        assert not missing_in_en, f"Leaf keys in de.json missing from en.json ({len(missing_in_en)}): {sorted(missing_in_en)[:10]}"
        assert not extra_in_en, f"Leaf keys in en.json missing from de.json ({len(extra_in_en)}): {sorted(extra_in_en)[:10]}"
        assert len(de_leafs) == len(en_leafs), f"Key counts differ: de={len(de_leafs)}, en={len(en_leafs)}"

    def test_100_percent_mutual_leaf_key_parity_de_and_sv(self):
        """Verify 100% leaf key parity between de.json and sv.json."""
        de_leafs = extract_leaf_keys(load_locale_json("de"))
        sv_leafs = extract_leaf_keys(load_locale_json("sv"))

        missing_in_sv = set(de_leafs.keys()) - set(sv_leafs.keys())
        extra_in_sv = set(sv_leafs.keys()) - set(de_leafs.keys())

        assert not missing_in_sv, f"Leaf keys in de.json missing from sv.json ({len(missing_in_sv)}): {sorted(missing_in_sv)[:10]}"
        assert not extra_in_sv, f"Leaf keys in sv.json missing from de.json ({len(extra_in_sv)}): {sorted(extra_in_sv)[:10]}"
        assert len(de_leafs) == len(sv_leafs), f"Key counts differ: de={len(de_leafs)}, sv={len(sv_leafs)}"

    def test_100_percent_mutual_leaf_key_parity_en_and_sv(self):
        """Verify 100% leaf key parity between en.json and sv.json."""
        en_leafs = extract_leaf_keys(load_locale_json("en"))
        sv_leafs = extract_leaf_keys(load_locale_json("sv"))

        diff_en_sv = set(en_leafs.keys()) ^ set(sv_leafs.keys())
        assert not diff_en_sv, f"Key mismatch between en.json and sv.json ({len(diff_en_sv)}): {sorted(diff_en_sv)[:10]}"

    def test_no_empty_or_whitespace_values_in_de(self):
        """Verify that de.json contains no unexpected empty or whitespace-only translation strings."""
        de_leafs = extract_leaf_keys(load_locale_json("de"))
        empty_keys = [k for k, v in de_leafs.items() if not v.strip() and k not in INTENTIONAL_EMPTY_KEYS]
        assert not empty_keys, f"Found empty translation values in de.json for keys: {empty_keys}"

    def test_no_empty_or_whitespace_values_in_en(self):
        """Verify that en.json contains no unexpected empty or whitespace-only translation strings."""
        en_leafs = extract_leaf_keys(load_locale_json("en"))
        empty_keys = [k for k, v in en_leafs.items() if not v.strip() and k not in INTENTIONAL_EMPTY_KEYS]
        assert not empty_keys, f"Found empty translation values in en.json for keys: {empty_keys}"

    def test_no_empty_or_whitespace_values_in_sv(self):
        """Verify that sv.json contains no unexpected empty or whitespace-only translation strings."""
        sv_leafs = extract_leaf_keys(load_locale_json("sv"))
        empty_keys = [k for k, v in sv_leafs.items() if not v.strip() and k not in INTENTIONAL_EMPTY_KEYS]
        assert not empty_keys, f"Found empty translation values in sv.json for keys: {empty_keys}"

    def test_no_null_or_none_leaf_values(self):
        """Verify that no leaf key in any locale maps to null / None."""
        for lang in ("de", "en", "sv"):
            data = load_locale_json(lang)
            leafs = extract_leaf_keys(data)
            none_keys = [k for k, v in leafs.items() if v is None or (v == "None" and not k.endswith("none_placeholder"))]
            assert not none_keys, f"Found null/None values in {lang}.json: {none_keys}"


# ============================================================================
# Tier 2: Placeholder & Format Token Preservation
# ============================================================================

class TestTranslationPlaceholders:
    """Verify that named format placeholders (e.g. {case_id}) match across all languages."""

    def test_format_placeholder_tokens_match_identically(self):
        """Ensure all interpolation tokens in UI strings match 100% in DE, EN, and SV."""
        de_leafs = extract_leaf_keys(load_locale_json("de"))
        en_leafs = extract_leaf_keys(load_locale_json("en"))
        sv_leafs = extract_leaf_keys(load_locale_json("sv"))

        mismatches = []
        for key, de_val in de_leafs.items():
            # Exclude markdown manual help documentation where curly braces may be used as documentation
            if key.startswith("help_content."):
                continue

            de_tokens = extract_format_tokens(de_val)
            en_val = en_leafs.get(key, "")
            sv_val = sv_leafs.get(key, "")
            en_tokens = extract_format_tokens(en_val)
            sv_tokens = extract_format_tokens(sv_val)

            if de_tokens != en_tokens:
                mismatches.append(f"Key '{key}': DE tokens {de_tokens} != EN tokens {en_tokens}")
            if de_tokens != sv_tokens:
                mismatches.append(f"Key '{key}': DE tokens {de_tokens} != SV tokens {sv_tokens}")

        assert not mismatches, f"Placeholder token mismatches found:\n" + "\n".join(mismatches)

    def test_placeholder_tokens_are_valid_identifiers(self):
        """Verify that all placeholder tokens inside curly braces are valid identifiers."""
        for lang in ("de", "en", "sv"):
            leafs = extract_leaf_keys(load_locale_json(lang))
            for key, val in leafs.items():
                if key.startswith("help_content."):
                    continue
                tokens = extract_format_tokens(val)
                for tok in tokens:
                    assert tok.isidentifier(), f"Invalid format token '{tok}' in {lang}.json at '{key}'"

    def test_no_unbalanced_curly_braces(self):
        """Ensure no unmatched or corrupted curly braces in UI translation strings."""
        for lang in ("de", "en", "sv"):
            leafs = extract_leaf_keys(load_locale_json(lang))
            for key, val in leafs.items():
                if key.startswith("help_content."):
                    continue
                open_count = val.count("{")
                close_count = val.count("}")
                assert open_count == close_count, (
                    f"Unbalanced braces in {lang}.json at '{key}': '{val}' "
                    f"({open_count} open vs {close_count} close)"
                )


# ============================================================================
# Tier 1 & 2: Translation Quality & Untranslated German Detection
# ============================================================================

class TestTranslationQualityAndLocalization:
    """Verify translation quality, natural translations, and absence of raw German in EN/SV."""

    # Words that are distinctively German and should not appear in English translations
    GERMAN_STOPWORDS_FOR_EN = [
        "wiedervorlage", "speichern", "abbrechen", "löschen", "loeschen",
        "mitarbeiter", "praxis", "praxen", "einstellungen", "anwendungsdokumentation",
        "bitte", "nicht", "hinzufügen", "bearbeiten", "kundendaten", "übergabe",
        "fallakte", "schließen", "dringend", "erledigt", "auswertungen", "zuständige",
        "vorlagen", "textbaustein", "datenaustausch", "zeitleiste", "störfall", "nachfragen"
    ]

    # Words that are distinctively German and should not appear in Swedish translations
    GERMAN_STOPWORDS_FOR_SV = [
        "wiedervorlage", "speichern", "abbrechen", "löschen", "loeschen",
        "mitarbeiter", "praxen", "einstellungen", "anwendungsdokumentation",
        "bitte", "nicht", "hinzufügen", "bearbeiten", "kundendaten", "übergabe",
        "fallakte", "schließen", "auswertungen", "zuständige", "vorlagen",
        "textbaustein", "datenaustausch", "zeitleiste", "störfall", "nachfragen"
    ]

    def test_no_untranslated_german_tokens_in_english(self):
        """Verify that en.json does not contain un-translated German keywords."""
        en_leafs = extract_leaf_keys(load_locale_json("en"))
        violations = []

        for key, val in en_leafs.items():
            if key.startswith("help_content."):
                continue
            val_lower = val.lower()
            for word in self.GERMAN_STOPWORDS_FOR_EN:
                if re.search(rf"\b{re.escape(word)}\b", val_lower):
                    violations.append(f"EN key '{key}' contains German word '{word}': \"{val}\"")

        assert not violations, f"German words detected in en.json ({len(violations)}):\n" + "\n".join(violations[:15])

    def test_no_untranslated_german_tokens_in_swedish(self):
        """Verify that sv.json does not contain un-translated German keywords."""
        sv_leafs = extract_leaf_keys(load_locale_json("sv"))
        violations = []

        for key, val in sv_leafs.items():
            if key.startswith("help_content."):
                continue
            val_lower = val.lower()
            for word in self.GERMAN_STOPWORDS_FOR_SV:
                if re.search(rf"\b{re.escape(word)}\b", val_lower):
                    violations.append(f"SV key '{key}' contains German word '{word}': \"{val}\"")

        assert not violations, f"German words detected in sv.json ({len(violations)}):\n" + "\n".join(violations[:15])

    def test_menu_section_translations(self):
        """Spot-check critical menu bar translations in all 3 languages."""
        de = load_locale_json("de")["menu"]
        en = load_locale_json("en")["menu"]
        sv = load_locale_json("sv")["menu"]

        # German checks
        assert "Neuer Fall" in de["new_case"]
        assert "Stammdaten" in de["master_data"]

        # English checks
        assert "New Case" in en["new_case"]
        assert "Master Data" in en["master_data"]
        assert "Templates" in en["templates"]

        # Swedish checks
        assert "Nytt ärende" in sv["new_case"]
        assert "Stamdata" in sv["master_data"] or "Grunddata" in sv["master_data"]
        assert "Mallar" in sv["templates"]

    def test_cockpit_actions_translations(self):
        """Spot-check cockpit action button translations."""
        de = load_locale_json("de")["cockpit"]
        en = load_locale_json("en")["cockpit"]
        sv = load_locale_json("sv")["cockpit"]

        assert "Speichern" in de["save"]
        assert "Save" in en["save"]
        assert "Spara" in sv["save"]

        assert "Archivieren" in de["archive"]
        assert "Archive" in en["archive"]
        assert "Arkivera" in sv["archive"]

        assert "Erledigt" in de["complete"]
        assert "Done" in en["complete"]
        assert "Klar" in sv["complete"]

    def test_dialog_titles_translations(self):
        """Verify key dialog titles in DE, EN, and SV."""
        de = load_locale_json("de")["dialog_titles"]
        en = load_locale_json("en")["dialog_titles"]
        sv = load_locale_json("sv")["dialog_titles"]

        assert de["new_case"] == "Neuen Support-Fall anlegen"
        assert en["new_case"] == "Create New Support Case"
        assert sv["new_case"] == "Skapa nytt supportärende"

        assert "Profil" in de["profile_settings"]
        assert "Profile" in en["profile_settings"]
        assert "Profil" in sv["profile_settings"]

    def test_board_column_headers_translations(self):
        """Verify Kanban board column header translations."""
        de = load_locale_json("de")["board"]
        en = load_locale_json("en")["board"]
        sv = load_locale_json("sv")["board"]

        assert "Support" in de["col_support"]
        assert "Support" in en["col_support"]
        assert "Support" in sv["col_support"]

        assert de["col_completed"] == "✓ Erledigte Fälle"
        assert en["col_completed"] == "✓ Completed Cases"
        assert sv["col_completed"] == "✓ Avslutade ärenden"

    def test_table_columns_translations(self):
        """Verify table view header column translations."""
        de = load_locale_json("de")["table_columns"]
        en = load_locale_json("en")["table_columns"]
        sv = load_locale_json("sv")["table_columns"]

        assert de["practice"] == "Praxis / Kunde ⇅"
        assert en["practice"] == "Practice / Customer ⇅"
        assert sv["practice"] == "Mottagning / Kund ⇅"

        assert de["actor"] == "Zuständigkeit ⇅"
        assert en["actor"] == "Responsibility ⇅"
        assert sv["actor"] == "Ansvar ⇅"

    def test_departments_translations(self):
        """Verify department translations across languages."""
        de = load_locale_json("de")["departments"]
        en = load_locale_json("en")["departments"]
        sv = load_locale_json("sv")["departments"]

        assert de["Entwicklung"] == "Entwicklung"
        assert en["Entwicklung"] == "Development"
        assert sv["Entwicklung"] == "Utveckling"

    def test_internal_task_categories_translations(self):
        """Verify internal task category translations."""
        de = load_locale_json("de")["internal_task_categories"]
        en = load_locale_json("en")["internal_task_categories"]
        sv = load_locale_json("sv")["internal_task_categories"]

        assert de["Dokumentation"] == "Dokumentation"
        assert en["Dokumentation"] == "Documentation"
        assert sv["Dokumentation"] == "Dokumentation"


# ============================================================================
# Tier 2: I18nService Behavior & Fallback Chain
# ============================================================================

class TestI18nServiceBehaviorAndFallback:
    """Verify runtime fallback logic, listener notifications, and kwargs formatting."""

    def test_service_supported_languages(self):
        """Verify supported languages dictionary."""
        assert "de" in SUPPORTED_LANGUAGES
        assert "en" in SUPPORTED_LANGUAGES
        assert "sv" in SUPPORTED_LANGUAGES
        assert SUPPORTED_LANGUAGES["de"] == "Deutsch"
        assert SUPPORTED_LANGUAGES["en"] == "English"
        assert SUPPORTED_LANGUAGES["sv"] == "Svenska"

    def test_i18n_service_lookup_all_three_languages(self):
        """Verify dynamic resolution across languages."""
        service = I18nService()

        service.current_language = "de"
        assert service.tr("cockpit.save") == "💾 Speichern"

        service.current_language = "en"
        assert service.tr("cockpit.save") == "💾 Save"

        service.current_language = "sv"
        assert service.tr("cockpit.save") == "💾 Spara"

        # Restore default
        service.current_language = "de"

    def test_fallback_chain_missing_in_sv_falls_back_to_de(self, tmp_path: Path):
        """When a key is missing in Swedish, it should fall back to German."""
        locales = tmp_path / "locales"
        locales.mkdir()
        (locales / "de.json").write_text('{"custom": {"feature": "Deutsche Version"}}', encoding="utf-8")
        (locales / "en.json").write_text('{}', encoding="utf-8")
        (locales / "sv.json").write_text('{}', encoding="utf-8")

        service = I18nService(locales_dir=locales)
        service.current_language = "sv"
        assert service.tr("custom.feature") == "Deutsche Version"

    def test_fallback_chain_missing_in_all_returns_default(self, tmp_path: Path):
        """When a key is missing in all locales, it should return the default parameter."""
        locales = tmp_path / "locales"
        locales.mkdir()
        for lang in ("de", "en", "sv"):
            (locales / f"{lang}.json").write_text('{}', encoding="utf-8")

        service = I18nService(locales_dir=locales)
        service.current_language = "en"
        assert service.tr("completely.missing.key", default="My Custom Default") == "My Custom Default"

    def test_fallback_chain_missing_in_all_without_default_returns_key(self, tmp_path: Path):
        """When a key is missing and no default is supplied, it should return the key itself."""
        locales = tmp_path / "locales"
        locales.mkdir()
        for lang in ("de", "en", "sv"):
            (locales / f"{lang}.json").write_text('{}', encoding="utf-8")

        service = I18nService(locales_dir=locales)
        service.current_language = "sv"
        assert service.tr("unknown.system.path") == "unknown.system.path"

    def test_kwargs_formatting_resilience(self, tmp_path: Path):
        """Verify format kwargs interpolation with valid, extra, and missing kwargs."""
        locales = tmp_path / "locales"
        locales.mkdir()
        (locales / "de.json").write_text('{"msg": "Hallo {user}, Fall #{case_id}!"}', encoding="utf-8")
        (locales / "en.json").write_text('{"msg": "Hello {user}, Case #{case_id}!"}', encoding="utf-8")
        (locales / "sv.json").write_text('{"msg": "Hej {user}, Ärende #{case_id}!"}', encoding="utf-8")

        service = I18nService(locales_dir=locales)
        service.current_language = "en"

        # Correct kwargs
        res = service.tr("msg", user="Alice", case_id=42)
        assert res == "Hello Alice, Case #42!"

        # Extra unused kwargs (should format without crashing)
        res_extra = service.tr("msg", user="Bob", case_id=99, extra="ignored")
        assert res_extra == "Hello Bob, Case #99!"

        # Missing kwargs (should not crash with KeyError, returns unformatted or safe string)
        res_missing = service.tr("msg", user="Charlie")
        assert "Charlie" in res_missing or res_missing == "Hello {user}, Case #{case_id}!"

    def test_unicode_special_characters_and_emojis_preserved(self, tmp_path: Path):
        """Verify special umlauts (ä, ö, ü, ß, å) and emojis are preserved intact."""
        locales = tmp_path / "locales"
        locales.mkdir()
        (locales / "de.json").write_text('{"test": "Grüße vom Support-Team 🩺 & Ärztinnen!"}', encoding="utf-8")
        (locales / "en.json").write_text('{"test": "Greetings from Support Team 🩺 & Doctors!"}', encoding="utf-8")
        (locales / "sv.json").write_text('{"test": "Hälsningar från Support-Teamet 🩺 & Läkare å, ä, ö!"}', encoding="utf-8")

        service = I18nService(locales_dir=locales)

        service.current_language = "de"
        assert "Grüße" in service.tr("test")
        assert "🩺" in service.tr("test")

        service.current_language = "sv"
        assert "Hälsningar" in service.tr("test")
        assert "å, ä, ö" in service.tr("test")
        assert "🩺" in service.tr("test")
