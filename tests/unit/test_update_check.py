"""update_check_service: version parsing/comparison, own version, GitHub fetch (mocked)."""

import io
from pathlib import Path
from urllib.error import URLError

import pytest

from services import update_check_service as ucs
from services.update_check_service import fetch_latest_version as real_fetch_latest_version

REPO = Path(__file__).resolve().parents[2]


@pytest.mark.parametrize("text, expected", [
    ("3.11.5", (3, 11, 5)),
    ("v3.11.5", (3, 11, 5)),
    (" 10.0.1-beta", (10, 0, 1)),
    ("3.11", None),
    ("", None),
    (None, None),
    ("abc", None),
])
def test_parse_version(text, expected):
    assert ucs.parse_version(text) == expected


@pytest.mark.parametrize("latest, current, expected", [
    ("3.11.6", "3.11.5", True),
    ("3.12.0", "3.11.9", True),
    ("4.0.0", "3.99.99", True),
    ("3.11.10", "3.11.9", True),   # numeric, not string comparison
    ("3.11.5", "3.11.5", False),
    ("3.11.4", "3.11.5", False),   # running a local build ahead of master
    (None, "3.11.5", False),
    ("3.11.6", None, False),
    ("garbage", "3.11.5", False),
])
def test_is_newer(latest, current, expected):
    assert ucs.is_newer(latest, current) is expected


def test_version_from_pyproject_text_reads_project_version_only():
    text = '[tool.x]\nversion = "9.9.9"\n\n[project]\nname = "x"\nversion = "1.2.3"\n'
    assert ucs.version_from_pyproject_text(text) == "1.2.3"


def test_version_from_pyproject_text_falls_back_on_broken_toml():
    assert ucs.version_from_pyproject_text('version = "2.0.1"\n[[[broken') == "2.0.1"
    assert ucs.version_from_pyproject_text("nothing here") is None


def test_current_version_matches_repo_pyproject():
    import tomllib
    expected = tomllib.loads((REPO / "pyproject.toml").read_text(encoding="utf-8"))["project"]["version"]
    assert ucs.get_current_version() == expected


def test_current_version_in_frozen_build_reads_meipass(tmp_path, monkeypatch):
    (tmp_path / "pyproject.toml").write_text('[project]\nversion = "7.7.7"\n', encoding="utf-8")
    monkeypatch.setattr(ucs.sys, "frozen", True, raising=False)
    monkeypatch.setattr(ucs.sys, "_MEIPASS", str(tmp_path), raising=False)
    assert ucs.get_current_version() == "7.7.7"


def test_current_version_missing_file_returns_none(tmp_path, monkeypatch):
    monkeypatch.setattr(ucs.sys, "frozen", True, raising=False)
    monkeypatch.setattr(ucs.sys, "_MEIPASS", str(tmp_path), raising=False)
    assert ucs.get_current_version() is None


class _FakeResponse(io.BytesIO):
    def __enter__(self):
        return self

    def __exit__(self, *exc):
        self.close()


def test_fetch_latest_version_parses_remote_pyproject(monkeypatch):
    seen = {}

    def fake_urlopen(req, timeout):
        seen["url"], seen["timeout"] = req.full_url, timeout
        return _FakeResponse(b'[project]\nname = "py-case-follow-up"\nversion = "3.12.0"\n')

    monkeypatch.setattr(ucs, "urlopen", fake_urlopen)
    assert real_fetch_latest_version() == "3.12.0"
    assert seen["url"] == ucs.UPDATE_CHECK_PYPROJECT_URL
    assert seen["timeout"] == ucs.UPDATE_CHECK_TIMEOUT_SECONDS


@pytest.mark.parametrize("error", [URLError("offline"), TimeoutError("slow"), OSError("proxy")])
def test_fetch_latest_version_swallows_network_errors(monkeypatch, error):
    def fake_urlopen(req, timeout):
        raise error

    monkeypatch.setattr(ucs, "urlopen", fake_urlopen)
    assert real_fetch_latest_version() is None


def test_fetch_async_returns_future_with_result(monkeypatch):
    monkeypatch.setattr(ucs, "fetch_latest_version", lambda: "5.0.0")
    assert ucs.fetch_latest_version_async().result(timeout=5) == "5.0.0"


def test_spec_bundles_pyproject_for_frozen_version_lookup():
    spec = (REPO / "py-case-follow-up.spec").read_text(encoding="utf-8")
    assert "('pyproject.toml', '.')" in spec
