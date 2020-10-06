#!/usr/bin/env bash

# shellcheck disable=SC1091
source .env

# no DBInstanceIdentifier is specified so that it is easier for CFN to update/replace it;
# to get the current RDS instance, query the CFN stack

#aws cloudformation describe-stack-resource \
#  --stack-name "appDevStack" \
#  --logical-resource-id database

RDS_ID=$(aws cloudformation describe-stack-resource \
  --stack-name "$APP_STACK_NAME" \
  --logical-resource-id database \
  --query 'StackResourceDetail.PhysicalResourceId' \
  --output text)

rds_status () {
    echo "CURRENT DATABASE STATUS ($RDS_ID)"
    aws rds describe-db-instances --db-instance-identifier "$RDS_ID"
}

rds_delete () {
  while true; do
    read -r -p "Please confirm delete of RDS ($RDS_ID)? (y || n) " yn
    case $yn in
        [Yy]* )
          echo "Deleting DB instance ($RDS_ID)"
          aws rds modify-db-instance --db-instance-identifier "$RDS_ID" --no-deletion-protection
          aws rds delete-db-instance --db-instance-identifier "$RDS_ID" --skip-final-snapshot
          break;;
        [Nn]* )
          echo "Skipping delete for DB instance ($RDS_ID)"
          break;;
        * ) echo "Please answer yes or no.";;
    esac
  done
}

#rds_status

#
# Parse RDS info using jq - https://stedolan.github.io/jq
#
RDS_JSON=$( aws rds describe-db-instances --db-instance-identifier "$RDS_ID" --output json)
#echo $RDS_JSON

RDS_HOST=$(echo "$RDS_JSON" | jq '.DBInstances[0].Endpoint.Address' | sed 's/["]//g')
RDS_PORT=$(echo "$RDS_JSON" | jq '.DBInstances[0].Endpoint.Port' | sed 's/["]//g')

APP_RDS_DB_RO="${APP_STACK_NAMESPACE}DbRO"
APP_RDS_DB_RW="${APP_STACK_NAMESPACE}DbRW"

RO_SECRETS_EXIST=false
RW_SECRETS_EXIST=false

# from app_env.sh:
#APP_RDS_DB_NAME="${APP_STACK_NAMESPACE}Db"

# shellcheck disable=SC2089
DB_SECRETS="{'username':'app_ro','password':'app_ro','engine':'postgres','host':'${RDS_HOST}','port':${RDS_PORT},'dbname':'${APP_RDS_DB_NAME}','dbInstanceIdentifier':'${RDS_ID}'}"
RO_SECRETS=${DB_SECRETS}
RW_SECRETS=${DB_SECRETS//app_ro/app_rw}

# ensure the strings are good json payloads
RO_SECRETS=$(python -c "import json; print(json.dumps(${RO_SECRETS}))")
RW_SECRETS=$(python -c "import json; print(json.dumps(${RW_SECRETS}))")

echo "${RO_SECRETS}"
echo "${RW_SECRETS}"

secret_names=$(aws secretsmanager list-secrets | jq '.SecretList[].Name' | sed 's/["]//g')

for secret_name in ${secret_names}
do
  if [ "$secret_name" == "${APP_RDS_DB_RO}" ]; then
    RO_SECRETS_EXIST=true
  fi
  if [ "$secret_name" == "${APP_RDS_DB_RW}" ]; then
    RW_SECRETS_EXIST=true
  fi
done


UPDATE=${UPDATE:=false}
DRY_RUN=${DRY_RUN:=true}

if [ "$RO_SECRETS_EXIST" == "true" ]; then
    if [ "$DRY_RUN" != "true" ]; then
      if [ "$UPDATE" == "true" ]; then
        echo "Updating ${APP_RDS_DB_RO}"
        aws secretsmanager update-secret --secret-id "$APP_RDS_DB_RO" \
          --description "read-only database connection" \
          --secret-string "${RO_SECRETS}"
      else
        echo "Skipping update for ${APP_RDS_DB_RO}"
      fi
    else
      echo "DRY_RUN:  Updating ${APP_RDS_DB_RO}"
      echo "DRY_RUN:  Secrets: ${RO_SECRETS}"
    fi
else
    if [ "$DRY_RUN" != "true" ]; then
      echo "Creating ${APP_RDS_DB_RO}"
      aws secretsmanager create-secret --name "$APP_RDS_DB_RO" \
          --description "read-only database connection" \
          --secret-string "${RO_SECRETS}"
    else
      echo "DRY_RUN:  Creating ${APP_RDS_DB_RO}"
      echo "DRY_RUN:  Secrets: ${RO_SECRETS}"
    fi
fi


if [ "$RW_SECRETS_EXIST" == "true" ]; then
    if [ "$DRY_RUN" != "true" ]; then
      if [ "$UPDATE" == "true" ]; then
        echo "Updating ${APP_RDS_DB_RW}"
        aws secretsmanager update-secret --secret-id "$APP_RDS_DB_RW" \
          --description "read-write database connection" \
          --secret-string "${RW_SECRETS}"
      else
        echo "Skipping update for ${APP_RDS_DB_RW}"
      fi
    else
      echo "DRY_RUN:  Updating ${APP_RDS_DB_RW}"
      echo "DRY_RUN:  Secrets: ${RW_SECRETS}"
    fi
else
    if [ "$DRY_RUN" != "true" ]; then
      echo "Creating ${APP_RDS_DB_RW}"
      aws secretsmanager create-secret --name "$APP_RDS_DB_RW" \
          --description "read-write database connection" \
          --secret-string "${RW_SECRETS}"
    else
      echo "DRY_RUN:  Creating ${APP_RDS_DB_RW}"
      echo "DRY_RUN:  Secrets: ${RW_SECRETS}"
    fi
fi


aws secretsmanager get-secret-value --secret-id "$APP_RDS_DB_ADMIN"
aws secretsmanager get-secret-value --secret-id "$APP_RDS_DB_RO"
aws secretsmanager get-secret-value --secret-id "$APP_RDS_DB_RW"
