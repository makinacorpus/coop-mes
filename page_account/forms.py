# -*- coding: utf-8 -*-

from django.contrib.auth.models import User
from django.contrib.auth.forms import UserCreationForm
from django import forms
from coop_local.models import Person
from django.contrib.auth.forms import AuthenticationForm as BaseAuthenticationForm


class PersonForm(forms.ModelForm):

    charte = forms.TypedChoiceField(coerce=lambda x: bool(int(x)),
                                    choices=((0, u'Non'), (1, u'Oui')),
                                    widget=forms.RadioSelect,
                                    initial=0)

    def __init__(self, *args, **kwargs):
        super(PersonForm, self).__init__(*args, **kwargs)
        for field in self.fields.itervalues():
            field.widget.attrs['class'] = 'form-control'

    def clean_charte(self):
        if not self.cleaned_data['charte']:
            raise forms.ValidationError(u'Vous devez accepter la charte pour pouvoir vous inscrire.')
        return True

    class Meta:
        model = Person
        fields = ('gender', 'first_name', 'last_name')


class AccountForm(UserCreationForm):

    class Meta:
        model = User
        fields = ('email', 'username')

    def __init__(self, *args, **kwargs):
        super(AccountForm, self).__init__(*args, **kwargs)
        for field in self.fields.itervalues():
            field.widget.attrs['class'] = 'form-control'


class AuthenticationForm(BaseAuthenticationForm):

    def __init__(self, *args, **kwargs):
        super(AuthenticationForm, self).__init__(*args, **kwargs)
        for field in self.fields.itervalues():
            field.widget.attrs['class'] = 'form-control'
