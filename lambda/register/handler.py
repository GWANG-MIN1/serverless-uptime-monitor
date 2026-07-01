import ipaddress
import json
import os
import socket
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


def _ip_is_blocked(ip_str):
    """IP 문자열이 내부/예약 대역이면 True."""
    try:
        ip = ipaddress.ip_address(ip_str)
    except ValueError:
        return False
    return (
        ip.is_private
        or ip.is_loopback
        or ip.is_link_local  # 169.254.0.0/16 (AWS IMDS 169.254.169.254 포함)
        or ip.is_reserved
        or ip.is_multicast
        or ip.is_unspecified
    )


def is_blocked_host(url):
    """SSRF 방어 — 호스트가 사설/루프백/링크로컬/예약 대역으로 해석되면 True.

    공개 API 로 등록된 URL 을 worker 가 그대로 GET 하므로, 내부망이나
    메타데이터 주소(169.254.169.254)로의 요청을 등록 단계에서 차단한다.
    """
    host = urlparse(url.strip()).hostname
    if not host:
        return True

    # 호스트가 이미 IP 리터럴이면 바로 검사
    if _ip_is_blocked(host):
        return True

    # 도메인이면 해석되는 모든 IP 를 검사 (하나라도 내부면 차단)
    try:
        infos = socket.getaddrinfo(host, None)
    except socket.gaierror:
        # 해석 실패는 여기서 판단하지 않는다 (worker 가 DOWN 으로 처리)
        return False
    return any(_ip_is_blocked(info[4][0]) for info in infos)


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
    if is_blocked_host(url):
        return response(400, {"message": "url resolves to a private or reserved address"})

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
    items = []
    kwargs = {}
    while True:
        result = endpoints_table.scan(**kwargs)
        items.extend(result.get("Items", []))
        last_key = result.get("LastEvaluatedKey")
        if not last_key:
            break
        kwargs["ExclusiveStartKey"] = last_key
    return response(200, items)


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
