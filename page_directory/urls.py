# -*- coding: utf-8 -*-

from django.conf.urls import patterns, url
from .views import (
    index_view,
    detail_view,
    add_view,
    change_view,
)

urlpatterns = patterns('',
    url(r'^$', index_view),
    url(r'^(?P<pk>\d+)/$', detail_view),
    url(r'^ajouter/$', add_view),
    url(r'^(?P<pk>\d+)/modifier/$', change_view),
)
