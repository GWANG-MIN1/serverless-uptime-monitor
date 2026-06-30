# 02. CloudWatch 로그 보존 + API 스로틀링

## 목표
- **로그 보존기간 미설정 = 영구 보관 = 비용 누수** → 보존기간을 명시한다.
- 공개 HTTP API 가 **무제한 호출 가능** → 스로틀링으로 남용을 막는다.

## A. CloudWatch 로그 보존기간

현재 `aws_cloudwatch_log_group` 리소스가 없어서 Lambda 로그가 무기한 보관된다.
Lambda 함수별로 로그 그룹을 명시 생성하고 `retention_in_days` 를 건다.

```hcl
# terraform/cloudwatch.tf 에 추가 예정 (내일 구현)
resource "aws_cloudwatch_log_group" "worker" {
  name              = "/aws/lambda/${aws_lambda_function.health_check_worker.function_name}"
  retention_in_days = 14
  tags              = local.common_tags
}
# register / health_check / alert / report 도 동일하게 (for_each 로 묶으면 깔끔)
```

- [ ] 5개 Lambda 로그 그룹 정의 (`for_each` 추천)
- [ ] `retention_in_days = 14` (필요 시 변수화)
- [ ] 기존에 자동 생성된 로그 그룹과 충돌 시 `terraform import` 로 흡수

## B. API Gateway 스로틀링

HTTP API 기본 스테이지에 **기본 라우트 스로틀링**을 건다.

```hcl
# terraform/api_gateway.tf 의 aws_apigatewayv2_stage 에 추가 예정
default_route_settings {
  throttling_burst_limit = 10
  throttling_rate_limit  = 5
}
```

- [ ] burst / rate 적정값 산정 (헬스체크 주기 고려)
- [ ] `terraform plan` 으로 변경 확인

## 면접 포인트
"로그 비용을 보존정책으로 관리하고, 공개 API 남용을 스로틀링으로 방어했습니다."
