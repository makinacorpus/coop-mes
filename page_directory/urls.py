# -*- coding: utf-8 -*-

from django.conf.urls import patterns, url
from .views import (
    index_view,
    detail_view,
    add_view,
    change_view,
    offer_update_view,
    offer_delete_view,
    offer_add_view,
)

urlpatterns = patterns('',
    url(r'^$', index_view),
    url(r'^(?P<pk>\d+)/$', detail_view),
    url(r'^ajouter/$', add_view),
    url(r'^modifier/$', change_view),
    url(r'^modifier/(?P<step>\d+)/$', change_view),
    url(r'^offre/(?P<pk>\d+)/modifier/$', offer_update_view),
    url(r'^offre/(?P<pk>\d+)/supprimer/$', offer_delete_view),
    url(r'^offre/ajouter/$', offer_add_view),
)
