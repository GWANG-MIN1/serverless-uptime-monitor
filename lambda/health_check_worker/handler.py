import json
import os
import socket
import time
import urllib.error
import urllib.request
from datetime import datetime, timedelta, timezone

import boto3

dynamodb = boto3.resource("dynamodb")
sqs = boto3.client("sqs")
endpoints_table = dynamodb.Table(os.environ["ENDPOINTS_TABLE"])
history_table = dynamodb.Table(os.environ["HISTORY_TABLE"])
ALERT_QUEUE_URL = os.environ["ALERT_QUEUE_URL"]

TTL_DAYS = 30


def lambda_handler(event, context):
    for record in event["Records"]:
        endpoint = json.loads(record["body"])
        check_endpoint(endpoint)


def check_endpoint(endpoint):
    endpoint_id = endpoint["id"]
    url = endpoint["url"]
    previous_status = endpoint.get("status", "UNKNOWN")

    start = time.time()
    status, status_code, error_msg = do_request(url)
    latency_ms = int((time.time() - start) * 1000)

    now = datetime.now(timezone.utc)
    expires_at = int((now + timedelta(days=TTL_DAYS)).timestamp())

    history_table.put_item(Item={
        "endpoint_id": endpoint_id,
        "checked_at": now.isoformat(),
        "status": status,
        "status_code": status_code,
        "latency_ms": latency_ms,
        "error": error_msg,
        "expires_at": expires_at,
    })

    endpoints_table.update_item(
        Key={"id": endpoint_id},
        UpdateExpression="SET #s = :s, last_checked_at = :t, last_latency_ms = :l",
        ExpressionAttributeNames={"#s": "status"},
        ExpressionAttributeValues={
            ":s": status,
            ":t": now.isoformat(),
            ":l": latency_ms,
        },
    )

    if previous_status != "DOWN" and status == "DOWN":
        # UP/UNKNOWN → DOWN: 장애 시작 시각을 기록하고 DOWN 알림 발송
        endpoints_table.update_item(
            Key={"id": endpoint_id},
            UpdateExpression="SET down_since = :t",
            ExpressionAttributeValues={":t": now.isoformat()},
        )
        _send_alert({
            "event_type": "DOWN",
            "endpoint_id": endpoint_id,
            "name": endpoint.get("name", url),
            "url": url,
            "status_code": status_code,
            "error": error_msg,
            "detected_at": now.isoformat(),
        })
    elif previous_status == "DOWN" and status == "UP":
        # DOWN → UP: 복구. 장애 지속시간을 계산해 RECOVERED 알림 발송
        down_since = _read_down_since(endpoint_id, endpoint)
        downtime_seconds = None
        if down_since:
            downtime_seconds = int((now - _parse_iso(down_since)).total_seconds())

        endpoints_table.update_item(
            Key={"id": endpoint_id},
            UpdateExpression="REMOVE down_since",
        )
        _send_alert({
            "event_type": "RECOVERED",
            "endpoint_id": endpoint_id,
            "name": endpoint.get("name", url),
            "url": url,
            "recovered_at": now.isoformat(),
            "downtime_seconds": downtime_seconds,
            "downtime_human": format_duration(downtime_seconds),
        })


def _send_alert(payload):
    sqs.send_message(QueueUrl=ALERT_QUEUE_URL, MessageBody=json.dumps(payload))


def _read_down_since(endpoint_id, endpoint):
    """장애 시작 시각을 구한다. SQS 메시지에 없으면 테이블에서 읽는다."""
    if endpoint.get("down_since"):
        return endpoint["down_since"]
    item = endpoints_table.get_item(Key={"id": endpoint_id}).get("Item") or {}
    return item.get("down_since")


def _parse_iso(value):
    return datetime.fromisoformat(value)


def format_duration(seconds):
    """초를 사람이 읽기 쉬운 문자열로 변환. 예: 3672 → '1h 1m 12s'."""
    if seconds is None:
        return None
    seconds = max(int(seconds), 0)
    hours, rem = divmod(seconds, 3600)
    minutes, secs = divmod(rem, 60)
    parts = []
    if hours:
        parts.append(f"{hours}h")
    if minutes:
        parts.append(f"{minutes}m")
    parts.append(f"{secs}s")
    return " ".join(parts)


def do_request(url):
    try:
        req = urllib.request.Request(url, method="GET")
        req.add_header("User-Agent", "uptime-monitor/1.0")
        with urllib.request.urlopen(req, timeout=10) as resp:
            code = resp.getcode()
            if code < 400:
                return "UP", code, None
            return "DOWN", code, f"HTTP {code}"
    except urllib.error.HTTPError as e:
        return "DOWN", e.code, f"HTTP {e.code} {e.reason}"
    except urllib.error.URLError as e:
        reason = e.reason
        if isinstance(reason, socket.timeout):
            return "DOWN", None, "Connection timed out"
        if isinstance(reason, socket.gaierror):
            return "DOWN", None, "DNS resolution failed"
        if isinstance(reason, OSError) and getattr(reason, "errno", None) in (16, 111):
            return "DOWN", None, "DNS resolution failed"
        return "DOWN", None, str(reason)
    except TimeoutError:
        return "DOWN", None, "Connection timed out"
    except Exception as e:
        return "DOWN", None, str(e)
