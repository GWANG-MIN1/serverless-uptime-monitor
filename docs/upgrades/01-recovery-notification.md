# 01. 복구(DOWN→UP) 알림 + 장애 지속시간

## 목표
현재는 **UP→DOWN 전환 시에만** 알림을 보낸다. 장애가 끝나 **DOWN→UP 으로 복구될 때도**
`🟢 RECOVERED` 알림을 보내고, **장애 지속시간(downtime)** 을 함께 표기한다.
→ 단순 "장애 감지"를 넘어 **인시던트 수명주기(시작~복구)** 를 다룬다.

## 현재 동작
`lambda/health_check_worker/handler.py`
```python
# 상태가 UP에서 DOWN으로 바뀔 때만 알림
if previous_status != "DOWN" and status == "DOWN":
    sqs.send_message(...)
```

## 구현 개요 (내일 진행)
1. **DOWN 진입 시각 저장**: endpoints 테이블에 `down_since` 필드 기록 (UP→DOWN 전환 때).
2. **복구 감지**: `previous_status == "DOWN" and status == "UP"` 분기 추가.
3. **지속시간 계산**: `now - down_since` → `"3m 12s"` 형태 문자열.
4. **알림 메시지 분기**: alert 핸들러에서 `event_type` (`DOWN` / `RECOVERED`)에 따라
   Slack 색상(danger/good)·문구·SNS 제목을 다르게.
5. 복구 후 `down_since` 제거(REMOVE).

## 손대는 파일
- [ ] `lambda/health_check_worker/handler.py` — 복구 분기 + `down_since` read/write
- [ ] `lambda/alert/handler.py` — `event_type` 별 메시지(색상/제목) 분기
- [ ] `tests/test_health_check_worker.py` — 복구 시 알림 발송 / downtime 계산 테스트
- [ ] `README.md` — 동작 설명에 복구 알림 추가

## 체크리스트
- [ ] UP→DOWN: 기존대로 DOWN 알림 + `down_since` 기록
- [ ] DOWN→UP: RECOVERED 알림 + downtime 표기
- [ ] UP→UP / DOWN→DOWN: 알림 없음(중복 방지 유지)
- [ ] downtime 포맷 단위 테스트(초/분/시)

## 면접 포인트
"장애 감지뿐 아니라 복구까지 추적하는 인시던트 수명주기를 구현했습니다."
