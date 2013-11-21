# -*- coding: utf-8 -*-
import floppyforms as forms
from ionyweb.forms import ModuloModelForm
from .models import Plugin_Zoomsur


class Plugin_ZoomsurForm(ModuloModelForm):

    class Meta:
        model = Plugin_Zoomsur