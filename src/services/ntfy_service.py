import json
import logging
import secrets
import threading
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from constants import (
    DEFAULT_NTFY_SERVER_URL,
    NTFY_HTTP_TIMEOUT_SECONDS,
    NTFY_PRIO_DEFAULT,
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
    def format_case_alert(
        case_id: str,
        priority_label: str,
        is_overdue: bool = False,
        anonymize: bool = True,
    ) -> tuple[str, str]:
        """Creates privacy-friendly, tokenized notification title and message."""
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
