import json
import os
import urllib.request

import boto3

sns = boto3.client("sns")
SNS_TOPIC_ARN = os.environ["SNS_TOPIC_ARN"]
SLACK_WEBHOOK_URL = os.environ.get("SLACK_WEBHOOK_URL", "")

# SNS Subject 는 최대 100자 제한
MAX_SUBJECT_LENGTH = 100


def lambda_handler(event, context):
    for record in event.get("Records", []):
        body = json.loads(record["body"])
        send_slack(body)
        send_sns(body)


def _is_recovered(alert):
    return alert.get("event_type") == "RECOVERED"


def build_slack_message(alert):
    """알림 종류(DOWN/RECOVERED)에 맞는 Slack 메시지 payload 를 만든다."""
    name = alert.get("name", alert.get("url"))
    url = alert.get("url")

    if _is_recovered(alert):
        downtime = alert.get("downtime_human") or "unknown"
        recovered_at = alert.get("recovered_at", "")
        return {
            "attachments": [
                {
                    "color": "good",
                    "title": f":large_green_circle: RECOVERED: {name}",
                    "fields": [
                        {"title": "URL", "value": url, "short": False},
                        {"title": "Downtime", "value": downtime, "short": True},
                        {"title": "Recovered At", "value": recovered_at, "short": True},
                    ],
                }
            ]
        }

    return {
        "attachments": [
            {
                "color": "danger",
                "title": f":red_circle: DOWN: {name}",
                "fields": [
                    {"title": "URL", "value": url, "short": False},
                    {"title": "Error", "value": alert.get("error", "Unknown error"), "short": True},
                    {"title": "Detected At", "value": alert.get("detected_at", ""), "short": True},
                ],
            }
        ]
    }


def build_sns_message(alert):
    """알림 종류에 맞는 SNS (subject, message) 를 만든다."""
    name = alert.get("name", alert.get("url"))
    url = alert.get("url")

    if _is_recovered(alert):
        downtime = alert.get("downtime_human") or "unknown"
        subject = f"[RECOVERED] {name}"[:MAX_SUBJECT_LENGTH]
        message = (
            f"Endpoint has RECOVERED\n\n"
            f"Name: {name}\n"
            f"URL: {url}\n"
            f"Downtime: {downtime}\n"
            f"Recovered At: {alert.get('recovered_at', '')}"
        )
        return subject, message

    subject = f"[DOWN] {name}"[:MAX_SUBJECT_LENGTH]
    message = (
        f"Endpoint is DOWN\n\n"
        f"Name: {name}\n"
        f"URL: {url}\n"
        f"Error: {alert.get('error', 'Unknown error')}\n"
        f"Detected At: {alert.get('detected_at', '')}"
    )
    return subject, message


def send_slack(alert):
    if not SLACK_WEBHOOK_URL:
        return

    data = json.dumps(build_slack_message(alert)).encode("utf-8")
    req = urllib.request.Request(
        SLACK_WEBHOOK_URL,
        data=data,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    try:
        urllib.request.urlopen(req, timeout=5)
    except Exception as e:
        print(f"Slack notification failed: {e}")


def send_sns(alert):
    subject, message = build_sns_message(alert)
    sns.publish(TopicArn=SNS_TOPIC_ARN, Subject=subject, Message=message)
