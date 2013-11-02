# -*- coding: utf-8 -*-

import floppyforms as forms
from ionyweb.forms import ModuloModelForm
from .models import PageApp_Newsletter
from coop_local.models import NewsletterSubscription
from crispy_forms.helper import FormHelper
from crispy_forms.layout import Layout, Fieldset, HTML, Field
from crispy_forms.bootstrap import InlineCheckboxes, FormActions, StrictButton, AppendedText

class PageApp_NewsletterForm(ModuloModelForm):

    class Meta:
        model = PageApp_Newsletter


class SubscriptionForm(forms.ModelForm):

    class Meta:
        model = NewsletterSubscription
        fields = (
            'name',
            'email',
            'structure',
        )

    def __init__(self, *args, **kwargs):
        super(SubscriptionForm, self).__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_tag = False
        self.helper.layout = Layout(
            'name',
            'email',
            'structure',
        )
