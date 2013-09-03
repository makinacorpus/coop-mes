# -*- coding: utf-8 -*-

import floppyforms as forms
from ionyweb.forms import ModuloModelForm
from .models import PageApp_Calls
from coop_local.models import CallForTenders, ActivityNomenclature, Organization
from coop_local.models.local_models import CLAUSE_CHOICES, ORGANIZATION_STATUSES
from django.conf import settings
from crispy_forms.helper import FormHelper
from crispy_forms.layout import Layout, Fieldset, HTML, Field
from crispy_forms.bootstrap import InlineCheckboxes, FormActions, StrictButton, AppendedText


ORG_TYPE_CHOICES = (
    ('tout', u'Public ou privé'),
    ('prive', u'Privé'),
    ('public', u'Public'),
)

PERIOD_CHOICES = (
    ('current', u'En cours'),
    ('archive', u'Archivé'),
    ('tout', u'Tout voir'),
)

class CallSearch(forms.Form):
    org_type = forms.ChoiceField(choices=ORG_TYPE_CHOICES, required=False)
    clause = forms.ChoiceField(choices=(('', u'Tout voir'), ) + CLAUSE_CHOICES, required=False)
    organization = forms.ModelChoiceField(queryset=Organization.objects.filter(status=ORGANIZATION_STATUSES.VALIDATED), required=False, empty_label=u'Toutes')
    sector = forms.ModelChoiceField(queryset=ActivityNomenclature.objects.filter(level=0), empty_label=u'Tout voir', required=False)
    period = forms.ChoiceField(choices=PERIOD_CHOICES, required=False)
    q = forms.CharField(required=False)

    def __init__(self, *args, **kwargs):
        super(CallSearch, self).__init__(*args, **kwargs)
        for field in self.fields.itervalues():
            field.widget.attrs['class'] = 'form-control'


class CallForm(forms.ModelForm):

    class Meta:
        model = CallForTenders
        fields = (
            'title',
            'activity',
            'area',
            'allotment',
            'lot_numbers',
            'clauses',
            'deadline',
            'url',
        )

    def __init__(self, *args, **kwargs):
        super(CallForm, self).__init__(*args, **kwargs)
        self.fields['activity'].help_text = u''
        self.helper = FormHelper()
        self.helper.form_tag = False
        self.helper.layout = Layout(
            'title',
            'activity',
            'area',
            'allotment',
            'lot_numbers',
            InlineCheckboxes('clauses'),
            'deadline',
            'url',
        )
