DJANGO_LISTEN?=localhost:8000
VENV=venv
PYTHON=$(VENV)/bin/python
PIP=$(VENV)/bin/pip
BACKUP=backups/$(shell date +%F_%H-%M-%S)

default: install

virtualenv: $(PYTHON)
$(PYTHON):
	virtualenv $(VENV)

requirements: virtualenv
	$(PIP) install -U distribute
	$(PIP) install --no-deps -r requirements.txt
	(cd $(VENV)/lib/python2.7/site-packages/; ln -s /usr/lib/python2.7/dist-packages/uno*.py .)

sync:
	$(PYTHON) manage.py collectstatic --noinput
	$(PYTHON) manage.py syncdb --all --noinput
	$(PYTHON) manage.py migrate --fake

fixtures:
	$(PYTHON) manage.py loaddata coop_local/fixtures/area_types.json
	$(PYTHON) manage.py loaddata coop_local/fixtures/django_site.json
	$(PYTHON) manage.py loaddata coop_local/fixtures/exchange_methods.json
	$(PYTHON) manage.py loaddata coop_local/fixtures/location_categories.json
	$(PYTHON) manage.py loaddata coop_local/fixtures/roles.json
	$(PYTHON) manage.py loaddata coop_local/fixtures/user.json
	$(PYTHON) manage.py loaddata coop_local/fixtures/legalstatus.json
	$(PYTHON) manage.py loaddata coop_local/fixtures/organizationcategory.json
	$(PYTHON) manage.py loaddata coop_local/fixtures/categoryiae.json
	$(PYTHON) manage.py loaddata coop_local/fixtures/activitynomenclatureavise.json
	$(PYTHON) manage.py loaddata coop_local/fixtures/activitynomenclature.json
	$(PYTHON) manage.py loaddata coop_local/fixtures/clienttarget.json
	$(PYTHON) manage.py loaddata coop_local/fixtures/transversetheme.json
	$(PYTHON) manage.py loaddata coop_local/fixtures/guaranty.json
	$(PYTHON) manage.py loaddata coop_local/fixtures/agreementiae.json
	$(PYTHON) manage.py loaddata coop_local/fixtures/contact_mediums.json
	$(PYTHON) manage.py loaddata coop_local/fixtures/relation_types.json
	$(PYTHON) manage.py loaddata coop_local/fixtures/group.json

install: requirements sync fixtures

makemessages:
	(cd coop_local; ../$(PYTHON) ../manage.py makemessages -l fr)

compilemessages:
	(cd coop_local; ../$(PYTHON) ../manage.py compilemessages -l fr)

serve:
	$(PYTHON) manage.py runserver $(DJANGO_LISTEN)

convert:
	soffice --invisible --headless --accept="socket,host=localhost,port=2002;urp;" &

css:
	(cd coop_local/static/css/; lessc theme-default.less theme-default.css)
	(cd coop_local/static/css/; lessc theme-orange.less theme-orange.css)
	(cd coop_local/static/css/; lessc theme-npdc.less theme-npdc.css)
	(cd coop_local/static/css/; lessc theme-bdis.less theme-bdis.css)
	(cd coop_local/static/css/bootstrap; lessc bootstrap.less bootstrap.css)

backup:
	mkdir -p $(BACKUP)
	./pg_dump.sh $(BACKUP)/db.sql.gz
	tar -cvzf $(BACKUP)/media.tgz --exclude cache media/
	tar -cvf $(BACKUP).tar $(BACKUP)
	rm -rf $(BACKUP)

restore:
	tar -xvf $(BACKUP).tar
	./pg_restore.sh $(BACKUP)/db.sql.gz
	tar -xvzf $(BACKUP)/media.tgz

clean:
	rm -rf static_collected

test:
	$(PYTHON) manage.py test page_directory --traceback
