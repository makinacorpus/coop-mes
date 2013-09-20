#!/bin/bash
set -e

[ -f .env ] && source .env

if [ -z "$DB_USER" ]; then
    echo "ERROR: DB_USER is not defined"
    exit 1
fi
if [ -z "$DB_NAME" ]; then
    echo "ERROR: DB_NAME is not defined"
    exit 1
fi
if [ -z "$1" ]; then
    OUTPUT="db_`date +%F_%H-%M-%S`.sql.gz"
else
    OUTPUT="$1"
fi

pg_dump -U "$DB_USER" -h localhost "$DB_NAME" | gzip > "$OUTPUT"
