# -*- coding: utf-8 -*-

from django.conf.urls import patterns, url
from .views import index_view, confirm_view, to_confirm_view

urlpatterns = patterns('',
                       url(r'^$', index_view),
                       url(r'^a-confirmer/$', to_confirm_view),
                       url(r'^confirmer/(?P<pk>\d+)/$', confirm_view),
                       )