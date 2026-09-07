"""Real i18n test coverage for the multi-language localization work.

Before this file, NO test in the project referenced i18n_service, current_language,
SUPPORTED_LANGUAGES or get_i18n at all (confirmed via a test-coverage audit) -
despite TEST_INFRA.md / TEST_READY.md documenting an elaborate 4-file, 64-test
i18n/E2E suite. Those 4 files (test_translation_parity_and_quality.py,
test_ast_i18n_scanner.py, test_dynamic_language_switch.py,
test_e2e_multilingual_workflows.py) do not exist in tests/ - this file is a
first real, minimal replacement covering the most important parts of what they
claimed to cover: static locale-file parity/quality, and I18nService's actual
runtime behavior (fallback chain, listener notification, LocalizedDict).
"""

import json
from pathlib import Path
import pytest

PROJECT_ROOT = Path(__file__).resolve().parent.parent
LOCALES_DIR = PROJECT_ROOT / "locales"
LANGUAGES = ("de", "en", "sv")

# Keys that are intentionally empty in en/sv because the underlying grammar
# construct (a trailing "Uhr"/suffix word) only exists in German.
KNOWN_INTENTIONAL_EMPTY_KEYS = {
    "datetime.o_clock",
    "handover_dialog.header_suffix",
}


def _flatten(d: dict, prefix: str = "") -> dict:
    out = {}
    for k, v in d.items():
        key = f"{prefix}.{k}" if prefix else k
        if isinstance(v, dict):
            out.update(_flatten(v, key))
        else:
            out[key] = v
    return out


@pytest.fixture(scope="module")
def locale_data() -> dict[str, dict]:
    data = {}
    for lang in LANGUAGES:
        path = LOCALES_DIR / f"{lang}.json"
        with open(path, "r", encoding="utf-8") as f:
            data[lang] = json.load(f)
    return data


@pytest.fixture(scope="module")
def flat_locale_data(locale_data) -> dict[str, dict]:
    return {lang: _flatten(data) for lang, data in locale_data.items()}


# ---------------------------------------------------------------------------
# Static locale-file checks (parity, quality)
# ---------------------------------------------------------------------------


def test_all_three_locale_files_exist_and_parse():
    for lang in LANGUAGES:
        path = LOCALES_DIR / f"{lang}.json"
        assert path.exists(), f"locales/{lang}.json is missing"
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
        assert isinstance(data, dict) and len(data) > 0


def test_leaf_key_parity_across_languages(flat_locale_data):
    de_keys = set(flat_locale_data["de"].keys())
    for lang in ("en", "sv"):
        lang_keys = set(flat_locale_data[lang].keys())
        missing_in_lang = de_keys - lang_keys
        extra_in_lang = lang_keys - de_keys
        assert not missing_in_lang, f"{lang}.json is missing keys present in de.json: {sorted(missing_in_lang)[:20]}"
        assert not extra_in_lang, f"{lang}.json has keys not present in de.json: {sorted(extra_in_lang)[:20]}"


def test_all_leaf_values_are_strings(flat_locale_data):
    for lang, flat in flat_locale_data.items():
        non_strings = {k: type(v).__name__ for k, v in flat.items() if not isinstance(v, str)}
        assert not non_strings, f"{lang}.json has non-string leaf values: {non_strings}"


def test_no_unexpected_empty_translation_values(flat_locale_data):
    for lang, flat in flat_locale_data.items():
        empty_keys = {
            k for k, v in flat.items()
            if v.strip() == "" and k not in KNOWN_INTENTIONAL_EMPTY_KEYS
        }
        assert not empty_keys, f"{lang}.json has unexpected empty values for keys: {sorted(empty_keys)}"


def test_known_intentional_empty_keys_are_non_empty_in_german(flat_locale_data):
    """Guards against the allowlist above silently hiding a real German gap too."""
    for key in KNOWN_INTENTIONAL_EMPTY_KEYS:
        assert flat_locale_data["de"].get(key, "").strip() != "", (
            f"de.json unexpectedly has an empty value for {key}, "
            "which is only supposed to be empty in en/sv"
        )


def test_format_placeholder_tokens_match_across_languages(flat_locale_data):
    import re

    token_re = re.compile(r"\{(\w+)\}")
    mismatches = []
    for key, de_val in flat_locale_data["de"].items():
        de_tokens = set(token_re.findall(de_val))
        if not de_tokens:
            continue
        for lang in ("en", "sv"):
            lang_val = flat_locale_data[lang].get(key, "")
            lang_tokens = set(token_re.findall(lang_val))
            if lang_tokens != de_tokens:
                mismatches.append((key, lang, sorted(de_tokens), sorted(lang_tokens)))

    assert not mismatches, (
        "Placeholder tokens (e.g. {case_id}) differ between languages for these keys "
        f"(key, lang, de_tokens, lang_tokens): {mismatches[:20]}"
    )


# ---------------------------------------------------------------------------
# I18nService runtime behavior
# ---------------------------------------------------------------------------


