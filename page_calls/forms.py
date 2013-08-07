# -*- coding: utf-8 -*-

import floppyforms as forms
from ionyweb.forms import ModuloModelForm
from .models import PageApp_Calls
from coop_local.models import CallForTenders, ActivityNomenclature, Organization
from coop_local.models.local_models import CLAUSE_CHOICES, ORGANIZATION_STATUSES
from django.conf import settings


ORG_TYPE_CHOICES = (
    ('tout', u'Public ou privé'),
    ('prive', u'Privé'),
    ('public', u'Public'),
)

PERIOD2_CHOICES = (
    ('current', u'En cours'),
    ('archive', u'Archivé'),
    ('tout', u'Tout voir'),
)

PERIOD_CHOICES = (
    ('', u'Tout voir'),
    ('15', u'15 jours'),
    ('30', u'1 mois'),
    ('90', u'3 mois'),
    ('365', u'1 an'),
)

class CallSearch(forms.Form):
    org_type = forms.ChoiceField(choices=ORG_TYPE_CHOICES, required=False)
    clause = forms.ChoiceField(choices=(('', u'Tout voir'), ) + CLAUSE_CHOICES, required=False)
    organization = forms.ModelChoiceField(queryset=Organization.objects.filter(status=ORGANIZATION_STATUSES.VALIDATED), required=False, empty_label=u'Toutes')
    sector = forms.ModelChoiceField(queryset=ActivityNomenclature.objects.filter(level=0), empty_label=u'Tout voir', required=False)
    period = forms.ChoiceField(choices=PERIOD_CHOICES, required=False)
    period2 = forms.ChoiceField(choices=PERIOD2_CHOICES, required=False)

    def __init__(self, *args, **kwargs):
        super(CallSearch, self).__init__(*args, **kwargs)
        for field in self.fields.itervalues():
            field.widget.attrs['class'] = 'form-control'
