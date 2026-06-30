"""moto 기반 통합테스트 (스켈레톤).

upgrade-04 — docs/upgrades/04-moto-integration-tests.md

지금은 뼈대만 잡아둔 상태로, 모든 테스트가 skip 처리되어 CI 를 막지 않는다.
내일부터 @pytest.mark.skip 을 하나씩 제거하며 채운다.

moto 가 설치돼 있지 않으면 모듈 전체를 건너뛴다.
"""

import pytest

# moto 미설치 환경에서는 이 모듈을 통째로 skip
pytest.importorskip("moto")

SKIP_REASON = "WIP(upgrade-04): 내일 구현 예정"


@pytest.mark.skip(reason=SKIP_REASON)
def test_create_endpoint_writes_to_dynamodb():
    """POST /endpoints 가 DynamoDB 에 아이템을 저장하는지 검증."""
    # TODO: @mock_aws 로 endpoints 테이블 생성 → register.create_endpoint 호출
    #       → get_item 으로 저장 확인
    raise NotImplementedError


@pytest.mark.skip(reason=SKIP_REASON)
def test_list_endpoints_returns_saved_items():
    """GET /endpoints 가 저장된 아이템 목록을 반환하는지 검증."""
    # TODO
    raise NotImplementedError


@pytest.mark.skip(reason=SKIP_REASON)
def test_delete_missing_endpoint_returns_404():
    """존재하지 않는 엔드포인트 DELETE 시 404."""
    # TODO
    raise NotImplementedError


@pytest.mark.skip(reason=SKIP_REASON)
def test_worker_writes_history_and_updates_status():
    """worker 가 history put + endpoints update 를 수행하는지 검증."""
    # TODO: requests/urlopen 모킹 + DynamoDB 테이블 생성
    raise NotImplementedError


@pytest.mark.skip(reason=SKIP_REASON)
def test_worker_sends_alert_on_down_transition():
    """UP→DOWN 전환 시 alert 큐로 메시지를 보내는지 검증 (upgrade-01 연계)."""
    # TODO
    raise NotImplementedError
