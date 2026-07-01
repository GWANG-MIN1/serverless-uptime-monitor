"""moto 기반 통합테스트.

실제 AWS 대신 moto 로 DynamoDB/SQS 를 가짜로 띄워, 핸들러가 AWS 를
호출하는 경로(put/query/update/send)까지 검증한다.
moto 미설치 환경에서는 모듈 전체를 건너뛴다.

upgrade-04 — docs/upgrades/04-moto-integration-tests.md
"""
import json
from unittest.mock import patch

import boto3
import pytest
from boto3.dynamodb.conditions import Key
from conftest import load_handler

mock_aws = pytest.importorskip("moto").mock_aws

REGION = "ap-northeast-2"


def _create_tables():
    ddb = boto3.resource("dynamodb", region_name=REGION)
    ddb.create_table(
        TableName="test-endpoints",
        KeySchema=[{"AttributeName": "id", "KeyType": "HASH"}],
        AttributeDefinitions=[{"AttributeName": "id", "AttributeType": "S"}],
        BillingMode="PAY_PER_REQUEST",
    )
    ddb.create_table(
        TableName="test-history",
        KeySchema=[
            {"AttributeName": "endpoint_id", "KeyType": "HASH"},
            {"AttributeName": "checked_at", "KeyType": "RANGE"},
        ],
        AttributeDefinitions=[
            {"AttributeName": "endpoint_id", "AttributeType": "S"},
            {"AttributeName": "checked_at", "AttributeType": "S"},
        ],
        BillingMode="PAY_PER_REQUEST",
    )
    return ddb


# ── register 핸들러 ──────────────────────────────────────────────────────────


@mock_aws
def test_create_endpoint_writes_to_dynamodb():
    _create_tables()
    register = load_handler("register")

    with patch.object(register, "is_blocked_host", return_value=False):
        resp = register.create_endpoint(
            {"body": json.dumps({"url": "https://example.com", "name": "Ex"})}
        )

    assert resp["statusCode"] == 201
    created = json.loads(resp["body"])
    item = register.endpoints_table.get_item(Key={"id": created["id"]})["Item"]
    assert item["url"] == "https://example.com"
    assert item["name"] == "Ex"
    assert item["status"] == "UNKNOWN"


@mock_aws
def test_list_and_delete_endpoints():
    _create_tables()
    register = load_handler("register")

    with patch.object(register, "is_blocked_host", return_value=False):
        created = json.loads(
            register.create_endpoint({"body": json.dumps({"url": "https://a.com"})})["body"]
        )
    eid = created["id"]

    listed = json.loads(register.list_endpoints()["body"])
    assert any(e["id"] == eid for e in listed)

    assert register.delete_endpoint(eid)["statusCode"] == 204
    assert register.delete_endpoint("does-not-exist")["statusCode"] == 404


# ── worker 핸들러 ────────────────────────────────────────────────────────────


@mock_aws
def test_worker_writes_history_and_updates_status():
    _create_tables()
    worker = load_handler("health_check_worker")
    worker.endpoints_table.put_item(Item={"id": "e1", "url": "https://ok.com", "status": "UP"})

    with patch.object(worker, "do_request", return_value=("UP", 200, None)):
        worker.check_endpoint({"id": "e1", "url": "https://ok.com", "status": "UP"})

    history = worker.history_table.query(KeyConditionExpression=Key("endpoint_id").eq("e1"))
    assert history["Count"] == 1
    endpoint = worker.endpoints_table.get_item(Key={"id": "e1"})["Item"]
    assert endpoint["status"] == "UP"


@mock_aws
def test_worker_sends_down_alert_and_records_down_since():
    _create_tables()
    sqs = boto3.client("sqs", region_name=REGION)
    queue_url = sqs.create_queue(QueueName="test-alert")["QueueUrl"]

    worker = load_handler("health_check_worker")
    worker.ALERT_QUEUE_URL = queue_url  # 로드 시점의 더미 URL 을 실제 큐로 교체
    worker.endpoints_table.put_item(
        Item={"id": "e1", "url": "https://x.com", "status": "UP", "name": "X"}
    )

    with patch.object(worker, "do_request", return_value=("DOWN", 500, "HTTP 500")):
        worker.check_endpoint({"id": "e1", "url": "https://x.com", "status": "UP", "name": "X"})

    messages = sqs.receive_message(QueueUrl=queue_url, MaxNumberOfMessages=10).get("Messages", [])
    assert len(messages) == 1
    body = json.loads(messages[0]["Body"])
    assert body["event_type"] == "DOWN"
    assert body["name"] == "X"

    endpoint = worker.endpoints_table.get_item(Key={"id": "e1"})["Item"]
    assert "down_since" in endpoint


@mock_aws
def test_worker_sends_recovered_alert_on_up_transition():
    _create_tables()
    sqs = boto3.client("sqs", region_name=REGION)
    queue_url = sqs.create_queue(QueueName="test-alert")["QueueUrl"]

    worker = load_handler("health_check_worker")
    worker.ALERT_QUEUE_URL = queue_url
    worker.endpoints_table.put_item(
        Item={
            "id": "e1",
            "url": "https://x.com",
            "status": "DOWN",
            "name": "X",
            "down_since": "2024-01-01T00:00:00+00:00",
        }
    )

    with patch.object(worker, "do_request", return_value=("UP", 200, None)):
        worker.check_endpoint({"id": "e1", "url": "https://x.com", "status": "DOWN", "name": "X"})

    messages = sqs.receive_message(QueueUrl=queue_url, MaxNumberOfMessages=10).get("Messages", [])
    assert len(messages) == 1
    body = json.loads(messages[0]["Body"])
    assert body["event_type"] == "RECOVERED"
    assert body["downtime_human"]  # None 이 아니어야 한다

    endpoint = worker.endpoints_table.get_item(Key={"id": "e1"})["Item"]
    assert "down_since" not in endpoint
