#!/bin/bash
if [ -z "${DB_USER}" ]; then
    echo "ERROR: DB_USER is not defined"
    exit 1
fi
if [ -z "${DB_NAME}" ]; then
    echo "ERROR: DB_NAME is not defined"
    exit 1
fi
if [ -z "${DB_PASS}" ]; then
    echo "ERROR: DB_PASS is not defined"
    exit 1
fi
sudo apt-get -y update
sudo apt-get -y install make git mercurial
sudo apt-get -y install python-dev python-virtualenv
sudo apt-get -y install postgresql postgresql-9.1-postgis postgresql-server-dev-9.1
sudo apt-get -y install gdal-bin libgeoip1

sudo sed -i 's/^local *all *all *peer$/local   all             all                                     ident/' /etc/postgresql/9.1/main/pg_hba.conf
sudo service postgresql restart

if ! sudo -u postgres psql -tAc "SELECT 'ok' FROM pg_roles WHERE rolname='${DB_USER}'" | grep "ok"; then
    sudo -u postgres psql -c "CREATE USER ${DB_USER} PASSWORD '${DB_PASS}';"
fi

if ! sudo -u postgres psql -tAl | grep "^${DB_NAME}"; then
    sudo -u postgres psql -c "CREATE DATABASE ${DB_NAME} OWNER ${DB_USER} ENCODING 'UTF8' LC_COLLATE 'C' LC_CTYPE 'C' TEMPLATE template0;"
    sudo -u postgres psql -f /usr/share/postgresql/9.1/contrib/postgis-1.5/postgis.sql -d ${DB_NAME}
    sudo -u postgres psql -f /usr/share/postgresql/9.1/contrib/postgis-1.5/spatial_ref_sys.sql -d ${DB_NAME}
    sudo -u postgres psql ${DB_NAME} -c "ALTER TABLE geometry_columns OWNER TO ${DB_USER};"
    sudo -u postgres psql ${DB_NAME} -c "ALTER TABLE spatial_ref_sys OWNER TO ${DB_USER};"
fi

make install
