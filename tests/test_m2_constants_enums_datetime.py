"""Dedicated test suite for Milestone 2:
System Constants, Enums, DateTime Utils, Seed Services, and Dynamic Localization.
"""

from datetime import datetime, timedelta
from pathlib import Path
import pytest

from constants import (
    DISPLAY_ACTOR_NAMES,
    DISPLAY_BOARD_COLUMN_NAMES,
    DISPLAY_CHANNEL_NAMES,
    DISPLAY_LAYOUT_NAMES,
    VALIDATION_MESSAGES,
    HOTKEY_ACTION_LABELS,
    HOTKEY_ACTION_LABELS_MAP,
    get_localized_hotkey_action_labels,
)
from enums import (
    Actor,
    BoardColumn,
    Channel,
    LayoutMode,
    get_actor_display,
    get_channel_display,
    get_layout_display,
    get_board_column_display,
)
from services.i18n_service import LocalizedDict, get_i18n, tr
from services.seed_case_data import build_seed_cases
from services.seed_service import SeedService
from services.snippet_service import SnippetService, get_default_snippets
from utils.datetime_utils import (
    get_relative_date_text,
    format_german_date,
    format_german_time,
    format_german_datetime,
    format_german_date_with_relative,
    parse_german_date,
    format_date,
    format_time,
    format_datetime,
)


@pytest.fixture(autouse=True)
def reset_i18n():
    i18n = get_i18n()
    i18n.current_language = "de"
    yield
    i18n.current_language = "de"


