# -*- coding: utf-8 -*-

import floppyforms as forms
from ionyweb.forms import ModuloModelForm
from .models import PageApp_PasrAgenda
from coop_local.models import (ActivityNomenclature, Area, TransverseTheme,
    Organization, Occurrence, Location)
from selectable.base import ModelLookup
from selectable.registry import registry, LookupAlreadyRegistered
from selectable.forms import AutoCompleteSelectField
from crispy_forms.helper import FormHelper
from crispy_forms.layout import Layout, HTML, Field
from tinymce.widgets import TinyMCE
from django.conf import settings
from coop_local.models import Event
from django.forms.models import inlineformset_factory
from coop_local.widgets import SplitDateTimeWidget
from page_directory.forms import geocode


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
    date = forms.DateField()
    interval = forms.ChoiceField(choices=((9999, '---'), (1, 'Le jour même'), (3, 'Dans les 3 jours'), (7, 'Dans la semaine'), (31, 'Dans le mois')))
    sector = forms.ModelChoiceField(queryset=ActivityNomenclature.objects.filter(level=0), empty_label=u'Tous', required=False)
    area = AutoCompleteSelectField(lookup_class=AreaLookup, required=False)
    radius = forms.IntegerField(required=False)
    q = forms.CharField(required=False, widget=forms.TextInput(attrs={'class':'form-control', 'placeholder': 'Recherche libre : mot clés'}))
    organization = forms.ModelChoiceField(queryset=Organization.objects.filter(status='V'), required=False, empty_label=u'Tous')

    def __init__(self, *args, **kwargs):
        super(EventSearch, self).__init__(*args, **kwargs)
        for name, field in self.fields.iteritems():
            field.widget.attrs['class'] = 'form-control'
        self.fields['area'].widget.attrs['placeholder'] = u'Tout voir'
        self.fields['area'].widget.attrs['class'] = u'form-control form-control-small'
        self.fields['radius'].widget.attrs['placeholder'] = u'Dans un rayon de'
        self.fields['radius'].widget.attrs['class'] = u'form-control form-control-small'


class FrontEventForm(forms.ModelForm):

    description = forms.CharField(widget=TinyMCE(mce_attrs=settings.TINYMCE_FRONTEND_CONFIG), label=u'Description')

    class Meta:
        model = Event
        fields = (
            'title',
            'brief_description',
            'description',
            'activity',
            'theme',
            'tags',
            'image',
        )

    def __init__(self, *args, **kwargs):
        super(FrontEventForm, self).__init__(*args, **kwargs)
        self.fields['tags'].help_text = u'Entrez des mots-clés séparés par une virgule.'
        self.fields['activity'].help_text = u''
        self.fields['theme'].help_text = u''
        self.helper = FormHelper()
        self.helper.form_tag = False
        self.helper.layout = Layout(
            'title',
            'brief_description',
            'description',
            'activity',
            'theme',
            'tags',
            'image',
        )


class OccurrenceForm(forms.ModelForm):

    class Meta:
        model = Occurrence
        fields = ('start_time', 'end_time')

    def __init__(self, *args, **kwargs):
        super(OccurrenceForm, self).__init__(*args, **kwargs)
        self.fields['start_time'].widget = SplitDateTimeWidget(time_format='%H:%M')
        self.fields['end_time'].widget = SplitDateTimeWidget(time_format='%H:%M')
        self.fields['start_time'].label = u'Début'
        self.fields['end_time'].label = u'Fin'
        self.fields['end_time'].help_text = u'Date au format jj/mm/aaaa. Heure au format hh:mm.'
        self.helper = FormHelper()
        self.helper.form_tag = False
        self.helper.layout = Layout(
            HTML('<fieldset class="formset-form occurence-form">'),
            'start_time',
            'end_time',
            Field('DELETE', template="bootstrap3/layout/delete.html"),
            HTML('</fieldset>'),
        )

    def clean_end_time(self):
        start_time = self.cleaned_data.get('start_time')
        end_time = self.cleaned_data.get('end_time')
        if start_time and end_time and end_time < start_time:
            raise forms.ValidationError('La fin est avant le début.')
        return end_time


OccurrencesForm = inlineformset_factory(Event, Occurrence, form=OccurrenceForm, extra=2)


class LocationForm(forms.ModelForm):

    class Meta:
        model = Location
        fields = ('adr1', 'adr2', 'zipcode', 'city')

    def __init__(self, *args, **kwargs):
        super(LocationForm, self).__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_tag = False
        self.layout = Layout(
            'adr1', 'adr2', 'zipcode', 'city'
        )

    def save(self, commit=True):
        location = super(LocationForm, self).save(commit=False)
        geocode(location)
        if commit:
            location.save()
        return location
