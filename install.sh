#!/bin/bash

db_name=coop_mes
db_user=coop_mes
db_pass=123456

sudo apt-get update
sudo apt-get install make git mercurial postgresql postgresql-9.1-postgis postgresql-server-dev-9.1 \
    python-virtualenv python-dev gdal-bin

test -e bin/python || virtualenv .
bin/pip install -r requirements.txt

if ! sudo -u postgres psql -tAc "SELECT 'ok' FROM pg_roles WHERE rolname='${db_user}'" | grep "ok"; then
    sudo -u postgres psql -c "CREATE USER ${db_user} PASSWORD '${db_pass}';"
fi

if ! sudo -u postgres psql -tAl | grep "^${db_name}"; then
        sudo -u postgres psql -c "CREATE DATABASE ${db_name} OWNER ${db_user};"
        sudo -u postgres psql -f /usr/share/postgresql/9.1/contrib/postgis-1.5/postgis.sql -d ${db_name}
        sudo -u postgres psql -f /usr/share/postgresql/9.1/contrib/postgis-1.5/spatial_ref_sys.sql -d ${db_user}
        sudo -u postgres psql ${db_name} -c "ALTER TABLE geometry_columns OWNER TO ${db_user};"
        sudo -u postgres psql ${db_name} -c "ALTER TABLE spatial_ref_sys OWNER TO ${db_user};"
fi

bin/python manage.py collectstatic --noinput
bin/python manage.py syncdb --migrate --noinput
bin/python manage.py loaddata coop_local/fixtures/areatypes.json
bin/python manage.py loaddata coop_local/fixtures/django_site.json
bin/python manage.py loaddata coop_local/fixtures/exchange_methods.json
bin/python manage.py loaddata coop_local/fixtures/linkproperty.json
bin/python manage.py loaddata coop_local/fixtures/location_categories.json
bin/python manage.py loaddata coop_local/fixtures/roles.json
bin/python manage.py loaddata coop_local/fixtures/uriredirect.json
bin/python manage.py loaddata coop_local/fixtures/user.json
bin/python manage.py loaddata coop_local/fixtures/legalstatus.json
bin/python manage.py loaddata coop_local/fixtures/organizationcategory.json
bin/python manage.py loaddata coop_local/fixtures/categoryiae.json
bin/python manage.py loaddata coop_local/fixtures/activitynomenclatureavise.json
bin/python manage.py loaddata coop_local/fixtures/activitynomenclature.json
bin/python manage.py loaddata coop_local/fixtures/clienttarget.json
bin/python manage.py loaddata coop_local/fixtures/transversetheme.json
bin/python manage.py loaddata coop_local/fixtures/guaranty.json
bin/python manage.py loaddata coop_local/fixtures/agreementiae.json
