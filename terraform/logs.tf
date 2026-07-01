# Lambda 로그 그룹을 명시적으로 관리해 보존기간을 건다.
# (미지정 시 로그가 무기한 보관되어 비용이 누적된다)

locals {
  lambda_functions = {
    register            = aws_lambda_function.register.function_name
    health_check        = aws_lambda_function.health_check.function_name
    health_check_worker = aws_lambda_function.health_check_worker.function_name
    alert               = aws_lambda_function.alert.function_name
    report              = aws_lambda_function.report.function_name
  }
}

resource "aws_cloudwatch_log_group" "lambda" {
  for_each = local.lambda_functions

  name              = "/aws/lambda/${each.value}"
  retention_in_days = var.log_retention_days
  tags              = local.common_tags
}
