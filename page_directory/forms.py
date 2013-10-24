# -*- coding: utf-8 -*-

from django import forms
from ionyweb.forms import ModuloModelForm
from .models import PageApp_Directory
from coop_local.models import (ActivityNomenclature, AgreementIAE, Area,
    Organization, Engagement, Role, Document, Relation, Located, Location,
    Contact, Person, Offer, Reference, OrgRelationType, ContactMedium)
from coop_local.models.local_models import normalize_text
from django.conf import settings
from tinymce.widgets import TinyMCE
from chosen import widgets as chosenwidgets
from django.contrib.auth.models import User
from django.utils.translation import ugettext, ugettext_lazy as _
from crispy_forms.helper import FormHelper
from crispy_forms.layout import Layout, Fieldset, HTML, Field
from crispy_forms.bootstrap import (InlineRadios, InlineCheckboxes,
    FormActions, StrictButton, AppendedText)
from selectable.base import ModelLookup
from selectable.registry import registry, LookupAlreadyRegistered
from selectable.forms import AutoCompleteSelectField
from django.db.models import Q
from django.contrib.contenttypes.generic import (
    generic_inlineformset_factory, BaseGenericInlineFormSet)
from django.contrib.contenttypes.models import ContentType
from django.contrib.auth import login, authenticate
import urllib, urllib2, json
from django.db import transaction


GMAP_URL = "http://maps.googleapis.com/maps/api/geocode/json?address=%s"\
           "&sensor=false"


class PageApp_DirectoryForm(ModuloModelForm):

    class Meta:
        model = PageApp_Directory


ORG_TYPE_CHOICES = (
    ('', u'Tout voir'),
    ('fournisseur', u'Fournisseurs'),
    ('acheteur-prive', u'Acheteurs privés'),
    ('acheteur-public', 'Acheteurs publics'),
)


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


class OrgSearch(forms.Form):
    org_type = forms.ChoiceField(choices=ORG_TYPE_CHOICES, required=False)
    prov_type = forms.ModelChoiceField(queryset=AgreementIAE.objects.all(), empty_label=u'Tout voir', required=False)
    interim = forms.BooleanField(required=False)
    sector = forms.ModelChoiceField(queryset=ActivityNomenclature.objects.filter(level=0), empty_label=u'Tout voir', required=False)
    area = AutoCompleteSelectField(lookup_class=AreaLookup, required=False)
    radius = forms.IntegerField(required=False)
    q = forms.CharField(required=False, widget=forms.TextInput(attrs={'class':'form-control', 'placeholder': 'Recherche libre : mot clés'}))

    def __init__(self, *args, **kwargs):
        super(OrgSearch, self).__init__(*args, **kwargs)
        for name, field in self.fields.iteritems():
            if name == 'interim':
                continue
            field.widget.attrs['class'] = 'form-control'
        self.fields['area'].widget.attrs['placeholder'] = u'Tout voir'
        self.fields['area'].widget.attrs['class'] = u'form-control form-control-small'
        self.fields['radius'].widget.attrs['placeholder'] = u'Dans un rayon de'
        self.fields['radius'].widget.attrs['class'] = u'form-control form-control-small'


class OrganizationMixin(object):

    def set_helper(self, fields):
        self.helper = FormHelper()
        self.helper.form_tag = False
        self.helper.layout = Layout()
        self.helper.layout.extend(fields)


