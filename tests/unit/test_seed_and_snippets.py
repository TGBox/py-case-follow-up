"""Demo seeding (cases, schemas, templates, wiki) in every language and the SnippetService catalog/CRUD."""

import sqlite3

import pytest

from config import AppConfig
from models.case import Case
from models.snippet import Snippet
from services.export_service import ExportService
from services.i18n_service import get_i18n
from services.scoring_service import ScoringService
from services.seed_case_data import build_seed_cases
from services.seed_service import SeedService
from services.snippet_service import SnippetService, get_default_snippets
from services.storage_service import StorageService

LANGS = ["de", "en", "sv"]


def _set_lang(lang: str) -> None:
    get_i18n().current_language = lang


# --- Seed cases -------------------------------------------------------------

@pytest.mark.parametrize("lang", LANGS)
def test_seed_cases_are_valid_scored_and_round_trip(lang):
    _set_lang(lang)
    cases = build_seed_cases()
    assert [c.case_id for c in cases] == [f"T-2026-{i:04d}" for i in range(1, 13)]

    scoring = ScoringService()
    for case in cases:
        title = case.classification.title
        assert title and not title.startswith("demo_cases."), f"untranslated title in {lang}: {title}"
        assert case.validate() == []
        scoring.update_case_scoring(case)
        assert case.classification.calculated_score >= 0.0
        restored = Case.from_dict(case.to_dict())
        assert restored.classification.title == title
        assert restored.customer.practice_name == case.customer.practice_name


def test_seed_case_titles_are_translated_per_language():
    titles = {}
    for lang in LANGS:
        _set_lang(lang)
        titles[lang] = [c.classification.title for c in build_seed_cases()]

    for i in range(12):
        assert len({titles[lang][i] for lang in LANGS}) == 3, f"case {i + 1} not translated: {titles['de'][i]}"

    assert "Zuzahlungsnachforderungsdatei" in titles["de"][0]
    assert titles["de"][10] == "Alte Nachforderung aus Vorquartal (Archiviert)"
    assert titles["de"][11] == "Absturz bei PVS-GKV Abrechnungsexport"
    assert "Archived" in titles["en"][10] and "Crash" in titles["en"][11]
    assert "Arkiverat" in titles["sv"][10] and "Krasch" in titles["sv"][11]


# --- SeedService pipeline ---------------------------------------------------

@pytest.mark.parametrize("lang", LANGS)
def test_run_seed_writes_complete_localized_workspace(tmp_path, lang):
    _set_lang(lang)
    config = AppConfig(workspace_dir=tmp_path, username="test_agent")
    storage = StorageService(config)

    summary = SeedService(storage).run_seed(force=True)
    assert summary == {**summary, "customers": 5, "cases": 12, "schemas": 5, "templates": 4}
    for path in (config.cases_path, config.customers_path, config.question_schemas_path,
                 config.export_templates_path, config.wiki_db_path):
        assert path.exists()
    assert len(storage.load_cases()) == 12

    schemas = storage.load_schemas()
    assert len(schemas) == 5
    for s in schemas:
        texts = [s.display_name, s.description, *(f.label for f in s.fields)]
        texts += [f.placeholder for f in s.fields if f.placeholder]
        if s.is_repeatable_group:
            texts.append(s.repeatable_group_title)
        assert all(t and not t.startswith("schemas.") for t in texts), f"{s.schema_id} in {lang}: {texts}"

    templates = storage.load_templates()
    assert len(templates) == 4
    for t in templates:
        assert t.display_name and not t.display_name.startswith("export_templates.")
        assert t.description and not t.description.startswith("export_templates.")

    # Every applicable template renders completely on the fully populated first case.
    case = storage.load_cases()[0]
    export = ExportService(storage)
    for t in templates:
        if not t.applicable_cases or case.classification.schema_id in t.applicable_cases:
            success, missing, rendered = export.render_template(case, t)
            assert success, f"{t.template_id} on {case.case_id}: missing={missing}"
            assert len(rendered) > 50

    with sqlite3.connect(config.wiki_db_path) as conn:
        hits = conn.execute("SELECT page_id, title FROM wiki_fts WHERE wiki_fts MATCH 'ERR_DB_EXPORT_902'").fetchall()
    assert hits
    if lang == "de":
        assert "Abrechnungs-Engine" in hits[0][1]


