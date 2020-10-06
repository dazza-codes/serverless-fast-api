#!/usr/bin/env bash

set -e
set -u

source .env

dump_file="${PGDATABASE}_schema_$(date +'%Y%m%d').sql"

echo "$dump_file"

pg_dump -h $PGHOST -d $PGDATABASE -U $PGUSER --schema-only > "$dump_file"
