# -*- coding: utf-8 -*-

import floppyforms as forms
from ionyweb.forms import ModuloModelForm
from .models import PageApp_PasrAgenda
from coop_local.models import ActivityNomenclature, Area
from selectable.base import ModelLookup
from selectable.registry import registry, LookupAlreadyRegistered
from selectable.forms import AutoCompleteSelectField

class PageApp_PasrAgendaForm(ModuloModelForm):

    class Meta:
        model = PageApp_PasrAgenda


class AreaLookup(ModelLookup):
    model = Area
    def get_query(self, request, term):
        qs = self.get_queryset()
        if term:
            for bit in term.split():
                qs = qs.filter(label__icontains=bit)
        return qs

try:
    registry.register(AreaLookup)
except LookupAlreadyRegistered:
    pass


class EventSearch(forms.Form):
    sector = forms.ModelChoiceField(queryset=ActivityNomenclature.objects.filter(level=0), empty_label=u'Tout voir', required=False)
    area = AutoCompleteSelectField(lookup_class=AreaLookup, required=False)
    radius = forms.IntegerField(required=False)
    q = forms.CharField(required=False, widget=forms.TextInput(attrs={'class':'form-control', 'placeholder': 'Recherche libre : mot clés'}))

    def __init__(self, *args, **kwargs):
        super(EventSearch, self).__init__(*args, **kwargs)
        for name, field in self.fields.iteritems():
            field.widget.attrs['class'] = 'form-control'
        self.fields['area'].widget.attrs['placeholder'] = u'Tout voir'
        self.fields['area'].widget.attrs['class'] = u'form-control form-control-small'
        self.fields['radius'].widget.attrs['placeholder'] = u'Dans un rayon de'
        self.fields['radius'].widget.attrs['class'] = u'form-control form-control-small'