# --- Snippets ---------------------------------------------------------------

@pytest.mark.parametrize("lang,all_label,first_category", [
    ("de", "Alle", "Rückfrage"),
    ("en", "All", "Inquiry"),
    ("sv", "Alla", "Förfrågan"),
])
def test_default_snippets_and_categories_are_localized(tmp_path, lang, all_label, first_category):
    _set_lang(lang)
    snippets = get_default_snippets()
    assert len(snippets) == 8
    assert first_category in snippets[0].category
    for s in snippets:
        assert s.snippet_id.startswith("SNIP-")
        assert not s.title.startswith("snippets.")
        assert not s.category.startswith("snippet_categories.")
        assert not s.content.startswith("snippets.")
        assert s.tags and not any(t.startswith("snippets.") for t in s.tags)
        assert s.validate() == []

    service = SnippetService(workspace_dir=tmp_path)
    assert service.get_categories()[0] == all_label
    # The "all" label of every language means no category filter.
    for label in ("Alle", "All", "Alla"):
        assert len(service.search_snippets(category=label)) == 8


def test_default_catalog_covers_core_support_scenarios(tmp_path):
    service = SnippetService(tmp_path)
    categories = service.get_categories()
    assert any("Telematik" in c for c in categories)
    assert {"Abrechnung", "System"} <= set(categories)

    titles = " | ".join(s.title for s in service.get_all_snippets())
    for word in ("Telematikinfrastruktur", "Abrechnung", "Backup", "Quartalsupdate"):
        assert word in titles


@pytest.mark.parametrize("query,expected_id", [
    ("konnektor", "SNIP-05"),
    ("SQL", "SNIP-03"),
    ("screenshot", None),
    ("backup", None),
    ("sYsTemLog", None),  # case-insensitive
])
def test_snippet_search_matches_title_content_and_tags(tmp_path, query, expected_id):
    results = SnippetService(tmp_path).search_snippets(query=query)
    assert results
    if expected_id:
        assert expected_id in [s.snippet_id for s in results]
    assert SnippetService(tmp_path).search_snippets(query="NONEXISTENT_KEYWORD_XYZ_999") == []


def test_snippet_crud_persists_and_recovers_from_corrupt_file(tmp_path):
    srv = SnippetService(workspace_dir=tmp_path)
    initial = len(srv.get_all_snippets())

    new = Snippet(title="Custom SQL Fix", category="SQL / Datenbank",
                  content="UPDATE dbo.Kunden SET status = 'ACTIVE';", tags=["custom", "sql"])
    srv.add_or_update_snippet(new)
    assert new.snippet_id == f"SNIP-{initial + 1:02d}"  # auto-assigned id

    reloaded = SnippetService(workspace_dir=tmp_path)
    assert [s.title for s in reloaded.search_snippets(query="UPDATE dbo.Kunden")] == ["Custom SQL Fix"]

    new.title = "Umbenannter Baustein 4711"
    reloaded.add_or_update_snippet(new)
    assert len(reloaded.get_all_snippets()) == initial + 1
    assert SnippetService(workspace_dir=tmp_path).search_snippets(query="4711")[0].snippet_id == new.snippet_id

    reloaded.delete_snippet(new.snippet_id)
    assert len(SnippetService(workspace_dir=tmp_path).get_all_snippets()) == initial

    (tmp_path / "data" / "snippets.json").write_text("{CORRUPTED INVALID JSON", encoding="utf-8")
    assert len(SnippetService(workspace_dir=tmp_path).get_all_snippets()) == 8