class OrganizationForm1(OrganizationMixin, forms.ModelForm):

    error_messages = {
        'duplicate_username': _("A user with that username already exists."),
        'password_mismatch': _("The two password fields didn't match."),
    }
    username = forms.RegexField(label=_("Username"), max_length=30,
        regex=r'^[\w.@+-]+$',
        help_text = _("Required. 30 characters or fewer. Letters, digits and "
                      "@/./+/-/_ only."),
        error_messages = {
            'invalid': _("This value may contain only letters, numbers and "
                         "@/./+/-/_ characters.")})
    password1 = forms.CharField(label=_("Password"),
        widget=forms.PasswordInput)
    password2 = forms.CharField(label=_("Password confirmation"),
        widget=forms.PasswordInput,
        help_text = _("Enter the same password as above, for verification."))
    gender = forms.ChoiceField(choices=(('M', u'M.'), ('W', u'Mme')),
        widget=forms.RadioSelect, required=False, label='Genre')
    charte = forms.TypedChoiceField(coerce=lambda x: bool(int(x)),
        choices=((0, u'Non'), (1, u'Oui')), widget=forms.RadioSelect,
        initial=0, required=False, label=u'J\'accepte la <a \
        data-toggle="modal" href="#charte">charte de l\'utilisateur</a>')
    last_name = forms.CharField(label=_(u'last name').capitalize(), max_length=100)
    first_name = forms.CharField(label=_(u'first name').capitalize(), max_length=100, required=False)
    email = forms.CharField(label='Email')

    class Meta:
        model = Organization
        fields = ('title', 'is_provider', 'is_customer')

    def __init__(self, request, propose, *args, **kwargs):
        self.request = request
        super(OrganizationForm1, self).__init__(*args, **kwargs)
        if self.instance.pk:
            self.person = request.user.get_profile()
        else:
            self.person = Person()
        self.fields['last_name'].required = True
        self.fields['gender'].initial = self.person.gender
        self.fields['first_name'].initial = self.person.user and self.person.user.first_name
        self.fields['last_name'].initial = self.person.user and self.person.user.last_name
        self.fields['email'].initial = self.person.user and self.person.user.email
        self.fields['is_provider'].label += '*'
        self.fields['is_customer'].label += '*'
        self.fields['charte'].label += '*'
        if self.instance.pk:
            del self.fields['username']
            del self.fields['password1']
            del self.fields['password2']
            del self.fields['charte']
            self.set_helper((
                HTML('<p>Vous</p>'),
                InlineRadios('gender'),
                'first_name',
                'last_name',
                'email',
                HTML('<hr>'),
                HTML('<p>Votre organisation</p>'),
                'title',
                'is_provider',
                'is_customer'))
        else:
            self.fields['username'].initial = self.person.user and self.person.user.username
            self.set_helper((
                HTML('<p>Vous</p>'),
                InlineRadios('gender'),
                'first_name',
                'last_name',
                'email',
                'username',
                'password1',
                'password2',
                HTML('<hr>'),
                HTML('<p>Votre organisation</p>'),
                'title',
                'is_provider',
                'is_customer',
                HTML('<hr>'),
                InlineRadios('charte', css_class="large-label")))

    def clean_title(self):
        title = self.cleaned_data['title']
        if Organization.objects.exclude(pk=self.instance.pk).filter(norm_title=normalize_text(title)).exists():
            raise forms.ValidationError(u'Un Fournisseur ou Acheteur avec ce nom existe déjà.')
        return title

    def clean_username(self):
        # Since User.username is unique, this check is redundant,
        # but it sets a nicer error message than the ORM. See #13147.
        username = self.cleaned_data["username"]
        existing_users  = User.objects.filter(username=username)
        #existing_users = existing_users.exclude(username=...)
        if existing_users.exists():
            raise forms.ValidationError(self.error_messages['duplicate_username'])
        return username

    def clean_password2(self):
        password1 = self.cleaned_data.get("password1", "")
        password2 = self.cleaned_data["password2"]
        if password1 != password2:
            raise forms.ValidationError(
                self.error_messages['password_mismatch'])
        return password2

    def clean_charte(self):
        if not self.cleaned_data['charte']:
            raise forms.ValidationError(u'Vous devez accepter la charte pour pouvoir vous inscrire.')
        return True

    def clean(self):
        cleaned_data = super(OrganizationForm1, self).clean()
        if not cleaned_data['is_provider'] and not cleaned_data['is_customer']:
            raise forms.ValidationError(u'Veuillez cocher une des cases Fournisseur ou Acheteur.')

        # Always return the full collection of cleaned data.
        return cleaned_data

    @transaction.commit_on_success
    def save(self):
        create = not self.instance.pk
        if create:
            user = User()
            user.username = self.cleaned_data['username']
            user.set_password(self.cleaned_data["password1"])
        else:
            user = self.request.user
        user.email = self.cleaned_data['email']
        user.first_name = self.cleaned_data['first_name']
        user.last_name = self.cleaned_data['last_name']
        user.save()
        if create:
            user = authenticate(username=user.username, password=self.cleaned_data['password1'])
            login(self.request, user)
            self.person.user = user
        self.person.gender = self.cleaned_data['gender']
        self.person.username = user.username
        self.person.email = user.email
        self.person.first_name = user.first_name
        self.person.last_name = user.last_name
        self.person.save()
        organization = super(OrganizationForm1, self).save(commit=False)
        if create:
            organization.transmission = 1 # proposed on line
        organization.save()
        if create:
            engagement = Engagement()
            engagement.person = self.person
            engagement.organization = self.instance
            engagement.org_admin = True
        else:
            engagement = Engagement.objects.get(person=self.person, organization=self.instance, org_admin=True)
        engagement.email = self.cleaned_data['email']
        engagement.save()
        return organization


