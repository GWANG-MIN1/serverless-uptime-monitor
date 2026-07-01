"""alert 핸들러 테스트."""
import json
from unittest.mock import patch

from conftest import load_handler

alert = load_handler("alert")

SAMPLE_ALERT = {
    "endpoint_id": "e1",
    "name": "My Site",
    "url": "https://mysite.com",
    "error": "Connection timed out",
    "detected_at": "2024-01-01T00:00:00+00:00",
}


def _event(body):
    return {"Records": [{"body": json.dumps(body)}]}


def test_sns_publish_called_with_down_subject():
    with patch.object(alert.sns, "publish") as mock_publish, \
         patch.object(alert, "send_slack"):
        alert.lambda_handler(_event(SAMPLE_ALERT), {})

    mock_publish.assert_called_once()
    kwargs = mock_publish.call_args[1]
    assert "[DOWN]" in kwargs["Subject"]
    assert "My Site" in kwargs["Subject"]


def test_sns_message_contains_url_and_error():
    with patch.object(alert.sns, "publish") as mock_publish, \
         patch.object(alert, "send_slack"):
        alert.lambda_handler(_event(SAMPLE_ALERT), {})

    message = mock_publish.call_args[1]["Message"]
    assert "https://mysite.com" in message
    assert "Connection timed out" in message


def test_slack_not_called_when_no_webhook():
    original = alert.SLACK_WEBHOOK_URL
    alert.SLACK_WEBHOOK_URL = ""
    try:
        with patch("urllib.request.urlopen") as mock_urlopen, \
             patch.object(alert.sns, "publish"):
            alert.lambda_handler(_event(SAMPLE_ALERT), {})
        mock_urlopen.assert_not_called()
    finally:
        alert.SLACK_WEBHOOK_URL = original


def test_slack_failure_does_not_abort_sns():
    original = alert.SLACK_WEBHOOK_URL
    alert.SLACK_WEBHOOK_URL = "https://hooks.slack.com/test"
    try:
        with patch("urllib.request.urlopen", side_effect=Exception("network error")), \
             patch.object(alert.sns, "publish") as mock_publish:
            alert.lambda_handler(_event(SAMPLE_ALERT), {})
        # Slack 실패해도 SNS는 호출돼야 한다
        mock_publish.assert_called_once()
    finally:
        alert.SLACK_WEBHOOK_URL = original


def test_multiple_records_processed():
    alert2 = {**SAMPLE_ALERT, "endpoint_id": "e2", "name": "Other Site"}
    event = {"Records": [{"body": json.dumps(SAMPLE_ALERT)}, {"body": json.dumps(alert2)}]}

    with patch.object(alert.sns, "publish") as mock_publish, \
         patch.object(alert, "send_slack"):
        alert.lambda_handler(event, {})

    assert mock_publish.call_count == 2


# ── 복구(RECOVERED) 알림 (upgrade-01) ────────────────────────────────────────

RECOVERED_ALERT = {
    "event_type": "RECOVERED",
    "endpoint_id": "e1",
    "name": "My Site",
    "url": "https://mysite.com",
    "recovered_at": "2024-01-01T00:05:00+00:00",
    "downtime_seconds": 312,
    "downtime_human": "5m 12s",
}


def test_recovered_sns_subject_and_downtime():
    subject, message = alert.build_sns_message(RECOVERED_ALERT)
    assert "[RECOVERED]" in subject
    assert "5m 12s" in message
    assert "My Site" in subject


def test_recovered_slack_uses_good_color():
    msg = alert.build_slack_message(RECOVERED_ALERT)
    attachment = msg["attachments"][0]
    assert attachment["color"] == "good"
    assert "RECOVERED" in attachment["title"]


def test_down_slack_uses_danger_color():
    msg = alert.build_slack_message(SAMPLE_ALERT)
    assert msg["attachments"][0]["color"] == "danger"


def test_long_name_subject_is_truncated_to_100():
    long_alert = {**SAMPLE_ALERT, "name": "N" * 200}
    subject, _ = alert.build_sns_message(long_alert)
    assert len(subject) <= 100
