# -*- coding: utf-8 -*-
import floppyforms as forms
from ionyweb.forms import ModuloModelForm
from .models import Plugin_Search
from coop_local.models import ActivityNomenclature, AgreementIAE


class Plugin_SearchForm(ModuloModelForm):

    class Meta:
        model = Plugin_Search


ORG_TYPE_CHOICES = (
    ('', u'Tout voir'),
    ('fournisseur', u'Fournisseurs'),
    ('acheteur-prive', u'Acheteurs privés'),
    ('acheteur-public', 'Acheteurs publics'),
)

class OrgSearch(forms.Form):
    org_type = forms.ChoiceField(choices=ORG_TYPE_CHOICES, required=False)
    prov_type = forms.ModelChoiceField(queryset=AgreementIAE.objects.all(), empty_label=u'Tout voir', required=False)
    sector = forms.ModelChoiceField(queryset=ActivityNomenclature.objects.filter(level=0), empty_label=u'Tout voir', required=False)
    area  = forms.ChoiceField(choices=(('', u'Tout voir'),), required=False)
    q = forms.CharField(required=False)
