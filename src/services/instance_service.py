"""Single-instance detection and case hand-off between processes.

Clicking a Windows notification cannot talk to the running app directly: Windows
starts a *new* process with the toast's launch URI on the command line. That
second process therefore has to notice the first one, hand the case over and
exit again, otherwise every click would open a second copy of the app.

The hand-off runs over two small files in the workspace directory:

  instance.lock          the running app rewrites it about twice a minute, so a
                         recent mtime means "an instance is alive". A lock left
                         behind by a crash simply ages out; no PID is consulted,
                         because os.kill(pid, 0) on Windows does not probe a
                         process - it terminates it.
  open_case_request.json what the second process leaves behind. The running app
                         polls for it, opens the case and deletes the file.

Requests carry a timestamp and are ignored once they are older than
REQUEST_MAX_AGE_SECONDS, so a request written while the app was being shut down
does not make it jump to an unrelated case at the next start.
"""

import json
import logging
import os
import sys
import time
from pathlib import Path
from urllib.parse import quote, unquote

from constants import (
    HEARTBEAT_INTERVAL_SECONDS,
    LOCK_FILENAME,
    LOCK_STALE_SECONDS,
    PROTOCOL_HANDLER_DESCRIPTION,
    REQUEST_FILENAME,
    REQUEST_MAX_AGE_SECONDS,
    URI_SCHEME,
)

logger = logging.getLogger("SupportCockpit")

_CASE_URI_PREFIX = f"{URI_SCHEME}://case/"

__all__ = [
    "HEARTBEAT_INTERVAL_SECONDS",
    "InstanceService",
    "LOCK_FILENAME",
    "LOCK_STALE_SECONDS",
    "PROTOCOL_HANDLER_DESCRIPTION",
    "REQUEST_FILENAME",
    "REQUEST_MAX_AGE_SECONDS",
    "URI_SCHEME",
    "build_case_uri",
    "parse_case_uri",
    "register_uri_scheme",
    "should_register",
]


def build_case_uri(case_id: str) -> str:
    """URI that opens one case. This is what a notification's launch action carries."""
    return _CASE_URI_PREFIX + quote(case_id, safe="")


def parse_case_uri(value: str | None) -> str | None:
    """Case id from a launch URI, or from a plain id passed via --open-case.

    Windows hands the protocol handler the raw URI, sometimes with a trailing
    slash appended by the shell, so both spellings have to be accepted.
    """
    if not value:
        return None
    text = value.strip().strip('"')
    if not text:
        return None

    lowered = text.lower()
    if lowered.startswith(f"{URI_SCHEME}:"):
        remainder = text[len(URI_SCHEME) + 1:].lstrip("/")
        if remainder.lower().startswith("case/"):
            remainder = remainder[len("case/"):]
        remainder = remainder.rstrip("/")
        return unquote(remainder) or None

    # A bare id, e.g. `--open-case T-2026-0042`.
    return text


class InstanceService:
    """Owns the lock and request files for one workspace.

    Scoped to the workspace directory on purpose: two workspaces are two
    unrelated apps and must not lock each other out.
    """

    def __init__(self, workspace_dir: Path | str):
        self.workspace_dir = Path(workspace_dir)
        self.lock_path = self.workspace_dir / LOCK_FILENAME
        self.request_path = self.workspace_dir / REQUEST_FILENAME
        self._owns_lock = False

    # --- lock ---

    def is_running(self) -> bool:
        """True when another instance has refreshed the lock recently."""
        try:
            age = time.time() - self.lock_path.stat().st_mtime
        except OSError:
            return False
        return age < LOCK_STALE_SECONDS

    @property
    def owns_lock(self) -> bool:
        """True when this process is the one answering hand-offs."""
        return self._owns_lock

    def acquire(self) -> bool:
        """Claims the lock. False when another instance already holds it, or the file is unwritable.

        Only the holder answers hand-offs. Without that restriction a second app
        on the same workspace would overwrite the lock and both would poll for
        the same request file - whichever happened to read it first would open
        the case, which is a coin toss from the user's side.
        """
        if self.is_running() and not self._owns_lock:
            return False
        if self.heartbeat():
            self._owns_lock = True
            return True
        return False

    def heartbeat(self) -> bool:
        """Refreshes the lock's mtime. Called periodically by the running app."""
        try:
            self.workspace_dir.mkdir(parents=True, exist_ok=True)
            self.lock_path.write_text(str(os.getpid()), encoding="utf-8")
            return True
        except OSError as err:
            logger.debug(f"Could not write instance lock: {err}")
            return False

    def release(self) -> None:
        """Drops the lock on a clean shutdown so a restart is not delayed by the stale window."""
        if not self._owns_lock:
            return
        self._owns_lock = False
        try:
            self.lock_path.unlink()
        except OSError:
            pass

    def handoff_or_claim(self, case_id: str | None) -> bool:
        """Decides what a starting process should do. True means "exit now".

        True only when a live instance actually accepted the case. If the
        request cannot be written the caller starts normally instead, so a
        read-only or full workspace costs the user a second window rather than
        a click that appears to do nothing.
        """
        if case_id and self.is_running() and self.write_open_case_request(case_id):
            return True
        self.acquire()
        return False

    # --- case hand-off ---

    def write_open_case_request(self, case_id: str) -> bool:
        """Leaves a case for the running instance to pick up.

        Written to a temporary file and moved into place: the running app polls
        this path, and os.replace is atomic, so it can never read a half-written
        file.
        """
        payload = {"case_id": case_id, "ts": time.time()}
        tmp_path = self.request_path.with_suffix(".tmp")
        try:
            self.workspace_dir.mkdir(parents=True, exist_ok=True)
            tmp_path.write_text(json.dumps(payload), encoding="utf-8")
            os.replace(tmp_path, self.request_path)
            return True
        except OSError as err:
            logger.warning(f"Could not write open-case request: {err}")
            try:
                tmp_path.unlink()
            except OSError:
                pass
            return False

    def consume_open_case_request(self) -> str | None:
        """Returns the requested case id once, deleting the request file.

        Deleting even an unreadable or outdated request is intentional: a file
        that cannot be acted on must not be re-read on every poll.
        """
        try:
            raw = self.request_path.read_text(encoding="utf-8")
        except OSError:
            return None

        try:
            self.request_path.unlink()
        except OSError:
            pass

        try:
            payload = json.loads(raw)
            case_id = str(payload.get("case_id") or "").strip()
            ts = float(payload.get("ts") or 0.0)
        except (ValueError, TypeError, AttributeError) as err:
            logger.debug(f"Ignoring malformed open-case request: {err}")
            return None

        if not case_id:
            return None
        if time.time() - ts > REQUEST_MAX_AGE_SECONDS:
            logger.info(f"Ignoring stale open-case request for {case_id}")
            return None
        return case_id


