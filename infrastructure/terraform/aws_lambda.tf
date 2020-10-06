#
# https://www.terraform.io/docs/providers/aws/r/lambda_function.html
#
# https://iwpnd.pw/articles/2020-01/deploy-fastapi-to-aws-lambda
#
# https://learn.hashicorp.com/terraform/aws/lambda-api-gateway
#

# aws s3api create-bucket --bucket=terraform-serverless-deploys
#    --acl=public-read \
#    --create-bucket-configuration='{"LocationConstraint": "us-west-2"}'
#    --region=us-west-2


provider "aws" {
  profile = var.aws_default_profile
  region  = var.region
  version = "~> 2.31"
}

resource "aws_iam_role" "iam_for_lambda" {
  name = "iam_for_${var.app_name}"

  assume_role_policy = <<EOF
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Action": "sts:AssumeRole",
      "Principal": {
        "Service": "lambda.amazonaws.com"
      },
      "Effect": "Allow",
      "Sid": ""
    }
  ]
}
EOF
}

resource "aws_lambda_layer_version" "fast_api_app_layer" {
  filename   = "${var.py_ver}-${var.project_name}-${var.app_version}-layer.zip"
  layer_name = "${var.app_name}_${var.app_stage}_layer"
}

resource "aws_lambda_function" "fast_api_app_function" {
  //  # The bucket name as created earlier with "aws s3api create-bucket" - not used yet
  //  s3_bucket = "terraform-serverless-deploys"
  //  s3_key    = "${var.project_name}/${var.project_name}-${var.app_version}-${var.app_stage}.zip"

  filename      = "${var.py_ver}-${var.project_name}-${var.app_version}-app.zip"
  function_name = "${var.app_name}_${var.app_stage}_app"
  role          = aws_iam_role.iam_for_lambda.arn

  handler     = "example_app.main.handler"
  memory_size = 128
  timeout     = 30

  layers = [aws_lambda_layer_version.fast_api_app_layer.arn]

  source_code_hash = filebase64sha256(aws_lambda_layer_version.fast_api_app_layer.filename)

  runtime = var.runtime

  //  environment {
  //    variables = {
  //      foo = "bar"
  //    }
  //  }
}


resource "aws_api_gateway_resource" "fast_api_proxy" {
  rest_api_id = aws_api_gateway_rest_api.fast_api_gw.id
  parent_id   = aws_api_gateway_rest_api.fast_api_gw.root_resource_id
  path_part   = "{proxy+}"
}

resource "aws_api_gateway_method" "fast_api_proxy" {
  rest_api_id   = aws_api_gateway_rest_api.fast_api_gw.id
  resource_id   = aws_api_gateway_resource.fast_api_proxy.id
  http_method   = "ANY"
  authorization = "NONE"
}

resource "aws_api_gateway_integration" "fast_api_lambda" {
  rest_api_id = aws_api_gateway_rest_api.fast_api_gw.id
  resource_id = aws_api_gateway_method.fast_api_proxy.resource_id
  http_method = aws_api_gateway_method.fast_api_proxy.http_method

  integration_http_method = "POST"
  type                    = "AWS_PROXY"
  uri                     = aws_lambda_function.fast_api_app_function.invoke_arn
}

resource "aws_api_gateway_method" "fast_api_proxy_root" {
  rest_api_id   = aws_api_gateway_rest_api.fast_api_gw.id
  resource_id   = aws_api_gateway_rest_api.fast_api_gw.root_resource_id
  http_method   = "ANY"
  authorization = "NONE"
}

resource "aws_api_gateway_integration" "fast_api_lambda_root" {
  rest_api_id = aws_api_gateway_rest_api.fast_api_gw.id
  resource_id = aws_api_gateway_method.fast_api_proxy_root.resource_id
  http_method = aws_api_gateway_method.fast_api_proxy_root.http_method

  integration_http_method = "POST"
  type                    = "AWS_PROXY"
  uri                     = aws_lambda_function.fast_api_app_function.invoke_arn
}

resource "aws_api_gateway_deployment" "fast_api" {
  depends_on = [
    aws_api_gateway_integration.fast_api_lambda,
    aws_api_gateway_integration.fast_api_lambda_root,
  ]

  rest_api_id = aws_api_gateway_rest_api.fast_api_gw.id
  stage_name  = var.app_stage
}

resource "aws_lambda_permission" "fast_api_gw" {
  statement_id  = "AllowAPIGatewayInvoke"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.fast_api_app_function.function_name
  principal     = "apigateway.amazonaws.com"

  # The "/*/*" portion grants access from any method on any resource
  # within the API Gateway REST API.
  source_arn = "${aws_api_gateway_rest_api.fast_api_gw.execution_arn}/*/*"
}

output "APP_ENDPOINT" {
  value = aws_api_gateway_deployment.fast_api.invoke_url
}
