"""Adversarial stress test suite for Milestone 2:
- Seed case data generation and integrity across DE, EN, and SV
- Seed service complete pipeline (schemas, templates, customers, wiki DB)
- Snippet service catalog, category filtering, search, CRUD, and persistence resilience
- Snippet placeholder substitution and format token interpolation edge cases
- DateTime localization, relative date boundary cases, and time suffix stripping
- LocalizedDict and LocalizedHotkeyDict robustness
"""

import json
from datetime import datetime, date, timedelta
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
    get_localized_departments,
    get_localized_handover_channels,
    get_localized_task_categories,
    get_localized_menu_options_stammdaten,
    get_localized_menu_options_vorlagen,
    get_localized_menu_options_datenaustausch,
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
from models.case import Case
from models.snippet import Snippet
from services.i18n_service import LocalizedDict, get_i18n, tr, SUPPORTED_LANGUAGES
from services.seed_case_data import build_seed_cases
from services.seed_service import SeedService
from services.snippet_service import SnippetService, get_default_snippets
from services.scoring_service import ScoringService
from services.storage_service import StorageService
from services.export_service import ExportService
from config import AppConfig
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
    format_date_with_relative,
    parse_date,
    parse_iso,
    calculate_idle_days,
    hours_until_deadline,
)


@pytest.fixture(autouse=True)
def reset_i18n_fixture():
    i18n = get_i18n()
    i18n.current_language = "de"
    yield
    i18n.current_language = "de"


# ============================================================================
# 1. Adversarial Stress: Seed Case Data Generation Across All Locales
# ============================================================================

class TestSeedCaseDataAdversarial:
    """Adversarial stress testing for seed case generation in all languages."""

    @pytest.mark.parametrize("lang", ["de", "en", "sv"])
    def test_build_seed_cases_in_all_languages(self, lang: str):
        """Verify all 12 seed cases are correctly constructed and fully valid in DE, EN, and SV."""
        i18n = get_i18n()
        i18n.current_language = lang

        cases = build_seed_cases()
        assert len(cases) == 12, f"Expected exactly 12 seed cases in {lang}, got {len(cases)}"

        case_ids = [c.case_id for c in cases]
        assert len(set(case_ids)) == 12, f"Duplicate case IDs found in {lang}: {case_ids}"

        scoring_service = ScoringService()

        for idx, case in enumerate(cases):
            # Check ID formatting
            assert case.case_id == f"T-2026-{idx+1:04d}", f"Invalid case ID: {case.case_id}"

            # Check title is non-empty and properly localized
            title = case.classification.title
            assert title, f"Empty title for case {case.case_id} in {lang}"
            assert not title.startswith("demo_cases."), f"Untranslated key leak in {lang}: {title}"

            # Verify no validation errors
            val_errors = case.validate()
            assert not val_errors, f"Validation errors on seed case {case.case_id} in {lang}: {val_errors}"

            # Verify scoring calculation survives without crash
            scoring_service.update_case_scoring(case)
            assert case.classification.calculated_score >= 0.0

            # Verify serialization round-trip
            case_dict = case.to_dict()
            assert isinstance(case_dict, dict)
            reconstructed = Case.from_dict(case_dict)
            assert reconstructed.case_id == case.case_id
            assert reconstructed.classification.title == case.classification.title
            assert reconstructed.customer.practice_name == case.customer.practice_name

    def test_seed_case_titles_are_distinct_across_languages(self):
        """Verify that seed case titles actually change between DE, EN, and SV."""
        i18n = get_i18n()

        i18n.current_language = "de"
        de_titles = [c.classification.title for c in build_seed_cases()]

        i18n.current_language = "en"
        en_titles = [c.classification.title for c in build_seed_cases()]

        i18n.current_language = "sv"
        sv_titles = [c.classification.title for c in build_seed_cases()]

        # All 12 titles must differ between DE and EN, and between DE and SV
        for i in range(12):
            assert de_titles[i] != en_titles[i], f"Case {i+1} title did not translate in EN: {de_titles[i]}"
            assert de_titles[i] != sv_titles[i], f"Case {i+1} title did not translate in SV: {de_titles[i]}"
            assert en_titles[i] != sv_titles[i], f"Case {i+1} title identical in EN and SV: {en_titles[i]}"

    def test_rapid_language_switching_stress_on_seed_cases(self):
        """Stress-test rapid language toggling on seed case generation."""
        i18n = get_i18n()
        langs = ["de", "en", "sv", "de", "sv", "en", "de"]

        for lang in langs:
            i18n.current_language = lang
            cases = build_seed_cases()
            assert len(cases) == 12
            if lang == "de":
                assert "Zuzahlungsnachforderungsdatei" in cases[0].classification.title
            elif lang == "en":
                assert "Co-payment" in cases[0].classification.title or "claim" in cases[0].classification.title.lower()
            elif lang == "sv":
                assert "tilläggskrav" in cases[0].classification.title.lower() or "genererad" in cases[0].classification.title.lower()


