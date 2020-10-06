#!/bin/bash
set -eo pipefail

# shellcheck disable=SC1091
source .env

# app_env.sh provides parameters for template-vpc-rds.yml
# - see restrictions on name patterns in the YAML file

aws cloudformation deploy \
  --template-file template-vpc-rds.yml \
  --stack-name "${APP_STACK_NAME}" \
  --capabilities CAPABILITY_NAMED_IAM \
  --parameter-overrides \
    appStage="$STAGE" \
    appDomain="$APP_DOMAIN" \
    appDataBucket="$APP_DATA_BUCKET_NAME" \
    databaseName="$APP_RDS_DB_NAME" \
    databaseAdmin="$APP_RDS_DB_ADMIN"
