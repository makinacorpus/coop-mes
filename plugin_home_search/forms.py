# -*- coding: utf-8 -*-
import floppyforms as forms
from ionyweb.forms import ModuloModelForm
from .models import Plugin_HomeSearch


class Plugin_HomeSearchForm(ModuloModelForm):

    class Meta:
        model = Plugin_HomeSearch