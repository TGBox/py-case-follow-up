import json
from email.message import Message
from unittest.mock import MagicMock, patch
from urllib.error import HTTPError, URLError

from constants import (
    DEFAULT_NTFY_SERVER_URL,
    NTFY_EVENT_FOLLOWUP,
    NTFY_EVENT_HANDOVER,
    NTFY_EVENT_NOTE,
    NTFY_PRIO_HIGH,
    NTFY_TAG_BELL,
    NTFY_TAG_DIGEST,
    NTFY_TAG_WARNING,
    NTFY_TOPIC_PREFIX,
)
from services.ntfy_service import NtfyListener, NtfyService


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


def test_format_case_alert_event_types():
    # Prio 1
    p1_title, p1_msg = NtfyService.format_case_alert("2001", event_type="prio1")
    assert "2001" in p1_title
    assert "Prio 1" in p1_title or "Notfall" in p1_title
    assert len(p1_msg) > 0

    # Handover
    ho_title, ho_msg = NtfyService.format_case_alert("2002", event_type="handover")
    assert "2002" in ho_title
    assert "Übergabe" in ho_title or "Handover" in ho_title
    assert len(ho_msg) > 0

    # Note
    note_title, note_msg = NtfyService.format_case_alert("2003", event_type="note")
    assert "2003" in note_title
    assert "Notiz" in note_title or "Note" in note_title
    assert len(note_msg) > 0


def test_get_event_tags():
    from constants import NTFY_TAG_BELL, NTFY_TAG_ESCALATION, NTFY_TAG_HANDOVER, NTFY_TAG_NOTE, NTFY_TAG_WARNING

    p1_tags = NtfyService.get_event_tags("prio1")
    assert NTFY_TAG_WARNING in p1_tags
    assert NTFY_TAG_ESCALATION in p1_tags

    ho_tags = NtfyService.get_event_tags("handover")
    assert NTFY_TAG_HANDOVER in ho_tags

    note_tags = NtfyService.get_event_tags("note")
    assert NTFY_TAG_NOTE in note_tags

    default_tags = NtfyService.get_event_tags("followup")
    assert NTFY_TAG_BELL in default_tags


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


def test_format_digest_alert():
    events = [
        {"case_id": "101", "event_type": NTFY_EVENT_FOLLOWUP},
        {"case_id": "102", "event_type": NTFY_EVENT_FOLLOWUP},
        {"case_id": "103", "event_type": NTFY_EVENT_HANDOVER},
        {"case_id": "104", "event_type": NTFY_EVENT_NOTE},
    ]
    title, message = NtfyService.format_digest_alert(events)
    assert "4" in title
    assert "2x" in message
    assert "1x" in message
    assert "#101" in message
    assert "#104" in message


def test_format_digest_alert_many_cases():
    events = [{"case_id": str(i), "event_type": NTFY_EVENT_FOLLOWUP} for i in range(1, 10)]
    title, message = NtfyService.format_digest_alert(events)
    assert "9" in title
    assert "9 Fälle" in message or "9 cases" in message or "9 ärenden" in message


def test_format_digest_alert_empty():
    title, message = NtfyService.format_digest_alert([])
    assert "0" in title
    assert len(message) > 0


def test_get_event_tags_digest():
    tags = NtfyService.get_event_tags("digest")
    assert tags == [NTFY_TAG_DIGEST]


def test_format_case_actions():
    actions = NtfyService.format_case_actions("1042", "desk-alert-cmd")
    assert len(actions) == 2
    assert actions[0]["action"] == "http"
    assert "desk-alert-cmd" in actions[0]["url"]
    assert actions[0]["body"] == "snooze:1042:30"
    assert actions[1]["action"] == "http"
    assert actions[1]["body"] == "take:1042"

    assert NtfyService.format_case_actions("", "desk-alert-cmd") == []
    assert NtfyService.format_case_actions("1042", "") == []


@patch("services.ntfy_service.urlopen")
def test_send_notification_with_actions(mock_urlopen):
    mock_resp = MagicMock()
    mock_resp.status = 200
    mock_resp.__enter__.return_value = mock_resp
    mock_urlopen.return_value = mock_resp

    actions = [{"action": "http", "label": "Test", "url": "https://ntfy.sh/cmd", "body": "test"}]
    success = NtfyService.send_notification(
        topic="test-topic",
        message="Alert with actions",
        actions=actions,
    )
    assert success is True
    req = mock_urlopen.call_args[0][0]
    payload = json.loads(req.data.decode("utf-8"))
    assert payload["actions"] == actions


def test_ntfy_listener_empty_topic():
    listener = NtfyListener(topic="")
    listener.start()
    assert not listener.is_running
    listener.stop()


@patch("services.ntfy_service.urlopen")
def test_ntfy_listener_stream_receives_command(mock_urlopen):
    import time
    mock_resp = MagicMock()
    mock_resp.__enter__.return_value = mock_resp
    lines = [
        json.dumps({"event": "keepalive"}).encode("utf-8") + b"\n",
        json.dumps({"event": "message", "message": "snooze:1042:30"}).encode("utf-8") + b"\n",
        b"",
    ]
    mock_resp.readline.side_effect = lines
    mock_urlopen.return_value = mock_resp

    received = []
    listener = NtfyListener(
        topic="test-cmd-topic",
        on_command=lambda cmd: received.append(cmd),
    )
    listener.start()
    assert listener.is_running
    time.sleep(0.1)
    listener.stop()
    assert not listener.is_running
    assert "snooze:1042:30" in received


def test_get_topic_url():
    assert NtfyService.get_topic_url("desk-123") == "https://ntfy.sh/desk-123"
    assert NtfyService.get_topic_url("desk-123", "https://ntfy.example.com/") == "https://ntfy.example.com/desk-123"
    assert NtfyService.get_topic_url("") == "https://ntfy.sh"


def test_generate_qr_image():
    from PIL import Image

    img = NtfyService.generate_qr_image("https://ntfy.sh/test-topic")
    assert isinstance(img, Image.Image)
    assert img.size[0] > 0
    assert img.size[1] > 0


