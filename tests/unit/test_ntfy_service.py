import json
from email.message import Message
from unittest.mock import MagicMock, patch
from urllib.error import HTTPError, URLError

from constants import (
    DEFAULT_NTFY_SERVER_URL,
    NTFY_PRIO_HIGH,
    NTFY_TAG_BELL,
    NTFY_TAG_WARNING,
    NTFY_TOPIC_PREFIX,
)
from services.ntfy_service import NtfyService


def test_generate_random_topic():
    topic1 = NtfyService.generate_random_topic()
    topic2 = NtfyService.generate_random_topic()
    assert topic1.startswith(NTFY_TOPIC_PREFIX)
    assert topic2.startswith(NTFY_TOPIC_PREFIX)
    assert topic1 != topic2


def test_format_case_alert():
    title, msg_due = NtfyService.format_case_alert("1042", "Hoch", is_overdue=False)
    assert "1042" in title
    assert "Hoch" in title
    assert len(msg_due) > 0

    _, msg_overdue = NtfyService.format_case_alert("1042", "Hoch", is_overdue=True)
    assert msg_due != msg_overdue


def test_send_notification_empty_topic():
    assert not NtfyService.send_notification("", "Hello")
    assert not NtfyService.send_notification("   ", "Hello")


@patch("services.ntfy_service.urlopen")
def test_send_notification_success(mock_urlopen):
    mock_resp = MagicMock()
    mock_resp.status = 200
    mock_resp.__enter__.return_value = mock_resp
    mock_urlopen.return_value = mock_resp

    success = NtfyService.send_notification(
        topic="test-topic",
        message="Test alert",
        title="Alert Title",
        priority=NTFY_PRIO_HIGH,
        tags=[NTFY_TAG_BELL, NTFY_TAG_WARNING],
    )

    assert success is True
    assert mock_urlopen.called
    req = mock_urlopen.call_args[0][0]
    assert req.method == "POST"
    assert req.full_url.startswith(DEFAULT_NTFY_SERVER_URL)
    payload = json.loads(req.data.decode("utf-8"))
    assert payload["topic"] == "test-topic"
    assert payload["message"] == "Test alert"
    assert payload["title"] == "Alert Title"
    assert payload["priority"] == NTFY_PRIO_HIGH
    assert payload["tags"] == [NTFY_TAG_BELL, NTFY_TAG_WARNING]


@patch("services.ntfy_service.urlopen")
def test_send_notification_http_error(mock_urlopen):
    mock_urlopen.side_effect = HTTPError("http://ntfy.sh", 500, "Server Error", Message(), None)
    success = NtfyService.send_notification(topic="test-topic", message="Fail")
    assert success is False


@patch("services.ntfy_service.urlopen")
def test_send_notification_network_timeout(mock_urlopen):
    mock_urlopen.side_effect = URLError("Connection timed out")
    success = NtfyService.send_notification(topic="test-topic", message="Timeout")
    assert success is False


@patch("services.ntfy_service.urlopen")
def test_send_notification_async(mock_urlopen):
    mock_resp = MagicMock()
    mock_resp.status = 200
    mock_resp.__enter__.return_value = mock_resp
    mock_urlopen.return_value = mock_resp

    results = []
    thread = NtfyService.send_notification_async(
        topic="async-topic",
        message="Async test",
        on_result=lambda res: results.append(res),
    )
    thread.join(timeout=2.0)

    assert len(results) == 1
    assert results[0] is True
