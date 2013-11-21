# -*- coding: utf-8 -*-

import floppyforms as forms
from ionyweb.forms import ModuloModelForm
from models import PageApp_Account
from ionyweb.widgets import TinyMCELargeTable

from django.contrib.auth.forms import AuthenticationForm as BaseAuthenticationForm


class PageApp_AccountForm(ModuloModelForm):

    class Meta:
        model = PageApp_Account


class AuthenticationForm(BaseAuthenticationForm):

    def __init__(self, *args, **kwargs):
        super(AuthenticationForm, self).__init__(*args, **kwargs)
        for field in self.fields.itervalues():
            field.widget.attrs['class'] = 'form-control'
