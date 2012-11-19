listen=localhost:8000

ALL: install serve

install:
	./install.sh

makemessages:
	(cd coop_local; ../bin/python ../manage.py makemessages -l fr)

compilemessages:
	(cd coop_local; ../bin/python ../manage.py compilemessages -l fr)

serve:
	bin/python manage.py runserver ${listen}

clean:
	rm -rf bin include lib local src static_collected