# -*- coding: utf-8 -*-

import floppyforms as forms
from ionyweb.forms import ModuloModelForm
from .models import PageApp_Map
from coop_local.models import ActivityNomenclature, AgreementIAE, Area

class PageApp_MapForm(ModuloModelForm):

    class Meta:
        model = PageApp_Map


ORG_TYPE_CHOICES = (
    ('', u'Tout voir'),
    ('fournisseur', u'Fournisseurs'),
    ('acheteur-prive', u'Acheteurs privés'),
    ('acheteur-public', 'Acheteurs publics'),
)

INTERIM_CHOICES = (
    ('1', u'Mise à disposition de personnel Travail temporaire'),
    ('2', u'Production de  bien et de service'),
)

class AreaModelChoiceField(forms.ModelChoiceField):
    def label_from_instance(self, obj):
        return "%s - %s" % (obj.reference, unicode(obj))

class OrgSearch(forms.Form):
    areas = Area.objects.filter(area_type_id=2).order_by('reference')
    org_type = forms.ChoiceField(choices=ORG_TYPE_CHOICES, required=False)
    prov_type = forms.ModelChoiceField(queryset=AgreementIAE.objects.all(), empty_label=u'Tout voir', required=False)
    interim = forms.ChoiceField(choices=INTERIM_CHOICES, widget=forms.RadioSelect)
    sector = forms.ModelChoiceField(queryset=ActivityNomenclature.objects.filter(level=0), empty_label=u'Tout voir', required=False)
    area  = AreaModelChoiceField(queryset=areas, empty_label=u'Tout voir', required=False)
    q = forms.CharField(required=False)