class TestLocalizedDictFeatures:
    """Test LocalizedDict dynamic resolution, .values(), .items(), and fallback mechanisms."""

    def test_localized_dict_values_and_items_dynamic_resolution(self):
        i18n = get_i18n()

        # German
        i18n.current_language = "de"
        de_cols = DISPLAY_BOARD_COLUMN_NAMES.values()
        assert "Neu" in de_cols
        assert "Aktion erforderlich" in de_cols
        assert ("NEW", "Neu") in DISPLAY_BOARD_COLUMN_NAMES.items()

        # English
        i18n.current_language = "en"
        en_cols = DISPLAY_BOARD_COLUMN_NAMES.values()
        assert "New" in en_cols
        assert "Action required" in en_cols or "Action Required" in en_cols
        assert ("NEW", "New") in DISPLAY_BOARD_COLUMN_NAMES.items()


        # Swedish
        i18n.current_language = "sv"
        sv_cols = DISPLAY_BOARD_COLUMN_NAMES.values()
        assert "Nytt" in sv_cols
        assert "Åtgärd krävs" in sv_cols
        assert ("NEW", "Nytt") in DISPLAY_BOARD_COLUMN_NAMES.items()

    def test_validation_messages_multilingual(self):
        i18n = get_i18n()

        i18n.current_language = "de"
        assert "erforderlich" in VALIDATION_MESSAGES["snippet_id_required"]

        i18n.current_language = "en"
        assert "required" in VALIDATION_MESSAGES["snippet_id_required"]

        i18n.current_language = "sv"
        assert "krävs" in VALIDATION_MESSAGES["snippet_id_required"]

    def test_hotkey_action_labels_unpacking_and_localization(self):
        i18n = get_i18n()

        # Check tuple unpacking in for-loop (backward compatibility)
        i18n.current_language = "de"
        items_de = [(k, v) for k, v in HOTKEY_ACTION_LABELS]
        assert any(k == "new_case" and "Neuer Fall" in v for k, v in items_de)

        i18n.current_language = "en"
        items_en = [(k, v) for k, v in HOTKEY_ACTION_LABELS]
        assert any(k == "new_case" and "New Case" in v for k, v in items_en)

        i18n.current_language = "sv"
        items_sv = [(k, v) for k, v in HOTKEY_ACTION_LABELS]
        assert any(k == "new_case" and "Nytt ärende" in v for k, v in items_sv)

        # Helper function check
        assert len(get_localized_hotkey_action_labels()) == 13

    def test_case_normalization_and_unknown_key_fallbacks(self):
        ld = LocalizedDict("test_prefix", {"MY_KEY": "Default Value"})
        assert ld["MY_KEY"] == "Default Value"
        assert ld.get("UNKNOWN", "Fallback") == "Fallback"

    def test_localized_dict_exact_translation_matching_default_no_false_fallback(self):
        """Verify that when locale translation is identical to default value, it does not falsely fallback."""
        i18n = get_i18n()

        # German
        i18n.current_language = "de"
        assert DISPLAY_ACTOR_NAMES["DATA_SUPPORT"] == "Data-AL Support / Hotline"
        assert DISPLAY_ACTOR_NAMES["DATA_HOTLINE"] == "Data-AL Hotline"
        assert DISPLAY_ACTOR_NAMES["DATA_DEVELOPMENT"] == "Data-AL Entwicklung"
        assert DISPLAY_ACTOR_NAMES["DATA_TECH"] == "Data-AL Technik"
        assert DISPLAY_ACTOR_NAMES["DATA_CUSTOMER"] == "Data-AL Kunde"
        assert DISPLAY_LAYOUT_NAMES["TABLE"] == "Tabelle & Details (Sortier-Matrix)"

        # English
        i18n.current_language = "en"
        assert DISPLAY_ACTOR_NAMES["DATA_SUPPORT"] == "Data-AL Support / Hotline"
        assert DISPLAY_ACTOR_NAMES["DATA_HOTLINE"] == "Data-AL Hotline"
        assert DISPLAY_ACTOR_NAMES["DATA_DEVELOPMENT"] == "Data-AL Development"
        assert DISPLAY_ACTOR_NAMES["DATA_TECH"] == "Data-AL Tech Support"
        assert DISPLAY_ACTOR_NAMES["DATA_CUSTOMER"] == "Data-AL Customer"
        assert DISPLAY_LAYOUT_NAMES["TABLE"] == "Table & Details (Sort Matrix)"

        # Swedish
        i18n.current_language = "sv"
        assert DISPLAY_ACTOR_NAMES["DATA_SUPPORT"] == "Data-AL Support / Hotline"
        assert DISPLAY_ACTOR_NAMES["DATA_HOTLINE"] == "Data-AL Hotline"
        assert DISPLAY_ACTOR_NAMES["DATA_DEVELOPMENT"] == "Data-AL Utveckling"
        assert DISPLAY_ACTOR_NAMES["DATA_TECH"] == "Data-AL Teknisk support"
        assert DISPLAY_ACTOR_NAMES["DATA_CUSTOMER"] == "Data-AL Kund"
        assert DISPLAY_LAYOUT_NAMES["TABLE"] == "Tabell & Detaljer (Sorteringsmatris)"

    def test_all_display_constants_all_locales(self):
        """Verify all keys across DISPLAY_ACTOR_NAMES, DISPLAY_LAYOUT_NAMES, DISPLAY_CHANNEL_NAMES, DISPLAY_BOARD_COLUMN_NAMES in DE, EN, SV."""
        i18n = get_i18n()

        for lang in ("de", "en", "sv"):
            i18n.current_language = lang

            for k in DISPLAY_ACTOR_NAMES.keys():
                val = DISPLAY_ACTOR_NAMES[k]
                assert val and isinstance(val, str), f"Empty or non-str actor name for {k} in {lang}"
                assert val != f"actors.{k}", f"Untranslated actor key {k} in {lang}"

            for k in DISPLAY_LAYOUT_NAMES.keys():
                val = DISPLAY_LAYOUT_NAMES[k]
                assert val and isinstance(val, str), f"Empty or non-str layout name for {k} in {lang}"
                assert val != f"layouts.{k}", f"Untranslated layout key {k} in {lang}"

            for k in DISPLAY_CHANNEL_NAMES.keys():
                val = DISPLAY_CHANNEL_NAMES[k]
                assert val and isinstance(val, str), f"Empty or non-str channel name for {k} in {lang}"
                assert val != f"channels.{k}", f"Untranslated channel key {k} in {lang}"

            for k in DISPLAY_BOARD_COLUMN_NAMES.keys():
                val = DISPLAY_BOARD_COLUMN_NAMES[k]
                assert val and isinstance(val, str), f"Empty or non-str board col name for {k} in {lang}"
                assert val != f"board_columns.{k}", f"Untranslated board column key {k} in {lang}"



