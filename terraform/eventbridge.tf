resource "aws_cloudwatch_event_rule" "health_check" {
  name                = "${var.project_name}-health-check"
  schedule_expression = "rate(${var.health_check_interval_minutes} minute)"
}

resource "aws_cloudwatch_event_target" "health_check" {
  rule      = aws_cloudwatch_event_rule.health_check.name
  target_id = "health-check-lambda"
  arn       = aws_lambda_function.health_check.arn
}

resource "aws_lambda_permission" "allow_eventbridge_health_check" {
  statement_id  = "AllowEventBridgeHealthCheck"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.health_check.function_name
  principal     = "events.amazonaws.com"
  source_arn    = aws_cloudwatch_event_rule.health_check.arn
}

resource "aws_cloudwatch_event_rule" "monthly_report" {
  name                = "${var.project_name}-monthly-report"
  schedule_expression = "cron(0 0 1 * ? *)"
}

resource "aws_cloudwatch_event_target" "monthly_report" {
  rule      = aws_cloudwatch_event_rule.monthly_report.name
  target_id = "report-lambda"
  arn       = aws_lambda_function.report.arn
}

resource "aws_lambda_permission" "allow_eventbridge_report" {
  statement_id  = "AllowEventBridgeReport"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.report.function_name
  principal     = "events.amazonaws.com"
  source_arn    = aws_cloudwatch_event_rule.monthly_report.arn
}
