# -*- coding:utf-8 -*-
import os
import sys

from django.conf import settings

# Here you can override any settings from coop default settings files
# See :
# - coop/default_project_settings.py
# - coop/db_settings.py

PROJECT_PATH = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

SITE_AUTHOR = 'Organisme'
SITE_TITLE = 'Demo Django-coop'
# DEFAULT_URI_DOMAIN = '{{ domain }}' useless use Site.objects.get_current().domain instead

# let this setting to False in production, except for urgent debugging
DEBUG = False

# Force DEBUG setting if we're developing locally or testing
if 'runserver' in sys.argv or 'test' in sys.argv or 'mail_calls' in sys.argv:
    DEBUG = True
    EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'

TEMPLATE_DEBUG = DEBUG
THUMBNAIL_DEBUG = DEBUG

TEMPLATE_DIRS = [
    PROJECT_PATH + '/coop_local/templates/',
]

ADMINS = (
    ('Administrateur', 'gael.utard@makina-corpus.com'),
)

MANAGERS = ADMINS
SEND_BROKEN_LINK_EMAILS = True
INTERNAL_IPS = ('127.0.0.1', '10.0.3.1')

SUBHUB_MAINTENANCE_AUTO = False    # set this value to True to automatically syncronize with agregator
PES_HOST = 'http://pes.domain.com'
THESAURUS_HOST = 'http://thess.domain.com'

# Need to be set to true, when domain stop moving,
# to keep history of renaming of uri
URI_FIXED = False

INSTALLED_APPS = settings.INSTALLED_APPS + [
    # select your coop components
    'coop.tag',
    'coop.agenda',
    #'coop.article',
    #'coop.mailing',
    #'coop.exchange',
    #'coop.webid',
    'coop_local',
     # coop optional modules
    'coop_geo',  # est obligatoirement APRES coop_local
    'mptt',
    'geodjangofla',
    'plugin_home_search',
    'plugin_last_news',
    'plugin_direct',
    'plugin_zoomsur',
    'plugin_subpages',
    'plugin_exchange',
    'page_directory',
    'page_map',
    'page_account',
    'page_calls',
    'page_pasr_agenda',
    'page_newsletter',
    'page_guaranties',
    'page_search',
    'leaflet',
    'crispy_forms',
    'ionyweb.page_app.page_blog',
    'ionyweb.plugin_app.plugin_blog_entries_list',
    'haystack',
]

TEMPLATE_CONTEXT_PROCESSORS =  settings.TEMPLATE_CONTEXT_PROCESSORS + [
    'coop_local.context_processors.my_organization',
]

# TODO: to be discuss this settings could be in default_project_setings.py
# file. To be check I knew more on how to configure sympa
SYMPA_SOAP = {
    'WSDL': 'http://sympa.{{ root_domain }}/sympa/wsdl',
    'APPNAME': 'djangoapp',
    'PASSWORD': 'test',
    'OWNER': ADMINS[0][1],
    'PARAMETER_SEPARATOR': '__SEP__',      # used for template
}

# Keyword arguments for the MULTISITE_FALLBACK view.
# Default: {}
MULTISITE_FALLBACK_KWARGS = {}

ADMIN_TOOLS_MENU = 'coop_local.ui.menu.CustomMenu'
ADMIN_TOOLS_INDEX_DASHBOARD = 'coop_local.ui.dashboard.CustomIndexDashboard'
ADMIN_TOOLS_THEMING_CSS = 'css/coop_local_bootstrap_theming.css'

TINYMCE_FRONTEND_CONFIG = {
    'theme': "advanced",
    'relative_urls': False,
    'theme_advanced_toolbar_location': 'top',
    'theme_advanced_buttons1': 'bold,italic,underline,|,formatselect,fontsizeselect,|,justifyleft,justifycenter,justifyright,justifyfull,|,bullist,numlist,|,link,unlink,|,code',
    'theme_advanced_buttons2': '', 'theme_advanced_buttons3': '',
    'theme_advanced_resizing': True,
    'theme_advanced_statusbar_location': 'bottom',
    'theme_advanced_resize_horizontal': False,
    'theme_advanced_path': False,
}

SITE_NAME = 'Achetons Solidaires'
DOMAIN_NAME = 'mes:8000'
ACTIVITY_NOMENCLATURE_LOOKUP_LEVEL = 2
REGION_LABEL = os.environ.get('REGION_LABEL', 'PROVENCE-ALPES-COTE D\'AZUR')

LEAFLET_CONFIG = {
    #'TILES_URL': 'http://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png',
    'TILES_URL': 'http://otile1.mqcdn.com/tiles/1.0.0/osm/{z}/{x}/{y}.png',
    #'SPATIAL_EXTENT': (2.56, 42.34, 9.14, 45.79),
    'DEFAULT_CENTER': (0, 46.39),
    'DEFAULT_ZOOM': 8,
}

LOGIN_URL = '/mon-compte/p/connexion/'

CRISPY_TEMPLATE_PACK = 'bootstrap3'