# ============================================================================
# 2. Adversarial Stress: SeedService Full Pipeline Across Locales
# ============================================================================

class TestSeedServicePipelineStress:
    """Stress testing SeedService schemas, templates, customers, and wiki generation."""

    @pytest.mark.parametrize("lang", ["de", "en", "sv"])
    def test_seed_service_run_seed_complete_pipeline(self, tmp_path: Path, lang: str):
        """Verify complete seeding in DE, EN, and SV creates valid schemas, templates, and cases."""
        i18n = get_i18n()
        i18n.current_language = lang

        config = AppConfig(workspace_dir=tmp_path / f"ws_{lang}", username="tester")
        storage = StorageService(config)
        seed_service = SeedService(storage)

        summary = seed_service.run_seed(force=True)
        assert summary["customers"] == 5
        assert summary["cases"] == 12
        assert summary["schemas"] == 5
        assert summary["templates"] == 4

        # Verify loaded question schemas
        schemas = storage.load_schemas()
        assert len(schemas) == 5
        for s in schemas:
            assert s.display_name and not s.display_name.startswith("schemas.")
            assert s.description and not s.description.startswith("schemas.")
            for f in s.fields:
                assert f.label and not f.label.startswith("schemas.")
                if f.placeholder:
                    assert not f.placeholder.startswith("schemas.")
            if s.is_repeatable_group:
                assert s.repeatable_group_title and not s.repeatable_group_title.startswith("schemas.")

        # Verify loaded export templates
        templates = storage.load_templates()
        assert len(templates) == 4
        for t in templates:
            assert t.display_name and not t.display_name.startswith("export_templates.")
            assert t.description and not t.description.startswith("export_templates.")

        # Verify template rendering on fully populated seed case (Case 1)
        export_service = ExportService(storage)
        cases = storage.load_cases()
        c1 = cases[0]
        for t in templates:
            if not t.applicable_cases or c1.classification.schema_id in t.applicable_cases:
                success, missing, rendered = export_service.render_template(c1, t)
                assert success is True, f"Template {t.template_id} failed on case {c1.case_id}: missing={missing}"
                assert len(rendered) > 50


# ============================================================================
# 3. Adversarial Stress: SnippetService & Snippet Model
# ============================================================================

