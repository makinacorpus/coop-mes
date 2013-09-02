# -*- coding: utf-8 -*-

from django.conf.urls import patterns, url
from .views import index_view, detail_view, update_view, delete_view, add_view

urlpatterns = patterns('',
                       url(r'^$', index_view),
                       url(r'^(?P<pk>\d+)/$', detail_view),
                       url(r'^(?P<pk>\d+)/modifier/$', update_view),
                       url(r'^(?P<pk>\d+)/supprimer/$', delete_view),
                       url(r'^ajouter/$', add_view),
                       )
