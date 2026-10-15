"""Static checks over locales/*.json: key parity, non-empty values, placeholders, translation quality."""

import json
import re
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parents[2]
LOCALES_DIR = REPO / "locales"
LANGUAGES = ("de", "en", "sv")

# Intentionally empty in en/sv: the grammar construct (trailing "Uhr"/suffix) only exists in German.
INTENTIONAL_EMPTY_KEYS = {"datetime.o_clock", "handover_dialog.header_suffix"}

TOKEN_RE = re.compile(r"\{([a-zA-Z0-9_]+)\}")


def _flatten(data: dict, prefix: str = "") -> dict:
    out = {}
    for key, value in data.items():
        full = f"{prefix}.{key}" if prefix else key
        if isinstance(value, dict):
            out.update(_flatten(value, full))
        elif isinstance(value, list):
            for idx, item in enumerate(value):
                if isinstance(item, dict):
                    out.update(_flatten(item, f"{full}[{idx}]"))
                else:
                    out[f"{full}[{idx}]"] = item
        else:
            out[full] = value
    return out


@pytest.fixture(scope="module")
def raw() -> dict[str, dict]:
    data = {}
    for lang in LANGUAGES:
        path = LOCALES_DIR / f"{lang}.json"
        assert path.is_file(), f"locales/{lang}.json is missing"
        data[lang] = json.loads(path.read_text(encoding="utf-8"))
        assert isinstance(data[lang], dict) and data[lang], f"{lang}.json must be a non-empty object"
    return data


@pytest.fixture(scope="module")
def flat(raw) -> dict[str, dict]:
    return {lang: _flatten(d) for lang, d in raw.items()}


def _ui_items(flat_lang: dict):
    """Leaf items excluding the markdown help text, where braces are documentation."""
    return ((k, v) for k, v in flat_lang.items() if not k.startswith("help_content."))


@pytest.mark.parametrize("lang", ["en", "sv"])
def test_section_and_leaf_key_parity_with_german(raw, flat, lang):
    assert set(raw[lang]) == set(raw["de"]), "top-level sections differ"
    missing = set(flat["de"]) - set(flat[lang])
    extra = set(flat[lang]) - set(flat["de"])
    assert not missing, f"{lang}.json is missing keys: {sorted(missing)[:20]}"
    assert not extra, f"{lang}.json has keys not in de.json: {sorted(extra)[:20]}"


def test_all_values_are_non_empty_strings(flat):
    for lang, leafs in flat.items():
        non_strings = {k: type(v).__name__ for k, v in leafs.items() if not isinstance(v, str)}
        assert not non_strings, f"{lang}.json has non-string leaf values: {non_strings}"
        empty = sorted(k for k, v in leafs.items() if not v.strip() and k not in INTENTIONAL_EMPTY_KEYS)
        assert not empty, f"{lang}.json has unexpected empty values: {empty}"
        nones = [k for k, v in leafs.items() if v == "None" and not k.endswith("none_placeholder")]
        assert not nones, f"{lang}.json has literal 'None' values: {nones}"
    for key in INTENTIONAL_EMPTY_KEYS:
        # Guards against the allowlist silently hiding a real German gap too.
        assert flat["de"].get(key, "").strip(), f"de.json must not be empty for {key}"


def test_placeholder_tokens_match_and_braces_are_balanced(flat):
    for lang in LANGUAGES:
        for key, val in _ui_items(flat[lang]):
            assert val.count("{") == val.count("}"), f"Unbalanced braces in {lang}.json at '{key}': {val!r}"
    mismatches = []
    for lang in ("en", "sv"):
        for key, val in flat[lang].items():
            de_tokens = set(TOKEN_RE.findall(flat["de"][key]))
            tokens = set(TOKEN_RE.findall(val))
            if tokens != de_tokens:
                mismatches.append(f"{lang} {key}: de={sorted(de_tokens)} {lang}={sorted(tokens)}")
    assert not mismatches, "Placeholder token mismatches:\n" + "\n".join(mismatches[:20])