class OrganizationForm2(OrganizationMixin, forms.ModelForm):

    class Meta:
        model = Organization
        fields = ('acronym', 'pref_label', 'logo', 'birth',
                  'legal_status', 'web', 'siret', 'customer_type')

    def __init__(self, propose, *args, **kwargs):
        super(OrganizationForm2, self).__init__(*args, **kwargs)
        self.propose = propose
        if propose:
            if self.instance.is_provider:
                self.fields['birth'].required = True
                self.fields['legal_status'].required = True
            self.fields['siret'].required = True
            self.fields['customer_type'].required = True
        else:
            if self.instance.is_provider:
                self.fields['birth'].label += '*'
                self.fields['legal_status'].label += '*'
            self.fields['siret'].label += '*'
            self.fields['customer_type'].label += '*'
        if not self.instance.is_customer:
            del self.fields['customer_type']
        if not self.instance.is_provider:
            del self.fields['siret']
        self.set_helper(self.fields.keys())


class OrganizationForm3(OrganizationMixin, forms.ModelForm):

    description = forms.CharField(widget=TinyMCE(mce_attrs=settings.TINYMCE_FRONTEND_CONFIG), required=False, label=u'Description', help_text=u'3000 caractères maximum.')

    class Meta:
        model = Organization
        fields = ('brief_description', 'description', 'added_value')

    def __init__(self, propose, *args, **kwargs):
        super(OrganizationForm3, self).__init__(*args, **kwargs)
        if propose:
            self.fields['brief_description'].required = True
        else:
            self.fields['brief_description'].label += '*'
        self.set_helper(('brief_description', 'description', 'added_value',))


class OrganizationForm4(OrganizationMixin, forms.ModelForm):

    class Meta:
        model = Organization
        fields = (
            'category',
            'agreement_iae',
            'category_iae',
            'tags',
            'activities',
            'transverse_themes',
            'guaranties',
        )

    def __init__(self, propose, *args, **kwargs):
        super(OrganizationForm4, self).__init__(*args, **kwargs)
        if propose:
            self.fields['activities'].required = True
        else:
            self.fields['activities'].label += '*'
        if not self.instance.is_customer:
            del self.fields['activities']
        else:
            self.fields['activities'].queryset = ActivityNomenclature.objects.filter(level=settings.ACTIVITY_NOMENCLATURE_LOOKUP_LEVEL).order_by('path')
        if not self.instance.is_provider:
            del self.fields['category']
            del self.fields['agreement_iae']
            del self.fields['category_iae']
            del self.fields['transverse_themes']
            del self.fields['guaranties']
        self.set_helper(self.fields.keys())
        for name, field in self.fields.iteritems():
            if name == 'tags':
                field.help_text = u'Entrez des mots-clés séparés par une virgule.'
            else:
                field.help_text = u''


class OrganizationForm5(OrganizationMixin, forms.ModelForm):

    class Meta:
        model = Organization
        fields = (
            'annual_revenue',
            'workforce',
            'production_workforce',
            'supervision_workforce',
            'integration_workforce',
            'annual_integration_number',
        )

    def __init__(self, propose, *args, **kwargs):
        super(OrganizationForm5, self).__init__(*args, **kwargs)
        if propose:
            self.fields['workforce'].required = True
        else:
            self.fields['workforce'].label += '*'
        if propose and self.instance.agreement_iae.filter(label=u'Conventionnement IAE').exists():
            self.fields['integration_workforce'].required = True
            self.fields['annual_integration_number'].required = True
        else:
            self.fields['integration_workforce'].label += '*'
            self.fields['annual_integration_number'].label += '*'
        for field in self.fields.itervalues():
            field.label = field.label.replace(' (ETP)', '')
            field.localize = True
        self.set_helper((
            AppendedText('annual_revenue', u'€'),
            AppendedText('workforce', u'ETP'),
            AppendedText('production_workforce', u'ETP'),
            AppendedText('supervision_workforce', u'ETP'),
            AppendedText('integration_workforce', u'ETP'),
            'annual_integration_number',
        ))


