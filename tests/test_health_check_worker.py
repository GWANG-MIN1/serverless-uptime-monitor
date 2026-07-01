"""health_check_worker 핸들러 테스트."""
import json
import socket
import urllib.error
from unittest.mock import MagicMock, patch

from conftest import load_handler

worker = load_handler("health_check_worker")


def _sqs_event(endpoint):
    return {"Records": [{"body": json.dumps(endpoint)}]}


# ── do_request ─────────────────────────────────────────────────────────────


def test_do_request_up_on_2xx():
    mock_resp = MagicMock()
    mock_resp.__enter__ = MagicMock(return_value=mock_resp)  # `with ... as resp` → resp = mock_resp
    mock_resp.getcode.return_value = 200

    with patch("urllib.request.urlopen", return_value=mock_resp):
        status, code, error = worker.do_request("https://example.com")

    assert status == "UP"
    assert code == 200
    assert error is None


def test_do_request_down_on_http_500():
    exc = urllib.error.HTTPError(url="", code=500, msg="Internal Server Error", hdrs={}, fp=None)
    with patch("urllib.request.urlopen", side_effect=exc):
        status, code, error = worker.do_request("https://example.com")

    assert status == "DOWN"
    assert code == 500
    assert "500" in error


def test_do_request_down_on_timeout():
    exc = urllib.error.URLError(socket.timeout("timed out"))
    with patch("urllib.request.urlopen", side_effect=exc):
        status, code, error = worker.do_request("https://example.com")

    assert status == "DOWN"
    assert error == "Connection timed out"


def test_do_request_down_on_dns_failure():
    exc = urllib.error.URLError(socket.gaierror("Name or service not known"))
    with patch("urllib.request.urlopen", side_effect=exc):
        status, code, error = worker.do_request("https://nonexistent.invalid")

    assert status == "DOWN"
    assert error == "DNS resolution failed"


def test_do_request_down_on_unexpected_exception():
    with patch("urllib.request.urlopen", side_effect=RuntimeError("unexpected")):
        status, code, error = worker.do_request("https://example.com")

    assert status == "DOWN"
    assert "unexpected" in error


# ── 알림 전환 로직 ─────────────────────────────────────────────────────────


def test_no_alert_when_endpoint_stays_up():
    endpoint = {"id": "e1", "url": "https://ok.com", "status": "UP"}

    with patch.object(worker, "do_request", return_value=("UP", 200, None)), \
         patch.object(worker.history_table, "put_item"), \
         patch.object(worker.endpoints_table, "update_item"), \
         patch.object(worker.sqs, "send_message") as mock_send:
        worker.lambda_handler(_sqs_event(endpoint), {})

    mock_send.assert_not_called()


def test_alert_sent_on_up_to_down_transition():
    endpoint = {"id": "e1", "url": "https://fail.com", "status": "UP", "name": "My Site"}

    with patch.object(worker, "do_request", return_value=("DOWN", None, "Connection timed out")), \
         patch.object(worker.history_table, "put_item"), \
         patch.object(worker.endpoints_table, "update_item"), \
         patch.object(worker.sqs, "send_message") as mock_send:
        worker.lambda_handler(_sqs_event(endpoint), {})

    mock_send.assert_called_once()
    body = json.loads(mock_send.call_args[1]["MessageBody"])
    assert body["endpoint_id"] == "e1"
    assert body["name"] == "My Site"
    assert body["error"] == "Connection timed out"


def test_no_duplicate_alert_when_already_down():
    endpoint = {"id": "e1", "url": "https://fail.com", "status": "DOWN"}

    with patch.object(worker, "do_request", return_value=("DOWN", None, "timeout")), \
         patch.object(worker.history_table, "put_item"), \
         patch.object(worker.endpoints_table, "update_item"), \
         patch.object(worker.sqs, "send_message") as mock_send:
        worker.lambda_handler(_sqs_event(endpoint), {})

    mock_send.assert_not_called()


def test_alert_sent_on_unknown_to_down():
    """최초 체크에서 UNKNOWN → DOWN 도 알림 대상이다."""
    endpoint = {"id": "e1", "url": "https://fail.com", "status": "UNKNOWN"}

    with patch.object(worker, "do_request", return_value=("DOWN", None, "timeout")), \
         patch.object(worker.history_table, "put_item"), \
         patch.object(worker.endpoints_table, "update_item"), \
         patch.object(worker.sqs, "send_message") as mock_send:
        worker.lambda_handler(_sqs_event(endpoint), {})

    mock_send.assert_called_once()


def test_history_written_for_every_check():
    endpoint = {"id": "e1", "url": "https://ok.com", "status": "UP"}

    with patch.object(worker, "do_request", return_value=("UP", 200, None)), \
         patch.object(worker.history_table, "put_item") as mock_put, \
         patch.object(worker.endpoints_table, "update_item"), \
         patch.object(worker.sqs, "send_message"):
        worker.lambda_handler(_sqs_event(endpoint), {})

    mock_put.assert_called_once()
    item = mock_put.call_args[1]["Item"]
    assert item["endpoint_id"] == "e1"
    assert item["status"] == "UP"
    assert "checked_at" in item
    assert "expires_at" in item


# ── 복구 지속시간 포맷 (upgrade-01) ─────────────────────────────────────────


def test_format_duration_seconds_only():
    assert worker.format_duration(45) == "45s"


def test_format_duration_minutes_and_seconds():
    assert worker.format_duration(312) == "5m 12s"


def test_format_duration_hours():
    assert worker.format_duration(3672) == "1h 1m 12s"


def test_format_duration_zero_and_negative():
    assert worker.format_duration(0) == "0s"
    assert worker.format_duration(-10) == "0s"


def test_format_duration_none():
    assert worker.format_duration(None) is None


def test_recovered_alert_sent_on_down_to_up():
    endpoint = {"id": "e1", "url": "https://ok.com", "status": "DOWN", "name": "My Site"}

    with patch.object(worker, "do_request", return_value=("UP", 200, None)), \
         patch.object(worker.history_table, "put_item"), \
         patch.object(worker.endpoints_table, "update_item"), \
         patch.object(worker, "_read_down_since", return_value="2024-01-01T00:00:00+00:00"), \
         patch.object(worker.sqs, "send_message") as mock_send:
        worker.lambda_handler(_sqs_event(endpoint), {})

    mock_send.assert_called_once()
    body = json.loads(mock_send.call_args[1]["MessageBody"])
    assert body["event_type"] == "RECOVERED"
    assert body["downtime_human"] is not None
