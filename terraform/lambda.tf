locals {
  lambda_env = {
    ENDPOINTS_TABLE   = aws_dynamodb_table.endpoints.name
    HISTORY_TABLE     = aws_dynamodb_table.check_history.name
    ALERT_QUEUE_URL   = aws_sqs_queue.alert_queue.url
    CHECK_QUEUE_URL   = aws_sqs_queue.check_queue.url
    SNS_TOPIC_ARN     = aws_sns_topic.alerts.arn
    SLACK_WEBHOOK_URL = var.slack_webhook_url
    REPORTS_BUCKET    = aws_s3_bucket.reports.bucket
  }
}

data "archive_file" "register" {
  type        = "zip"
  source_dir  = "${path.module}/../lambda/register"
  output_path = "${path.module}/../lambda/register.zip"
}

data "archive_file" "health_check" {
  type        = "zip"
  source_dir  = "${path.module}/../lambda/health_check"
  output_path = "${path.module}/../lambda/health_check.zip"
}

data "archive_file" "alert" {
  type        = "zip"
  source_dir  = "${path.module}/../lambda/alert"
  output_path = "${path.module}/../lambda/alert.zip"
}

data "archive_file" "report" {
  type        = "zip"
  source_dir  = "${path.module}/../lambda/report"
  output_path = "${path.module}/../lambda/report.zip"
}

resource "aws_lambda_function" "register" {
  function_name    = "${var.project_name}-register"
  filename         = data.archive_file.register.output_path
  source_code_hash = data.archive_file.register.output_base64sha256
  role             = aws_iam_role.lambda_exec.arn
  handler          = "handler.lambda_handler"
  runtime          = "python3.12"
  timeout          = 10

  environment {
    variables = local.lambda_env
  }

  tags = local.common_tags
}

resource "aws_lambda_function" "health_check" {
  function_name    = "${var.project_name}-health-check"
  filename         = data.archive_file.health_check.output_path
  source_code_hash = data.archive_file.health_check.output_base64sha256
  role             = aws_iam_role.lambda_exec.arn
  handler          = "handler.lambda_handler"
  runtime          = "python3.12"
  timeout          = 60

  environment {
    variables = local.lambda_env
  }

  tags = local.common_tags
}

data "archive_file" "health_check_worker" {
  type        = "zip"
  source_dir  = "${path.module}/../lambda/health_check_worker"
  output_path = "${path.module}/../lambda/health_check_worker.zip"
}

resource "aws_lambda_function" "health_check_worker" {
  function_name    = "${var.project_name}-health-check-worker"
  filename         = data.archive_file.health_check_worker.output_path
  source_code_hash = data.archive_file.health_check_worker.output_base64sha256
  role             = aws_iam_role.lambda_exec.arn
  handler          = "handler.lambda_handler"
  runtime          = "python3.12"
  timeout          = 20

  environment {
    variables = local.lambda_env
  }

  tags = local.common_tags
}

resource "aws_lambda_event_source_mapping" "sqs_to_health_check_worker" {
  event_source_arn = aws_sqs_queue.check_queue.arn
  function_name    = aws_lambda_function.health_check_worker.arn
  batch_size       = 1
}

resource "aws_lambda_function" "alert" {
  function_name    = "${var.project_name}-alert"
  filename         = data.archive_file.alert.output_path
  source_code_hash = data.archive_file.alert.output_base64sha256
  role             = aws_iam_role.lambda_exec.arn
  handler          = "handler.lambda_handler"
  runtime          = "python3.12"
  timeout          = 30

  environment {
    variables = local.lambda_env
  }

  tags = local.common_tags
}

resource "aws_lambda_function" "report" {
  function_name    = "${var.project_name}-report"
  filename         = data.archive_file.report.output_path
  source_code_hash = data.archive_file.report.output_base64sha256
  role             = aws_iam_role.lambda_exec.arn
  handler          = "handler.lambda_handler"
  runtime          = "python3.12"
  timeout          = 60

  environment {
    variables = local.lambda_env
  }

  tags = local.common_tags
}

resource "aws_lambda_event_source_mapping" "sqs_to_alert" {
  event_source_arn = aws_sqs_queue.alert_queue.arn
  function_name    = aws_lambda_function.alert.arn
  batch_size       = 1
}
