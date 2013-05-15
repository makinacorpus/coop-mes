#!/bin/bash

db_name=coop_mes
db_user=coop_mes
db_pass=123456

sudo apt-get update
sudo apt-get install make git mercurial postgresql postgresql-9.1-postgis postgresql-server-dev-9.1 \
    python-virtualenv python-dev gdal-bin libgeoip1

test -e ve/bin/python || virtualenv ve
ve/bin/pip install -U distribute
ve/bin/pip install --no-deps -r requirements.txt

if ! sudo -u postgres psql -tAc "SELECT 'ok' FROM pg_roles WHERE rolname='${db_user}'" | grep "ok"; then
    sudo -u postgres psql -c "CREATE USER ${db_user} PASSWORD '${db_pass}';"
fi

if ! sudo -u postgres psql -tAl | grep "^${db_name}"; then
        sudo -u postgres psql -c "CREATE DATABASE ${db_name} OWNER ${db_user};"
        sudo -u postgres psql -f /usr/share/postgresql/9.1/contrib/postgis-1.5/postgis.sql -d ${db_name}
        sudo -u postgres psql -f /usr/share/postgresql/9.1/contrib/postgis-1.5/spatial_ref_sys.sql -d ${db_name}
        sudo -u postgres psql ${db_name} -c "ALTER TABLE geometry_columns OWNER TO ${db_user};"
        sudo -u postgres psql ${db_name} -c "ALTER TABLE spatial_ref_sys OWNER TO ${db_user};"
fi

ve/bin/python manage.py collectstatic --noinput
ve/bin/python manage.py syncdb --all --noinput
ve/bin/python manage.py migrate --fake
ve/bin/python manage.py loaddata coop_local/fixtures/area_types.json
ve/bin/python manage.py loaddata coop_local/fixtures/django_site.json
ve/bin/python manage.py loaddata coop_local/fixtures/exchange_methods.json
ve/bin/python manage.py loaddata coop_local/fixtures/linking_properties.json
ve/bin/python manage.py loaddata coop_local/fixtures/location_categories.json
ve/bin/python manage.py loaddata coop_local/fixtures/roles.json
ve/bin/python manage.py loaddata coop_local/fixtures/uriredirect.json
ve/bin/python manage.py loaddata coop_local/fixtures/user.json
ve/bin/python manage.py loaddata coop_local/fixtures/legalstatus.json
ve/bin/python manage.py loaddata coop_local/fixtures/organizationcategory.json
ve/bin/python manage.py loaddata coop_local/fixtures/categoryiae.json
ve/bin/python manage.py loaddata coop_local/fixtures/activitynomenclatureavise.json
ve/bin/python manage.py loaddata coop_local/fixtures/activitynomenclature.json
ve/bin/python manage.py loaddata coop_local/fixtures/clienttarget.json
ve/bin/python manage.py loaddata coop_local/fixtures/transversetheme.json
ve/bin/python manage.py loaddata coop_local/fixtures/guaranty.json
ve/bin/python manage.py loaddata coop_local/fixtures/agreementiae.json
ve/bin/python manage.py loaddata coop_local/fixtures/contact_mediums.json
ve/bin/python manage.py loaddata coop_local/fixtures/relation_types.json
ve/bin/python manage.py loaddata coop_local/fixtures/group.json
