# -*- coding: utf-8 -*-

from django import forms
from ionyweb.forms import ModuloModelForm
from .models import PageApp_Directory
from coop_local.models import (ActivityNomenclature, AgreementIAE, Area,
    Organization, Engagement, Role)
from coop_local.models.local_models import normalize_text
from django.conf import settings
from tinymce.widgets import TinyMCE
from chosen import widgets as chosenwidgets
from django.contrib.auth.forms import UserCreationForm, UserChangeForm
from coop_local.models import Person
from django.utils.translation import ugettext, ugettext_lazy as _
from crispy_forms.helper import FormHelper
from crispy_forms.layout import Layout, Fieldset, HTML, Field
from crispy_forms.bootstrap import InlineRadios, FormActions, StrictButton


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
        for name, field in self.fields.iteritems():
            if name == 'interim':
                continue
            field.widget.attrs['class'] = 'form-control'


class OrganizationMixin(object):

    def set_helper(self, step, fields):
        self.helper = FormHelper()
        self.helper.form_tag = False
        self.helper.layout = Layout(Fieldset(''))
        self.helper.layout[0].extend(fields)
        self.helper.layout[0].append(HTML('<hr>'))
        if step == '0':
            self.helper.layout[0].append(FormActions(
                StrictButton(u'Étape suivante', type='submit', css_class='btn-default'),
            ))
        else:
            prev = str(int(step) - 1)
            self.helper.layout[0].append(FormActions(
                    StrictButton(u'Étape précédente', type='submit', name='wizard_goto_step', value=prev, css_class='btn--form'),
                    StrictButton(u'Étape suivante', type='submit', css_class='btn-default'),
            ))


class OrganizationForm0(OrganizationMixin, UserCreationForm):

    charte = forms.TypedChoiceField(coerce=lambda x: bool(int(x)),
        choices=((0, u'Non'), (1, u'Oui')), widget=forms.RadioSelect,
        initial=0, required=False, label=u'J\'accepte la <a \
        data-toggle="modal" href="#charte">charte de l\'utilisateur</a>')

    def __init__(self, step, *args, **kwargs):
        super(OrganizationForm0, self).__init__(*args, **kwargs)
        self.set_helper(step, (
            'username',
            'password1',
            'password2',
            HTML('<hr>'),
            InlineRadios('charte', css_class="large-label")))

    def clean_charte(self):
        if not self.cleaned_data['charte']:
            raise forms.ValidationError(u'Vous devez accepter la charte pour pouvoir vous inscrire.')
        return True


class OrganizationForm1(OrganizationMixin, forms.ModelForm):

    gender = forms.ChoiceField(choices=(('M', u'M.'), ('W', u'Mme')),
        widget=forms.RadioSelect, required=False, label='Genre')
    tel = forms.CharField(required=False, label=u'Téléphone')
    role = forms.ModelChoiceField(queryset=Role.objects, required=False, label=u'Rôle')

    def __init__(self, step, *args, **kwargs):
        super(OrganizationForm1, self).__init__(*args, **kwargs)
        self.set_helper(step, (
            InlineRadios('gender'),
            'last_name',
            'first_name',
            'email',
            'tel',
            'role'))

    class Meta:
        model = Person
        fields = ('gender', 'first_name', 'last_name', 'email')


class OrganizationForm2(OrganizationMixin, forms.ModelForm):

    class Meta:
        model = Organization
        fields = ('title', 'acronym', 'pref_label', 'logo', 'birth',
                  'legal_status', 'web', 'siret', 'is_provider',
                  'is_customer', 'customer_type')

    def __init__(self, step, *args, **kwargs):
        super(OrganizationForm2, self).__init__(*args, **kwargs)
        self.set_helper(step, (
            'title', 'acronym', 'pref_label', 'logo', 'birth',
            'legal_status', 'web', 'siret', 'is_provider',
            'is_customer', 'customer_type'))

    def clean_title(self):
        title = self.cleaned_data['title']
        if Organization.objects.exclude(pk=self.instance.pk).filter(norm_title=normalize_text(title)).exists():
            raise forms.ValidationError(u'Un Fournisseur ou Acheteur avec ce nom existe déjà.')
        return title

    def clean(self):
        cleaned_data = super(OrganizationForm2, self).clean()
        if not cleaned_data['is_provider'] and not cleaned_data['is_customer']:
            raise forms.ValidationError(u'Veuillez cocher une des cases Fournisseur ou Acheteur.')
        if cleaned_data['is_customer'] and not cleaned_data['customer_type']:
            raise forms.ValidationError(u'Veuillez sélectionner un type d\'Acheteur.')

        # Always return the full collection of cleaned data.
        return cleaned_data


class OrganizationForm3(OrganizationMixin, forms.ModelForm):

    description = forms.CharField(widget=TinyMCE(mce_attrs=settings.TINYMCE_FRONTEND_CONFIG), required=False)

    class Meta:
        model = Organization
        fields = ('brief_description', 'description', 'added_value')

    def __init__(self, step, *args, **kwargs):
        super(OrganizationForm3, self).__init__(*args, **kwargs)
        self.set_helper(step, ('brief_description', 'description', 'added_value',))


class OrganizationForm4(OrganizationMixin, forms.ModelForm):

    class Meta:
        model = Organization
        fields = ('tags', 'activities', 'transverse_themes')
        widgets = {
            'transverse_themes': forms.CheckboxSelectMultiple(),
        }

    def __init__(self, step, *args, **kwargs):
        super(OrganizationForm4, self).__init__(*args, **kwargs)
        self.set_helper(step, ('tags', 'activities', 'transverse_themes'))
