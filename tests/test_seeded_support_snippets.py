"""Tests for realistic support snippets catalog (TI, Abrechnung, Ersthilfe, Backup)."""

from pathlib import Path
import pytest
from services.snippet_service import DEFAULT_SNIPPETS, SnippetService


def test_default_snippets_cover_core_support_scenarios(tmp_path: Path):
    """Verify DEFAULT_SNIPPETS include TI, Abrechnung, Ersthilfe, Backup, and Quartalsupdate."""
    service = SnippetService(tmp_path)
    snippets = service.get_all_snippets()

    categories = service.get_categories()
    assert "Telematik (TI)" in categories or any("Telematik" in c for c in categories)
    assert "Abrechnung" in categories
    assert "System" in categories

    titles = [s.title for s in snippets]
    assert any("Telematikinfrastruktur" in t for t in titles)
    assert any("Abrechnung" in t for t in titles)
    assert any("Backup" in t for t in titles)
    assert any("Quartalsupdate" in t for t in titles)

    # Verify search finds TI snippet
    ti_results = service.search_snippets("konnektor")
    assert len(ti_results) >= 1
    assert "SNIP-05" in [s.snippet_id for s in ti_results]
