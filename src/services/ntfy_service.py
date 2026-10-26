import json
import logging
import secrets
import threading
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from constants import (
    DEFAULT_NTFY_SERVER_URL,
    NTFY_EVENT_FOLLOWUP,
    NTFY_EVENT_HANDOVER,
    NTFY_EVENT_NOTE,
    NTFY_EVENT_PRIO1,
    NTFY_HTTP_TIMEOUT_SECONDS,
    NTFY_PRIO_DEFAULT,
    NTFY_TAG_BELL,
    NTFY_TAG_DIGEST,
    NTFY_TAG_ESCALATION,
    NTFY_TAG_HANDOVER,
    NTFY_TAG_NOTE,
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
    def get_event_tags(event_type: str = NTFY_EVENT_FOLLOWUP) -> list[str]:
        """Returns relevant emoji tag list based on the event type."""
        if event_type == "digest":
            return [NTFY_TAG_DIGEST]
        if event_type == NTFY_EVENT_PRIO1:
            return [NTFY_TAG_WARNING, NTFY_TAG_ESCALATION]
        if event_type == NTFY_EVENT_HANDOVER:
            return [NTFY_TAG_HANDOVER]
        if event_type == NTFY_EVENT_NOTE:
            return [NTFY_TAG_NOTE]
        return [NTFY_TAG_BELL]

    @staticmethod
    def format_case_alert(
        case_id: str,
        priority_label: str = "",
        is_overdue: bool = False,
        event_type: str = NTFY_EVENT_FOLLOWUP,
        anonymize: bool = True,
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

    @classmethod
    def send_notification(
        cls,
        topic: str,
        message: str,
        title: str | None = None,
        priority: int = NTFY_PRIO_DEFAULT,
        tags: list[str] | None = None,
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
