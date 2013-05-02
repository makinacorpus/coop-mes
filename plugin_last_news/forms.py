# -*- coding: utf-8 -*-
import floppyforms as forms
from ionyweb.forms import ModuloModelForm
from .models import Plugin_LastNews


class Plugin_LastNewsForm(ModuloModelForm):

    class Meta:
        model = Plugin_LastNews