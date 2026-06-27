resource "aws_dynamodb_table" "endpoints" {
  name         = "${var.project_name}-endpoints"
  billing_mode = "PAY_PER_REQUEST"
  hash_key     = "id"

  attribute {
    name = "id"
    type = "S"
  }

  tags = local.common_tags
}

resource "aws_dynamodb_table" "check_history" {
  name         = "${var.project_name}-check-history"
  billing_mode = "PAY_PER_REQUEST"
  hash_key     = "endpoint_id"
  range_key    = "checked_at"

  attribute {
    name = "endpoint_id"
    type = "S"
  }

  attribute {
    name = "checked_at"
    type = "S"
  }

  ttl {
    attribute_name = "expires_at"
    enabled        = true
  }

  tags = local.common_tags
}
