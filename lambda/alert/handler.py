import json
import os
import urllib.request

import boto3

sns = boto3.client("sns")
SNS_TOPIC_ARN = os.environ["SNS_TOPIC_ARN"]
SLACK_WEBHOOK_URL = os.environ.get("SLACK_WEBHOOK_URL", "")


def lambda_handler(event, context):
    for record in event.get("Records", []):
        body = json.loads(record["body"])
        send_slack(body)
        send_sns(body)


def send_slack(alert):
    if not SLACK_WEBHOOK_URL:
        return

    name = alert.get("name", alert.get("url"))
    url = alert.get("url")
    error = alert.get("error", "Unknown error")
    detected_at = alert.get("detected_at", "")

    message = {
        "attachments": [
            {
                "color": "danger",
                "title": f":red_circle: DOWN: {name}",
                "fields": [
                    {"title": "URL", "value": url, "short": False},
                    {"title": "Error", "value": error, "short": True},
                    {"title": "Detected At", "value": detected_at, "short": True},
                ],
            }
        ]
    }

    data = json.dumps(message).encode("utf-8")
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
    name = alert.get("name", alert.get("url"))
    url = alert.get("url")
    error = alert.get("error", "Unknown error")

    sns.publish(
        TopicArn=SNS_TOPIC_ARN,
        Subject=f"[DOWN] {name}",
        Message=(
            f"Endpoint is DOWN\n\n"
            f"Name: {name}\n"
            f"URL: {url}\n"
            f"Error: {error}\n"
            f"Detected At: {alert.get('detected_at', '')}"
        ),
    )
