#!/bin/bash
if [ -z "${DB_NAME}" ]; then
    echo "ERROR: DB_NAME is not defined"
    exit 1
fi

pg_dump -Fc -U coop_mes -h localhost ${DB_NAME} > pg_dump.`date +%FT%T`
