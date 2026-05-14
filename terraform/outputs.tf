output "api_endpoint" {
  value = aws_apigatewayv2_stage.default.invoke_url
}

output "alert_queue_url" {
  value = aws_sqs_queue.alert_queue.url
}

output "reports_bucket" {
  value = aws_s3_bucket.reports.bucket
}
