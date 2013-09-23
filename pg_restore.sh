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
if [ -z "$DOMAIN" ]; then
    echo "ERROR: DOMAIN is not defined"
    exit 1
fi
if [ -z "$1" ]; then
    echo "ERROR: No dump file provided"
    exit 1
fi

PSQL="sudo -u postgres psql -d $DB_NAME"

$PSQL -c "DROP SCHEMA public CASCADE;"
$PSQL -c "CREATE SCHEMA public AUTHORIZATION $DB_USER;"

gzip -cd $1 \
    | sed "s/ALTER TABLE \([^ ]*\) OWNER TO .*;/ALTER TABLE \1 OWNER TO $DB_USER;/g" \
    | sed "s/GRANT ALL ON TABLE \([^ ]*\) TO .*;/GRANT ALL ON TABLE \1 TO $DB_USER;/g" \
    | $PSQL

$PSQL -c "UPDATE django_site SET name='localhost', domain='$DOMAIN' WHERE id=1;"
$PSQL -c "UPDATE multisite_alias SET domain='$DOMAIN' WHERE id=1;"
