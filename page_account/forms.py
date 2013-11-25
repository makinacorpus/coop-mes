# -*- coding: utf-8 -*-

import floppyforms as forms
from ionyweb.forms import ModuloModelForm
from models import PageApp_Account
from ionyweb.widgets import TinyMCELargeTable
from crispy_forms.helper import FormHelper
from crispy_forms.layout import Layout

from django.contrib.auth.forms import AuthenticationForm as BaseAuthenticationForm
from coop_local.models import Organization


class PageApp_AccountForm(ModuloModelForm):

    class Meta:
        model = PageApp_Account


class AuthenticationForm(BaseAuthenticationForm):

    def __init__(self, *args, **kwargs):
        super(AuthenticationForm, self).__init__(*args, **kwargs)
        for field in self.fields.itervalues():
            field.widget.attrs['class'] = 'form-control'


class PreferencesForm(forms.ModelForm):

    class Meta:
        model = Organization
        fields = (
            'newsletter_subscription',
            'calls_subscription',
            'events_subscription',
            'exchanges_subscription',
        )

    def __init__(self, *args, **kwargs):
        super(PreferencesForm, self).__init__(*args, **kwargs)
        self.fields['newsletter_subscription'].label = u'Newsletter'
        self.fields['newsletter_subscription'].help_text = u'Recevoir la newsletter'
        self.fields['calls_subscription'].label = 'Appels d\'offres'
        self.fields['calls_subscription'].help_text = u'Etre informé des appels d’offres correspondant aux secteurs d’activité de mes offres'
        if not self.instance.is_provider:
            del self.fields['calls_subscription']
        self.fields['events_subscription'].empty_label = 'Aucun'
        self.fields['events_subscription'].label = 'Événements de mon/ma'
        self.fields['events_subscription'].help_text = u'Etre informé des évènements se déroulant à ce niveau'
        self.fields['exchanges_subscription'].label = u'Échanges'
        self.fields['exchanges_subscription'].help_text = u'Recevoir des propositions ou des demandes correspondant à votre secteur'
        self.helper = FormHelper()
        self.helper.form_tag = False
        self.helper.layout = Layout(*self.fields.keys())
