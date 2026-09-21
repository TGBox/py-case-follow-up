import json
import urllib.error
import urllib.request
from pathlib import Path

import pytest

from config import AppConfig
from enums import SyncMode
from models.profile import WikiSettings
from services.wiki_sync_service import WikiSyncService
from services.i18n_service import tr


class MockBookStackClient:
    def get_pages(self):
        return [
            {"id": 1, "book_id": 10, "name": "Abrechnung FAQ", "slug": "abrechnung-faq", "url": "http://wiki/pages/1", "updated_at": "2026-08-01"},
            {"id": 2, "book_id": 10, "name": "Fehlercode ERR_DB_902", "slug": "err-db-902", "url": "http://wiki/pages/2", "updated_at": "2026-08-02"},
        ]

    def get_page_content(self, page_id):
        if page_id == 1:
            return "Anleitung zur KV-Abrechnung und Nachforderungsdateien."
        return "Detailierte Beschreibung von ERR_DB_902 und Datenbank-Patches."


def test_wiki_sync_metadata(tmp_path: Path):
    config = AppConfig(workspace_dir=tmp_path)
    settings = WikiSettings(api_url="http://wiki", sync_mode=SyncMode.METADATA_ONLY)
    service = WikiSyncService(config, settings)

    mock_client = MockBookStackClient()
    success, msg = service.sync_from_bookstack(mock_client=mock_client)

    assert success is True
    # Die Erfolgsmeldung ist uebersetzt - gegen den Locale-Key pruefen statt
    # gegen einen festen Wortlaut, sonst bricht der Test bei jeder Sprache.
    assert msg == tr("wiki.sync_success", "{count} Artikel synchronisiert.", count=2)

    results = service.search("Abrechnung")
    assert len(results) >= 1
    assert "Abrechnung FAQ" in results[0]["title"]


def test_wiki_sync_full_offline(tmp_path: Path):
    config = AppConfig(workspace_dir=tmp_path)
    settings = WikiSettings(api_url="http://wiki", sync_mode=SyncMode.FULL_OFFLINE)
    service = WikiSyncService(config, settings)

    mock_client = MockBookStackClient()
    success, msg = service.sync_from_bookstack(mock_client=mock_client)

    assert success is True

    results = service.search("ERR_DB_902")
    assert len(results) >= 1
    assert "ERR_DB_902" in results[0]["title"]


def test_env_file_loading_and_secret_resolution(tmp_path: Path):
    import os
    from utils.security import load_env_file, resolve_secret

    env_file = tmp_path / ".env"
    env_file.write_text("ENV_BOOKSTACK_TOKEN_ID=test_id_123\nBOOKSTACK_TOKEN_SECRET=test_secret_456\n", encoding="utf-8")

    load_env_file(env_file)

    assert os.environ.get("ENV_BOOKSTACK_TOKEN_ID") == "test_id_123"
    assert os.environ.get("BOOKSTACK_TOKEN_SECRET") == "test_secret_456"

    assert resolve_secret("ENV_BOOKSTACK_TOKEN_ID") == "test_id_123"
    assert resolve_secret("ENV_BOOKSTACK_TOKEN_SECRET") == "test_secret_456"


def test_clean_html_snippet_and_link_sanitization(tmp_path: Path):
    from services.wiki_sync_service import clean_html_snippet

    raw_html = "<b>Erster</b> Kontakt mit dem Kunden<br><p>Um die Einrichtung &amp; Registrierung...</p>"
    cleaned = clean_html_snippet(raw_html)
    assert "<b>" not in cleaned
    assert "<br>" not in cleaned
    assert "Erster Kontakt mit dem Kunden Um die Einrichtung & Registrierung..." == cleaned

    config = AppConfig(workspace_dir=tmp_path)
    settings = WikiSettings(api_url="https://wiki.data-al.de", sync_mode=SyncMode.METADATA_ONLY)
    service = WikiSyncService(config, settings)

    mock_client = MockBookStackClient()
    service.sync_from_bookstack(mock_client=mock_client)
    results = service.search("Abrechnung")

    assert len(results) >= 1
    assert "https://wiki.data-al.de/link/1" in results[0]["url"]


