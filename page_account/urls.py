# -*- coding: utf-8 -*-

from django.conf.urls import patterns, url
from .views import (
    index_view,
    login_view,
    logout_view,
    password_reset_view,
    password_reset_done_view,
    password_reset_confirm_view,
    password_reset_complete_view,
    organizations_view,
    my_calls_view,
    my_offers_view,
    my_preferences_view,
)

urlpatterns = patterns('',
    url(r'^$', index_view),
    url(r'^connexion/$', login_view),
    url(r'^deconnexion/$', logout_view),
    url(r'^password_reset/$', password_reset_view),
    url(r'^password_reset_done/$', password_reset_done_view),
    url(r'^password_reset_confirm/(?P<uidb36>[0-9A-Za-z]{1,13})-(?P<token>[0-9A-Za-z]{1,13}-[0-9A-Za-z]{1,20})/$',
        password_reset_confirm_view),
    url(r'^password_reset_complete/$', password_reset_complete_view),
    url(r'^mes-organisations/$', organizations_view),
    url(r'^mes-appels-doffres/$', my_calls_view),
    url(r'^mes-offres/$', my_offers_view),
    url(r'^mes-preferences/$', my_preferences_view),
)