class OrganizationForm6(OrganizationMixin, forms.ModelForm):

    testimony = forms.CharField(widget=TinyMCE(mce_attrs=settings.TINYMCE_FRONTEND_CONFIG), required=False, label=u'Témoignage')

    class Meta:
        model = Organization
        fields = ('testimony', )

    def __init__(self, propose, *args, **kwargs):
        super(OrganizationForm6, self).__init__(*args, **kwargs)
        self.set_helper(('testimony', ))


class DocumentForm(OrganizationMixin, forms.ModelForm):

    class Meta:
        model = Document
        fields = ('name', 'attachment', 'type', )

    def __init__(self, *args, **kwargs):
        super(DocumentForm, self).__init__(*args, **kwargs)
        self.set_helper((
            HTML('<fieldset class="formset-form">'),
            'name',
            'attachment',
            'type',
            Field('DELETE', template="bootstrap3/layout/delete.html"),
            HTML('</fieldset>'),
        ))


OrganizationForm7 = forms.models.inlineformset_factory(Organization, Document, form=DocumentForm, extra=2)
OrganizationForm7.__init__ = lambda self, propose, *args, **kwargs: forms.models.BaseInlineFormSet.__init__(self, *args, **kwargs)
OrganizationForm7.add_label = u'Ajouter un document'


class RelationForm(OrganizationMixin, forms.ModelForm):

    class Meta:
        model = Relation
        fields = ('relation_type', 'target')

    def __init__(self, *args, **kwargs):
        super(RelationForm, self).__init__(*args, **kwargs)
        self.fields['relation_type'].required = True
        self.set_helper((
            HTML('<fieldset class="formset-form">'),
            'relation_type',
            'target',
            Field('DELETE', template="bootstrap3/layout/delete.html"),
            HTML('</fieldset>'),
        ))


OrganizationForm8 = forms.models.inlineformset_factory(Organization, Relation, form=RelationForm, fk_name='source', extra=2)
OrganizationForm8.__init__ = lambda self, propose, *args, **kwargs: forms.models.BaseInlineFormSet.__init__(self, *args, **kwargs)
OrganizationForm8.add_label = u'Ajouter une relation'


class FixedBaseGenericInlineFormSet(BaseGenericInlineFormSet):

    # Fix https://code.djangoproject.com/ticket/17927
    def __init__(self, data=None, files=None, instance=None, save_as_new=None,
                 prefix=None, queryset=None, **kwargs):
        # Avoid a circular import.
        from django.contrib.contenttypes.models import ContentType
        opts = self.model._meta
        self.instance = instance
        self.rel_name = '-'.join((
            opts.app_label, opts.object_name.lower(),
            self.ct_field.name, self.ct_fk_field.name,
        ))
        if self.instance is None or self.instance.pk is None:
            qs = self.model._default_manager.none()
        else:
            if queryset is None:
                queryset = self.model._default_manager
            qs = queryset.filter(**{
                self.ct_field.name: ContentType.objects.get_for_model(self.instance),
                self.ct_fk_field.name: self.instance.pk,
            })
        super(BaseGenericInlineFormSet, self).__init__(
            queryset=qs, data=data, files=files,
            prefix=prefix, **kwargs
        )



class SaveGenericInlineFormset(FixedBaseGenericInlineFormSet):

    def save_new(self, form, commit=True):
        """ Default save_new does not call our form.save() method. """
        return form.save(commit, self.instance)


def geocode(location):

    addr = urllib.quote_plus(location.city.encode("utf-8"))
    if location.adr1:
        addr += ",+" + urllib.quote_plus(location.adr1.encode("utf-8"))
    if location.adr2:
        addr += ",+" + urllib.quote_plus(location.adr2.encode("utf-8"))
    if location.zipcode:
        addr += ",+" + urllib.quote_plus(location.zipcode.encode("utf-8"))
    addr += "&region=fr"
    try:
        r = urllib2.urlopen(GMAP_URL % addr)
    except urllib2.URLError:
        r = None
    if not r or r.msg != 'OK':
        return
    res = json.loads(r.read())
    results = res.get('results')
    if not results:
        return
    try:
        latlon = results[0].get('geometry').get('location')
    except AttributeError:
        return
    wkt = 'SRID=4326;POINT (%s %s)' % (latlon['lng'], latlon['lat'])
    location.point = wkt