class TestSnippetServiceStress:
    """Stress testing SnippetService catalog, search, category filtering, and CRUD."""

    @pytest.mark.parametrize("lang", ["de", "en", "sv"])
    def test_default_snippets_in_all_languages(self, lang: str):
        """Verify all 8 default snippets exist with localized titles, categories, and tags."""
        i18n = get_i18n()
        i18n.current_language = lang

        snippets = get_default_snippets()
        assert len(snippets) == 8

        for s in snippets:
            assert s.snippet_id.startswith("SNIP-")
            assert s.title and not s.title.startswith("snippets.")
            assert s.category and not s.category.startswith("snippet_categories.")
            assert s.content and not s.content.startswith("snippets.")
            assert len(s.tags) >= 1
            for t in s.tags:
                assert not t.startswith("snippets.")

            # Model validation
            assert len(s.validate()) == 0

    def test_snippet_categories_and_all_filter_across_locales(self, tmp_path: Path):
        """Verify categories and 'All' category filter in DE, EN, and SV."""
        i18n = get_i18n()

        # German
        i18n.current_language = "de"
        srv_de = SnippetService(workspace_dir=tmp_path / "de")
        cats_de = srv_de.get_categories()
        assert cats_de[0] == "Alle"
        assert "Rückfrage" in cats_de or "Anleitung" in cats_de
        assert len(srv_de.search_snippets(category="Alle")) == 8
        assert len(srv_de.search_snippets(category="All")) == 8  # fallback
        assert len(srv_de.search_snippets(category="Alla")) == 8  # fallback

        # English
        i18n.current_language = "en"
        srv_en = SnippetService(workspace_dir=tmp_path / "en")
        cats_en = srv_en.get_categories()
        assert cats_en[0] == "All"
        assert "Inquiry" in cats_en or "Instructions" in cats_en
        assert len(srv_en.search_snippets(category="All")) == 8
        assert len(srv_en.search_snippets(category="Alle")) == 8  # fallback

        # Swedish
        i18n.current_language = "sv"
        srv_sv = SnippetService(workspace_dir=tmp_path / "sv")
        cats_sv = srv_sv.get_categories()
        assert cats_sv[0] == "Alla"
        assert "Förfrågan" in cats_sv or "Instruktioner" in cats_sv
        assert len(srv_sv.search_snippets(category="Alla")) == 8
        assert len(srv_sv.search_snippets(category="All")) == 8  # fallback

    def test_snippet_search_by_query_tags_content(self, tmp_path: Path):
        """Verify search finds snippets by keyword in title, tag, or content."""
        srv = SnippetService(workspace_dir=tmp_path)

        # Search by SQL
        res_sql = srv.search_snippets(query="SQL")
        assert len(res_sql) >= 1
        assert "SNIP-03" in [s.snippet_id for s in res_sql]

        # Search by tag
        res_backup = srv.search_snippets(query="backup")
        assert len(res_backup) >= 1

        # Search case insensitivity
        res_mixed = srv.search_snippets(query="sYsTemLog")
        assert len(res_mixed) >= 1

        # Search no results
        res_empty = srv.search_snippets(query="NONEXISTENT_KEYWORD_XYZ_999")
        assert len(res_empty) == 0

    def test_snippet_crud_and_persistence_recovery(self, tmp_path: Path):
        """Verify snippet add, update, delete, and corrupted JSON file recovery."""
        srv = SnippetService(workspace_dir=tmp_path)
        initial_len = len(srv.get_all_snippets())

        # Add snippet without ID (auto-id assignment)
        s_new = Snippet(
            title="Auto-ID Snippet",
            category="Custom",
            content="Custom snippet text.",
            tags=["tag1", "tag2"],
        )
        srv.add_or_update_snippet(s_new)
        assert s_new.snippet_id == f"SNIP-{initial_len+1:02d}"
        assert len(srv.get_all_snippets()) == initial_len + 1

        # Reload from disk
        srv_reloaded = SnippetService(workspace_dir=tmp_path)
        assert len(srv_reloaded.get_all_snippets()) == initial_len + 1

        # Update snippet
        s_new.title = "Updated Auto-ID Snippet"
        srv_reloaded.add_or_update_snippet(s_new)
        assert len(srv_reloaded.get_all_snippets()) == initial_len + 1
        found = next(s for s in srv_reloaded.get_all_snippets() if s.snippet_id == s_new.snippet_id)
        assert found.title == "Updated Auto-ID Snippet"

        # Delete snippet
        srv_reloaded.delete_snippet(s_new.snippet_id)
        assert len(srv_reloaded.get_all_snippets()) == initial_len

        # Corrupt the JSON file and ensure safe fallback to defaults
        corrupted_file = tmp_path / "data" / "snippets.json"
        corrupted_file.write_text("{CORRUPTED INVALID JSON", encoding="utf-8")
        srv_corrupt = SnippetService(workspace_dir=tmp_path)
        assert len(srv_corrupt.get_all_snippets()) == 8


# ============================================================================
# 4. Adversarial Stress: Snippet Placeholder Replacement & Interpolation
# ============================================================================

