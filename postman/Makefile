# https://www.gnu.org/software/make/manual/html_node/Makefile-Conventions.html

SHELL = /bin/bash

.ONESHELL:
.SUFFIXES:

PROJECT=serverless-fast-api-postman

S3_BUCKET=app-serverless-deploys
S3_PREFIX=$(PROJECT)

AWS_PROFILE=${AWS_PROFILE}
AWS_REGION=${AWS_DEFAULT_REGION:-us-west-2}

clean:
	@rm -rf .aws-sam

format:
	@yarn run prettier src

init:
	@yarn

test:
	@yarn run jest

sam-build:
	@cp package.json layer/
	@sam build --use-container

sam-package: sam-build
	@sam package \
		--s3-bucket $(S3_BUCKET) --s3-prefix $(S3_PREFIX) \
		--profile $(AWS_PROFILE) --region $(AWS_REGION)

sam-deploy: sam-build
	@sam deploy \
		--stack-name $(PROJECT) --capabilities CAPABILITY_IAM \
		--s3-bucket $(S3_BUCKET) --s3-prefix $(S3_PREFIX) \
		--profile $(AWS_PROFILE) --region $(AWS_REGION)

.PHONY: clean format init test sam-build sam-package sam-deploy

#
# Invoke specific project collections
#

sam-local-invoke-app-dev: sam-build
	@sam local invoke AppDevPostman

.PHONY: sam-local-invoke-app
