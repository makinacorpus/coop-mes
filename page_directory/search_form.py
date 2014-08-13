# -*- coding: utf-8 -*-

from django import forms
from coop_local.models import (ActivityNomenclature, AgreementIAE, Area,
    Guaranty)
from selectable.base import ModelLookup
from selectable.registry import registry, LookupAlreadyRegistered
from selectable.forms import AutoCompleteSelectField


ORG_TYPE_CHOICES = (
    ('', u'Tout voir'),
    ('fournisseur', u'Fournisseurs'),
    ('acheteur-prive', u'Acheteurs privés'),
    ('acheteur-public', 'Acheteurs publics'),
)


GEO_CHOICES = (
    (1, u'Implantation'),
    (2, u'Intervention'),
)


class AreaLookup(ModelLookup):
    model = Area
    def get_query(self, request, term):
        qs = self.get_queryset().filter(polygon__isnull=False)
        if term:
            for bit in term.split():
                qs = qs.filter(label__icontains=bit)
        return qs

try:
    registry.register(AreaLookup)
except LookupAlreadyRegistered:
    pass


class SubsectorField(forms.ModelChoiceField):
   def label_from_instance(self, obj):
        return obj.label


class OrgSearch(forms.Form):
    org_type = forms.ChoiceField(choices=ORG_TYPE_CHOICES, required=False)
    prov_type = forms.ModelChoiceField(queryset=AgreementIAE.objects.all(), empty_label=u'Tout voir', required=False)
    interim = forms.BooleanField(required=False)
    geo = forms.ChoiceField(choices=GEO_CHOICES, widget=forms.widgets.RadioSelect, required=False)
    sector = forms.ModelChoiceField(queryset=ActivityNomenclature.objects.filter(level=0).order_by('label'), empty_label=u'Tout voir', required=False)
    subsector = SubsectorField(queryset=ActivityNomenclature.objects.none(), empty_label=u'Tout voir', required=False)
    area = AutoCompleteSelectField(lookup_class=AreaLookup, required=False)
    radius = forms.IntegerField(required=False)
    q = forms.CharField(required=False, widget=forms.TextInput(attrs={'class':'form-control', 'placeholder': 'Recherche libre : mot clés'}))
    guaranty = forms.ModelChoiceField(queryset=Guaranty.objects.all(), empty_label=u'Tout voir', required=False)

    def __init__(self, data, *args, **kwargs):
        super(OrgSearch, self).__init__(data, *args, **kwargs)
        for name, field in self.fields.iteritems():
            if name == 'interim':
                continue
            field.widget.attrs['class'] = 'form-control'
        self.fields['area'].widget.attrs['placeholder'] = u'Tout voir'
        self.fields['radius'].widget.attrs['placeholder'] = u'Dans un rayon de'
        sector_pk = data.get('sector')
        if sector_pk and sector_pk.isdigit():
            try:
                sector = ActivityNomenclature.objects.get(pk=sector_pk)
            except ActivityNomenclature.DoesNotExist:
                sector = None
            if sector:
                self.fields['subsector'].queryset = sector.get_children()
