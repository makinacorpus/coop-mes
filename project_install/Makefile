listen=localhost:8000

ALL: install serve

install:
	sudo ./script_install.sh
	fab server_setup
	fab coop_setup
	fab initialize_django_env
	fab initialize_geo_django

makemessages:
	(cd coop_local; ../bin/python ../manage.py makemessages -l fr)

compilemessages:
	(cd coop_local; ../bin/python ../manage.py compilemessages -l fr)

serve:
	bin/python manage.py runserver ${listen}

clean:
	rm -rf bin include lib local src static_collected