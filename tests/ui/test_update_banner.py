"""Update banner in the main window: shown for a newer GitHub version, hidden otherwise, dismissable, relabelled on language switch."""

from concurrent.futures import Future

import customtkinter as ctk
import pytest

from constants import UPDATE_CHECK_REPO_URL
from services import update_check_service
from services.i18n_service import get_i18n
from services.storage_service import StorageService
from ui.app import SupportCockpitApp


@pytest.fixture
def app(config):
    storage = StorageService(config)
    storage.save_profile(storage.load_profile())
    a = SupportCockpitApp(config)
    a.current_version = "3.11.5"
    a.update()
    yield a
    try:
        a.destroy()
    except Exception:
        pass


def _banner_texts(app) -> list[str]:
    assert app.update_banner is not None
    return [w.cget("text") for w in app.update_banner.winfo_children() if isinstance(w, (ctk.CTkLabel, ctk.CTkButton))]


def test_no_banner_without_update_information(app):
    assert app.update_banner is None


@pytest.mark.parametrize("latest", ["3.11.5", "3.11.4"])
def test_no_banner_when_not_newer(app, latest):
    app.on_latest_version_known(latest)
    assert app.update_banner is None


def test_banner_shows_both_versions_between_menu_and_content(app):
    app.on_latest_version_known("3.12.0")
    app.update()
    assert app.update_banner is not None and app.update_banner.winfo_manager() == "pack"
    assert any("3.12.0" in t and "3.11.5" in t for t in _banner_texts(app))
    order = app.pack_slaves()
    assert order.index(app.menu_frame) < order.index(app.update_banner) < order.index(app.container_frame)


def test_dismiss_hides_until_an_even_newer_version(app):
    app.on_latest_version_known("3.12.0")
    app.dismiss_update_banner()
    assert app.update_banner is None
    app.on_latest_version_known("3.12.0")  # periodic re-check, same version
    assert app.update_banner is None
    app.on_latest_version_known("3.12.1")
    assert app.update_banner is not None


def test_open_button_opens_repo_page(app, monkeypatch):
    opened = []
    import webbrowser
    monkeypatch.setattr(webbrowser, "open", lambda url, *a, **k: opened.append(url))
    app.on_latest_version_known("3.12.0")
    buttons = [w for w in app.update_banner.winfo_children() if isinstance(w, ctk.CTkButton) and w.cget("text") != "✕"]
    buttons[0].invoke()
    assert opened == [UPDATE_CHECK_REPO_URL]


def test_language_switch_relabels_banner_and_keeps_order(app):
    app.on_latest_version_known("3.12.0")
    get_i18n().current_language = "en"
    app.on_language_changed("en")
    app.update()
    assert any("newer version" in t for t in _banner_texts(app))
    order = app.pack_slaves()
    assert order.index(app.menu_frame) < order.index(app.update_banner) < order.index(app.container_frame)


def test_poll_picks_up_worker_result_and_reschedules(app, monkeypatch):
    future: Future = Future()
    monkeypatch.setattr(update_check_service, "fetch_latest_version_async", lambda: future)
    app._start_update_check()
    app._poll_update_check()          # not done yet -> keeps polling
    assert app.update_banner is None and app._update_check_future is future
    future.set_result("4.0.0")
    app._poll_update_check()
    assert app.update_banner is not None
    assert app._update_check_future is None and app._update_check_timer_id is not None


def test_failed_check_leaves_no_banner(app, monkeypatch):
    future: Future = Future()
    future.set_result(None)
    monkeypatch.setattr(update_check_service, "fetch_latest_version_async", lambda: future)
    app._start_update_check()
    app._poll_update_check()
    assert app.update_banner is None


def test_unknown_own_version_skips_the_check(app, monkeypatch):
    called = []
    monkeypatch.setattr(update_check_service, "fetch_latest_version_async", lambda: called.append(1))
    app.current_version = None
    app._start_update_check()
    assert called == []