class LocatedForm(OrganizationMixin, forms.ModelForm):

    adr1 = forms.CharField(label=u'Adresse', max_length=100)
    adr2 = forms.CharField(label=u'Adresse (option)', required=False, max_length=100)
    zipcode = forms.CharField(label=u'Code postal', required=False, max_length=5)
    city = forms.CharField(label=u'Ville', required=False, max_length=100)

    class Meta:
        model = Located
        fields = ('main_location', 'category', 'opening')

    def __init__(self, *args, **kwargs):
        instance = kwargs.get('instance')
        if instance and instance.location:
            kwargs['initial'] = dict([(field, getattr(instance.location, field))
                for field in ('adr1', 'adr2', 'zipcode', 'city')])
        super(LocatedForm, self).__init__(*args, **kwargs)
        self.fields['zipcode'].required = True
        self.fields['city'].required = True
        self.fields['adr1'].label += '*'
        self.fields['zipcode'].label += '*'
        self.fields['city'].label += '*'
        self.set_helper((
            HTML('<fieldset class="formset-form">'),
            'main_location',
            'category',
            'adr1', 'adr2', 'zipcode', 'city',
            'opening',
            Field('DELETE', template="bootstrap3/layout/delete.html"),
            HTML('</fieldset>'),
        ))

    def save(self, commit=True, rel_instance=None):
        located = super(LocatedForm, self).save(commit=False)
        if rel_instance:
            located.content_type = ContentType.objects.get_for_model(rel_instance)
            located.object_id = rel_instance.pk
        location = located.location
        if location is None:
            location = Location()
        for field in ('adr1', 'adr2', 'zipcode', 'city'):
            setattr(location, field, self.cleaned_data[field])
        geocode(location)
        if commit:
            location.save()
        located.location = location
        if commit:
            located.save()
        return located


OrganizationForm9 = generic_inlineformset_factory(Located, form=LocatedForm, formset=SaveGenericInlineFormset, extra=2)
OrganizationForm9.__init__ = lambda self, propose, *args, **kwargs: SaveGenericInlineFormset.__init__(self, *args, **kwargs)
OrganizationForm9.add_label = u'Ajouter un lieu'


class ContactInlineFormSet(FixedBaseGenericInlineFormSet):

    def _construct_form(self, i, **kwargs):
        kwargs['organization'] = self.instance
        return super(ContactInlineFormSet, self)._construct_form(i, **kwargs)


class ContactForm(OrganizationMixin, forms.ModelForm):

    class Meta:
        model = Contact
        fields = ('contact_medium', 'content', 'location')

    def __init__(self, *args, **kwargs):
        organization = kwargs.pop('organization', None)
        super(ContactForm, self).__init__(*args, **kwargs)
        if organization:
            queryset = Location.objects.filter(located__organization=organization)
            self.fields['location'].queryset = queryset
        else:
            queryset = Location.objects.none()
        self.fields['contact_medium'].label = u'Coordonnées'
        self.set_helper((
            HTML('<fieldset class="formset-form">'),
            'contact_medium',
            'content',
            'location',
            Field('DELETE', template="bootstrap3/layout/delete.html"),
            HTML('</fieldset>'),
        ))


OrganizationForm10 = generic_inlineformset_factory(Contact, form=ContactForm, formset=ContactInlineFormSet, extra=2)
OrganizationForm10.__init__ = lambda self, propose, *args, **kwargs: ContactInlineFormSet.__init__(self, *args, **kwargs)
OrganizationForm10.add_label = u'Ajouter un contact'


class EngagementForm(OrganizationMixin, forms.ModelForm):

    gender = forms.ChoiceField(choices=(('', u'---'), ('M',  _(u'Mr')), ('W',  _(u'Mrs'))), label=_(u'gender').capitalize(), required=False)
    last_name = forms.CharField(label=_(u'last name').capitalize(), max_length=100)
    first_name = forms.CharField(label=_(u'first name').capitalize(), max_length=100, required=False)

    class Meta:
        model = Engagement
        fields = ('role', 'tel', 'email')

    def __init__(self, *args, **kwargs):
        instance = kwargs.get('instance')
        if instance and instance.person:
            kwargs['initial'] = dict([(field, getattr(instance.person, field))
                for field in ('gender', 'last_name', 'first_name')])
        super(EngagementForm, self).__init__(*args, **kwargs)
        self.set_helper((
            HTML('<fieldset class="formset-form">'),
            HTML('{% if subform.instance.person.user == request.user %}<h3>Vous</h3>{% endif %}'),
            'gender',
            'first_name',
            'last_name',
            'role',
            'tel',
            'email',
            Field('DELETE', template="bootstrap3/layout/delete-engagement.html"),
            HTML('</fieldset>'),
        ))

    def save(self, commit=True, rel_instance=None):
        engagement = super(EngagementForm, self).save(commit=False)
        if rel_instance:
            engagement.content_type = ContentType.objects.get_for_model(rel_instance)
            engagement.object_id = rel_instance.pk
        try:
            person = engagement.person
        except Person.DoesNotExist:
            person = Person()
        for field in ('gender', 'first_name', 'last_name'):
            setattr(person, field, self.cleaned_data[field])
        person.save()
        engagement.person = person
        if commit:
            engagement.save()
        return engagement


