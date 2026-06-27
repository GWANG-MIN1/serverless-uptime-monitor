resource "aws_cloudwatch_metric_alarm" "check_dlq_not_empty" {
  alarm_name          = "${var.project_name}-check-dlq-not-empty"
  alarm_description   = "check_queue DLQ에 메시지가 쌓이면 worker Lambda가 반복 실패 중"
  namespace           = "AWS/SQS"
  metric_name         = "ApproximateNumberOfMessagesVisible"
  dimensions          = { QueueName = aws_sqs_queue.check_dlq.name }
  statistic           = "Sum"
  period              = 60
  evaluation_periods  = 1
  threshold           = 1
  comparison_operator = "GreaterThanOrEqualToThreshold"
  treat_missing_data  = "notBreaching"
  alarm_actions       = [aws_sns_topic.alerts.arn]
}

resource "aws_cloudwatch_metric_alarm" "alert_dlq_not_empty" {
  alarm_name          = "${var.project_name}-alert-dlq-not-empty"
  alarm_description   = "alert_queue DLQ에 메시지가 쌓이면 알림 Lambda가 반복 실패 중"
  namespace           = "AWS/SQS"
  metric_name         = "ApproximateNumberOfMessagesVisible"
  dimensions          = { QueueName = aws_sqs_queue.alert_dlq.name }
  statistic           = "Sum"
  period              = 60
  evaluation_periods  = 1
  threshold           = 1
  comparison_operator = "GreaterThanOrEqualToThreshold"
  treat_missing_data  = "notBreaching"
  alarm_actions       = [aws_sns_topic.alerts.arn]
}

resource "aws_cloudwatch_metric_alarm" "health_check_errors" {
  alarm_name          = "${var.project_name}-health-check-errors"
  alarm_description   = "health_check enumerator Lambda 실행 오류 — 체크 자체가 시작되지 않음"
  namespace           = "AWS/Lambda"
  metric_name         = "Errors"
  dimensions          = { FunctionName = aws_lambda_function.health_check.function_name }
  statistic           = "Sum"
  period              = 300
  evaluation_periods  = 1
  threshold           = 1
  comparison_operator = "GreaterThanOrEqualToThreshold"
  treat_missing_data  = "notBreaching"
  alarm_actions       = [aws_sns_topic.alerts.arn]
}

resource "aws_cloudwatch_metric_alarm" "health_check_worker_error_rate" {
  alarm_name          = "${var.project_name}-health-check-worker-error-rate"
  alarm_description   = "worker Lambda 오류가 5분 내 3회 이상 — 다수 엔드포인트 체크 누락 가능"
  namespace           = "AWS/Lambda"
  metric_name         = "Errors"
  dimensions          = { FunctionName = aws_lambda_function.health_check_worker.function_name }
  statistic           = "Sum"
  period              = 300
  evaluation_periods  = 2
  threshold           = 3
  comparison_operator = "GreaterThanOrEqualToThreshold"
  treat_missing_data  = "notBreaching"
  alarm_actions       = [aws_sns_topic.alerts.arn]
}

resource "aws_cloudwatch_metric_alarm" "health_check_not_invoked" {
  alarm_name          = "${var.project_name}-health-check-not-invoked"
  alarm_description   = "enumerator가 10분 이상 호출되지 않음 — EventBridge 규칙 또는 Lambda 연결 이상"
  namespace           = "AWS/Lambda"
  metric_name         = "Invocations"
  dimensions          = { FunctionName = aws_lambda_function.health_check.function_name }
  statistic           = "Sum"
  period              = 600
  evaluation_periods  = 1
  threshold           = 1
  comparison_operator = "LessThanThreshold"
  treat_missing_data  = "breaching"
  alarm_actions       = [aws_sns_topic.alerts.arn]
}
