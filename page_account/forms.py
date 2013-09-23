# -*- coding: utf-8 -*-

from django.contrib.auth.forms import AuthenticationForm as BaseAuthenticationForm


class AuthenticationForm(BaseAuthenticationForm):

    def __init__(self, *args, **kwargs):
        super(AuthenticationForm, self).__init__(*args, **kwargs)
        for field in self.fields.itervalues():
            field.widget.attrs['class'] = 'form-control'