class EngagementInlineFormSet(forms.models.BaseInlineFormSet):

    # FIXME: filter delete field when engagement.person.user = current user
    def add_fields(self, form, index):
        return super(EngagementInlineFormSet, self).add_fields(form, index)

OrganizationForm11 = forms.models.inlineformset_factory(Organization, Engagement, form=EngagementForm, formset=EngagementInlineFormSet,  extra=2)
OrganizationForm11.__init__ = lambda self, propose, *args, **kwargs: EngagementInlineFormSet.__init__(self, *args, **kwargs)
OrganizationForm11.add_label = u'Ajouter un membre'


class ReferenceForm(OrganizationMixin, forms.ModelForm):

    class Meta:
        model = Reference
        fields = ('target', 'from_year', 'to_year', 'services')

    def __init__(self, *args, **kwargs):
        super(ReferenceForm, self).__init__(*args, **kwargs)
        self.fields['target'].queryset = Organization.objects.filter(is_customer=True)
        self.set_helper((
            HTML('<fieldset class="formset-form">'),
            'target',
            'from_year',
            'to_year',
            'services',
            Field('DELETE', template="bootstrap3/layout/delete.html"),
            HTML('</fieldset>'),
        ))

    def save(self, commit=True):
        ref = super(ReferenceForm, self).save(commit=False)
        ref.relation_type = OrgRelationType.objects.get(id=6)
        if commit:
            ref.save()
        return ref


OrganizationForm12 = forms.models.inlineformset_factory(Organization, Reference, form=ReferenceForm, fk_name='source', extra=2)
OrganizationForm12.__init__ = lambda self, propose, *args, **kwargs: forms.models.BaseInlineFormSet.__init__(self, *args, **kwargs)
OrganizationForm12.add_label = u'Ajouter une référence'


PROVIDER_FORMS = (
    OrganizationForm1,
    OrganizationForm2,
    OrganizationForm3,
    OrganizationForm4,
    OrganizationForm5,
    OrganizationForm6,
    OrganizationForm7,
    OrganizationForm8,
    OrganizationForm9,
    OrganizationForm10,
    OrganizationForm11,
    OrganizationForm12,
)

NOT_PROVIDER_FORMS = (
    OrganizationForm1,
    OrganizationForm2,
    OrganizationForm3,
    OrganizationForm4,
    OrganizationForm6,
    OrganizationForm7,
    OrganizationForm8,
    OrganizationForm9,
    OrganizationForm10,
    OrganizationForm11,
)


class OfferForm(forms.ModelForm):

    class Meta:
        model = Offer
        fields = (
            'activity',
            'description',
            'targets',
            'technical_means',
            'workforce',
            'practical_modalities',
            'area',
        )

    def __init__(self, *args, **kwargs):
        super(OfferForm, self).__init__(*args, **kwargs)
        self.fields['activity'].queryset = ActivityNomenclature.objects.filter(level=settings.ACTIVITY_NOMENCLATURE_LOOKUP_LEVEL).order_by('path')
        self.fields['activity'].help_text = u''
        self.fields['targets'].widget = forms.widgets.CheckboxSelectMultiple()
        self.fields['targets'].help_text = u''
        self.fields['area'].help_text = u''
        self.fields['workforce'].label = self.fields['workforce'].label.replace(' (ETP)', '')
        self.helper = FormHelper()
        self.helper.form_tag = False
        self.helper.layout = Layout(
            'activity',
            'description',
            InlineCheckboxes('targets'),
            'technical_means',
            AppendedText('workforce', u'ETP'),
            'practical_modalities',
            'area',
        )
