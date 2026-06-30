# 업그레이드 로드맵 (주니어 레벨)

`serverless-uptime-monitor` 를 한 단계 끌어올리기 위한 작업 목록입니다.
지금은 **개요/스켈레톤만** 잡아둔 상태이고, 실제 구현은 순차적으로 진행합니다.

> 다른 레포(`aws-serverless-agent`)와 겹치지 않는 주제로만 선정했습니다.
> (OIDC·X-Ray·CloudWatch 대시보드·CloudFront 등은 그쪽에서 이미 다뤘으므로 제외)

## 작업 목록

| # | 항목 | 난이도 | 예상 시간 | 상태 |
|---|---|---|---|---|
| 1 | [복구(DOWN→UP) 알림 + 장애 지속시간](01-recovery-notification.md) | 쉬움 | 1~2h | ⬜ 예정 |
| 2 | [CloudWatch 로그 보존 + API 스로틀링](02-log-retention-and-throttling.md) | 매우 쉬움 | 1h | ⬜ 예정 |
| 3 | [CI 품질 게이트 (ruff/terraform fmt/tfsec)](03-ci-quality-gate.md) | 쉬움 | 반나절 | ⬜ 예정 |
| 4 | [moto 통합테스트](04-moto-integration-tests.md) | 중간 | 반나절~1일 | ⬜ 예정 |
| 5 | [SSRF 가드 (사설 IP 차단)](05-ssrf-guard.md) | 쉬움 | 1h | ⬜ 예정 |

## 진행 원칙

- 항목별로 **커밋을 분리**한다.
- 각 항목은 **테스트를 함께** 추가/수정한다.
- 인프라(terraform) 변경은 `terraform plan` 으로 먼저 확인한다.
- 완료 시 위 표의 상태를 ✅ 로 바꾸고 README 본문에도 반영한다.
