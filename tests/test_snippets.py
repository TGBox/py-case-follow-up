from pathlib import Path
from models.snippet import Snippet
from services.snippet_service import SnippetService


def test_snippet_model_validation():
    s = Snippet(snippet_id="S-01", title="Test", content="Text")
    assert len(s.validate()) == 0

    invalid = Snippet(snippet_id="", title="", content="")
    errors = invalid.validate()
    assert len(errors) == 3


def test_snippet_service_default_seeding_and_crud(tmp_path: Path):
    service = SnippetService(workspace_dir=tmp_path)

    # Defaults seeded
    all_snips = list(service.get_all_snippets())
    initial_count = len(all_snips)
    assert initial_count >= 4

    # Search filter
    res = service.search_snippets(query="screenshot")
    assert len(res) >= 1
    assert "Screenshots" in res[0].title

    # Add new snippet
    new_snip = Snippet(
        snippet_id="SNIP-CUSTOM",
        title="Custom SQL Fix",
        category="SQL / Datenbank",
        content="UPDATE dbo.Kunden SET status = 'ACTIVE';",
        tags=["custom", "sql"],
    )
    service.add_or_update_snippet(new_snip)

    assert len(service.get_all_snippets()) == initial_count + 1
    custom_res = service.search_snippets(query="UPDATE dbo.Kunden")
    assert len(custom_res) == 1
    assert custom_res[0].title == "Custom SQL Fix"

    # Delete snippet
    service.delete_snippet("SNIP-CUSTOM")
    assert len(service.get_all_snippets()) == initial_count
