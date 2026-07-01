resource "aws_apigatewayv2_api" "main" {
  name          = "${var.project_name}-api"
  protocol_type = "HTTP"
}

resource "aws_apigatewayv2_stage" "default" {
  api_id      = aws_apigatewayv2_api.main.id
  name        = "$default"
  auto_deploy = true

  # 공개 API 남용 방지를 위한 기본 라우트 스로틀링
  default_route_settings {
    throttling_burst_limit = var.api_throttling_burst_limit
    throttling_rate_limit  = var.api_throttling_rate_limit
  }
}

resource "aws_apigatewayv2_integration" "register" {
  api_id                 = aws_apigatewayv2_api.main.id
  integration_type       = "AWS_PROXY"
  integration_uri        = aws_lambda_function.register.invoke_arn
  payload_format_version = "2.0"
}

resource "aws_apigatewayv2_route" "post_endpoint" {
  api_id    = aws_apigatewayv2_api.main.id
  route_key = "POST /endpoints"
  target    = "integrations/${aws_apigatewayv2_integration.register.id}"
}

resource "aws_apigatewayv2_route" "get_endpoints" {
  api_id    = aws_apigatewayv2_api.main.id
  route_key = "GET /endpoints"
  target    = "integrations/${aws_apigatewayv2_integration.register.id}"
}

resource "aws_apigatewayv2_route" "get_endpoint" {
  api_id    = aws_apigatewayv2_api.main.id
  route_key = "GET /endpoints/{id}"
  target    = "integrations/${aws_apigatewayv2_integration.register.id}"
}

resource "aws_apigatewayv2_route" "delete_endpoint" {
  api_id    = aws_apigatewayv2_api.main.id
  route_key = "DELETE /endpoints/{id}"
  target    = "integrations/${aws_apigatewayv2_integration.register.id}"
}

resource "aws_apigatewayv2_route" "get_history" {
  api_id    = aws_apigatewayv2_api.main.id
  route_key = "GET /endpoints/{id}/history"
  target    = "integrations/${aws_apigatewayv2_integration.register.id}"
}

resource "aws_lambda_permission" "allow_api_gateway" {
  statement_id  = "AllowAPIGateway"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.register.function_name
  principal     = "apigateway.amazonaws.com"
  source_arn    = "${aws_apigatewayv2_api.main.execution_arn}/*/*"
}
