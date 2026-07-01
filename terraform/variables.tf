variable "aws_region" {
  default = "ap-northeast-2"
}

variable "project_name" {
  default = "uptime-monitor"
}

variable "slack_webhook_url" {
  description = "Slack Incoming Webhook URL"
  type        = string
  sensitive   = true
}

variable "alert_email" {
  description = "Email address for SNS alerts"
  type        = string
}

variable "health_check_interval_minutes" {
  description = "Health check interval in minutes"
  type        = number
  default     = 1
}

variable "log_retention_days" {
  description = "CloudWatch Lambda 로그 보존기간(일)"
  type        = number
  default     = 14
}

variable "api_throttling_burst_limit" {
  description = "HTTP API 기본 라우트 burst 한도"
  type        = number
  default     = 20
}

variable "api_throttling_rate_limit" {
  description = "HTTP API 기본 라우트 초당 요청 한도"
  type        = number
  default     = 10
}
