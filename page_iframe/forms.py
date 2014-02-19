# -*- coding: utf-8 -*-

import floppyforms as forms
from ionyweb.forms import ModuloModelForm
from .models import PageApp_Iframe
from tinymce.widgets import TinyMCE
from django.conf import settings

class PageApp_IframeForm(ModuloModelForm):

    right_content = forms.CharField(widget=TinyMCE(mce_attrs=settings.TINYMCE_IONYWEB_CONFIG), label=u'Colonne de droite')

    class Meta:
        model = PageApp_Iframe