# -*- coding: utf-8 -*-

from django.contrib import admin
from .models import *
from django.contrib.sites.models import Site
from tinymce.widgets import AdminTinyMCE
from django import forms


class IFrameAdminForm(forms.ModelForm):

    top_content = forms.CharField(widget=AdminTinyMCE(attrs={'cols': 80, 'rows': 60}), required=False, label=u"Texte du haut")

    class Meta:
        model = IFrame


class IFrameAdmin(admin.ModelAdmin):
    change_form_template = 'admin/page_iframe/iframe/tabbed_change_form.html'
    list_display = ('id', 'domain', 'title')
    list_display_links = ('domain', )
    form = IFrameAdminForm

    def change_view(self, request, object_id, form_url='', extra_context=None):
        extra_context = extra_context or {}
        extra_context['domain'] = site = Site.objects.get_current().domain
        return super(IFrameAdmin, self).change_view(request, object_id,
            form_url, extra_context=extra_context)


admin.site.register(IFrame, IFrameAdmin)

admin.site.register(PageApp_Iframe)