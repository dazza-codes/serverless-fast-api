variable "aws_default_profile" {
  default = "consulting"
}

variable "region" {
  default = "us-west-2"
}

# The pyproject.toml defines the python version etc., keep these in sync;
# See also Makefile definitions.

variable "runtime" {
  default = "python3.7"
}

variable "py_version" {
  default = "3.7"
}

variable "py_ver" {
  default = "py37"
}

variable "project_name" {
  default = "serverless-fast-api"
}

variable "app_name" {
  default = "fastapi_demo"
}

# invoke-release manages this version string, via tasks.py

variable "app_version" {
  default = "0.2.0"
}

variable "app_stage" {
  default = "dev"
}

variable "app_s3_bucket" {
  default = "app-serverless-deploys"
}
