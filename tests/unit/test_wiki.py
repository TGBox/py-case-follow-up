"""BookStack wiki sync into the offline SQLite index: config guards, HTTP path, sync modes, failure handling, search."""
import json
import os
import urllib.error
import urllib.request
from pathlib import Path

import pytest

from config import AppConfig
from enums import SyncMode
from models.profile import WikiSettings
from services.i18n_service import tr
from services.wiki_sync_service import WikiSyncService, clean_html_snippet

#: Both spellings resolve_secret() looks at, for each of the two token refs.
_TOKEN_ENV_VARS = ("BOOKSTACK_TOKEN_ID", "ENV_BOOKSTACK_TOKEN_ID", "BOOKSTACK_TOKEN_SECRET", "ENV_BOOKSTACK_TOKEN_SECRET")


@pytest.fixture
def no_wiki_tokens(monkeypatch):
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


class _RecordingMockClient:
    """A mock_client that remembers whether its page bodies were asked for."""

    def __init__(self, pages=None):
        self.pages = pages or [_page(1, "Abrechnung FAQ")]
        self.content_requested_for: list[int] = []

    def get_pages(self):
        return self.pages

    def get_page_content(self, page_id):
        self.content_requested_for.append(page_id)
        return f"Volltext zur KV-Abrechnung Seite {page_id}"


def _service(tmp_path: Path, api_url="https://wiki.example", sync_mode=SyncMode.FULL_OFFLINE) -> WikiSyncService:
    return WikiSyncService(AppConfig(workspace_dir=tmp_path), WikiSettings(api_url=api_url, sync_mode=sync_mode))


def _page(page_id: int, name: str, url: str = "") -> dict:
    return {"id": page_id, "book_id": 1, "name": name, "slug": f"p{page_id}", "url": url, "updated_at": "2026-09-01"}


def _content_by_id(service) -> dict:
    return {p["page_id"]: p["content"] for p in service.get_all_pages()}


# --- helpers ------------------------------------------------------------------

def test_env_file_tokens_are_resolved(tmp_path, monkeypatch):
    from utils.security import load_env_file, resolve_secret

    for var in _TOKEN_ENV_VARS:
        monkeypatch.delenv(var, raising=False)
    env_file = tmp_path / ".env"
    env_file.write_text("ENV_BOOKSTACK_TOKEN_ID=test_id_123\nBOOKSTACK_TOKEN_SECRET=test_secret_456\n", encoding="utf-8")
    load_env_file(env_file)
    try:
        assert resolve_secret("ENV_BOOKSTACK_TOKEN_ID") == "test_id_123"
        assert resolve_secret("ENV_BOOKSTACK_TOKEN_SECRET") == "test_secret_456"
    finally:
        for var in _TOKEN_ENV_VARS:
            os.environ.pop(var, None)


@pytest.mark.parametrize("raw, cleaned", [
    ("", ""),
    ("<b>Erster</b> Kontakt mit dem Kunden<br><p>Um die Einrichtung &amp; Registrierung...</p>",
     "Erster Kontakt mit dem Kunden Um die Einrichtung & Registrierung..."),
    ("<div><p>A&nbsp;&amp;&nbsp;B</p></div>", "A & B"),
])
def test_clean_html_snippet(raw, cleaned):
    assert clean_html_snippet(raw) == cleaned


# --- configuration guards -----------------------------------------------------

def test_sync_without_api_url_says_so_and_stores_nothing(tmp_path, no_wiki_tokens):
    service = _service(tmp_path, api_url="")
    assert service.sync_from_bookstack() == (False, tr("wiki.err_no_api_url", "Wiki-API-URL ist nicht konfiguriert."))
    assert service.get_all_pages() == []


def test_sync_with_unresolved_env_tokens_reports_missing_tokens(tmp_path, no_wiki_tokens):
    """The failure that hit a colleague: the profile only holds ENV_ references and the .env was never copied along."""
    service = _service(tmp_path)
    assert service.settings.token_id.startswith("ENV_")
    assert service.sync_from_bookstack() == (
        False, tr("wiki.err_missing_tokens", "BookStack-API-Tokens fehlen in den Umgebungsvariablen."))