class TestLocalizedDateTimeUtils:
    """Test relative date formatting and time suffix across DE, EN, and SV."""

    def test_relative_date_text_across_languages(self):
        i18n = get_i18n()
        ref_date = datetime(2026, 8, 23, 12, 0, 0)

        # Today (0 days diff)
        i18n.current_language = "de"
        assert get_relative_date_text(ref_date, ref_date=ref_date) == "heute"
        i18n.current_language = "en"
        assert get_relative_date_text(ref_date, ref_date=ref_date) == "today"
        i18n.current_language = "sv"
        assert get_relative_date_text(ref_date, ref_date=ref_date) == "idag"

        # Tomorrow (+1 day)
        tomorrow = ref_date + timedelta(days=1)
        i18n.current_language = "de"
        assert get_relative_date_text(tomorrow, ref_date=ref_date) == "morgen"
        i18n.current_language = "en"
        assert get_relative_date_text(tomorrow, ref_date=ref_date) == "tomorrow"
        i18n.current_language = "sv"
        assert get_relative_date_text(tomorrow, ref_date=ref_date) == "imorgon"

        # Day after tomorrow (+2 days)
        day_after = ref_date + timedelta(days=2)
        i18n.current_language = "de"
        assert get_relative_date_text(day_after, ref_date=ref_date) == "übermorgen"
        i18n.current_language = "en"
        assert get_relative_date_text(day_after, ref_date=ref_date) == "day after tomorrow"
        i18n.current_language = "sv"
        assert get_relative_date_text(day_after, ref_date=ref_date) == "i övermorgon"

        # Yesterday (-1 day)
        yesterday = ref_date - timedelta(days=1)
        i18n.current_language = "de"
        assert get_relative_date_text(yesterday, ref_date=ref_date) == "gestern"
        i18n.current_language = "en"
        assert get_relative_date_text(yesterday, ref_date=ref_date) == "yesterday"
        i18n.current_language = "sv"
        assert get_relative_date_text(yesterday, ref_date=ref_date) == "igår"

        # Day before yesterday (-2 days)
        day_before = ref_date - timedelta(days=2)
        i18n.current_language = "de"
        assert get_relative_date_text(day_before, ref_date=ref_date) == "vorgestern"
        i18n.current_language = "en"
        assert get_relative_date_text(day_before, ref_date=ref_date) == "day before yesterday"
        i18n.current_language = "sv"
        assert get_relative_date_text(day_before, ref_date=ref_date) == "i förrgår"

    def test_time_formatting_suffix_across_languages(self):
        i18n = get_i18n()
        sample_dt = "2026-08-23T14:30:00"

        # German has "Uhr" suffix
        i18n.current_language = "de"
        assert format_german_time(sample_dt, with_uhr=True) == "14:30 Uhr"
        assert format_german_datetime(sample_dt, with_uhr=True) == "23.08.2026 14:30 Uhr"

        # English has no suffix
        i18n.current_language = "en"
        assert format_german_time(sample_dt, with_uhr=True) == "14:30"
        assert format_german_datetime(sample_dt, with_uhr=True) == "23.08.2026 14:30"

        # Swedish has no suffix
        i18n.current_language = "sv"
        assert format_german_time(sample_dt, with_uhr=True) == "14:30"
        assert format_german_datetime(sample_dt, with_uhr=True) == "23.08.2026 14:30"

    def test_generic_aliases_match_german_functions(self):
        sample = "2026-08-23T14:30:00"
        assert format_date(sample) == format_german_date(sample)
        assert format_time(sample) == format_german_time(sample)
        assert format_datetime(sample) == format_german_datetime(sample)


class TestSeedAndSnippetLocalization:
    """Test localized seed case generation, schemas, and snippet services."""

    def test_seed_case_titles_localization(self):
        i18n = get_i18n()

        i18n.current_language = "de"
        cases_de = build_seed_cases()
        assert len(cases_de) == 12
        assert cases_de[10].classification.title == "Alte Nachforderung aus Vorquartal (Archiviert)"
        assert cases_de[11].classification.title == "Absturz bei PVS-GKV Abrechnungsexport"

        i18n.current_language = "en"
        cases_en = build_seed_cases()
        assert "Archived" in cases_en[10].classification.title
        assert "Crash" in cases_en[11].classification.title

        i18n.current_language = "sv"
        cases_sv = build_seed_cases()
        assert "Arkiverat" in cases_sv[10].classification.title
        assert "Krasch" in cases_sv[11].classification.title

    def test_snippet_service_and_category_localization(self, tmp_path: Path):
        i18n = get_i18n()

        # German
        i18n.current_language = "de"
        snips_de = get_default_snippets()
        assert "Rückfrage" in snips_de[0].category

        service = SnippetService(workspace_dir=tmp_path / "de_ws")
        categories_de = service.get_categories()
        assert categories_de[0] == "Alle"

        # Search with "Alle"
        assert len(service.search_snippets(category="Alle")) >= 8

        # English
        i18n.current_language = "en"
        snips_en = get_default_snippets()
        assert "Inquiry" in snips_en[0].category

        service_en = SnippetService(workspace_dir=tmp_path / "en_ws")
        categories_en = service_en.get_categories()
        assert categories_en[0] == "All"
        assert len(service_en.search_snippets(category="All")) >= 8

        # Swedish
        i18n.current_language = "sv"
        snips_sv = get_default_snippets()
        assert "Förfrågan" in snips_sv[0].category

        service_sv = SnippetService(workspace_dir=tmp_path / "sv_ws")
        categories_sv = service_sv.get_categories()
        assert categories_sv[0] == "Alla"
        assert len(service_sv.search_snippets(category="Alla")) >= 8
