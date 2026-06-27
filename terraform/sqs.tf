resource "aws_sqs_queue" "check_queue" {
  name                       = "${var.project_name}-check-queue"
  message_retention_seconds  = 300
  visibility_timeout_seconds = 35

  redrive_policy = jsonencode({
    deadLetterTargetArn = aws_sqs_queue.check_dlq.arn
    maxReceiveCount     = 2
  })

  tags = local.common_tags
}

resource "aws_sqs_queue" "check_dlq" {
  name = "${var.project_name}-check-dlq"
  tags = local.common_tags
}

resource "aws_sqs_queue" "alert_queue" {
  name                       = "${var.project_name}-alert-queue"
  message_retention_seconds  = 86400
  visibility_timeout_seconds = 60

  redrive_policy = jsonencode({
    deadLetterTargetArn = aws_sqs_queue.alert_dlq.arn
    maxReceiveCount     = 3
  })

  tags = local.common_tags
}

resource "aws_sqs_queue" "alert_dlq" {
  name = "${var.project_name}-alert-dlq"
  tags = local.common_tags
}
