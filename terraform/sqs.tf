resource "aws_sqs_queue" "alert_queue" {
  name                       = "${var.project_name}-alert-queue"
  message_retention_seconds  = 86400
  visibility_timeout_seconds = 60

  redrive_policy = jsonencode({
    deadLetterTargetArn = aws_sqs_queue.alert_dlq.arn
    maxReceiveCount     = 3
  })
}

resource "aws_sqs_queue" "alert_dlq" {
  name = "${var.project_name}-alert-dlq"
}
