import json
import os
from datetime import datetime, timedelta, timezone

import boto3
from boto3.dynamodb.conditions import Key

dynamodb = boto3.resource("dynamodb")
s3 = boto3.client("s3")
endpoints_table = dynamodb.Table(os.environ["ENDPOINTS_TABLE"])
history_table = dynamodb.Table(os.environ["HISTORY_TABLE"])
REPORTS_BUCKET = os.environ["REPORTS_BUCKET"]


def lambda_handler(event, context):
    now = datetime.now(timezone.utc)
    # 전월 범위 계산
    first_of_this_month = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    first_of_last_month = (first_of_this_month - timedelta(days=1)).replace(day=1)
    report_month = first_of_last_month.strftime("%Y-%m")

    endpoints = endpoints_table.scan().get("Items", [])
    report = {"month": report_month, "generated_at": now.isoformat(), "endpoints": []}

    for endpoint in endpoints:
        stats = get_stats(endpoint["id"], first_of_last_month, first_of_this_month)
        report["endpoints"].append({
            "id": endpoint["id"],
            "name": endpoint.get("name", endpoint["url"]),
            "url": endpoint["url"],
            **stats,
        })

    key = f"reports/{report_month}.json"
    s3.put_object(
        Bucket=REPORTS_BUCKET,
        Key=key,
        Body=json.dumps(report, default=str),
        ContentType="application/json",
    )
    print(f"Report saved: s3://{REPORTS_BUCKET}/{key}")
    return {"report_month": report_month, "endpoint_count": len(endpoints)}


def get_stats(endpoint_id, start, end):
    result = history_table.query(
        KeyConditionExpression=(
            Key("endpoint_id").eq(endpoint_id) &
            Key("checked_at").between(start.isoformat(), end.isoformat())
        )
    )
    return compute_stats(result.get("Items", []))


def compute_stats(items):
    """헬스체크 이력 리스트로부터 업타임 통계를 계산하는 순수 함수."""
    if not items:
        return {"total_checks": 0, "uptime_pct": None, "avg_latency_ms": None, "incidents": 0}

    total = len(items)
    up_count = sum(1 for i in items if i.get("status") == "UP")
    latencies = [int(i["latency_ms"]) for i in items if i.get("latency_ms") is not None]
    incidents = sum(1 for i in items if i.get("status") == "DOWN")

    return {
        "total_checks": total,
        "uptime_pct": round(up_count / total * 100, 2),
        "avg_latency_ms": round(sum(latencies) / len(latencies)) if latencies else None,
        "incidents": incidents,
    }