# ---------------------------------------------------------------------------
# The real BookStack path
#
# Everything above drives the service through mock_client, which skips the URL
# and token checks entirely and never touches urllib - so the code that runs in
# production was untested. These tests fake urlopen instead, which is the first
# layer the service does not own.
# ---------------------------------------------------------------------------

#: Both spellings resolve_secret() looks at, for each of the two token refs.
_TOKEN_ENV_VARS = (
    "BOOKSTACK_TOKEN_ID", "ENV_BOOKSTACK_TOKEN_ID",
    "BOOKSTACK_TOKEN_SECRET", "ENV_BOOKSTACK_TOKEN_SECRET",
)


@pytest.fixture
def no_wiki_tokens(monkeypatch):
    """Guarantees an unconfigured environment.

    test_env_file_loading_and_secret_resolution above puts real values into
    os.environ and never takes them out, so without this the token tests would
    pass or fail depending on the order pytest happens to run them in.
    """
    for var in _TOKEN_ENV_VARS:
        monkeypatch.delenv(var, raising=False)


@pytest.fixture
def wiki_tokens(monkeypatch):
    monkeypatch.setenv("BOOKSTACK_TOKEN_ID", "id-from-env")
    monkeypatch.setenv("BOOKSTACK_TOKEN_SECRET", "secret-from-env")


class _FakeResponse:
    def __init__(self, payload: dict):
        self._body = json.dumps(payload).encode("utf-8")

    def read(self) -> bytes:
        return self._body

    def __enter__(self):
        return self

    def __exit__(self, *_exc):
        return False


class _FakeBookStackApi:
    """Stands in for urlopen and answers the two endpoints the service calls."""

    def __init__(self, pages, details=None, fail_list=False, fail_detail_for=()):
        self.pages = pages
        self.details = details or {}
        self.fail_list = fail_list
        self.fail_detail_for = set(fail_detail_for)
        self.requested_urls: list[str] = []
        self.auth_headers: list[str | None] = []

    def __call__(self, req, timeout=None):
        url = getattr(req, "full_url", str(req))
        self.requested_urls.append(url)
        self.auth_headers.append(req.get_header("Authorization"))

        if url.endswith("/api/pages"):
            if self.fail_list:
                raise urllib.error.URLError("list endpoint unreachable")
            return _FakeResponse({"data": self.pages})

        page_id = int(url.rsplit("/", 1)[-1])
        if page_id in self.fail_detail_for:
            raise urllib.error.URLError("detail endpoint unreachable")
        return _FakeResponse(self.details.get(page_id, {}))


def _service(
    tmp_path: Path,
    api_url: str = "https://wiki.example",
    sync_mode=SyncMode.FULL_OFFLINE,
    **kwargs,
) -> WikiSyncService:
    return WikiSyncService(
        AppConfig(workspace_dir=tmp_path),
        WikiSettings(api_url=api_url, sync_mode=sync_mode, **kwargs),
    )


def _page(page_id: int, name: str, url: str = "") -> dict:
    return {"id": page_id, "book_id": 1, "name": name, "slug": f"p{page_id}",
            "url": url, "updated_at": "2026-09-01"}


# --- configuration guards --------------------------------------------------


def test_sync_without_api_url_says_so_and_stores_nothing(tmp_path: Path, no_wiki_tokens):
    service = _service(tmp_path, api_url="")

    success, msg = service.sync_from_bookstack()

    assert success is False
    assert msg == tr("wiki.err_no_api_url", "Wiki-API-URL ist nicht konfiguriert.")
    assert service.get_all_pages() == []


def test_sync_with_unresolved_env_tokens_reports_missing_tokens(tmp_path: Path, no_wiki_tokens):
    """The failure that hit a colleague: the profile only holds ENV_ references
    and the .env holding the actual values was never copied along."""
    service = _service(tmp_path)
    assert service.settings.token_id.startswith("ENV_")

    success, msg = service.sync_from_bookstack()

    assert success is False
    assert msg == tr("wiki.err_missing_tokens", "BookStack-API-Tokens fehlen in den Umgebungsvariablen.")


