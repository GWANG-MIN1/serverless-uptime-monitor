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
