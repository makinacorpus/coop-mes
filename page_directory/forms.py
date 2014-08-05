# -*- coding: utf-8 -*-

from django import forms
from ionyweb.forms import ModuloModelForm
from .models import PageApp_Directory
from coop_local.models import (ActivityNomenclature,
    Organization, Engagement, Document, Relation, Located, Location,
    Contact, Person, Offer, Reference, OrgRelationType, OfferDocument,
    ContactMedium)
from coop_local.models.local_models import normalize_text
from django.conf import settings
from tinymce.widgets import TinyMCE
from django.contrib.auth.models import User
from django.utils.translation import ugettext_lazy as _
from crispy_forms.helper import FormHelper
from crispy_forms.layout import Layout, HTML, Field
from crispy_forms.bootstrap import (InlineRadios, InlineCheckboxes,
    AppendedText)
from django.contrib.contenttypes.generic import (
    generic_inlineformset_factory, BaseGenericInlineFormSet)
from django.contrib.contenttypes.models import ContentType
from django.contrib.auth import login, authenticate
import urllib, urllib2, json
from django.db import transaction
from coop_local.sync_contacts import sync_contacts
from django.core.urlresolvers import reverse
from ionyweb.plugin_app.plugin_contact.models import Plugin_Contact
from django.contrib.sites.models import Site
from coop_local.mixed_email import send_mixed_email


GMAP_URL = "http://maps.googleapis.com/maps/api/geocode/json?address=%s"\
           "&sensor=false"


class PageApp_DirectoryForm(ModuloModelForm):

    class Meta:
        model = PageApp_Directory


class OrganizationMixin(object):

    def set_helper(self, fields):
        self.helper = FormHelper()
        self.helper.form_tag = False
        self.helper.layout = Layout()
        self.helper.layout.extend(fields)
        self.helper.help_text_inline = True


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
    last_name = forms.CharField(label=_(u'last name').capitalize(), max_length=30)
    first_name = forms.CharField(label=_(u'first name').capitalize(), max_length=30, required=False)
    email = forms.CharField(label='Courriel', max_length=75)

    class Meta:
        model = Organization
        fields = ('title', 'is_provider', 'is_customer')

    def __init__(self, request, bdis, propose, *args, **kwargs):
        self.request = request
        self.bdis = bdis
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
        self.fields['title'].help_text = u"<p>Nom complet de l’organisation ; ce nom ne doit pas être précédé de votre statut juridique.</p><p>Exemple : A votre service ou Acheteur durable et non pas Association A Votre Service ou SA Acheteur durable</p>"
        if self.bdis:
            del self.fields['is_provider']
            del self.fields['is_customer']

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
        if not self.bdis and not cleaned_data['is_provider'] and not cleaned_data['is_customer']:
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
            if self.bdis:
                organization.is_bdis = True
                organization.is_provider = True
            else:
                organization.is_pasr = True
                if organization.is_provider:
                    organization.is_bdis = True
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

        # send a welcome email
        if create:
            sender = Plugin_Contact.objects.get(pages__pages__website=self.request.website).email
            site = Site.objects.get_current().domain
            context = {
                'person': self.person,
                'sender': sender,
                'site': site,
                'slug': settings.REGION_SLUG,
                'region': settings.REGION_NAME,
                'login': user.username,
                'password': self.cleaned_data["password1"],
            }
            subject = u'Votre inscription sur %s' % site
            if self.bdis:
                template = 'email/inscription-bdis'
            else:
                template = 'email/inscription-pasr'
            email = user.email
            send_mixed_email(sender, email, subject, template, context)

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
            if self.instance.is_pasr:
                self.fields['siret'].required = True
            self.fields['customer_type'].required = True
        else:
            if self.instance.is_provider:
                self.fields['birth'].label += '*'
                self.fields['legal_status'].label += '*'
            if self.instance.is_pasr:
                self.fields['siret'].label += '*'
            self.fields['customer_type'].label += '*'
        if not self.instance.is_customer:
            del self.fields['customer_type']
        if not self.instance.is_provider:
            del self.fields['siret']
        if self.instance.is_provider:
            self.fields['acronym'].help_text = u"<p>Le nom de votre organisation en abrégé ; exemple AVS pour A Votre Service</p>"
        else:
            self.fields['acronym'].help_text = u"<p>Le nom de votre organisation en abrégé ; exemple AD pour Acheteur durable</p>"
        self.set_helper(self.fields.keys())


