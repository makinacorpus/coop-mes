# -*- coding: utf-8 -*-

import floppyforms as forms
from ionyweb.forms import ModuloModelForm
from .models import PageApp_Search

class PageApp_SearchForm(ModuloModelForm):

    class Meta:
        model = PageApp_Search