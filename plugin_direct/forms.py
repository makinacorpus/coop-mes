# -*- coding: utf-8 -*-
import floppyforms as forms
from ionyweb.forms import ModuloModelForm
from .models import Plugin_Direct


class Plugin_DirectForm(ModuloModelForm):

    class Meta:
        model = Plugin_Direct