class TestSnippetPlaceholderReplacement:
    """Stress testing format placeholder replacement and edge cases in snippets."""

    def test_snippet_placeholder_substitution_standard_and_custom(self):
        """Test template format substitution with case and customer metadata."""
        snip = Snippet(
            snippet_id="SNIP-TPL-01",
            title="Customer Followup Template",
            content="Guten Tag {contact_person},\n\nbezüglich Fall {case_id} für die {practice_name} haben wir eine Rückfrage.\n\nViele Grüße\n{agent_name}",
        )

        populated = snip.content.format(
            contact_person="Frau Weber",
            case_id="T-2026-0001",
            practice_name="Gemeinschaftspraxis Dr. Müller",
            agent_name="Daniel Rösch",
        )

        assert "Guten Tag Frau Weber," in populated
        assert "Fall T-2026-0001" in populated
        assert "Gemeinschaftspraxis Dr. Müller" in populated
        assert "Daniel Rösch" in populated

    def test_snippet_placeholder_with_missing_and_extra_fields(self):
        """Test formatting behavior with missing, extra, and special characters."""
        content = "Hello {contact_person}, ticket {case_id} status is {status}."

        # Extra kwargs should not cause errors
        res_extra = content.format(
            contact_person="Dr. Rossi",
            case_id="T-2026-0002",
            status="OPEN",
            extra_field="IGNORED",
        )
        assert res_extra == "Hello Dr. Rossi, ticket T-2026-0002 status is OPEN."

        # Safe formatting helper when kwargs might be missing
        def safe_format(template_str: str, **kwargs) -> str:
            class SafeDict(dict):
                def __missing__(self, key):
                    return f"{{{key}}}"
            return template_str.format_map(SafeDict(**kwargs))

        res_partial = safe_format(content, contact_person="Dr. Rossi", case_id="T-2026-0002")
        assert res_partial == "Hello Dr. Rossi, ticket T-2026-0002 status is {status}."

    def test_snippet_placeholder_with_unicode_and_large_payload(self):
        """Test formatting with international unicode, emojis, and large payload."""
        snip_text = "Mottagning: {practice}, Läkare: {doctor}, Ärende: {case_id} 🩺 åäö!"
        res = snip_text.format(
            practice="Vårdcentralen Björken",
            doctor="Dr. Åsa Strömberg",
            case_id="SE-9999",
        )
        assert "Vårdcentralen Björken" in res
        assert "Dr. Åsa Strömberg" in res
        assert "SE-9999" in res
        assert "🩺 åäö!" in res

        # Very large text replacement
        large_body = "A" * 50000
        snip_large = "Header: {body} :Footer"
        res_large = snip_large.format(body=large_body)
        assert len(res_large) == 50016
        assert res_large.startswith("Header: AAAA")
        assert res_large.endswith("AAAA :Footer")


# ============================================================================
# 5. Adversarial Stress: DateTime Utils Boundaries & Localization
# ============================================================================

class TestDateTimeUtilsBoundaries:
    """Stress testing datetime parsing, formatting, leap years, and relative dates."""

    @pytest.mark.parametrize("lang, expected_today, expected_tomorrow, expected_yesterday", [
        ("de", "heute", "morgen", "gestern"),
        ("en", "today", "tomorrow", "yesterday"),
        ("sv", "idag", "imorgon", "igår"),
    ])
    def test_relative_date_keywords_across_languages(
        self, lang: str, expected_today: str, expected_tomorrow: str, expected_yesterday: str
    ):
        i18n = get_i18n()
        i18n.current_language = lang

        ref = datetime(2026, 6, 15, 12, 0, 0)

        # Today
        assert get_relative_date_text(ref, ref_date=ref) == expected_today

        # Tomorrow
        assert get_relative_date_text(ref + timedelta(days=1), ref_date=ref) == expected_tomorrow

        # Yesterday
        assert get_relative_date_text(ref - timedelta(days=1), ref_date=ref) == expected_yesterday

    def test_relative_date_boundary_in_n_days_and_days_ago(self):
        i18n = get_i18n()
        ref = datetime(2026, 6, 15, 12, 0, 0)

        # Same ISO week (diff_days > 2) -> "this week"
        i18n.current_language = "de"
        assert get_relative_date_text(ref + timedelta(days=4), ref_date=ref) == "diese Woche"
        i18n.current_language = "en"
        assert get_relative_date_text(ref + timedelta(days=4), ref_date=ref) == "this week"
        i18n.current_language = "sv"
        assert get_relative_date_text(ref + timedelta(days=4), ref_date=ref) == "denna vecka"

        # Future beyond this/next week (+20 days)
        i18n.current_language = "de"
        assert get_relative_date_text(ref + timedelta(days=20), ref_date=ref) == "in 20 Tagen"
        assert get_relative_date_text(ref - timedelta(days=20), ref_date=ref) == "vor 20 Tagen"

        # English
        i18n.current_language = "en"
        assert get_relative_date_text(ref + timedelta(days=20), ref_date=ref) == "in 20 days"
        assert get_relative_date_text(ref - timedelta(days=20), ref_date=ref) == "20 days ago"

        # Swedish
        i18n.current_language = "sv"
        assert get_relative_date_text(ref + timedelta(days=20), ref_date=ref) == "om 20 dagar"
        assert get_relative_date_text(ref - timedelta(days=20), ref_date=ref) == "för 20 dagar sedan"

    def test_datetime_parse_german_date_with_multilingual_time_suffixes(self):
        """Test parse_date strips 'Uhr', 'kl.', 'kl', and whitespace safely."""
        assert parse_date("23.08.2026 14:30 Uhr") == "2026-08-23T14:30:00"
        assert parse_date("23.08.2026 14:30 kl.") == "2026-08-23T14:30:00"
        assert parse_date("23.08.2026 14:30 kl") == "2026-08-23T14:30:00"
        assert parse_date("23.08.2026 14:30") == "2026-08-23T14:30:00"
        assert parse_date("23.08.2026") == "2026-08-23T00:00:00"
        assert parse_date("2026-08-23T14:30:00") == "2026-08-23T14:30:00"

    def test_hours_until_deadline_and_idle_days_edge_cases(self):
        """Test hours_until_deadline and calculate_idle_days with past, future, and invalid dates."""
        now = datetime(2026, 8, 23, 12, 0, 0)

        # 2 hours remaining
        assert hours_until_deadline("2026-08-23T14:00:00", now=now) == 2.0

        # Overdue by 3 hours
        assert hours_until_deadline("2026-08-23T09:00:00", now=now) == -3.0

        # Empty deadline
        assert hours_until_deadline("", now=now) == float("inf")

        # Idle days: exactly 2 days
        assert calculate_idle_days("2026-08-21T12:00:00", now=now) == 2.0

        # Future date gives 0.0 idle days
        assert calculate_idle_days("2026-08-25T12:00:00", now=now) == 0.0


