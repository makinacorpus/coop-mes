# -*- coding: utf-8 -*-
import floppyforms as forms
from ionyweb.forms import ModuloModelForm
from .models import Plugin_Subpages


class Plugin_SubpagesForm(ModuloModelForm):

    class Meta:
        model = Plugin_Subpages