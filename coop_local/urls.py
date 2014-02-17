# -*- coding:utf-8 -*-
from django.contrib import admin
from django.conf.urls.defaults import patterns, include, url
from page_directory.views import add_target_view
from mce_filebrowser import views

# # https://code.djangoproject.com/ticket/10405#comment:11
# from django.db.models.loading import cache as model_cache
# if not model_cache.loaded:
#     model_cache.get_models()

admin.autodiscover()


# Add you own URLs here
urlpatterns = patterns('',
    #('^$', 'django.views.generic.simple.redirect_to', {'url': '/admin', 'permanent': False}),
    url(r'^ajouter_organisation/$', add_target_view, name='add_target'),
    #url(r'^tinymce/', include('tinymce.urls')),
    #url(r'^mce_filebrowser/', include('mce_filebrowser.urls')),
    # .__closure__[0].cell_contents -> strips @staff_member_required decorator
    url(r'^mce_filebrowser/image/$', 
        views.filebrowser.__closure__[0].cell_contents, 
        {'file_type': 'img'},
        name='mce-filebrowser-images'
    ),
    url(r'^mce_filebrowser/file/$', 
        views.filebrowser.__closure__[0].cell_contents, 
        {'file_type': 'doc'},
        name='mce-filebrowser-documents'
    ),
    url(r'^mce_filebrowser/image/remove/(?P<item_id>\d+)/$', 
        views.filebrowser_remove_file.__closure__[0].cell_contents, 
        {'file_type': 'img'},
        name='mce-filebrowser-remove-image'
    ),
    url(r'^mce_filebrowser/file/remove/(?P<item_id>\d+)/$', 
        views.filebrowser_remove_file.__closure__[0].cell_contents, 
        {'file_type': 'doc'},
        name='mce-filebrowser-remove-document'
    ),
    url('^iframe/(?P<pk>\d+)/$', 'iframe.views.iframe', name='iframe'),
    url('^iframe_carto/(?P<pk>\d+)/$', 'iframe.views.iframe_carto', name='iframe_carto'),
    url('^iframe/(?P<pk>\d+)/(?P<org_pk>\d+)/$', 'iframe.views.detail'),
    url('^subsectors/(?P<pk>\d+)/$', 'page_directory.views.subsectors_view', name='subsectors'),
)


from coop.default_project_urls import urlpatterns as default_project_urls
urlpatterns += default_project_urls

