import json
import os

import boto3

dynamodb = boto3.resource("dynamodb")
sqs = boto3.client("sqs")
endpoints_table = dynamodb.Table(os.environ["ENDPOINTS_TABLE"])
CHECK_QUEUE_URL = os.environ["CHECK_QUEUE_URL"]


def lambda_handler(event, context):
    endpoints = []
    kwargs = {}
    while True:
        result = endpoints_table.scan(**kwargs)
        endpoints.extend(result.get("Items", []))
        last_key = result.get("LastEvaluatedKey")
        if not last_key:
            break
        kwargs["ExclusiveStartKey"] = last_key

    for endpoint in endpoints:
        sqs.send_message(
            QueueUrl=CHECK_QUEUE_URL,
            MessageBody=json.dumps(endpoint),
        )

    return {"dispatched": len(endpoints)}
