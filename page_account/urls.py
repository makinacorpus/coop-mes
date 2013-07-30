# -*- coding: utf-8 -*-

from django.conf.urls import patterns, url
from .views import (
    index_view,
    login_view,
    logout_view,
    InscriptionView,
    inscription_forms
)

urlpatterns = patterns('',
    url(r'^$', index_view),
    url(r'^inscription/$', InscriptionView.as_view(inscription_forms)),
    url(r'^connexion/$', login_view),
    url(r'^deconnexion/$', logout_view),
)
