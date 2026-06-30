# 04. moto 통합테스트

## 목표
현재 테스트는 **순수 로직(URL 검증, 통계 계산)만** 검증한다.
`moto` 로 DynamoDB/SQS 를 가짜로 띄워 **핸들러가 실제로 AWS 호출하는 경로**까지 테스트한다.

## 현재 테스트 범위
- `test_register.py` — `is_valid_url` 만
- `test_health_check_worker.py` 등 — 로직 위주, 실제 put/update 미검증

## 구현 개요 (내일 진행)
1. `requirements-dev.txt` 에 `moto[dynamodb,sqs]` 추가 (완료).
2. `@mock_aws` 로 가짜 DynamoDB 테이블 생성 → 핸들러 호출 → 저장 결과 검증.
3. 핸들러는 import 시점에 boto3 리소스를 만들므로(conftest 참고),
   **테이블 생성 fixture 를 import 전/후 순서에 맞게** 구성해야 한다.
   (moto 컨텍스트 안에서 핸들러 모듈을 reload 하거나, 리소스 생성을 지연시키는 방식 검토)

## 스켈레톤
`tests/test_integration_moto.py` 에 **skip 처리된 뼈대**를 넣어둠.
내일 `@pytest.mark.skip` 을 제거하며 하나씩 채운다.

## 손대는 파일
- [x] `requirements-dev.txt` — moto 추가
- [x] `tests/test_integration_moto.py` — 스켈레톤(skip)
- [ ] register: POST → DynamoDB put 검증
- [ ] register: GET list/get/delete 검증
- [ ] worker: 체크 결과 history put + endpoints update 검증
- [ ] worker: DOWN 전환 시 SQS send 검증 (upgrade-01 과 연계)

## 면접 포인트
"순수 단위테스트에서 moto 기반 통합테스트로 확장해 AWS 연동 경로까지 검증했습니다."
