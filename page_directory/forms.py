# -*- coding: utf-8 -*-

import floppyforms as forms
from ionyweb.forms import ModuloModelForm
from .models import PageApp_Directory
from coop_local.models import (ActivityNomenclature, AgreementIAE, Area,
    Organization, Engagement)
from django.conf import settings
from tinymce.widgets import TinyMCE
from chosen import widgets as chosenwidgets


class PageApp_DirectoryForm(ModuloModelForm):

    class Meta:
        model = PageApp_Directory


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
    areas = Area.objects.filter(parent_rels__parent__label=settings.REGION_LABEL).order_by('reference')
    org_type = forms.ChoiceField(choices=ORG_TYPE_CHOICES, required=False)
    prov_type = forms.ModelChoiceField(queryset=AgreementIAE.objects.all(), empty_label=u'Tout voir', required=False)
    interim = forms.ChoiceField(choices=INTERIM_CHOICES, widget=forms.RadioSelect)
    sector = forms.ModelChoiceField(queryset=ActivityNomenclature.objects.filter(level=0), empty_label=u'Tout voir', required=False)
    area  = AreaModelChoiceField(queryset=areas, empty_label=u'Tout voir', required=False)
    q = forms.CharField(required=False, widget=forms.TextInput(attrs={'class':'form-control', 'placeholder': 'ex : restauration'}))

    def __init__(self, *args, **kwargs):
        super(OrgSearch, self).__init__(*args, **kwargs)
        for field in self.fields.itervalues():
            field.widget.attrs['class'] = 'form-control'


class OrganizationForm1(forms.ModelForm):

    class Meta:
        model = Organization
        fields = ('title', 'acronym', 'pref_label', 'logo', 'birth',
                  'legal_status', 'web', 'siret', 'is_provider',
                  'is_customer', 'customer_type')

    def __init__(self, *args, **kwargs):
        super(OrganizationForm1, self).__init__(*args, **kwargs)
        for field in self.fields.itervalues():
            field.widget.attrs['class'] = 'form-control'

    def clean(self):
        cleaned_data = super(OrganizationForm1, self).clean()
        if not cleaned_data['is_provider'] and not cleaned_data['is_customer']:
            raise forms.ValidationError(u'Veuillez cocher une des cases Fournisseur ou Acheteur.')
        if cleaned_data['is_customer'] and not cleaned_data['customer_type']:
            raise forms.ValidationError(u'Veuillez sélectionner un type d\'Acheteur.')

        # Always return the full collection of cleaned data.
        return cleaned_data


class OrganizationForm2(forms.ModelForm):

    description = forms.CharField(widget=TinyMCE(mce_attrs=settings.TINYMCE_FRONTEND_CONFIG), required=False)

    class Meta:
        model = Organization
        fields = ('brief_description', 'description', 'added_value')

    def __init__(self, *args, **kwargs):
        super(OrganizationForm2, self).__init__(*args, **kwargs)
        for field in self.fields.itervalues():
            field.widget.attrs['class'] = 'form-control'


class OrganizationForm3(forms.ModelForm):

    class Meta:
        model = Organization
        fields = ('tags', 'activities', 'transverse_themes')
        widgets = {
            'activities': chosenwidgets.ChosenSelectMultiple(),
            'transverse_themes': forms.CheckboxSelectMultiple(),
        }

    def __init__(self, *args, **kwargs):
        super(OrganizationForm3, self).__init__(*args, **kwargs)
        for field in self.fields.itervalues():
            field.widget.attrs['class'] = 'form-control'
