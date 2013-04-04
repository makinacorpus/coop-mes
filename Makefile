listen=mes:8000

ALL: install serve

install:
	./install.sh

makemessages:
	(cd coop_local; ../ve/bin/python ../manage.py makemessages -l fr)

compilemessages:
	(cd coop_local; ../ve/bin/python ../manage.py compilemessages -l fr)

serve:
	ve/bin/python manage.py runserver ${listen}

clean:
	rm -rf bin include lib local src static_collected

convert:
	soffice --invisible --headless --accept="socket,host=localhost,port=2002;urp;" &