def test_sync_with_env_tokens_present_reaches_the_api(tmp_path: Path, wiki_tokens, monkeypatch):
    service = _service(tmp_path)
    fake = _FakeBookStackApi(pages=[_page(1, "Abrechnung")], details={1: {"markdown": "Inhalt"}})
    monkeypatch.setattr(urllib.request, "urlopen", fake)

    success, _msg = service.sync_from_bookstack()

    assert success is True
    assert fake.requested_urls[0] == "https://wiki.example/api/pages"
    # The resolved secrets must reach the API, not the ENV_ placeholders.
    assert fake.auth_headers[0] == "Token id-from-env:secret-from-env"


# --- indexing --------------------------------------------------------------


def test_sync_indexes_pages_from_the_http_api(tmp_path: Path, wiki_tokens, monkeypatch):
    service = _service(tmp_path)
    monkeypatch.setattr(urllib.request, "urlopen", _FakeBookStackApi(
        pages=[_page(1, "Abrechnung FAQ"), _page(2, "Fehlercode ERR_DB_902")],
        details={1: {"markdown": "KV-Abrechnung und Nachforderungen"},
                 2: {"markdown": "Datenbank-Patch fuer ERR_DB_902"}},
    ))

    success, msg = service.sync_from_bookstack()

    assert success is True
    assert msg == tr("wiki.sync_success", "{count} Artikel synchronisiert.", count=2)
    assert {p["page_id"] for p in service.get_all_pages()} == {1, 2}
    hits = service.search("Nachforderungen")
    assert hits and hits[0]["page_id"] == 1


def test_sync_replaces_a_pages_url_with_the_short_link(tmp_path: Path, wiki_tokens, monkeypatch):
    """A /pages/ URL breaks once a page is renamed, so it is swapped for /link/."""
    service = _service(tmp_path)
    monkeypatch.setattr(urllib.request, "urlopen", _FakeBookStackApi(
        pages=[_page(7, "Umbenannt", url="https://wiki.example/books/b/pages/alter-slug")],
        details={7: {"markdown": "Inhalt"}},
    ))

    service.sync_from_bookstack()

    page = service.get_all_pages()[0]
    assert page["url"] == "https://wiki.example/link/7"


def test_sync_makes_a_relative_detail_url_absolute(tmp_path: Path, wiki_tokens, monkeypatch):
    service = _service(tmp_path)
    monkeypatch.setattr(urllib.request, "urlopen", _FakeBookStackApi(
        pages=[_page(8, "Relativ")],
        details={8: {"url": "/link/8", "markdown": "Inhalt"}},
    ))

    service.sync_from_bookstack()

    assert service.get_all_pages()[0]["url"] == "https://wiki.example/link/8"


def test_sync_keeps_a_usable_absolute_detail_url(tmp_path: Path, wiki_tokens, monkeypatch):
    service = _service(tmp_path)
    monkeypatch.setattr(urllib.request, "urlopen", _FakeBookStackApi(
        pages=[_page(9, "Absolut")],
        details={9: {"url": "https://wiki.example/link/9", "markdown": "Inhalt"}},
    ))

    service.sync_from_bookstack()

    assert service.get_all_pages()[0]["url"] == "https://wiki.example/link/9"


# --- failure handling ------------------------------------------------------


def test_sync_survives_a_failing_detail_fetch(tmp_path: Path, wiki_tokens, monkeypatch):
    """One unreachable page must not cost the whole sync."""
    service = _service(tmp_path)
    monkeypatch.setattr(urllib.request, "urlopen", _FakeBookStackApi(
        pages=[_page(1, "Geht"), _page(2, "Geht nicht")],
        details={1: {"markdown": "Inhalt"}},
        fail_detail_for=(2,),
    ))

    success, _msg = service.sync_from_bookstack()

    assert success is True
    by_id = {p["page_id"]: p for p in service.get_all_pages()}
    assert set(by_id) == {1, 2}
    assert by_id[1]["content"] == "Inhalt"
    # Indexed by title, so the page stays findable even without its body.
    assert by_id[2]["content"] == ""
    assert service.search("Geht nicht")


