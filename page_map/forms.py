# -*- coding: utf-8 -*-

from ionyweb.forms import ModuloModelForm
from .models import PageApp_Map


class PageApp_MapForm(ModuloModelForm):

    class Meta:
        model = PageApp_Map
