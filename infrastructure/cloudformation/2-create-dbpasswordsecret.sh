#!/bin/bash
set -eo pipefail

# shellcheck disable=SC1091
source .env

secret_names=$(aws secretsmanager list-secrets | awk '/"Name":/ { print $2 }' | sed 's/[",]//g')

for secret_name in ${secret_names}
do
  if [ "$secret_name" == "${APP_RDS_DB_ADMIN}" ]
  then
    echo "Using ${APP_RDS_DB_ADMIN} that exists already"
    exit
  fi
done

echo "Creating ${APP_RDS_DB_ADMIN} secret with random password"

DB_PASSWORD=$(dd if=/dev/random bs=8 count=1 2>/dev/null | od -An -tx1 | tr -d ' \t\n')
aws secretsmanager create-secret --name "$APP_RDS_DB_ADMIN" \
    --description "database password" \
    --secret-string "{\"username\":\"$APP_RDS_DB_ADMIN\",\"password\":\"$DB_PASSWORD\"}"


# TO delete secrets that are not cleaned up:
# aws secretsmanager delete-secret --secret-id {secret-arn}

# This password generator is from infrastructure/database/create-database.sh
#pw=$(cat /dev/urandom | tr -dc 'a-zA-Z0-9' | fold -w 12 | head -n 1)

# See also rds_functions.sh for details of the application secrets;
# this script only creates an admin-user and password secret.

# Note: for another option to get random passwords:
#$ aws secretsmanager get-random-password
#{
#    "RandomPassword": "}o9vY@C!M^|,N4|PnD~JP?$Yz2!E^$bT"
#}
