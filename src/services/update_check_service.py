"""Checks whether a newer version of the app is published on GitHub.

The single source of truth for the version is ``version`` in pyproject.toml,
which the pre-commit hook bumps on every commit. The running app reads its own
copy (bundled into the .exe via the spec file) and compares it with the copy
on the master branch of the public GitHub repository.

Everything here is UI-free and never raises: no network, a proxy that blocks
GitHub or a malformed file simply mean "no update information".
"""

import logging
import re
import sys
import threading
import tomllib
from concurrent.futures import Future
from pathlib import Path
from urllib.request import Request, urlopen

from constants import (
    PYPROJECT_FILENAME,
    UPDATE_CHECK_PYPROJECT_URL,
    UPDATE_CHECK_TIMEOUT_SECONDS,
)

logger = logging.getLogger("SupportCockpit")

_VERSION_RE = re.compile(r"^\s*v?(\d+)\.(\d+)\.(\d+)")
_TOML_VERSION_RE = re.compile(r'^\s*version\s*=\s*"([^"]+)"', re.MULTILINE)


def parse_version(text: str | None) -> tuple[int, int, int] | None:
    """'3.11.5' / 'v3.11.5' -> (3, 11, 5); anything unparseable -> None."""
    if not text:
        return None
    m = _VERSION_RE.match(text)
    return (int(m.group(1)), int(m.group(2)), int(m.group(3))) if m else None


def is_newer(latest: str | None, current: str | None) -> bool:
    """True only if both versions parse and latest is strictly greater."""
    lat, cur = parse_version(latest), parse_version(current)
    return lat is not None and cur is not None and lat > cur


def version_from_pyproject_text(text: str) -> str | None:
    """Extracts [project].version from pyproject.toml content."""
    try:
        version = tomllib.loads(text).get("project", {}).get("version")
        if isinstance(version, str):
            return version
    except tomllib.TOMLDecodeError:
        pass
    # Fallback for a truncated/odd download: the first top-level version line.
    m = _TOML_VERSION_RE.search(text)
    return m.group(1) if m else None


def _local_pyproject_path() -> Path:
    if getattr(sys, "frozen", False) and hasattr(sys, "_MEIPASS"):
        return Path(getattr(sys, "_MEIPASS", "")) / PYPROJECT_FILENAME
    # src/services/update_check_service.py -> repo root
    return Path(__file__).resolve().parents[2] / PYPROJECT_FILENAME


def get_current_version() -> str | None:
    """Version of the running app, or None if it cannot be determined."""
    path = _local_pyproject_path()
    try:
        return version_from_pyproject_text(path.read_text(encoding="utf-8"))
    except OSError as err:
        logger.warning(f"Update check: could not read own version from {path}: {err}")
        return None


def fetch_latest_version(url: str = UPDATE_CHECK_PYPROJECT_URL, timeout: float = UPDATE_CHECK_TIMEOUT_SECONDS) -> str | None:
    """Version on GitHub master, or None on any network/parse problem."""
    try:
        req = Request(url, headers={"User-Agent": "py-case-follow-up-update-check", "Cache-Control": "no-cache"})
        with urlopen(req, timeout=timeout) as resp:
            text = resp.read().decode("utf-8", errors="replace")
        return version_from_pyproject_text(text)
    except Exception as err:  # URLError, HTTPError, timeout, SSL, ...
        logger.info(f"Update check: could not fetch latest version: {err}")
        return None


def fetch_latest_version_async() -> Future:
    """Runs fetch_latest_version on a daemon thread and returns its Future.

    A daemon thread (not a ThreadPoolExecutor, whose workers are joined at
    interpreter exit) so quitting the app never waits for a slow network.
    Deliberately takes no callback: the caller polls ``future.done()`` from the
    Tk main thread, so the worker never touches or holds any Tk object - see
    the Tk-finalizer-in-thread exit hang fixed earlier.
    """
    future: Future = Future()

    def _run() -> None:
        future.set_result(fetch_latest_version())

    threading.Thread(target=_run, name="update-check", daemon=True).start()
    return future