class OrganizationForm3(OrganizationMixin, forms.ModelForm):

    description = forms.CharField(widget=TinyMCE(mce_attrs=settings.TINYMCE_FRONTEND_CONFIG), required=False, label=u'Description', help_text=u'3000 caractères maximum.')

    class Meta:
        model = Organization
        fields = ('brief_description', 'description', 'added_value')

    def __init__(self, propose, *args, **kwargs):
        super(OrganizationForm3, self).__init__(*args, **kwargs)
        self.fields['added_value'].help_text = u"<p>En quoi votre structure est-elle porteuse une utilité sociale et environnementale :</p><p>Exemple : pour A Votre Service, formation et qualification de publics éloignés de l’emploi ; produits écologiques et équitables ; réduction de la consommation d’énergie"
        if propose:
            self.fields['brief_description'].required = True
        else:
            self.fields['brief_description'].label += '*'
        if not self.instance.is_provider:
            del self.fields['added_value']
        if self.instance.is_provider:
            self.fields['brief_description'].help_text = u"<p>Décrivez et valorisez l’activité de votre structure en une phrase</p><p>Exemple : pour l’association A Votre Service</p><p>Prestations de nettoyage de vos locaux avec des produits écologiques</p>"
        else:
            self.fields['brief_description'].help_text = u"<p>Décrivez et valorisez l’activité de votre structure en une phrase</p><p>Exemple : pour Acheteur durable</p><p>Une société régionale dans le domaine du BTP</p>"
        self.set_helper(self.fields.keys())


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
        for name, field in self.fields.iteritems():
            field.help_text = u''
        if self.instance.is_provider:
            self.fields['tags'].help_text = u"<p>Entrez des mots-clés séparés par une virgule.</p><p>Les mots clés permettent d’affiner les recherches sur votre structure ; ils correspondent aux termes ciblant le plus précisément votre activité</P><p>Exemple : entretien, nettoyage industriel, propreté pour A Votre Service"
        else:
            self.fields['tags'].help_text = u"<p>Entrez des mots-clés séparés par une virgule.</p><p>Les mots clés permettent d’affiner les recherches sur votre structure ; ils correspondent aux termes ciblant le plus précisément votre activité</P><p>Exemple : bâtiment, gros œuvre, démolition, voirie"
        self.fields['activities'].help_text = u"<p>Correspond aux achats responsables que vous souhaitez effectuer en tant qu’acheteur.</p><p>Exemple : nettoyage de locaux, jardins</p>"
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
        if self.instance.agreement_iae.filter(label=u'Conventionnement IAE').exists():
            if propose:
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
        if self.instance.is_provider:
            self.fields['testimony'].help_text = u"<p>Vous pouvez apporter un témoignage sur vos expériences en matière de partenariats d’achats responsables</p>"
        else:
            self.fields['testimony'].help_text = u"<p>Vous pouvez apporter un témoignage sur la politique d’achat responsable que vous mettez en œuvre dans votre entreprise</p>"
        self.set_helper(('testimony', ))


