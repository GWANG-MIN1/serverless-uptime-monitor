# 05. SSRF 가드 (사설 IP 차단)

## 목표
공개 API 라 누구나 임의의 URL 을 등록할 수 있고, worker 가 그 URL 로 GET 요청을 보낸다.
`http://169.254.169.254`(메타데이터), `http://10.0.0.5`, `http://192.168.x`, `localhost` 같은
**내부/사설 대역**으로의 요청을 차단한다. (SSRF 기본 방어)

## 현재 동작
`lambda/register/handler.py` 의 `is_valid_url` 은 스킴/호스트 존재만 검사한다.
사설 IP·로컬호스트도 통과한다.

## 구현 개요 (내일 진행)
1. 호스트명을 추출해 IP 로 해석(`socket.getaddrinfo`).
2. `ipaddress` 모듈로 **사설/루프백/링크로컬/예약** 대역인지 검사.
   - `is_private`, `is_loopback`, `is_link_local`, `is_reserved`
   - 특히 `169.254.169.254`(IMDS) 명시 차단.
3. 차단 시 등록을 `400` 으로 거부.
4. 등록 시점뿐 아니라 **worker 의 do_request 직전에도** 재검증(DNS rebinding 대비) 검토.

## 스켈레톤
`register/handler.py` 에 `is_blocked_host()` **스텁 함수**를 추가해 둠(아직 미연결).
내일 본문을 채우고 `is_valid_url`/검증 흐름에 연결한다.

```python
def is_blocked_host(url):
    # TODO(upgrade-05): 호스트 IP 해석 후 사설/루프백/링크로컬/예약 대역이면 True
    return False
```

## 손대는 파일
- [x] `lambda/register/handler.py` — `is_blocked_host` 스텁
- [ ] `is_blocked_host` 본문 구현 + `create_endpoint` 검증에 연결
- [ ] `lambda/health_check_worker/handler.py` — do_request 전 재검증(선택)
- [ ] `tests/test_register.py` — 사설/루프백/IMDS 차단 테스트 추가

## 면접 포인트
"공개 API 의 SSRF 위험을 인지하고, 사설/메타데이터 대역 차단으로 방어했습니다."