def test_sync_reports_an_unreachable_page_list(tmp_path: Path, wiki_tokens, monkeypatch):
    service = _service(tmp_path)
    monkeypatch.setattr(urllib.request, "urlopen", _FakeBookStackApi(pages=[], fail_list=True))

    success, msg = service.sync_from_bookstack()

    assert success is False
    assert msg.startswith(tr("wiki.sync_error", "Wiki-Sync-Fehler: {error}", error="").rstrip())


def test_a_failed_sync_rolls_back_and_leaves_the_index_usable(tmp_path: Path, wiki_tokens, monkeypatch):
    """A crash mid-write must not cost the previously synced pages, and must not
    leave the SQLite file locked for the next read."""
    service = _service(tmp_path)

    monkeypatch.setattr(urllib.request, "urlopen", _FakeBookStackApi(
        pages=[_page(1, "Bestandsartikel")], details={1: {"markdown": "Alter Inhalt"}},
    ))
    assert service.sync_from_bookstack()[0] is True

    # A page whose id sqlite cannot bind blows up mid-loop, after page 2 was
    # already written inside the same transaction.
    monkeypatch.setattr(urllib.request, "urlopen", _FakeBookStackApi(
        pages=[_page(2, "Neu"), {"id": {"unbindable": True}, "name": "Kaputt"}],
        details={2: {"markdown": "Neuer Inhalt"}},
    ))
    success, _msg = service.sync_from_bookstack()

    assert success is False
    ids = {p["page_id"] for p in service.get_all_pages()}
    assert ids == {1}, "the half-written run should have been rolled back"
    # Reading still works, so the connection was closed despite the failure.
    assert service.search("Bestandsartikel")


# --- reading ---------------------------------------------------------------


def test_search_ignores_an_empty_query(tmp_path: Path):
    service = _service(tmp_path)
    assert service.search("") == []
    assert service.search("   ") == []


def test_get_all_pages_without_a_database_returns_empty(tmp_path: Path):
    service = _service(tmp_path)
    Path(service.db_path).unlink()
    assert service.get_all_pages() == []


def test_clean_html_snippet_handles_empty_and_nested_markup():
    from services.wiki_sync_service import clean_html_snippet

    assert clean_html_snippet("") == ""
    assert clean_html_snippet("<div><p>A&nbsp;&amp;&nbsp;B</p></div>") == "A & B"


# ---------------------------------------------------------------------------
# sync_mode
#
# The setting was stored, shown and saved, but sync_from_bookstack never read
# it - both modes fetched every page body. These pin down the difference.
# ---------------------------------------------------------------------------


class _RecordingMockClient:
    """A mock_client that remembers whether its page bodies were asked for."""

    def __init__(self):
        self.content_requested_for: list[int] = []

    def get_pages(self):
        return [_page(1, "Abrechnung FAQ")]

    def get_page_content(self, page_id):
        self.content_requested_for.append(page_id)
        return "Volltext zur KV-Abrechnung"


def test_metadata_only_asks_for_the_page_list_and_nothing_else(tmp_path: Path, wiki_tokens, monkeypatch):
    service = _service(tmp_path, sync_mode=SyncMode.METADATA_ONLY)
    fake = _FakeBookStackApi(
        pages=[_page(1, "Abrechnung FAQ"), _page(2, "Fehlercode ERR_DB_902")],
        details={1: {"markdown": "Volltext"}, 2: {"markdown": "Volltext"}},
    )
    monkeypatch.setattr(urllib.request, "urlopen", fake)

    success, _msg = service.sync_from_bookstack()

    assert success is True
    # One request for the list, none per page - that is the point of the mode.
    assert fake.requested_urls == ["https://wiki.example/api/pages"]
    pages = {p["page_id"]: p for p in service.get_all_pages()}
    assert set(pages) == {1, 2}
    assert all(p["content"] == "" for p in pages.values())


