import json
import logging
import secrets
import threading
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from constants import (
    DEFAULT_NTFY_SERVER_URL,
    NTFY_ACTION_SNOOZE_MINUTES,
    NTFY_ACTION_TYPE_HTTP,
    NTFY_CMD_PREFIX_SNOOZE,
    NTFY_CMD_PREFIX_TAKE,
    NTFY_CMD_SEPARATOR,
    NTFY_EVENT_FOLLOWUP,
    NTFY_EVENT_HANDOVER,
    NTFY_EVENT_NOTE,
    NTFY_EVENT_PRIO1,
    NTFY_HTTP_TIMEOUT_SECONDS,
    NTFY_PRIO_DEFAULT,
    NTFY_STREAM_RECONNECT_DELAY_SECONDS,
    NTFY_STREAM_TIMEOUT_SECONDS,
    NTFY_TAG_BELL,
    NTFY_TAG_DIGEST,
    NTFY_TAG_ESCALATION,
    NTFY_TAG_HANDOVER,
    NTFY_TAG_NOTE,
    NTFY_TAG_ON_CALL,
    NTFY_TAG_WARNING,
    NTFY_TOPIC_PREFIX,
    NTFY_TOPIC_RANDOM_LENGTH,
)
from services.i18n_service import tr

logger = logging.getLogger("SupportCockpit")