# --- HTTP path ----------------------------------------------------------------

def test_full_sync_over_http_indexes_bodies_with_resolved_tokens(tmp_path, wiki_tokens, monkeypatch):
    service = _service(tmp_path)
    fake = _FakeBookStackApi(
        pages=[_page(1, "Abrechnung FAQ"), _page(2, "Fehlercode ERR_DB_902")],
        details={1: {"markdown": "KV-Abrechnung und Nachforderungen"}, 2: {"markdown": "Datenbank-Patch"}},
    )
    monkeypatch.setattr(urllib.request, "urlopen", fake)

    assert service.sync_from_bookstack() == (True, tr("wiki.sync_success", "{count} Artikel synchronisiert.", count=2))
    assert fake.requested_urls == ["https://wiki.example/api/pages", "https://wiki.example/api/pages/1",
                                   "https://wiki.example/api/pages/2"]
    # The resolved secrets must reach the API, not the ENV_ placeholders.
    assert fake.auth_headers[0] == "Token id-from-env:secret-from-env"
    assert set(_content_by_id(service)) == {1, 2}
    hits = service.search("Nachforderungen")
    assert hits and hits[0]["page_id"] == 1
    assert service.search("ERR_DB_902")[0]["page_id"] == 2


@pytest.mark.parametrize("page_url, detail, expected", [
    # A /pages/ URL breaks once a page is renamed, so it is swapped for /link/.
    ("https://wiki.example/books/b/pages/alter-slug", {}, "https://wiki.example/link/7"),
    ("", {"url": "/link/7"}, "https://wiki.example/link/7"),
    ("", {"url": "https://wiki.example/link/77"}, "https://wiki.example/link/77"),
])
def test_sync_stores_a_stable_absolute_page_link(tmp_path, wiki_tokens, monkeypatch, page_url, detail, expected):
    service = _service(tmp_path)
    monkeypatch.setattr(urllib.request, "urlopen", _FakeBookStackApi(
        pages=[_page(7, "Seite", url=page_url)], details={7: {**detail, "markdown": "Inhalt"}}))
    service.sync_from_bookstack()
    assert service.get_all_pages()[0]["url"] == expected


def test_mock_client_links_point_at_the_short_link(tmp_path):
    service = _service(tmp_path, api_url="https://wiki.data-al.de", sync_mode=SyncMode.METADATA_ONLY)
    service.sync_from_bookstack(mock_client=_RecordingMockClient([_page(1, "Abrechnung FAQ", "http://wiki/pages/1")]))
    assert "https://wiki.data-al.de/link/1" in service.search("Abrechnung")[0]["url"]


# --- failure handling ---------------------------------------------------------

def test_sync_survives_a_failing_detail_fetch(tmp_path, wiki_tokens, monkeypatch):
    """One unreachable page must not cost the whole sync."""
    service = _service(tmp_path)
    monkeypatch.setattr(urllib.request, "urlopen", _FakeBookStackApi(
        pages=[_page(1, "Geht"), _page(2, "Geht nicht")], details={1: {"markdown": "Inhalt"}}, fail_detail_for=(2,)))

    assert service.sync_from_bookstack()[0] is True
    assert _content_by_id(service) == {1: "Inhalt", 2: ""}
    # Indexed by title, so the page stays findable even without its body.
    assert service.search("Geht nicht")


def test_sync_reports_an_unreachable_page_list(tmp_path, wiki_tokens, monkeypatch):
    service = _service(tmp_path)
    monkeypatch.setattr(urllib.request, "urlopen", _FakeBookStackApi(pages=[], fail_list=True))
    success, msg = service.sync_from_bookstack()
    assert success is False
    assert msg.startswith(tr("wiki.sync_error", "Wiki-Sync-Fehler: {error}", error="").rstrip())


