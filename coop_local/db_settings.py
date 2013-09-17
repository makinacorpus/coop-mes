# -*- coding:utf-8 -*-
import os
from coop_local.settings import PROJECT_NAME

DATABASES = {
    'default': {
        'ENGINE': 'django.contrib.gis.db.backends.postgis',  # Add 'postgresql_psycopg2', 'postgresql', 'mysql', 'sqlite3' or 'oracle'.
        'NAME': os.environ.get('DB_NAME', PROJECT_NAME),     # Or path to database file if using sqlite3.
        'USER': os.environ.get('DB_USER', 'coop_mes'),       # Not used with sqlite3.
        'PASSWORD': os.environ.get('DB_PASS', '123456'),     # Not used with sqlite3.
        'HOST': 'localhost',
    },
    'geofla_db': {
        'ENGINE': 'django.contrib.gis.db.backends.postgis',  # Add 'postgresql_psycopg2', 'postgresql', 'mysql', 'sqlite3' or 'oracle'.
        'NAME': 'geofla',                                    # Or path to database file if using sqlite3.
        'USER': 'geofla',                                    # Not used with sqlite3.
        'PASSWORD': 'geofla',                                # Not used with sqlite3.
        'HOST': 'localhost',
    },
}

# For redis
REDIS_PORT = 6379  # Please ask for a redis port to your administrator.
                   # Default value 6379, may already been used'

# # For django-rq, this mandatory to run rqworker command from manage.py
RQ_QUEUES = {
    'default': {
        'HOST': '127.0.0.1',
        'PORT': REDIS_PORT,
        'DB': 0,
    },
}


# Elastic search
HAYSTACK_CONNECTIONS = {
    'default': {
        'ENGINE': 'haystack.backends.whoosh_backend.WhooshEngine',
        'PATH': os.path.join(os.path.dirname(__file__), 'whoosh_index'),
    },
}
HAYSTACK_REALTIME = True  # To rebuild on the fly