def _registered_command() -> str | None:
    """What HKCU currently runs for supportcockpit://, or None if nothing is registered."""
    try:
        import winreg  # pyright: ignore[reportMissingModuleSource] - Windows-only stdlib module

        with winreg.OpenKey(winreg.HKEY_CURRENT_USER, rf"Software\Classes\{URI_SCHEME}\shell\open\command") as key:
            # "" is the key's default value - the entry Windows actually runs.
            value, _ = winreg.QueryValueEx(key, "")
            return str(value)
    except Exception:
        return None


def _launch_command() -> str:
    """Command line Windows should run for a supportcockpit:// URI.

    A frozen build is its own executable; a development run is the interpreter
    plus main.py, and both have to survive spaces in the path, hence the quotes.
    """
    exe = Path(sys.executable).resolve()
    if getattr(sys, "frozen", False):
        return f'"{exe}" --open-case "%1"'
    script = Path(__file__).resolve().parents[2] / "main.py"
    return f'"{exe}" "{script}" --open-case "%1"'


def should_register(current: str | None, command: str, frozen: bool) -> bool:
    """Whether the URI handler should be (re)written.

    Three rules, in order: an unchanged entry is left alone so a normal start
    does not touch the registry at all; nothing registered means this build
    claims it; and an entry that belongs to another build is only overwritten by
    a packaged .exe - so a quick run from source cannot take the handler away
    from the installed app and leave every later click pointing at a checkout.
    """
    if current == command:
        return False
    if not current:
        return True
    return frozen


def register_uri_scheme() -> bool:
    """Registers supportcockpit:// for the current user (HKCU, no admin rights).

    Without this the OS notification's launch action goes nowhere and clicking
    the toast does nothing at all. Writing under HKCU\\Software\\Classes keeps it
    per-user and installer-free, which is what a copied .exe needs.

    Windows-only; a no-op elsewhere. Cannot be exercised on Linux/CI, so the
    registry values are kept to the documented minimum.
    """
    if not sys.platform.startswith("win"):
        return False

    command = _launch_command()
    current = _registered_command()
    if not should_register(current, command, frozen=bool(getattr(sys, "frozen", False))):
        if current != command:
            logger.info(f"Leaving the registered {URI_SCHEME}:// handler untouched: {current}")
        return current == command

    try:
        import winreg  # pyright: ignore[reportMissingModuleSource] - Windows-only stdlib module

        base = rf"Software\Classes\{URI_SCHEME}"
        with winreg.CreateKey(winreg.HKEY_CURRENT_USER, base) as key:
            winreg.SetValueEx(key, None, 0, winreg.REG_SZ, PROTOCOL_HANDLER_DESCRIPTION)
            winreg.SetValueEx(key, "URL Protocol", 0, winreg.REG_SZ, "")
        with winreg.CreateKey(winreg.HKEY_CURRENT_USER, rf"{base}\shell\open\command") as key:
            winreg.SetValueEx(key, None, 0, winreg.REG_SZ, command)
        logger.info(f"Registered {URI_SCHEME}:// handler: {command}")
        return True
    except Exception as err:
        logger.warning(f"Could not register {URI_SCHEME}:// URI scheme: {err}")
        return False