@pytest.mark.parametrize("section,key,placeholder", [
    ("handover_dialog", "header_full", "{case_id}"),
    ("handover_dialog", "current_line", "{actor}"),
    ("export_dialog", "export_for_case", "{case_id}"),
])
def test_placeholder_keys_used_in_source_exist_in_every_locale(raw, section, key, placeholder):
    """A new key that only lives in the source falls back to German everywhere."""
    for lang in LANGUAGES:
        value = raw[lang].get(section, {}).get(key)
        assert value, f"{lang}.json fehlt {section}.{key}"
        assert placeholder in value, f"{lang}.json: {section}.{key} ohne Platzhalter {placeholder}"


_GERMAN_WORDS = [
    "wiedervorlage", "speichern", "abbrechen", "löschen", "loeschen", "mitarbeiter", "praxen",
    "einstellungen", "anwendungsdokumentation", "bitte", "nicht", "hinzufügen", "bearbeiten",
    "kundendaten", "übergabe", "fallakte", "schließen", "auswertungen", "zuständige", "vorlagen",
    "textbaustein", "datenaustausch", "zeitleiste", "störfall", "nachfragen",
]
# "praxis", "dringend", "erledigt" are checked for English only.
_GERMAN_WORDS_EN = _GERMAN_WORDS + ["praxis", "dringend", "erledigt"]


@pytest.mark.parametrize("lang,words", [("en", _GERMAN_WORDS_EN), ("sv", _GERMAN_WORDS)])
def test_no_untranslated_german_words(flat, lang, words):
    pattern = re.compile(r"\b(" + "|".join(map(re.escape, words)) + r")\b")
    violations = [
        f"{key}: {val!r}" for key, val in _ui_items(flat[lang]) if pattern.search(val.lower())
    ]
    assert not violations, f"German words in {lang}.json:\n" + "\n".join(violations[:15])


# (key, de, en, sv) - exact values for the most visible strings.
SPOT_CHECKS = [
    ("dialog_titles.new_case", "Neuen Support-Fall anlegen", "Create New Support Case", "Skapa nytt supportärende"),
    ("board.col_completed", "✓ Erledigte Fälle", "✓ Completed Cases", "✓ Avslutade ärenden"),
    ("table_columns.practice", "Praxis / Kunde ⇅", "Practice / Customer ⇅", "Mottagning / Kund ⇅"),
    ("table_columns.actor", "Zuständigkeit ⇅", "Responsibility ⇅", "Ansvar ⇅"),
    ("departments.Entwicklung", "Entwicklung", "Development", "Utveckling"),
    ("internal_task_categories.Dokumentation", "Dokumentation", "Documentation", "Dokumentation"),
]
# (key, de, en, sv) - substrings that must appear.
SPOT_CONTAINS = [
    ("menu.new_case", "Neuer Fall", "New Case", "Nytt ärende"),
    ("menu.master_data", "Stammdaten", "Master Data", "Stamdata"),
    ("menu.templates", None, "Templates", "Mallar"),
    ("cockpit.save", "Speichern", "Save", "Spara"),
    ("cockpit.archive", "Archivieren", "Archive", "Arkivera"),
    ("cockpit.complete", "Erledigt", "Done", "Klar"),
    ("dialog_titles.profile_settings", "Profil", "Profile", "Profil"),
    ("board.col_support", "Hotline", "Hotline", "Hotline"),
]


def test_spot_check_key_translations(flat):
    for key, *expected in SPOT_CHECKS:
        for lang, exp in zip(LANGUAGES, expected):
            assert flat[lang][key] == exp, f"{lang} {key}"
    for key, *expected in SPOT_CONTAINS:
        for lang, exp in zip(LANGUAGES, expected):
            if exp is not None:
                assert exp in flat[lang][key], f"{lang} {key}: {flat[lang][key]!r}"
