"""pytest 공통 설정.

Lambda 핸들러는 import 시점에 환경 변수를 읽고 boto3 리소스를 만든다.
테스트에서는 실제 AWS에 연결하지 않으므로, import 전에 더미 환경 변수를 넣어 준다.
또 두 핸들러 파일 이름이 모두 handler.py 라서, 경로로 직접 불러와 이름 충돌을 피한다.
"""

import importlib.util
import os
from pathlib import Path

# 핸들러 import 전에 필요한 환경 변수를 채워 둔다.
os.environ.setdefault("AWS_DEFAULT_REGION", "ap-northeast-2")
os.environ.setdefault("ENDPOINTS_TABLE", "test-endpoints")
os.environ.setdefault("HISTORY_TABLE", "test-history")
os.environ.setdefault("ALERT_QUEUE_URL", "https://sqs.test/queue")
os.environ.setdefault("SNS_TOPIC_ARN", "arn:aws:sns:test")
os.environ.setdefault("REPORTS_BUCKET", "test-reports")

LAMBDA_DIR = Path(__file__).resolve().parent.parent / "lambda"


def load_handler(name):
    """lambda/<name>/handler.py 를 고유한 모듈 이름으로 불러온다."""
    path = LAMBDA_DIR / name / "handler.py"
    spec = importlib.util.spec_from_file_location(f"{name}_handler", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module