class DocumentForm(OrganizationMixin, forms.ModelForm):

    class Meta:
        model = Document
        fields = ('name', 'attachment', 'type', )

    def __init__(self, *args, **kwargs):
        super(DocumentForm, self).__init__(*args, **kwargs)
        self.fields['name'].help_text = u"<p>Déposez vos documents (formats pdf ou image) de présentation de votre structure : exemple plaquette de, présentation, flyer, dossiers techniques, historique…</p><p>Poids maximum des documents : 1,5 Mo</p>"
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
        instance = kwargs.get('instance')
        self.fields['relation_type'].required = True
        self.fields['target'].label = u'Partenaire'
        self.fields['relation_type'].help_text = u"<p>Exemple : appartient au réseau des entreteneurs durables, a pour fournisseur A Votre Service</p>"
        self.set_helper((
            HTML('<fieldset class="formset-form">'),
            'relation_type',
            'target',
            HTML('<div class="form-group"><div class="col-lg-3"></div><div class="col-lg-9"><p class="help-block">Si le partenaire n\'apparait pas dans la liste ci-dessus vous pouvez l\'<a class="add-target-link" data-toggle="modal" href="#" data-remote="%s?html" data-target="#add_target">ajouter</a>.</p></div></div>' % reverse('add_target')),
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


class ContactInlineFormSet(SaveGenericInlineFormset):

    def _construct_form(self, i, **kwargs):
        kwargs['organization'] = self.instance
        return super(ContactInlineFormSet, self)._construct_form(i, **kwargs)


class ContactForm(OrganizationMixin, forms.ModelForm):

    class Meta:
        model = Contact
        fields = ('contact_medium', 'content', 'location')

    def __init__(self, *args, **kwargs):
        self.organization = kwargs.pop('organization', None)
        super(ContactForm, self).__init__(*args, **kwargs)
        if self.organization:
            queryset = Location.objects.filter(located__organization=self.organization)
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

    def save(self, commit=True, rel_instance=None):
        contact = super(ContactForm, self).save(commit=False)
        if rel_instance:
            contact.content_type = ContentType.objects.get_for_model(rel_instance)
            contact.object_id = rel_instance.pk
        if commit:
            contact.save()
        if contact.contact_medium.label in (u'Téléphone', u'Mobile') and not self.organization.pref_phone:
            self.organization.pref_phone = contact
        if contact.contact_medium.label == 'Courriel' and not self.organization.pref_email:
            self.organization.pref_email = contact
        if commit:
            self.organization.save()
        return contact


OrganizationForm10 = generic_inlineformset_factory(Contact, form=ContactForm, formset=ContactInlineFormSet, extra=2)
OrganizationForm10.__init__ = lambda self, propose, *args, **kwargs: ContactInlineFormSet.__init__(self, *args, **kwargs)
OrganizationForm10.add_label = u'Ajouter un contact'


class EngagementForm(OrganizationMixin, forms.ModelForm):

    gender = forms.ChoiceField(choices=(('', u'---'), ('M',  _(u'Mr')), ('W',  _(u'Mrs'))), label=_(u'gender').capitalize(), required=False)
    last_name = forms.CharField(label=_(u'last name').capitalize(), max_length=30)
    first_name = forms.CharField(label=_(u'first name').capitalize(), max_length=30, required=False)
    tel = forms.CharField(label=_(u'tél.'), required=False)
    email = forms.EmailField(label=_(u'email'), max_length=7, required=False)

    class Meta:
        model = Engagement
        fields = ('role', )

    def __init__(self, *args, **kwargs):
        instance = kwargs.get('instance')
        initial = {}
        if instance and instance.person:
            for field in ('gender', 'last_name', 'first_name'):
                initial[field] = getattr(instance.person, field)
        if instance and instance.id:
            engagement_ct = ContentType.objects.get(app_label="coop_local", model="engagement")
            get_kwargs = {
                'content_type': engagement_ct,
                'object_id': instance.id,
                'contact_medium': ContactMedium.objects.get(label=u'Téléphone'),
            }
            try:
                initial['tel'] = Contact.objects.get(**get_kwargs).content
            except Contact.DoesNotExist:
                pass
            get_kwargs['contact_medium'] = ContactMedium.objects.get(label=u'Courriel')
            try:
                initial['email'] = Contact.objects.get(**get_kwargs).content
            except Contact.DoesNotExist:
                pass
        kwargs['initial'] = initial
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
    def save(self, commit=True):
        engagements = super(EngagementInlineFormSet, self).save(commit)
        for engagement in engagements:
            for form in self.forms:
                if form.instance == engagement:
                    sync_contacts(engagement, form.cleaned_data)
        return engagements

    def add_fields(self, form, index):
        return super(EngagementInlineFormSet, self).add_fields(form, index)

OrganizationForm11 = forms.models.inlineformset_factory(Organization, Engagement, form=EngagementForm, formset=EngagementInlineFormSet,  extra=2)
OrganizationForm11.__init__ = lambda self, propose, *args, **kwargs: EngagementInlineFormSet.__init__(self, *args, **kwargs)
OrganizationForm11.add_label = u'Ajouter un membre'


class AddTargetForm(OrganizationMixin, forms.ModelForm):

    tel = forms.CharField(label=_(u'tél.'), required=False)
    email = forms.EmailField(label=_(u'email'), required=True)

    class Meta:
        model = Organization
        fields = ('title', 'web', 'tel', 'email')

    def __init__(self, *args, **kwargs):
        super(AddTargetForm, self).__init__(*args, **kwargs)
        self.set_helper((
            'title', 'web', 'tel', 'email',
        ))

    def clean_title(self):
        title = self.cleaned_data['title']
        if Organization.objects.exclude(pk=self.instance.pk).filter(norm_title=normalize_text(title)).exists():
            raise forms.ValidationError(u'Un Fournisseur ou Acheteur avec ce nom existe déjà.')
        return title


class ReferenceForm(OrganizationMixin, forms.ModelForm):

    class Meta:
        model = Reference
        fields = ('target', 'from_year', 'to_year', 'services', 'relation_ptr')

    def __init__(self, *args, **kwargs):
        super(ReferenceForm, self).__init__(*args, **kwargs)
        self.set_helper((
            HTML('<fieldset class="formset-form">'),
            'target',
            HTML('<div class="form-group"><div class="col-lg-3"></div><div class="col-lg-9"><p class="help-block">Si l\'acheteur n\'apparait pas dans la liste ci-dessus vous pouvez l\'<a class="add-target-link" data-toggle="modal" href="#" data-remote="%s?html" data-target="#add_target">ajouter</a>.</p></div></div>' % reverse('add_target')),
            'from_year',
            'to_year',
            'services',
            'relation_ptr',
            Field('DELETE', template="bootstrap3/layout/delete.html"),
            HTML('</fieldset>'),
        ))
        self.helper.help_text_inline = False

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
            'tags',
        )

    def __init__(self, *args, **kwargs):
        super(OfferForm, self).__init__(*args, **kwargs)
        self.fields['activity'].queryset = ActivityNomenclature.objects.filter(level=settings.ACTIVITY_NOMENCLATURE_LOOKUP_LEVEL).order_by('path')
        self.fields['activity'].help_text = u"<p>Vous pouvez saisir plusieurs secteurs d’activité associés à votre offre</p><p>Pour accéder rapidement à un secteur d’activité, entrer un terme générique</p><p>Exemple : « nettoyage » vous permet de sélectionner nettoyage de locaux, nettoyage de parties communes, nettoyage urbain</p>"
        self.fields['description'].help_text = u"<p>Description synthétique qui valorise votre offre de biens et de services auprès des acheteurs professionnels</p><p>Nettoyage de locaux industriels de toute taille sur le département du …, avec des produits écologiques</p><p>400 caractères maximum</p>"
        self.fields['targets'].widget = forms.widgets.CheckboxSelectMultiple()
        self.fields['targets'].help_text = u''
        self.fields['technical_means'].help_text = u"<p>Locaux, équipements,logiciels, …</p><p>400 caractères maximum</p>"
        self.fields['area'].help_text = u"<p>Vous pouvez sélectionner plusieurs lieux d’intervention en région associés, à cette offre de biens et de services</p>"
        self.fields['workforce'].label = self.fields['workforce'].label.replace(' (ETP)', '')
        self.fields['practical_modalities'].help_text = u"<p>Informations relatives à la tarification, les délais de réponse et d’intervention, la prise de contact…</p><p>400 caractères maximum</p>"
        self.helper = FormHelper()
        self.helper.help_text_inline = True
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


class OfferDocumentForm(OrganizationMixin, forms.ModelForm):

    class Meta:
        model = OfferDocument
        fields = ('name', 'attachment', 'type', )

    def __init__(self, *args, **kwargs):
        super(OfferDocumentForm, self).__init__(*args, **kwargs)
        self.fields['name'].help_text = u"<p>Déposez vos documents (formats pdf ou image) de présentation de votre OFFRE :</p><p>exemple : dossiers techniques, photos de produits, expériences liée à cette offre…</p><p>Poids maximum des documents : 1,5 Mo"
        self.set_helper((
            HTML('<fieldset class="formset-form"><p>Document / Image</p>'),
            'name',
            'attachment',
            'type',
            Field('DELETE', template="bootstrap3/layout/delete.html"),
            HTML('</fieldset>'),
        ))


OfferDocumentsFormset = forms.models.inlineformset_factory(Offer, OfferDocument, form=OfferDocumentForm, extra=2)
