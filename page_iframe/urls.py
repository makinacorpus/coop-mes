# -*- coding: utf-8 -*-

from django.conf.urls import patterns, url
from .views import index_view, list_view, carto_view, detail_view

urlpatterns = patterns('',
    url(r'^$', index_view),
    url('^(?P<pk>\d+)/$', list_view),
    url('^(?P<pk>\d+)/carto/$', carto_view),
    url('^(?P<pk>\d+)/(?P<org_pk>\d+)/$', detail_view),
)
