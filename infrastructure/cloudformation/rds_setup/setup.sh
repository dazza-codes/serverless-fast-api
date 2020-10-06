#!/usr/bin/env bash

set -e
set -u

echo "This setup has been run already"
echo "Check the RDS and/or run setup manually"
exit

# shellcheck disable=SC1091
source .env

psql -f setup_database.sql > setup_database.log 2>&1
psql -f app_pgdump_20200101.sql > pgdump.log 2>&1