def test_metadata_only_still_finds_pages_by_title(tmp_path: Path, wiki_tokens, monkeypatch):
    service = _service(tmp_path, sync_mode=SyncMode.METADATA_ONLY)
    monkeypatch.setattr(urllib.request, "urlopen", _FakeBookStackApi(
        pages=[_page(1, "Fehlercode ERR_DB_902")], details={1: {"markdown": "Volltext"}},
    ))

    service.sync_from_bookstack()

    assert service.search("ERR_DB_902")


def test_full_offline_fetches_every_page_body(tmp_path: Path, wiki_tokens, monkeypatch):
    service = _service(tmp_path, sync_mode=SyncMode.FULL_OFFLINE)
    fake = _FakeBookStackApi(
        pages=[_page(1, "Abrechnung FAQ"), _page(2, "Fehlercode ERR_DB_902")],
        details={1: {"markdown": "KV-Abrechnung und Nachforderungen"},
                 2: {"markdown": "Datenbank-Patch"}},
    )
    monkeypatch.setattr(urllib.request, "urlopen", fake)

    service.sync_from_bookstack()

    assert fake.requested_urls == [
        "https://wiki.example/api/pages",
        "https://wiki.example/api/pages/1",
        "https://wiki.example/api/pages/2",
    ]
    # Only the full mode makes the article text searchable offline.
    assert service.search("Nachforderungen")


def test_metadata_only_does_not_find_body_text(tmp_path: Path, wiki_tokens, monkeypatch):
    service = _service(tmp_path, sync_mode=SyncMode.METADATA_ONLY)
    monkeypatch.setattr(urllib.request, "urlopen", _FakeBookStackApi(
        pages=[_page(1, "Abrechnung FAQ")],
        details={1: {"markdown": "KV-Abrechnung und Nachforderungen"}},
    ))

    service.sync_from_bookstack()

    assert service.search("Abrechnung FAQ")
    assert service.search("Nachforderungen") == []


def test_switching_back_to_metadata_only_drops_the_stored_bodies(tmp_path: Path, wiki_tokens, monkeypatch):
    """Keeping bodies from an earlier full sync would contradict the setting."""
    service = _service(tmp_path, sync_mode=SyncMode.FULL_OFFLINE)
    monkeypatch.setattr(urllib.request, "urlopen", _FakeBookStackApi(
        pages=[_page(1, "Abrechnung FAQ")],
        details={1: {"markdown": "KV-Abrechnung und Nachforderungen"}},
    ))
    service.sync_from_bookstack()
    assert service.get_all_pages()[0]["content"] != ""

    service.settings.sync_mode = SyncMode.METADATA_ONLY
    service.sync_from_bookstack()

    assert service.get_all_pages()[0]["content"] == ""
    assert service.search("Nachforderungen") == []
    assert service.search("Abrechnung FAQ")


def test_mode_read_from_a_plain_settings_string(tmp_path: Path, wiki_tokens, monkeypatch):
    """The settings combo hands over a str, not the enum member."""
    service = _service(tmp_path, sync_mode="FULL_OFFLINE")
    fake = _FakeBookStackApi(pages=[_page(1, "Abrechnung")], details={1: {"markdown": "Volltext"}})
    monkeypatch.setattr(urllib.request, "urlopen", fake)

    service.sync_from_bookstack()

    assert "https://wiki.example/api/pages/1" in fake.requested_urls
    assert service.get_all_pages()[0]["content"] == "Volltext"


def test_mock_client_path_honours_metadata_only(tmp_path: Path):
    """The mode has to hold on the mock path too, or the tests above would be
    testing something the mocked callers never see."""
    service = _service(tmp_path, sync_mode=SyncMode.METADATA_ONLY)
    client = _RecordingMockClient()

    service.sync_from_bookstack(mock_client=client)

    assert client.content_requested_for == []
    assert service.get_all_pages()[0]["content"] == ""


def test_mock_client_path_honours_full_offline(tmp_path: Path):
    service = _service(tmp_path, sync_mode=SyncMode.FULL_OFFLINE)
    client = _RecordingMockClient()

    service.sync_from_bookstack(mock_client=client)

    assert client.content_requested_for == [1]
    assert service.get_all_pages()[0]["content"] == "Volltext zur KV-Abrechnung"
