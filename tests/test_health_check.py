"""health_check enumerator 핸들러 테스트."""
import json
from unittest.mock import patch

from conftest import load_handler

health_check = load_handler("health_check")


def test_dispatches_all_endpoints_single_page():
    endpoints = [
        {"id": "e1", "url": "https://a.com"},
        {"id": "e2", "url": "https://b.com"},
    ]
    with patch.object(health_check.endpoints_table, "scan", return_value={"Items": endpoints}), \
         patch.object(health_check.sqs, "send_message") as mock_send:
        result = health_check.lambda_handler({}, {})

    assert result["dispatched"] == 2
    assert mock_send.call_count == 2


def test_dispatches_across_multiple_pages():
    page1 = {"Items": [{"id": "e1", "url": "https://a.com"}], "LastEvaluatedKey": {"id": "e1"}}
    page2 = {"Items": [{"id": "e2", "url": "https://b.com"}]}

    with patch.object(health_check.endpoints_table, "scan", side_effect=[page1, page2]) as mock_scan, \
         patch.object(health_check.sqs, "send_message") as mock_send:
        result = health_check.lambda_handler({}, {})

    assert result["dispatched"] == 2
    assert mock_scan.call_count == 2
    # 두 번째 scan 호출에 ExclusiveStartKey 전달됐는지 확인
    assert mock_scan.call_args_list[1][1]["ExclusiveStartKey"] == {"id": "e1"}
    assert mock_send.call_count == 2


def test_returns_zero_when_no_endpoints():
    with patch.object(health_check.endpoints_table, "scan", return_value={"Items": []}), \
         patch.object(health_check.sqs, "send_message") as mock_send:
        result = health_check.lambda_handler({}, {})

    assert result["dispatched"] == 0
    mock_send.assert_not_called()


def test_message_body_contains_endpoint_data():
    endpoint = {"id": "e1", "url": "https://a.com", "status": "UP"}
    with patch.object(health_check.endpoints_table, "scan", return_value={"Items": [endpoint]}), \
         patch.object(health_check.sqs, "send_message") as mock_send:
        health_check.lambda_handler({}, {})

    sent_body = json.loads(mock_send.call_args[1]["MessageBody"])
    assert sent_body["id"] == "e1"
    assert sent_body["url"] == "https://a.com"
