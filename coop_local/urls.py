# -*- coding:utf-8 -*-
from django.contrib import admin
from django.conf.urls.defaults import patterns, include, url
from page_directory.views import add_target_view

# # https://code.djangoproject.com/ticket/10405#comment:11
# from django.db.models.loading import cache as model_cache
# if not model_cache.loaded:
#     model_cache.get_models()

admin.autodiscover()


# Add you own URLs here
urlpatterns = patterns('',
    ('^$', 'django.views.generic.simple.redirect_to', {'url': '/admin', 'permanent': False}),
    url(r'^ajouter_acheteur/$', add_target_view, name='add_target'),
)


from coop.default_project_urls import urlpatterns as default_project_urls
urlpatterns += default_project_urls