@pytest.fixture(autouse=True)
def reset_i18n_singleton():
    """Isolate the global I18nService singleton between tests."""
    import services.i18n_service as i18n_module

    previous = i18n_module._i18n_instance
    i18n_module._i18n_instance = None
    yield
    i18n_module._i18n_instance = previous


def test_i18n_service_loads_real_locales_and_serves_all_three_languages():
    from services.i18n_service import I18nService

    svc = I18nService()  # default locales_dir -> project_root/locales
    assert svc.current_language == "de"

    for lang in LANGUAGES:
        svc.current_language = lang
        # dialog_titles.followup exists in all three locale files (used by
        # FollowupDialog); resolving it must not fall back to the raw key.
        result = svc.tr("dialog_titles.followup")
        assert result and result != "dialog_titles.followup"


def test_i18n_service_current_language_setter_ignores_unsupported_and_same_value(tmp_path):
    from services.i18n_service import I18nService

    svc = I18nService(locales_dir=tmp_path)
    notifications = []
    svc.register_listener(lambda lang: notifications.append(lang))

    svc.current_language = "de"  # already "de" -> no-op, no notification
    assert svc.current_language == "de"
    assert notifications == []

    svc.current_language = "xx"  # unsupported -> ignored
    assert svc.current_language == "de"
    assert notifications == []

    svc.current_language = "en"  # supported and different -> applies + notifies
    assert svc.current_language == "en"
    assert notifications == ["en"]


def test_i18n_service_listener_unregister_stops_further_notifications(tmp_path):
    from services.i18n_service import I18nService

    svc = I18nService(locales_dir=tmp_path)
    received = []

    def listener(lang):
        received.append(lang)

    svc.register_listener(listener)
    svc.current_language = "en"
    assert received == ["en"]

    svc.unregister_listener(listener)
    svc.current_language = "sv"
    assert received == ["en"]  # no new notification after unregistering


def test_i18n_service_fallback_chain_de_then_default_then_raw_key(tmp_path):
    from services.i18n_service import I18nService

    (tmp_path / "de.json").write_text(
        json.dumps({"greeting": {"hello": "Hallo"}}, ensure_ascii=False), encoding="utf-8"
    )
    (tmp_path / "en.json").write_text(json.dumps({}), encoding="utf-8")
    (tmp_path / "sv.json").write_text(json.dumps({}), encoding="utf-8")

    svc = I18nService(locales_dir=tmp_path)
    svc.current_language = "en"

    # Missing in "en" -> falls back to "de"
    assert svc.tr("greeting.hello") == "Hallo"

    # Missing in "en" and "de" -> falls back to the provided default
    assert svc.tr("greeting.bye", default="Bye!") == "Bye!"

    # Missing everywhere and no default -> falls back to the raw key
    assert svc.tr("greeting.bye") == "greeting.bye"


def test_i18n_service_tr_formats_kwargs_and_survives_missing_placeholder(tmp_path):
    from services.i18n_service import I18nService

    (tmp_path / "de.json").write_text(
        json.dumps({"followup": {"header": "Wiedervorlage einplanen: {case_id}"}}, ensure_ascii=False),
        encoding="utf-8",
    )
    (tmp_path / "en.json").write_text(json.dumps({}), encoding="utf-8")
    (tmp_path / "sv.json").write_text(json.dumps({}), encoding="utf-8")

    svc = I18nService(locales_dir=tmp_path)

    assert svc.tr("followup.header", case_id="T-1") == "Wiedervorlage einplanen: T-1"

    # Missing kwarg -> .format() raises internally and tr() must not blow up,
    # it should just return the unformatted string.
    assert svc.tr("followup.header") == "Wiedervorlage einplanen: {case_id}"


def test_localized_dict_resolves_translation_and_falls_back_to_initial_value(tmp_path):
    from services.i18n_service import I18nService, LocalizedDict
    import services.i18n_service as i18n_module

    (tmp_path / "de.json").write_text(
        json.dumps({"widgets": {"save": "Speichern"}}, ensure_ascii=False), encoding="utf-8"
    )
    (tmp_path / "en.json").write_text(json.dumps({"widgets": {"save": "Save"}}, ensure_ascii=False), encoding="utf-8")
    (tmp_path / "sv.json").write_text(json.dumps({}), encoding="utf-8")

    # LocalizedDict.__getitem__ calls the *module-level* tr(), which reads
    # the global singleton - so we point the singleton at our temp service.
    i18n_module._i18n_instance = I18nService(locales_dir=tmp_path)

    widget_texts = LocalizedDict("widgets", {"save": "Save (fallback)", "cancel": "Cancel (fallback)"})

    # "save" is translated in de.json
    assert widget_texts["save"] == "Speichern"

    # "cancel" has no translation anywhere -> falls back to the dict's own
    # initial value rather than the raw key.
    assert widget_texts["cancel"] == "Cancel (fallback)"

    # Switching language re-resolves dynamically without rebuilding the dict.
    i18n_module._i18n_instance.current_language = "en"
    assert widget_texts["save"] == "Save"

    # .values()/.items() must go through the same dynamic resolution.
    assert widget_texts.values() == ["Save", "Cancel (fallback)"]
    assert widget_texts.items() == [("save", "Save"), ("cancel", "Cancel (fallback)")]
