# -*- coding: utf-8 -*-

import floppyforms as forms
from ionyweb.forms import ModuloModelForm
from .models import PageApp_Calls
from coop_local.models import CallForTenders, Area, ActivityNomenclature 
from django.conf import settings


ORG_TYPE_CHOICES = (
    ('prive', u'Privé'),
    ('public', u'Public'),
)

PERIOD_CHOICES = (
    ('current', u'En cours'),
    ('archive', u'Archivé'),
)

class AreaModelChoiceField(forms.ModelChoiceField):
    def label_from_instance(self, obj):
        return "%s - %s" % (obj.reference, unicode(obj))

class CallSearch(forms.Form):
    areas = Area.objects.filter(reference__in=settings.SEARCH_DEPARTEMENTS).order_by('reference')
    org_type = forms.ChoiceField(choices=ORG_TYPE_CHOICES, widget=forms.RadioSelect, required=False)
    sector = forms.ModelChoiceField(queryset=ActivityNomenclature.objects.filter(level=0), empty_label=u'Tout voir', required=False)
    area  = AreaModelChoiceField(queryset=areas, empty_label=u'Tout voir', required=False)