def test_a_failed_sync_rolls_back_and_leaves_the_index_usable(tmp_path, wiki_tokens, monkeypatch):
    """A crash mid-write must not cost the previously synced pages, and must not leave the SQLite file locked."""
    service = _service(tmp_path)
    monkeypatch.setattr(urllib.request, "urlopen", _FakeBookStackApi(
        pages=[_page(1, "Bestandsartikel")], details={1: {"markdown": "Alter Inhalt"}}))
    assert service.sync_from_bookstack()[0] is True

    # A page whose id sqlite cannot bind blows up mid-loop, after page 2 was written in the same transaction.
    monkeypatch.setattr(urllib.request, "urlopen", _FakeBookStackApi(
        pages=[_page(2, "Neu"), {"id": {"unbindable": True}, "name": "Kaputt"}], details={2: {"markdown": "Neu"}}))
    assert service.sync_from_bookstack()[0] is False

    assert set(_content_by_id(service)) == {1}, "the half-written run should have been rolled back"
    assert service.search("Bestandsartikel")


# --- sync_mode (was stored but ignored: both modes fetched every body) ----------

def test_metadata_only_requests_just_the_list_and_indexes_titles(tmp_path, wiki_tokens, monkeypatch):
    service = _service(tmp_path, sync_mode=SyncMode.METADATA_ONLY)
    fake = _FakeBookStackApi(
        pages=[_page(1, "Abrechnung FAQ"), _page(2, "Fehlercode ERR_DB_902")],
        details={1: {"markdown": "KV-Abrechnung und Nachforderungen"}, 2: {"markdown": "Volltext"}},
    )
    monkeypatch.setattr(urllib.request, "urlopen", fake)

    assert service.sync_from_bookstack()[0] is True
    assert fake.requested_urls == ["https://wiki.example/api/pages"]
    assert _content_by_id(service) == {1: "", 2: ""}
    assert service.search("ERR_DB_902")
    assert service.search("Nachforderungen") == []


def test_switching_back_to_metadata_only_drops_the_stored_bodies(tmp_path, wiki_tokens, monkeypatch):
    """Keeping bodies from an earlier full sync would contradict the setting."""
    service = _service(tmp_path, sync_mode="FULL_OFFLINE")  # the settings combo hands over a plain str
    monkeypatch.setattr(urllib.request, "urlopen", _FakeBookStackApi(
        pages=[_page(1, "Abrechnung FAQ")], details={1: {"markdown": "KV-Abrechnung und Nachforderungen"}}))
    service.sync_from_bookstack()
    assert _content_by_id(service) == {1: "KV-Abrechnung und Nachforderungen"}

    service.settings.sync_mode = SyncMode.METADATA_ONLY
    service.sync_from_bookstack()

    assert _content_by_id(service) == {1: ""}
    assert service.search("Nachforderungen") == []
    assert service.search("Abrechnung FAQ")


@pytest.mark.parametrize("mode, fetched", [(SyncMode.METADATA_ONLY, []), (SyncMode.FULL_OFFLINE, [1, 2])])
def test_mock_client_path_honours_the_sync_mode(tmp_path, mode, fetched):
    """The mode has to hold on the mock path too, or mocked callers test something production never does."""
    service = _service(tmp_path, sync_mode=mode)
    client = _RecordingMockClient([_page(1, "Zuzahlungsnachforderung im PVS"), _page(2, "GitLab Bug-Report")])

    assert service.sync_from_bookstack(mock_client=client) == (
        True, tr("wiki.sync_success", "{count} Artikel synchronisiert.", count=2))
    assert client.content_requested_for == fetched
    assert service.search("Zuzahlung")[0]["page_id"] == 1
    assert service.search("GitLab")[0]["page_id"] == 2
    assert bool(service.search("Seite")) is bool(fetched)


# --- reading ----------------------------------------------------------------

def test_reading_edge_cases(tmp_path):
    service = _service(tmp_path)
    assert service.search("") == [] and service.search("   ") == []
    Path(service.db_path).unlink()
    assert service.get_all_pages() == []


def test_wiki_widget_search_shows_no_results_hint_on_empty_index(root, config):
    from ui.widgets.wiki_widget import WikiWidget

    widget = WikiWidget(root, wiki_service=WikiSyncService(config))
    widget.search_entry.insert(0, "Setup")
    widget.on_search()
    texts = [w.cget("text") for w in widget.scroll_frame.winfo_children()]
    assert texts == [tr("wiki.no_results", "Keine treffenden Artikel im Offline-Index.")]
