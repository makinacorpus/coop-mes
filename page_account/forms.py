# -*- coding: utf-8 -*-

from django.contrib.auth.models import User
from django.contrib.auth.forms import UserCreationForm
from django import forms
from coop_local.models import Person


class PersonForm(forms.ModelForm):

    charte = forms.TypedChoiceField(coerce=lambda x: bool(int(x)),
                                    choices=((0, u'Non'), (1, u'Oui')),
                                    widget=forms.RadioSelect,
                                    initial=0)

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