class NtfyService:
    """Dispatches outbound push notifications to ntfy.sh or self-hosted ntfy servers."""

    @staticmethod
    def generate_random_topic() -> str:
        """Generates a random, non-guessable topic string for zero-setup pairing."""
        num_bytes = max(1, NTFY_TOPIC_RANDOM_LENGTH // 2)
        random_suffix = secrets.token_hex(num_bytes)
        return f"{NTFY_TOPIC_PREFIX}{random_suffix}"

    @staticmethod
    def get_event_tags(event_type: str = NTFY_EVENT_FOLLOWUP, on_call: bool = False) -> list[str]:
        """Returns relevant emoji tag list based on the event type."""
        if event_type == "digest":
            tags = [NTFY_TAG_DIGEST]
        elif event_type == NTFY_EVENT_PRIO1:
            tags = [NTFY_TAG_WARNING, NTFY_TAG_ESCALATION]
        elif event_type == NTFY_EVENT_HANDOVER:
            tags = [NTFY_TAG_HANDOVER]
        elif event_type == NTFY_EVENT_NOTE:
            tags = [NTFY_TAG_NOTE]
        else:
            tags = [NTFY_TAG_BELL]
        if on_call:
            tags.append(NTFY_TAG_ON_CALL)
        return tags

    @staticmethod
    def format_case_alert(
        case_id: str,
        priority_label: str = "",
        is_overdue: bool = False,
        event_type: str = NTFY_EVENT_FOLLOWUP,
        anonymize: bool = True,
        on_call: bool = False,
    ) -> tuple[str, str]:
        """Creates privacy-friendly, tokenized notification title and message."""
        if event_type == NTFY_EVENT_PRIO1:
            title = tr(
                "ntfy.prio1_alert_title",
                "🚨 Notfall / Prio 1: Fall #{case_id}",
                case_id=case_id,
            )
            message = tr(
                "ntfy.prio1_alert_msg",
                "Kritischer Fall erfordert sofortige Aufmerksamkeit.",
            )
        elif event_type == NTFY_EVENT_HANDOVER:
            title = tr(
                "ntfy.handover_alert_title",
                "📋 Übergabe: Fall #{case_id}",
                case_id=case_id,
            )
            message = tr(
                "ntfy.handover_alert_msg",
                "Neuer Fall an Sie übergeben oder zugewiesen.",
            )
        elif event_type == NTFY_EVENT_NOTE:
            title = tr(
                "ntfy.note_alert_title",
                "📝 Notiz: Fall #{case_id}",
                case_id=case_id,
            )
            message = tr(
                "ntfy.note_alert_msg",
                "Neue Kunden- oder Vorgangsnotiz erfasst.",
            )
        else:
            title = tr(
                "ntfy.case_alert_title",
                "🔔 Fall #{case_id} ({priority})",
                case_id=case_id,
                priority=priority_label,
            )
            if is_overdue:
                message = tr(
                    "ntfy.case_alert_overdue",
                    "⚠ Wiedervorlage überfällig am Arbeitsplatz!",
                )
            else:
                message = tr(
                    "ntfy.case_alert_due",
                    "Wiedervorlage fällig am Arbeitsplatz.",
                )

        if on_call:
            prefix = tr("ntfy.on_call_prefix", "[Notdienst] ")
            title = f"{prefix}{title}"

        return title, message

    @staticmethod
    def format_digest_alert(events: list[dict[str, Any]], anonymize: bool = True) -> tuple[str, str]:
        """Creates a bundled, privacy-friendly summary of multiple routine events."""
        total = len(events)
        title = tr(
            "ntfy.digest_alert_title",
            "📦 Sammelbericht: {count} neue Ereignisse",
            count=total,
        )
        followup_count = sum(1 for e in events if e.get("event_type") == NTFY_EVENT_FOLLOWUP)
        handover_count = sum(1 for e in events if e.get("event_type") == NTFY_EVENT_HANDOVER)
        note_count = sum(1 for e in events if e.get("event_type") == NTFY_EVENT_NOTE)
        prio1_count = sum(1 for e in events if e.get("event_type") == NTFY_EVENT_PRIO1)

        lines: list[str] = []
        if prio1_count > 0:
            lines.append(tr("ntfy.digest_prio1_line", "🚨 {count}x Notfall / Prio 1", count=prio1_count))
        if followup_count > 0:
            lines.append(tr("ntfy.digest_followup_line", "🔔 {count}x Fällige Wiedervorlage", count=followup_count))
        if handover_count > 0:
            lines.append(tr("ntfy.digest_handover_line", "📋 {count}x Übergabe / Zuweisung", count=handover_count))
        if note_count > 0:
            lines.append(tr("ntfy.digest_note_line", "📝 {count}x Neue Notiz", count=note_count))

        case_ids = list(dict.fromkeys(str(e.get("case_id", "")) for e in events if e.get("case_id")))
        if case_ids:
            if len(case_ids) <= 5:
                id_list = ", ".join(f"#{cid}" for cid in case_ids)
                lines.append(tr("ntfy.digest_cases_line", "Betroffene Fälle: {cases}", cases=id_list))
            else:
                lines.append(tr("ntfy.digest_cases_many_line", "{count} Fälle betroffen", count=len(case_ids)))

        message = "\n".join(lines) if lines else tr("ntfy.digest_empty_msg", "Keine neuen Details.")
        return title, message

    @staticmethod
    def format_case_actions(
        case_id: str,
        response_topic: str,
        server_url: str = DEFAULT_NTFY_SERVER_URL,
    ) -> list[dict[str, Any]]:
        """Creates action buttons for interactive push notifications (snooze, take)."""
        clean_server = (server_url or DEFAULT_NTFY_SERVER_URL).strip().rstrip("/")
        clean_resp_topic = (response_topic or "").strip()
        clean_case_id = (case_id or "").strip()
        if not clean_resp_topic or not clean_case_id:
            return []
        target_url = f"{clean_server}/{clean_resp_topic}"
        return [
            {
                "action": NTFY_ACTION_TYPE_HTTP,
                "label": tr("ntfy.action_snooze", "Schlummern (30m)"),
                "url": target_url,
                "method": "POST",
                "body": f"{NTFY_CMD_PREFIX_SNOOZE}{NTFY_CMD_SEPARATOR}{clean_case_id}{NTFY_CMD_SEPARATOR}{NTFY_ACTION_SNOOZE_MINUTES}",
                "clear": True,
            },
            {
                "action": NTFY_ACTION_TYPE_HTTP,
                "label": tr("ntfy.action_take", "Übernehmen"),
                "url": target_url,
                "method": "POST",
                "body": f"{NTFY_CMD_PREFIX_TAKE}{NTFY_CMD_SEPARATOR}{clean_case_id}",
                "clear": True,
            },
        ]

    @classmethod
    def send_notification(
        cls,
        topic: str,
        message: str,
        title: str | None = None,
        priority: int = NTFY_PRIO_DEFAULT,
        tags: list[str] | None = None,
        actions: list[dict[str, Any]] | None = None,
        server_url: str = DEFAULT_NTFY_SERVER_URL,
        timeout: float = NTFY_HTTP_TIMEOUT_SECONDS,
    ) -> bool:
        """Sends a notification synchronously to the ntfy server via HTTP POST with JSON body."""
        clean_topic = (topic or "").strip()
        if not clean_topic:
            logger.warning("NtfyService: Cannot send notification without a topic.")
            return False

        clean_server = (server_url or DEFAULT_NTFY_SERVER_URL).strip().rstrip("/")
        endpoint = f"{clean_server}/"

        payload: dict[str, Any] = {
            "topic": clean_topic,
            "message": message,
            "priority": priority,
        }
        if title:
            payload["title"] = title
        if tags:
            payload["tags"] = tags
        if actions:
            payload["actions"] = actions

        try:
            body = json.dumps(payload).encode("utf-8")
            req = Request(
                endpoint,
                data=body,
                headers={
                    "Content-Type": "application/json; charset=utf-8",
                    "User-Agent": "SupportCockpit-Desktop",
                },
                method="POST",
            )
            with urlopen(req, timeout=timeout) as response:
                status_code = getattr(response, "status", getattr(response, "code", 200))
                is_ok = 200 <= status_code < 300
                if is_ok:
                    logger.info(f"NtfyService: Push sent successfully to topic '{clean_topic}'.")
                else:
                    logger.warning(f"NtfyService: Server responded with status {status_code}.")
                return is_ok
        except (HTTPError, URLError, TimeoutError, OSError) as e:
            logger.warning(f"NtfyService: Network error while sending to '{clean_topic}': {e}")
            return False
        except Exception as e:
            logger.error(f"NtfyService: Unexpected error: {e}", exc_info=True)
            return False

    @classmethod
    def send_notification_async(
        cls,
        topic: str,
        message: str,
        title: str | None = None,
        priority: int = NTFY_PRIO_DEFAULT,
        tags: list[str] | None = None,
        actions: list[dict[str, Any]] | None = None,
        server_url: str = DEFAULT_NTFY_SERVER_URL,
        timeout: float = NTFY_HTTP_TIMEOUT_SECONDS,
        on_result: Any | None = None,
    ) -> threading.Thread:
        """Dispatches notification in a background daemon thread to avoid blocking the GUI."""
        def worker() -> None:
            success = cls.send_notification(
                topic=topic,
                message=message,
                title=title,
                priority=priority,
                tags=tags,
                actions=actions,
                server_url=server_url,
                timeout=timeout,
            )
            if on_result:
                try:
                    on_result(success)
                except Exception as cb_err:
                    logger.debug(f"NtfyService on_result callback error: {cb_err}")

        thread = threading.Thread(target=worker, daemon=True)
        thread.start()
        return thread


class NtfyListener:
    """Listens to an ntfy response topic via streaming JSON in a background daemon thread."""

    def __init__(
        self,
        topic: str,
        server_url: str = DEFAULT_NTFY_SERVER_URL,
        on_command: Any | None = None,
        timeout: float = NTFY_STREAM_TIMEOUT_SECONDS,
        reconnect_delay: float = NTFY_STREAM_RECONNECT_DELAY_SECONDS,
    ) -> None:
        self.topic = (topic or "").strip()
        self.server_url = (server_url or DEFAULT_NTFY_SERVER_URL).strip().rstrip("/")
        self.on_command = on_command
        self.timeout = timeout
        self.reconnect_delay = reconnect_delay
        self._stop_event = threading.Event()
        self._thread: threading.Thread | None = None
        self._active_response: Any = None

    @property
    def is_running(self) -> bool:
        return self._thread is not None and self._thread.is_alive() and not self._stop_event.is_set()

    def start(self) -> None:
        """Starts background streaming listener loop."""
        if not self.topic:
            logger.warning("NtfyListener: Cannot start without a topic.")
            return
        if self.is_running:
            return
        self._stop_event.clear()
        self._thread = threading.Thread(
            target=self._stream_loop,
            name=f"NtfyListener-{self.topic}",
            daemon=True,
        )
        self._thread.start()
        logger.info("NtfyListener: Started streaming listener on '%s'.", self.topic)

    def stop(self, timeout: float = 2.0) -> None:
        """Stops the streaming listener loop and interrupts ongoing socket reads."""
        self._stop_event.set()
        if self._active_response is not None:
            try:
                self._active_response.close()
            except Exception:
                pass
            self._active_response = None
        if self._thread and self._thread.is_alive():
            self._thread.join(timeout=timeout)
        self._thread = None
        logger.info("NtfyListener: Stopped streaming listener on '%s'.", self.topic)

    def _stream_loop(self) -> None:
        stream_url = f"{self.server_url}/{self.topic}/json?since=now"
        while not self._stop_event.is_set():
            try:
                req = Request(
                    stream_url,
                    headers={"User-Agent": "SupportCockpit-Desktop-Listener"},
                    method="GET",
                )
                with urlopen(req, timeout=self.timeout) as resp:
                    self._active_response = resp
                    while not self._stop_event.is_set():
                        line_bytes = resp.readline()
                        if not line_bytes:
                            break
                        line = line_bytes.decode("utf-8", errors="replace").strip()
                        if not line:
                            continue
                        try:
                            payload = json.loads(line)
                        except Exception:
                            continue
                        if payload.get("event") == "message":
                            msg = str(payload.get("message", "")).strip()
                            if msg and self.on_command:
                                try:
                                    self.on_command(msg)
                                except Exception as cb_err:
                                    logger.warning("NtfyListener callback error: %s", cb_err)
            except (HTTPError, URLError, TimeoutError, OSError) as net_err:
                if not self._stop_event.is_set():
                    logger.debug("NtfyListener: Disconnected (%s), reconnecting...", net_err)
                    self._stop_event.wait(self.reconnect_delay)
            except Exception as exc:
                if not self._stop_event.is_set():
                    logger.warning("NtfyListener: Unexpected error (%s), reconnecting...", exc)
                    self._stop_event.wait(self.reconnect_delay)
            finally:
                self._active_response = None

