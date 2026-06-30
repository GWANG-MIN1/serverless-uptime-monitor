import json
import os
import socket
import time
from datetime import datetime, timezone, timedelta

import boto3
import urllib.request
import urllib.error

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

    # 상태가 UP에서 DOWN으로 바뀔 때만 알림
    # TODO(upgrade-01): 복구(DOWN→UP) 알림 추가 — docs/upgrades/01-recovery-notification.md
    #   - UP→DOWN 전환 시 endpoints 테이블에 down_since 기록
    #   - previous_status == "DOWN" and status == "UP" 분기에서 RECOVERED 알림 + downtime 계산
    if previous_status != "DOWN" and status == "DOWN":
        sqs.send_message(
            QueueUrl=ALERT_QUEUE_URL,
            MessageBody=json.dumps({
                "endpoint_id": endpoint_id,
                "name": endpoint.get("name", url),
                "url": url,
                "status_code": status_code,
                "error": error_msg,
                "detected_at": now.isoformat(),
            }),
        )


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
