# -*- coding: utf-8 -*-
import floppyforms as forms
from ionyweb.forms import ModuloModelForm
from .models import Plugin_HomeSearch
from coop_local.models import ActivityNomenclature, Area
from django.conf import settings


class Plugin_HomeSearchForm(ModuloModelForm):

    class Meta:
        model = Plugin_HomeSearch


ORG_TYPE_CHOICES = (
    ('', u'Acheteur/Fournisseur'),
    ('fournisseur', u'Fournisseurs'),
    ('acheteur-prive', u'Acheteurs privés'),
    ('acheteur-public', 'Acheteurs publics'),
)

class AreaModelChoiceField(forms.ModelChoiceField):
    def label_from_instance(self, obj):
        return "%s - %s" % (obj.reference, unicode(obj))

class OrgSearch(forms.Form):
    areas = Area.objects.filter(parent_rels__parent__label=settings.REGION_LABEL).order_by('reference')
    org_type = forms.ChoiceField(choices=ORG_TYPE_CHOICES, required=False)
    sector = forms.ModelChoiceField(queryset=ActivityNomenclature.objects.filter(level=0), empty_label=u'Secteur d\'activité', required=False)
    area  = AreaModelChoiceField(queryset=areas, empty_label=u'Territoire', required=False)
