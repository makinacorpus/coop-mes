# -*- coding: utf-8 -*-

from django.conf.urls import patterns, url
from .views import (
    index_view,
    login_view,
    logout_view,
    inscription_view,
    organizations_view,
    my_calls_view,
)

urlpatterns = patterns('',
    url(r'^$', index_view),
    url(r'^inscription/$', inscription_view),
    url(r'^connexion/$', login_view),
    url(r'^deconnexion/$', logout_view),
    url(r'^mes-organisations/$', organizations_view),
    url(r'^mes-appels-doffres/$', my_calls_view),
)
