# -*- coding:utf-8 -*-

from django.conf import settings
import sys

# Here you can override any settings from coop default settings files
# See :
# - coop/default_project_settings.py
# - coop/db_settings.py

SITE_AUTHOR = 'Organisme'
SITE_TITLE = 'Demo Django-coop'
# DEFAULT_URI_DOMAIN = '{{ domain }}' useless use Site.objects.get_current().domain instead

# let this setting to False in production, except for urgent debugging
DEBUG = False

# Force DEBUG setting if we're developing locally or testing
if 'runserver' in sys.argv or 'test' in sys.argv:
    DEBUG = True

TEMPLATE_DEBUG = DEBUG

ADMINS = (
    ('Administrateur', 'web@quinode.fr'),
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
    #'coop.agenda',
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
    'plugin_subpages',
    'page_directory',
    'page_map',
    'leaflet',
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

#TINYMCE_DEFAULT_CONFIG = {
    #'theme': "advanced",
    #'relative_urls': False,
    #'width': '617px', 'height': '220px',
    #'theme_advanced_toolbar_location': 'top',
    #'theme_advanced_statusbar_location': 'none',
    #'theme_advanced_buttons1': 'bold,italic,|,justifyleft,justifycenter,justifyright,|,bullist,numlist,|,link,unlink,|,code',
    #'theme_advanced_buttons2': '', 'theme_advanced_buttons3': ''
#}

SITE_NAME = 'Achetons Solidaires'
DOMAIN_NAME = 'mes:8000'
ACTIVITY_NOMENCLATURE_LOOKUP_LEVEL = 2
SEARCH_DEPARTEMENTS = (
    u'01', u'02', u'03', u'04', u'05', u'06', u'07', u'08', u'09', u'10',
    u'11', u'12', u'13', u'14', u'15', u'16', u'17', u'18', u'19',
    u'2A', u'2B',
    u'21', u'22', u'23', u'24', u'25', u'26', u'27', u'28', u'29', u'30',
    u'31', u'32', u'33', u'34', u'35', u'36', u'37', u'38', u'39', u'40',
    u'41', u'42', u'43', u'44', u'45', u'46', u'47', u'48', u'49', u'50',
    u'51', u'52', u'53', u'54', u'55', u'56', u'57', u'58', u'59', u'60',
    u'61', u'62', u'63', u'64', u'65', u'66', u'67', u'68', u'69', u'70',
    u'71', u'72', u'73', u'74', u'75', u'76', u'77', u'78', u'79', u'80',
    u'81', u'82', u'83', u'84', u'85', u'86', u'87', u'88', u'89', u'90',
    u'91', u'92', u'93', u'94', u'95'
)

LEAFLET_CONFIG = {
    'TILES_URL': 'http://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png',
    #'SPATIAL_EXTENT': (2.56, 42.34, 9.14, 45.79),
    'DEFAULT_CENTER': (0, 46.39),
    'DEFAULT_ZOOM': 8,
}
