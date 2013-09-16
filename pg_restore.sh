#!/bin/bash
if [ -z "${DB_USER}" ]; then
    echo "ERROR: DB_USER is not defined"
    exit 1
fi
if [ -z "${DB_NAME}" ]; then
    echo "ERROR: DB_NAME is not defined"
    exit 1
fi

echo "DROP SCHEMA public CASCADE;" | sudo -u postgres psql $DB_NAME
echo "CREATE SCHEMA public AUTHORIZATION ${DB_USER};" | sudo -u postgres psql $DB_NAME
pg_restore $1 | sudo -u postgres psql $DB_NAME
