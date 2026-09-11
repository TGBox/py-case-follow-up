from pathlib import Path
from config import AppConfig
from models.case import Case, TimelineEntry
from services.search_service import SearchService, parse_search_query
from services.storage_service import StorageService


def test_case_searchable_text_caching():
    case = Case(case_id="T-1001")
    case.classification.title = "Druckerprobleme in Praxis"
    case.customer.practice_name = "Praxis Dr. Med"
    case.timeline.append(TimelineEntry(note="Netzwerkkabel getauscht", author="Dani"))

    # Initial state: cache is None
    assert case._searchable_text is None

    # First call: computes and caches
    text1 = case.get_searchable_text()
    assert "t-1001" in text1
    assert "druckerprobleme in praxis" in text1
    assert "praxis dr. med" in text1
    assert "netzwerkkabel getauscht" in text1
    assert case._searchable_text is not None
    assert case._searchable_text == text1

    # Mutating field without invalidation returns cached text
    case.classification.title = "Neue Scanner Installation"
    assert case.get_searchable_text() == text1
    assert "scanner" not in case.get_searchable_text()

    # Invalidate cache
    case.invalidate_search_cache()
    assert case._searchable_text is None

    # Next call computes new text
    text2 = case.get_searchable_text()
    assert "neue scanner installation" in text2
    assert "scanner" in text2

    # Verify _searchable_text is transient (not serialized in to_dict)
    d = case.to_dict()
    assert "_searchable_text" not in d
    assert "searchable_text" not in d


def test_search_service_uses_cache():
    case = Case(case_id="T-2002")
    case.classification.title = "Serverabsturz Cobra CRM"
    case.customer.practice_name = "Klinik Nord"

    query = parse_search_query("Cobra")
    assert case._searchable_text is None

    matched = SearchService.matches_query(case, query)
    assert matched is True
    # The search query caused the cache to be populated
    assert case._searchable_text is not None
    assert "cobra" in case._searchable_text

    # Negative match
    query_false = parse_search_query("Apotheke")
    assert SearchService.matches_query(case, query_false) is False


def test_storage_service_update_invalidates_cache(tmp_path: Path):
    config = AppConfig(workspace_dir=tmp_path)
    config.ensure_directories()
    storage = StorageService(config)

    case = Case(case_id="T-3003")
    case.classification.title = "Initialer Titel"
    storage.save_cases([case], sync=True)

    # Compute cache
    cached = case.get_searchable_text()
    assert "initialer titel" in cached

    # Update case via storage_service
    case.classification.title = "Aktualisierter Titel"
    storage.update_single_case(case)

    # Cache should have been invalidated by update_single_case
    new_cached = case.get_searchable_text()
    assert "aktualisierter titel" in new_cached