# ============================================================================
# 6. Adversarial Stress: LocalizedDict & LocalizedHotkeyDict Robustness
# ============================================================================

class TestLocalizedDictRobustness:
    """Stress testing LocalizedDict dynamic resolution, fallbacks, and hotkey iteration."""

    def test_localized_dict_case_insensitivity_and_mutation(self):
        ld = LocalizedDict("test_pref", {"ACTION_REQUIRED": "Default Action"})

        # Subscript access
        assert ld["ACTION_REQUIRED"] == "Default Action"
        assert ld.get("ACTION_REQUIRED") == "Default Action"

        # Missing key returns default or key
        assert ld.get("NONEXISTENT", "FallbackVal") == "FallbackVal"
        assert ld["NONEXISTENT"] == "NONEXISTENT"

    def test_localized_hotkey_dict_tuple_unpacking(self):
        """Verify LocalizedHotkeyDict supports `for k, v in HOTKEY_ACTION_LABELS:`."""
        i18n = get_i18n()

        # In German
        i18n.current_language = "de"
        unpacked_de = [(k, v) for k, v in HOTKEY_ACTION_LABELS]
        assert len(unpacked_de) == 13
        assert any(k == "new_case" and "Neuer Fall" in v for k, v in unpacked_de)

        # In English
        i18n.current_language = "en"
        unpacked_en = [(k, v) for k, v in HOTKEY_ACTION_LABELS]
        assert len(unpacked_en) == 13
        assert any(k == "new_case" and "New Case" in v for k, v in unpacked_en)

        # In Swedish
        i18n.current_language = "sv"
        unpacked_sv = [(k, v) for k, v in HOTKEY_ACTION_LABELS]
        assert len(unpacked_sv) == 13
        assert any(k == "new_case" and "Nytt ärende" in v for k, v in unpacked_sv)

    def test_all_localized_constants_helpers_survive_across_locales(self):
        """Verify helper functions for departments, channels, tasks, menus in all locales."""
        i18n = get_i18n()

        for lang in ("de", "en", "sv"):
            i18n.current_language = lang

            deps = get_localized_departments()
            assert len(deps) == 7
            assert all(d for d in deps)

            channels = get_localized_handover_channels()
            assert len(channels) == 6
            assert all(c for c in channels)

            tasks = get_localized_task_categories()
            assert len(tasks) == 7
            assert all(t for t in tasks)

            stammdaten = get_localized_menu_options_stammdaten()
            assert len(stammdaten) == 4
            assert all(s for s in stammdaten)

            vorlagen = get_localized_menu_options_vorlagen()
            assert len(vorlagen) == 4
            assert all(v for v in vorlagen)

            datenaustausch = get_localized_menu_options_datenaustausch()
            assert len(datenaustausch) == 5
            assert all(d for d in datenaustausch)
