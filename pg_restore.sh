#!/bin/bash

echo 'DROP SCHEMA public CASCADE;' | sudo -u postgres psql coop_mes
echo ' CREATE SCHEMA public AUTHORIZATION coop_mes;' | sudo -u postgres psql coop_mes
pg_restore pg_dump.data | sudo -u postgres psql coop_mes

