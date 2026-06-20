import json
import os
import uuid
from datetime import datetime, timezone
from urllib.parse import urlparse

import boto3
from boto3.dynamodb.conditions import Key

dynamodb = boto3.resource("dynamodb")
endpoints_table = dynamodb.Table(os.environ["ENDPOINTS_TABLE"])
history_table = dynamodb.Table(os.environ["HISTORY_TABLE"])

# 이름이 너무 길면 잘라서 저장 (DynamoDB/알림 메시지 보호)
MAX_NAME_LENGTH = 100


def is_valid_url(url):
    """http/https 스킴과 호스트가 모두 있어야 유효한 URL로 본다."""
    if not isinstance(url, str):
        return False
    parsed = urlparse(url.strip())
    return parsed.scheme in ("http", "https") and bool(parsed.netloc)


def lambda_handler(event, context):
    method = event.get("requestContext", {}).get("http", {}).get("method", "")
    path = event.get("rawPath", "")
    path_params = event.get("pathParameters") or {}

    if method == "POST" and path == "/endpoints":
        return create_endpoint(event)
    elif method == "GET" and path == "/endpoints":
        return list_endpoints()
    elif method == "GET" and "/history" in path:
        return get_history(path_params.get("id"))
    elif method == "GET" and path_params.get("id"):
        return get_endpoint(path_params.get("id"))
    elif method == "DELETE" and path_params.get("id"):
        return delete_endpoint(path_params.get("id"))

    return response(404, {"message": "Not found"})


def create_endpoint(event):
    try:
        body = json.loads(event.get("body") or "{}")
    except json.JSONDecodeError:
        return response(400, {"message": "Request body must be valid JSON"})

    url = (body.get("url") or "").strip()
    if not url:
        return response(400, {"message": "url is required"})
    if not is_valid_url(url):
        return response(400, {"message": "url must start with http:// or https://"})

    name = (body.get("name") or url).strip()[:MAX_NAME_LENGTH]

    endpoint_id = str(uuid.uuid4())
    item = {
        "id": endpoint_id,
        "url": url,
        "name": name,
        "status": "UNKNOWN",
        "created_at": datetime.now(timezone.utc).isoformat(),
    }
    endpoints_table.put_item(Item=item)
    return response(201, item)


def list_endpoints():
    result = endpoints_table.scan()
    return response(200, result.get("Items", []))


def get_endpoint(endpoint_id):
    result = endpoints_table.get_item(Key={"id": endpoint_id})
    item = result.get("Item")
    if not item:
        return response(404, {"message": "Endpoint not found"})
    return response(200, item)


def delete_endpoint(endpoint_id):
    result = endpoints_table.delete_item(
        Key={"id": endpoint_id},
        ReturnValues="ALL_OLD",
    )
    if not result.get("Attributes"):
        return response(404, {"message": "Endpoint not found"})
    return response(204, {})


def get_history(endpoint_id):
    result = history_table.query(
        KeyConditionExpression=Key("endpoint_id").eq(endpoint_id),
        ScanIndexForward=False,
        Limit=50,
    )
    return response(200, result.get("Items", []))


def response(status_code, body):
    return {
        "statusCode": status_code,
        "headers": {"Content-Type": "application/json"},
        "body": json.dumps(body, default=str),
    }
