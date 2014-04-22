# -*- coding:utf-8 -*-
from django import forms
from django.contrib import admin
from django.core.exceptions import ImproperlyConfigured, PermissionDenied
from django.db.models.loading import get_model
from django.contrib.contenttypes.models import ContentType
from django.db import models
from django.db.models import Q
from django.utils.translation import ugettext as _
from django.contrib.contenttypes.generic import generic_inlineformset_factory
from django.conf.urls.defaults import patterns, url
from django.shortcuts import get_object_or_404, render
from django.http import HttpResponse, HttpResponseRedirect
from django.template.defaultfilters import slugify
from django.contrib.admin.widgets import RelatedFieldWidgetWrapper
from django.contrib.admin.util import unquote
from django.core.urlresolvers import reverse
from django.contrib.admin.templatetags.admin_static import static
from django.utils.safestring import mark_safe
from django.conf import settings
from django.core.mail import send_mail
from coop_local.mixed_email import send_mixed_email
from django.contrib.auth.models import User
from django.contrib.admin.util import flatten_fieldsets
from django.utils.formats import number_format
from django.contrib.sites.models import Site

from chosen import widgets as chosenwidgets
from selectable.base import ModelLookup
from selectable.registry import registry
from selectable.exceptions import LookupAlreadyRegistered
from selectable.forms import AutoCompleteSelectMultipleWidget
from mptt.admin import MPTTModelAdmin
from sorl.thumbnail.admin import AdminImageMixin
from djappypod.response import OdtTemplateResponse
from tinymce.widgets import AdminTinyMCE
import csv
from django.contrib import messages
import unicodedata
import re
import random
import string
from coop_local.sync_contacts import sync_contacts
from haystack import connections

from coop.org.admin import (
    OrganizationAdmin as BaseOrganizationAdmin,
    OrganizationAdminForm as BaseOrganizationAdminForm,
    RelationInline,
    LocatedInline,
    ContactInline as BaseContactInline,
    EngagementInline as BaseEngagementInline,
    OrgInline)
from coop.person.admin import (
    PersonAdmin as BasePersonAdmin)
from coop.agenda.admin import (
    EventAdmin as BaseEventAdmin,
    EventAdminForm as BaseEventAdminForm,
    OccurrenceInline)
from coop_geo.admin import LocationAdmin as BaseLocationAdmin
from coop.utils.autocomplete_admin import (
    FkAutocompleteAdmin,
    InlineAutocompleteAdmin,
    SelectableAdminMixin,
    AutoComboboxSelectEditWidget,
    AutoCompleteSelectEditWidget,
    register)
from coop_geo.models import Location, Area
from coop_local.models.local_models import normalize_text
from coop_local.models import (LegalStatus, CategoryIAE, Document, Guaranty, Reference, ActivityNomenclature,
    ActivityNomenclatureAvise, Offer, TransverseTheme, DocumentType, AgreementIAE,
    Location, Engagement, ContactMedium, CallForTenders)

try:
    from coop.base_admin import *
except ImportError, exp:
    raise ImproperlyConfigured("Unable to find coop/base_admin.py file")


# subclass existing ModelAdmins and add your own model's ModelAdmins here

"""
# ---- overriding main models when needed : example -----------------------

# first unregister previous ModelAdmin
admin.site.unregister(Person)

# define anothe admin
class MyPersonAdmin(PersonAdmin):
    Add custom fields you defined in coop_local.models
    fieldsets = (
        ('Identification', {
            'fields': (('first_name', 'last_name'),
                        ('location', 'location_display'),  # Using coop-geo
                        'email',
                        'category'
                        ),
            }),
        ('Notes', {
            'fields': ('structure', 'notes',)
        })
    )
    Using coop-geo
    related_search_fields = {'location': ('label', 'adr1', 'adr2', 'zipcode', 'city'), }
admin.site.register(Person, MyPersonAdmin)

# ----- admin for classifications : ultra-simple -----------------------------

admin.site.register(Statut, CoopTagTreeAdmin)



"""


class LocationLookup(ModelLookup):
    model = Location
    search_fields = ('label', 'adr1', 'adr2', 'zipcode', 'city')

    def get_query(self, request, term):
        results = super(LocationLookup, self).get_query(request, term)
        if 'pks' in request.GET:
            if request.GET['pks']:
                pks = request.GET['pks'].split(',')
                results = results.filter(pk__in=pks)
            else:
                results = results.none()
        return results


class AreaLookup(ModelLookup):
    model = Area
    search_fields = ('label__icontains', 'reference__icontains')


class MediumLookup(ModelLookup):
    model = ContactMedium
    search_fields = ('label__icontains', )


class ActivityLookup(ModelLookup):
    model = ActivityNomenclature
    search_fields = ('path__icontains', )
    #filters = {'level': settings.ACTIVITY_NOMENCLATURE_LOOKUP_LEVEL}


try:
    registry.register(LocationLookup)
except LookupAlreadyRegistered:
    pass
try:
    registry.register(AreaLookup)
except LookupAlreadyRegistered:
    pass
try:
    registry.register(MediumLookup)
except LookupAlreadyRegistered:
    pass
try:
    registry.register(ActivityLookup)
except LookupAlreadyRegistered:
    pass


def make_contact_form(pks, admin_site, request):
    class ContactForm(forms.ModelForm):
        def __init__(self, *args, **kwargs):
            super(ContactForm, self).__init__(*args, **kwargs)
            location_rel = Contact._meta.get_field_by_name('location')[0].rel
            medium_rel = Contact._meta.get_field_by_name('contact_medium')[0].rel
            self.fields['location'].widget = AutoComboboxSelectEditWidget(location_rel, admin_site, LocationLookup)
            if pks is not None:
                self.fields['location'].widget.update_query_parameters({'pks': ','.join(map(str, pks))})
            self.fields['location'].widget.choices = None
            self.fields['location'].widget = RelatedFieldWidgetWrapper(self.fields['location'].widget, location_rel, admin_site, can_add_related=False)
            self.fields['contact_medium'].widget = RelatedFieldWidgetWrapper(self.fields['contact_medium'].widget, medium_rel, admin_site, can_add_related=False)
        class Meta:
            model = Contact
            fields = ('contact_medium', 'content', 'details', 'location', 'display')
    return ContactForm


class ContactInline(BaseContactInline):
    fields = ('contact_medium', 'content', 'details', 'location', 'display')
    def get_formset(self, request, obj=None, **kwargs):
        if not obj:
            pks = None
        elif isinstance(obj, Organization):
            pks = Location.objects.filter(located__organization=obj).values_list('pk', flat=True)
        elif isinstance(obj, Person):
            pks = [obj.location.pk] if obj.location else []
            pks += Location.objects.filter(located__organization__members=obj).values_list('pk', flat=True)
        else:
            pks = None
        return generic_inlineformset_factory(Contact, form=make_contact_form(pks, self.admin_site, request))


class EngagementForm(forms.ModelForm):
    tel = forms.CharField(label=_(u'tél.'), required=False)
    email = forms.EmailField(label=_(u'email'), required=False)

    class Meta:
        model = Engagement
        fields = ('person', 'role', 'role_detail', 'org_admin', 'engagement_display')

    def __init__(self, *args, **kwargs):
        instance = kwargs.get('instance')
        initial = {}
        if instance and instance.id:
            try:
                initial['tel'] = instance.contacts.get(contact_medium__label=u'Téléphone').content
            except Contact.DoesNotExist:
                pass
            try:
                initial['email'] = instance.contacts.get(contact_medium__label=u'Courriel').content
            except Contact.DoesNotExist:
                pass
        kwargs['initial'] = initial
        super(EngagementForm, self).__init__(*args, **kwargs)


class EngagementFormSet(forms.models.BaseInlineFormSet):

    def save(self, commit=True):
        engagements = super(EngagementFormSet, self).save(commit)
        for engagement in engagements:
            for form in self.forms:
                if form.instance == engagement:
                    sync_contacts(engagement, form.cleaned_data)
        return engagements


class EngagementInline(BaseEngagementInline):
    form = EngagementForm
    formset = EngagementFormSet
    fields = ('person', 'role', 'role_detail', 'tel', 'email', 'org_admin', 'engagement_display')
    related_search_fields = {
        'person': ('last_name', 'first_name'),
        'role': ('label', )
    }
    related_combobox = ('role', )


class DocumentInline(InlineAutocompleteAdmin):

    model = Document
    verbose_name = _(u'document')
    verbose_name_plural = _(u'documents')
    extra = 1

    def has_change_permission(self, request, obj=None):
        return True

    def has_add_permission(self, request, obj=None):
        return True

    def has_delete_permission(self, request, obj=None):
        return True


class ReferenceInline(InlineAutocompleteAdmin):

    model = Reference
    verbose_name = _(u'reference')
    verbose_name_plural = _(u'references')
    fk_name = 'source'
    readonly_fields = ('created',)
    fields = ('target', 'from_year', 'to_year', 'services', 'created')
    related_search_fields = {'target': ('title', 'subtitle', 'acronym',), }
    extra = 1

    def queryset(self, request):
        queryset = super(ReferenceInline, self).queryset(request)
        return queryset.filter(relation_type_id=6)


class ActivityWidget(AutoCompleteSelectEditWidget):

    def render(self, name, value, attrs=None):
        markup = super(ActivityWidget, self).render(name, value, attrs)
        related_url = reverse('admin:coop_local_offer_activity_list', current_app=self.admin_site.name)
        markup += u'&nbsp;<a href="%s" class="activity-lookup" id="lookup_id_%s" onclick="return showActivityLookupPopup(this);">' % (related_url, name)
        markup += u'<img src="%s" width="16" height="16"></a>' % static('admin/img/selector-search.gif')
        return mark_safe(markup)


class OrganizationAdminForm(BaseOrganizationAdminForm):

    testimony = forms.CharField(widget=AdminTinyMCE(attrs={'cols': 80, 'rows': 60}), required=False)

    class Meta:
        model = get_model('coop_local', 'Organization')
        widgets = {
            'category': chosenwidgets.ChosenSelectMultiple(),
            'category_iae': chosenwidgets.ChosenSelectMultiple(),
            'guaranties': chosenwidgets.ChosenSelectMultiple(),
            'authors': chosenwidgets.ChosenSelectMultiple(),
            'activities': chosenwidgets.ChosenSelectMultiple(),
            'transverse_themes': forms.CheckboxSelectMultiple(),
        }

    def __init__(self, *args, **kwargs):

        # We do not call just super class, but super super class, because of redefinition of all parent logic
        super(OrganizationAdminForm, self).__init__(*args, **kwargs)
        self.fields['category_iae'].help_text = None

        engagements = self.instance.engagement_set.all()
        members_id = engagements.values_list('id', flat=True)
        org_contacts = Contact.objects.filter(
            Q(content_type=ContentType.objects.get(model='organization'), object_id=self.instance.id)
          | Q(content_type=ContentType.objects.get(model='engagement'), object_id__in=members_id)
            )
        phone_categories = [1, 2]
        self.fields['pref_email'].queryset = org_contacts.filter(contact_medium_id=8)
        self.fields['pref_phone'].queryset = org_contacts.filter(contact_medium_id__in=phone_categories)
        self.fields['category'].help_text = None

        member_locations_id = [m.location.id for m in
            Person.objects.filter(id__in=members_id).exclude(location=None)]  # limit SQL to location field

        self.fields['pref_address'].queryset = Location.objects.filter(
            Q(id__in=self.instance.located.all().values_list('location_id', flat=True))
          | Q(id__in=member_locations_id)
            )

        for field_name in ('workforce', 'production_workforce', 'supervision_workforce',
            'integration_workforce', 'annual_integration_number'):
            self.fields[field_name].localize = True

    def clean_title(self):
        title = self.cleaned_data['title']
        norm_title = normalize_text(title)
        if Organization.objects.filter(norm_title=norm_title).exclude(pk=self.instance.pk).exists():
            raise forms.ValidationError(_('An organization with this title already exists.'))
        return title

    def clean_is_provider(self):
        is_provider = self.cleaned_data['is_provider']
        is_bdis = self.cleaned_data.get('is_bdis')
        if is_bdis and not is_provider:
            raise forms.ValidationError(u"Une organisation de la BDIS doit être un fournisseur")
        return is_provider

    def clean_is_pasr(self):
        if not self.cleaned_data.get('is_pasr') and not self.cleaned_data.get('is_bdis'):
            raise forms.ValidationError(u"Veuillez cocher au moins un des deux choix : PASR ou BDIS")
        return self.cleaned_data['is_pasr']

    def clean_is_network(self):
        if not self.cleaned_data.get('is_provider') and not self.cleaned_data.get('is_customer') and not self.cleaned_data.get('is_network'):
            raise forms.ValidationError(u"Veuillez cocher au moins un des trois choix : fournisseur, acheteur ou réseau")
        return self.cleaned_data['is_network']


class AuthorListFilter(admin.SimpleListFilter):
    title = u'rédacteur'
    parameter_name = 'redacteur'

    def lookups(self, request, model_admin):
        return [(user.id, user.username) for user in User.objects.filter(is_staff=True)]

    def queryset(self, request, queryset):
        if not self.value():
            return queryset
        return queryset.filter(authors__id=self.value())


class OrganizationAdmin(BaseOrganizationAdmin):

    form = OrganizationAdminForm
    list_display = ['logo_list_display', 'title', 'acronym', 'status', 'is_provider',
        'is_customer', 'is_network', 'active', 'creation', 'modification']
    list_display_links = ['title', 'acronym']
    readonly_fields = ['creation', 'modification']
    list_filter = ['status', 'transmission', 'is_bdis', 'is_pasr', 'is_provider', 'is_customer', 'is_network', 'a_la_une', 'en_direct', 'zoom_sur', AuthorListFilter]
    ordering = ['norm_title']
    fieldsets = (
        (_(u'Key info'), {
            'fields': ['title', ('acronym', 'pref_label'), 'logo', 'birth', 'active',
                       'legal_status', 'category', 'category_iae', 'agreement_iae',
                       'web', 'siret', 'bdis_id', 'a_la_une', 'en_direct', 'zoom_sur']
            }),
        (_(u'Organization type'), {
            'fields': ['is_bdis', 'is_pasr', 'is_provider', 'is_customer', 'is_network', 'customer_type']
            }),
        (_(u'Economic info'), {
            'fields': [('annual_revenue', 'workforce'), ('production_workforce', 'supervision_workforce'),
                       ('integration_workforce', 'annual_integration_number')]
            }),
        (_(u'Description'), {
            'fields': ['brief_description', 'description', 'added_value', 'activities', 'tags', 'transverse_themes']
            }),
        (_(u'Guaranties'), {
            'fields': ['guaranties']
            }),
        (_(u'Management'), {
            'fields': ['creation', 'modification', 'status', 'correspondence', 'transmission',
                       'transmission_date', 'authors', 'validation']
            }),
        (_(u'Préférences de contact'), {
            'fields': ['pref_email', 'pref_phone', 'pref_address', 'notes',]
            }),
        (_(u'Testimony'), {
            'fields': ['testimony',]
            }),
        (_(u'Preferences'), {
            'fields': ['newsletter_subscription', 'calls_subscription',
                       'events_subscription', 'exchanges_subscription']
            }),
    )
    restricted_fieldsets = (
        (_(u'Key info'), {
            'fields': ['title', ('acronym', 'pref_label'), 'logo', 'birth', 'active',
                       'legal_status', 'category', 'category_iae', 'agreement_iae',
                       'web', 'siret', 'bdis_id']
            }),
        (_(u'Organization type'), {
            'fields': ['is_bdis', 'is_pasr', 'is_provider', 'is_customer', 'is_network', 'customer_type']
            }),
        (_(u'Economic info'), {
            'fields': [('annual_revenue', 'workforce'), ('production_workforce', 'supervision_workforce'),
                       ('integration_workforce', 'annual_integration_number')]
            }),
        (_(u'Description'), {
            'fields': ['brief_description', 'description', 'added_value', 'activities', 'tags', 'transverse_themes']
            }),
        (_(u'Guaranties'), {
            'fields': ['guaranties']
            }),
        (_(u'Management'), {
            'fields': ['creation', 'modification', 'status', 'correspondence', 'transmission',
                       'transmission_date', 'authors', 'validation']
            }),
        (_(u'Préférences de contact'), {
            'fields': ['pref_email', 'pref_phone', 'pref_address', 'notes',]
            }),
        (_(u'Testimony'), {
            'fields': ['testimony',]
            }),
        (_(u'Preferences'), {
            'fields': ['newsletter_subscription', 'calls_subscription',
                       'events_subscription', 'exchanges_subscription']
            }),
    )
    inlines = [DocumentInline, RelationInline, LocatedInline, ContactInline, EngagementInline, ReferenceInline]
    change_form_template = 'admin/coop_local/organization/tabbed_change_form.html'
    search_fields = ['norm_title', 'acronym']
    related_search_fields = {'legal_status': ('label', )}
    related_combobox = ('legal_status', )

    class Media:
        js = ('mce_filebrowser/js/filebrowser_init.js',)

    def get_fieldsets(self, request, obj=None):
        if request.user.is_superuser:
            return super(OrganizationAdmin, self).get_fieldsets(request, obj)
        return self.restricted_fieldsets

    def get_form(self, request, obj=None, **kwargs):
        """
        Workaround bug http://code.djangoproject.com/ticket/9360 (thanks to peritus)
        """
        return super(OrganizationAdmin, self).get_form(request, obj, fields=flatten_fieldsets(self.get_fieldsets(request, obj)))

    def changelist_view(self, request, extra_context=None):
        query_dict = request.GET.copy()
        if 'q' in query_dict:
            query_dict['q'] = normalize_text(query_dict['q'])
        request.GET = query_dict
        return super(OrganizationAdmin, self).changelist_view(request, extra_context)

    def change_view(self, request, object_id, form_url='', extra_context={}):
        obj = self.get_object(request, unquote(object_id))
        if request.user.is_superuser:
            has_object_change_permission = True
        elif not request.user.has_perm('coop_local.change_organization'):
            has_object_change_permission = False
        elif request.user.has_perm('coop_local.change_only_his_organization'):
            has_object_change_permission = request.user in obj.authors.all()
        else:
            has_object_change_permission = True
        if not has_object_change_permission and request.method == 'POST':
            opts = obj._meta
            module_name = opts.module_name
            if "_continue" in request.POST:
                if "_popup" in request.REQUEST:
                    return HttpResponseRedirect(request.path + "?_popup=1")
                else:
                    return HttpResponseRedirect(request.path)
            elif "_saveasnew" in request.POST:
                return HttpResponseRedirect(reverse('admin:%s_%s_change' %
                                            (opts.app_label, module_name),
                                            args=(pk_value,),
                                            current_app=self.admin_site.name))
            elif "_addanother" in request.POST:
                return HttpResponseRedirect(reverse('admin:%s_%s_add' %
                                            (opts.app_label, module_name),
                                            current_app=self.admin_site.name))
            else:
                return HttpResponseRedirect(reverse('admin:%s_%s_changelist' %
                                            (opts.app_label, module_name),
                                            current_app=self.admin_site.name))
        extra_context['has_object_change_permission'] = has_object_change_permission
        return super(OrganizationAdmin, self).change_view(request, object_id, form_url, extra_context)

    def add_view(self, request, form_url='', extra_context={}):
        extra_context['has_object_change_permission'] = True
        return super(OrganizationAdmin, self).add_view(request, form_url, extra_context)

    def get_actions(self, request):
        """ Remove actions set by OrganizationAdmin class without removing ModelAdmin ones."""
        return super(OrganizationAdmin, self).get_actions(request)

    def save_related(self, request, form, formsets, change):
        super(OrganizationAdmin, self).save_related(request, form, formsets, change)
        if not change:
            form.instance.authors.add(request.user)
        ui = connections.all()[0].get_unified_index()
        ui.get_index(Organization).update_object(instance=form.instance)

    def save_model(self, request, obj, form, change):
        """Send an email if just validated"""
        if change and obj.status == 'V':
            if Organization.objects.get(pk=obj.pk).status == 'P':
                from ionyweb.plugin_app.plugin_contact.models import Plugin_Contact
                try:
                    sender = Plugin_Contact.objects.all()[0].email
                except IndexError:
                    sender = None
                dests = Person.objects.filter(engagements__org_admin=True, engagements__organization=obj).values_list('email', flat=True)
                site = Site.objects.get_current().domain
                subject = u"Validation de votre fiche sur la plateforme %s" % site
                context = {
                    'site': site,
                    'slug': settings.REGION_SLUG,
                    'region': settings.REGION_NAME,
                    'org': obj,
                }
                send_mixed_email(sender, list(dests), subject, 'email/org_validation', context)
        super(OrganizationAdmin, self).save_model(request, obj, form, change)

    def odt_view(self, request, pk, format):
        organization = get_object_or_404(Organization, pk=pk)
        themes = TransverseTheme.objects.all()
        client_targets = ClientTarget.objects.all()
        content_type = {
            'odt': 'application/vnd.oasis.opendocument.text',
            'doc': 'application/ms-word',
            'pdf': 'application/pdf',
        }[format]
        response = OdtTemplateResponse(request,
            'export/organization.odt', {'provider': organization, 'themes': themes,
            'client_targets': client_targets, 'content_type': content_type},
            content_type=content_type)
        response['Content-Disposition'] = 'attachment; filename=%s.%s' % (slugify(organization.title), format)
        response.render()
        return response

    def csv_view(self, request):
        domain = Site.objects.get_current().domain
        response = HttpResponse(mimetype='text/csv')
        response['Content-Disposition'] = 'attachment; filename=%s.csv' % _('organizations')
        writer = csv.writer(response, delimiter=',', quotechar='"', quoting=csv.QUOTE_ALL)
        writer.writerow([s.encode('cp1252') for s in [
            _('creation'), _('modification'), _('status'), _('transmission'),
            _('transmission_date'),  _('validation'), _('authors'),
            _('corporate name'), _('acronym'), _('is a provider'),
            _('is a customer'), _('is a network'), _('Customer type'),
            _('creation date'), _('legal status'), _('category IAE'),
            _('category ESS'), u'spécificités', _('web site'),
            _('No. SIRET'), _('brief description'), _('annual revenue'),
            _('added value'), u'mots-clés', _('transverse themes'),
            _('workforce'), _('production workforce'),
            _('supervision workforce'), _('integration workforce'),
            _('annual integration number'), _('preferred phone'),
            _('preferred email'),
            u'adresse', u'autre adresse', u'code postal', u'ville',
            u'recevoir newsletter', u'recevoir AO', u'recevoir événements', u'recevoir échanges',
            u'PASR', u'BDIS', u'id BDIS', u'URL fiche', u'URL logo']])
        for organization in Organization.objects.order_by('title'):
            row = [organization.creation.strftime('%d/%m/%Y') if organization.creation else '']
            row.append(organization.modification.strftime('%d/%m/%Y') if organization.modification else '')
            row.append(organization.get_status_display() or '')
            row.append(organization.get_transmission_display() or '')
            row.append(organization.transmission_date.strftime('%d/%m/%Y') if organization.transmission_date else '')
            row.append(organization.validation.strftime('%d/%m/%Y') if organization.validation else '')
            row.append(', '.join([unicode(a) for a in organization.authors.all()]))
            row.append(organization.title)
            row.append(organization.acronym or '')
            row.append('X' if organization.is_provider else '')
            row.append('X' if organization.is_customer else '')
            row.append('X' if organization.is_network else '')
            row.append(organization.get_customer_type_display() or '')
            row += [organization.birth.strftime('%d/%m/%Y') if organization.birth else '']
            row += [unicode(organization.legal_status) if organization.legal_status else '']
            row += [', '.join([unicode(c) for c in organization.category_iae.all()])]
            row += [', '.join([unicode(c) for c in organization.category.all()])]
            row += [', '.join([unicode(a) for a in organization.agreement_iae.all()])]
            row.append(organization.web or '')
            row.append(organization.siret)
            row.append(organization.brief_description)
            row.append(str(organization.annual_revenue) if  organization.annual_revenue is not None else '')
            row.append(organization.added_value)
            row += [', '.join([unicode(t) for t in organization.tags.all()])]
            row += [', '.join([unicode(t) for t in organization.transverse_themes.all()])]
            row.append(number_format(organization.workforce) if  organization.workforce is not None else '')
            row.append(number_format(organization.production_workforce) if  organization.production_workforce is not None else '')
            row.append(number_format(organization.supervision_workforce) if  organization.supervision_workforce is not None else '')
            row.append(number_format(organization.integration_workforce) if  organization.integration_workforce is not None else '')
            row.append(number_format(organization.annual_integration_number) if  organization.annual_integration_number is not None else '')
            row.append(organization.pref_phone.content if organization.pref_phone else '')
            row.append(organization.pref_email.content if organization.pref_email else '')
            row.append(organization.pref_address.adr1 if organization.pref_address and organization.pref_address.adr1 else '')
            row.append(organization.pref_address.adr2 if organization.pref_address and organization.pref_address.adr2 else '')
            row.append(organization.pref_address.zipcode if organization.pref_address and organization.pref_address.zipcode else '')
            row.append(organization.pref_address.city if organization.pref_address and organization.pref_address.city else '')
            row.append('X' if organization.newsletter_subscription else '')
            row.append('X' if organization.calls_subscription else '')
            row.append(organization.events_subscription.label if organization.events_subscription else '')
            row.append('X' if organization.exchanges_subscription else '')
            row.append('X' if organization.is_pasr else '')
            row.append('X' if organization.is_bdis else '')
            row.append(str(organization.bdis_id) if organization.bdis_id else '')
            row.append('http://' + domain + organization.get_absolute_url())
            row.append(('http://' + domain + organization.logo.url) if organization.logo else '')
            writer.writerow([s.encode('cp1252', 'xmlcharrefreplace') for s in row])
        return response

    def references_csv_view(self, request):
        response = HttpResponse(mimetype='text/csv')
        response['Content-Disposition'] = 'attachment; filename=references.csv'
        writer = csv.writer(response, delimiter=',', quotechar='"', quoting=csv.QUOTE_ALL)
        writer.writerow([s.encode('cp1252') for s in [
            u'fournisseur', u'acheteur', u'prestation']])
        for reference in Reference.objects.order_by('source__title', 'target__title'):
            row = [reference.source.title, reference.target.title, reference.services]
            writer.writerow([s.encode('cp1252', 'xmlcharrefreplace') for s in row])
        return response

    def contacts_csv_view(self, request):
        response = HttpResponse(mimetype='text/csv')
        response['Content-Disposition'] = 'attachment; filename=contacts.csv'
        writer = csv.writer(response, delimiter=',', quotechar='"', quoting=csv.QUOTE_ALL)
        writer.writerow([s.encode('cp1252') for s in [
            u'organisation', u'medium', u'contenu', u'détail', u'affichage']])
        for org in Organization.objects.order_by('title'):
            for contact in org.contacts.all():
                row = [org.title, unicode(contact.contact_medium), contact.content, contact.details, contact.get_display_display()]
                writer.writerow([s.encode('cp1252', 'xmlcharrefreplace') for s in row])
        return response

    def relations_csv_view(self, request):
        response = HttpResponse(mimetype='text/csv')
        response['Content-Disposition'] = 'attachment; filename=relations.csv'
        writer = csv.writer(response, delimiter=',', quotechar='"', quoting=csv.QUOTE_ALL)
        writer.writerow([s.encode('cp1252') for s in [
            u'organisation source', u'type de relation', u'organisation cible']])
        for rel in Relation.objects.order_by('source__title', 'target__title'):
            row = [rel.source.title, rel.relation_type.label if rel.relation_type else '', rel.target.title]
            writer.writerow([s.encode('cp1252', 'xmlcharrefreplace') for s in row])
        return response

    def get_urls(self):
        urls = super(OrganizationAdmin, self).get_urls()
        my_urls = patterns('',
            url(r'^(?P<pk>\d+)/(?P<format>(odt|doc|pdf))/$', self.admin_site.admin_view(self.odt_view), name='organization_odt'),
            url(r'^csv/$', self.admin_site.admin_view(self.csv_view), name='organization_csv'),
            url(r'^references_csv/$', self.admin_site.admin_view(self.references_csv_view)),
            url(r'^contacts_csv/$', self.admin_site.admin_view(self.contacts_csv_view)),
            url(r'^relations_csv/$', self.admin_site.admin_view(self.relations_csv_view)),
            url(r'^activity_list/$', self.activity_list_view, name='coop_local_offer_activity_list')
        )
        return my_urls + urls

    def activity_list_view(self, request):
        activities = ActivityNomenclature.objects.all()
        return render(request, 'admin/activity_list.html', {'activities': activities, 'is_popup': True, 'filter_level': settings.ACTIVITY_NOMENCLATURE_LOOKUP_LEVEL})

    def has_change_permission(self, request, obj=None):
        return request.user.has_perm('coop_local.view_organization')

    def has_delete_permission(self, request, obj=None):
        if request.user.is_superuser:
            return True
        elif not request.user.has_perm('coop_local.delete_organization'):
            return False
        elif obj is not None and request.user.has_perm('coop_local.delete_only_his_organization'):
            return request.user in obj.authors.all()
        else:
            return True


class GuarantyAdmin(AdminImageMixin, admin.ModelAdmin):

    list_display = ('logo_list_display', 'type', 'name')
    list_display_links = ('name', )
    list_filter = ('type', )
    search_fields = ('type', 'name')

    def csv_view(self, request):
        response = HttpResponse(mimetype='text/csv')
        response['Content-Disposition'] = 'attachment; filename=%s.csv' % _('guaranties')
        writer = csv.writer(response, delimiter=',', quotechar='"', quoting=csv.QUOTE_ALL)
        writer.writerow([s.encode('cp1252') for s in [u'organisation', u'garantie']])
        for organization in Organization.objects.order_by('title'):
            for guaranty in organization.guaranties.order_by('name'):
                row = [organization.title, guaranty.name]
                writer.writerow([s.encode('cp1252', 'xmlcharrefreplace') for s in row])
        return response

    def get_urls(self):
        urls = super(GuarantyAdmin, self).get_urls()
        my_urls = patterns('',
            url(r'^csv/$', self.admin_site.admin_view(self.csv_view)),
        )
        return my_urls + urls


class PersonAdmin(BasePersonAdmin):
    inlines = [ContactInline, OrgInline]
    list_display = ('last_name', 'first_name', 'structure', 'user_link', 'my_organization_link')
    search_fields = ('last_name', 'first_name', 'user__username', 'engagements__organization__title', 'engagements__organization__acronym', 'structure')
    change_form_template = 'admin/coop_local/person/tabbed_change_form.html'

    def csv_view(self, request):
        response = HttpResponse(mimetype='text/csv')
        response['Content-Disposition'] = 'attachment; filename=personnes.csv'
        writer = csv.writer(response, delimiter=',', quotechar='"', quoting=csv.QUOTE_ALL)
        writer.writerow([s.encode('cp1252') for s in [u'organisation', u'prénom',
            u'nom', u'fonction', u'téléphone', 'courriel personnel', 'courriel organisation', u'affichage', 'fournisseur', 'acheteur', 'administrateur', 'identifiant', 'PASR', 'BDIS', 'id BDIS']])
        engagement_ct = ContentType.objects.get(app_label="coop_local", model="engagement")
        for organization in Organization.objects.order_by('title'):
            for e in organization.engagement_set.order_by('person__last_name'):
                p = e.person
                get_kwargs = {
                    'content_type': engagement_ct,
                    'object_id': e.id,
                    'contact_medium': ContactMedium.objects.get(label=u'Téléphone'),
                }
                try:
                    tel = Contact.objects.get(**get_kwargs).content
                except Contact.DoesNotExist:
                    tel = u''
                get_kwargs['contact_medium'] = ContactMedium.objects.get(label=u'Courriel')
                try:
                    email = Contact.objects.get(**get_kwargs).content
                except Contact.DoesNotExist:
                    email = u''
                row = [
                    organization.title,
                    p.first_name, p.last_name,
                    e.role.label if e.role else '',
                    tel, email,
                    organization.pref_email.content if organization.pref_email else '',
                    e.get_engagement_display_display(),
                    'X' if organization.is_provider else '',
                    'X' if organization.is_customer else '',
                    u'administrateur' if (p.user and p.user.is_superuser) else (u'administrateur restreint' if (p.user and p.user.is_staff and p.user.groups.filter(name=u'Administrateur restreint').exists()) else ''),
                    p.user.username if p.user else '',
                    'X' if organization.is_pasr else '',
                    'X' if organization.is_bdis else '',
                    str(p.bdis_id) if p.bdis_id else '',
                ]
                writer.writerow([s.encode('cp1252', 'xmlcharrefreplace') for s in row])
        return response

    def get_urls(self):
        urls = super(PersonAdmin, self).get_urls()
        my_urls = patterns('',
            url(r'^csv/$', self.admin_site.admin_view(self.csv_view)),
            url(r'^(?P<pk>\d+)/create_user/$', self.admin_site.admin_view(self.create_user), name='create_user'),
        )
        return my_urls + urls

    def create_user(self, request, pk):
        person = get_object_or_404(Person, pk=pk)
        if person.user:
            return HttpResponseRedirect(reverse('admin:coop_local_person_change', args=[pk]))
        org = person.my_organization()
        if not org:
            messages.error(request, u"L'utilisateur n'est éditeur d'aucune organisation.")
            return HttpResponseRedirect(reverse('admin:coop_local_person_change', args=[pk]))
        member = Engagement.objects.get(person=person, organization=org, org_admin=True)
        try:
            email = member.contacts.get(contact_medium__label='Courriel').content
        except Contact.DoesNotExist:
            email = None
        if not email:
            messages.error(request, u"L'utilisateur n'a pas de courriel lié à son engagement dans %s." % unicode(org))
            return HttpResponseRedirect(reverse('admin:coop_local_person_change', args=[pk]))
        username = (person.first_name.strip() + '.' + person.last_name.strip())[:30]
        username = unicodedata.normalize('NFKD', unicode(username))
        username = username.encode('ASCII', 'ignore')
        username = username.lower()
        username = username.replace(' ', '_')
        username = re.sub(r'[^a-z0-9_\.-]', '-', username)
        username = re.sub(r'[_.-]+$', '', username)
        username = username.replace('_-_', '-')
        for i in range(0, 10):
            if i == 0:
                _username = username
            else:
                _username = username + '%u' % i
            if not User.objects.filter(username=_username).exists() and not Person.objects.filter(username=_username).exists():
                username = _username
                break
        password = ''.join([random.choice(string.digits + string.letters) for i in range(0, 6)]).lower()
        user = User(
            first_name=person.first_name[:30],
            last_name=person.last_name[:30],
            email=email,
            username=username
        )
        user.set_password(password)
        user.save()
        person.user = user
        person.username = username
        person.save()
        messages.success(request, u"L'utilisateur %s mot de passe %s a été créé avec succès." % (username, password))
        return HttpResponseRedirect(reverse('admin:coop_local_person_change', args=[pk]))


class CFTActivityInline(InlineAutocompleteAdmin):
    model = CallForTenders.activity.through
    related_search_fields = {'activitynomenclature': ('path', ), }
    verbose_name = u'Secteur d\'activité'
    verbose_name_plural = u'Secteurs d\'activité'

    def get_formset(self, request, obj=None, **kwargs):
        kwargs['form'] = make_activity_form(self.admin_site, request)
        return super(CFTActivityInline, self).get_formset(request, obj, **kwargs)

    def has_change_permission(self, request, obj=None):
        return True

    def has_add_permission(self, request, obj=None):
        return True

    def has_delete_permission(self, request, obj=None):
        return True


class AreaInline(InlineAutocompleteAdmin):
    model = CallForTenders.areas.through
    related_search_fields = {'area': ('label', ), }
    verbose_name = u'Lieu d\'exécution'
    verbose_name_plural = u'Lieux d\'exécution'


class CallForTendersAdmin(FkAutocompleteAdmin):

    list_display = ('deadline_str', 'title', 'organization', 'activities', 'en_direct')
    search_fields = ('title', 'organization__title', 'organization__acronym')
    list_filter = ('en_direct', )
    related_search_fields = {
        'organization': ('title', 'acronym', ),
    }
    inlines = [CFTActivityInline, AreaInline]
    date_hierarchy = 'deadline'
    change_form_template = 'admin/coop_local/callfortenders/tabbed_change_form.html'
    fieldsets = (
        (_(u'Key info'), {
            'fields': ['title', 'organization', 'allotment', 'lot_numbers',
                       'deadline', 'clauses', 'url', 'en_direct',
                       'force_publication', 'description']}),
    )

    def deadline_str(self, obj):
        return obj.deadline.strftime('%d/%m/%Y')
    deadline_str.short_description = _('deadline')
    deadline_str.admin_order_field = 'deadline'

    def get_form(self, request, obj=None, **kwargs):
         if request.user.is_superuser:
             self.exclude = ('activity', 'areas')
         else:
             self.exclude = ('activity', 'areas', 'en_direct', 'a_la_une')
         return super(CallForTendersAdmin, self).get_form(request, obj, **kwargs)

    def csv_view(self, request):
        response = HttpResponse(mimetype='text/csv')
        response['Content-Disposition'] = 'attachment; filename=ao.csv'
        writer = csv.writer(response, delimiter=',', quotechar='"', quoting=csv.QUOTE_ALL)
        writer.writerow([s.encode('cp1252') for s in [u'titre', u'organisation',
            u'secteur d\'activité', u'localisation', u'allotement', u'numéros de lot',
            u'date limite', u'clauses', u'url', u'description']])
        for call in CallForTenders.objects.order_by('title'):
            row = [
                call.title,
                call.organization.title,
                call.activities(),
                ', '.join([area.label for area in call.areas.all()]),
                'oui' if call.allotment else 'non',
                call.lot_numbers,
                call.deadline.strftime('%d/%m/%Y %H:%M') if call.deadline else '',
                ', '.join(call.clauses),
                call.url,
                call.description,
            ]
            writer.writerow([s.encode('cp1252', 'xmlcharrefreplace') for s in row])
        return response

    def get_urls(self):
        urls = super(CallForTendersAdmin, self).get_urls()
        my_urls = patterns('',
            url(r'^csv/$', self.admin_site.admin_view(self.csv_view)),
        )
        return my_urls + urls

    def save_related(self, request, form, formsets, change):
        super(CallForTendersAdmin, self).save_related(request, form, formsets, change)
        ui = connections.all()[0].get_unified_index()
        ui.get_index(CallForTenders).update_object(instance=form.instance)


class OfferDocumentInline(DocumentInline):

    model = OfferDocument


def make_activity_form(admin_site, request):
    class ActivityForm(forms.ModelForm):
        class Meta:
            model = Offer.activity.through
        def __init__(self, *args, **kwargs):
            super(ActivityForm, self).__init__(*args, **kwargs)
            activity_rel = Offer.activity.through._meta.get_field_by_name('activitynomenclature')[0].rel
            related_modeladmin = admin_site._registry.get(activity_rel.to)
            can_change_related = bool(related_modeladmin and
                related_modeladmin.has_change_permission(request))
            can_add_related = bool(related_modeladmin and
                related_modeladmin.has_add_permission(request))
            activity_widget = ActivityWidget(activity_rel, admin_site, ActivityLookup, can_change_related=can_change_related)
            activity_widget.choices = None
            self.fields['activitynomenclature'].label = u"Secteur d'activité"
            self.fields['activitynomenclature'].widget = RelatedFieldWidgetWrapper(activity_widget, activity_rel, admin_site, can_add_related=can_add_related)
    return ActivityForm


class OActivityInline(InlineAutocompleteAdmin):
    model = Offer.activity.through
    related_search_fields = {'activitynomenclature': ('path', ), }
    verbose_name = u'Secteur d\'activité'
    verbose_name_plural = u'Secteurs d\'activité'

    def get_formset(self, request, obj=None, **kwargs):
        kwargs['form'] = make_activity_form(self.admin_site, request)
        return super(OActivityInline, self).get_formset(request, obj, **kwargs)
    
    def has_change_permission(self, request, obj=None):
        return True

    def has_add_permission(self, request, obj=None):
        return True

    def has_delete_permission(self, request, obj=None):
        return True


class OfferAreaInline(InlineAutocompleteAdmin):
    model = Offer.area.through
    related_search_fields = {'area': ('label', ), }
    verbose_name = u'Couverture géographique'
    verbose_name_plural = u'Couverture géographique'


class OfferAdmin(FkAutocompleteAdmin):

    list_display = ('provider', 'activities', 'description')
    search_fields = ('activity__label', 'provider__title', 'provider__acronym')
    related_search_fields = {
        'provider': ('title', 'acronym', ),
    }
    inlines = [OActivityInline, OfferAreaInline, OfferDocumentInline]
    exclude = ('activity', 'area')
    change_form_template = 'admin/coop_local/offer/tabbed_change_form.html'
    fieldsets = (
        (_(u'Key info'), {
            'fields': ['provider', 'description', 'targets', 'tags',
                       'technical_means', 'workforce', 'practical_modalities']}),
    )
    formfield_overrides = {models.ManyToManyField: {'widget': forms.CheckboxSelectMultiple(attrs={'class':'multiple_checkboxes'})}}

    def save_model(self, request, obj, form, change):
        super(OfferAdmin, self).save_model(request, obj, form, change)
        obj.provider.save() # Update modification date

    def save_related(self, request, form, formsets, change):
        super(OfferAdmin, self).save_related(request, form, formsets, change)
        ui = connections.all()[0].get_unified_index()
        ui.get_index(Organization).update_object(instance=form.instance.provider)

    def csv_view(self, request):
        response = HttpResponse(mimetype='text/csv')
        response['Content-Disposition'] = 'attachment; filename=offres.csv'
        writer = csv.writer(response, delimiter=',', quotechar='"', quoting=csv.QUOTE_ALL)
        writer.writerow([s.encode('cp1252') for s in [u'organisation',
            u'secteur d\'activité', u'description', u'cibles client',
            u'moyens techniques disponibles',
            u'effectif total mobilisable (ETP)',
            u'modalités pratiques', u'couverture géographique',
            u'mots-clés']])
        for offer in Offer.objects.order_by('provider__title'):
            row = [offer.provider.title]
            row.append(', '.join([unicode(a) for a in offer.activity.all()]))
            row.append(offer.description)
            row.append(', '.join([unicode(t) for t in offer.targets.all()]))
            row.append(offer.technical_means)
            row.append(number_format(offer.workforce) if  offer.workforce is not None else '')
            row.append(offer.practical_modalities)
            row.append(', '.join([unicode(a) for a in offer.area.all()]))
            row.append(', '.join([unicode(t) for t in offer.tags.all()]))
            writer.writerow([s.encode('cp1252', 'xmlcharrefreplace') for s in row])
        return response

    def get_urls(self):
        urls = super(OfferAdmin, self).get_urls()
        my_urls = patterns('',
            url(r'^csv/$', self.admin_site.admin_view(self.csv_view)),
        )
        return my_urls + urls


class EventDocumentInline(DocumentInline):

    model = EventDocument


class EventAdminForm(BaseEventAdminForm):

    description = forms.CharField(widget=AdminTinyMCE(attrs={'cols': 80, 'rows': 60}), required=False)

    class Meta:
        model = Event
        widgets = {
            'sites': chosenwidgets.ChosenSelectMultiple(),
            'category': chosenwidgets.ChosenSelectMultiple(),
            'activity': chosenwidgets.ChosenSelectMultiple(),
            'theme': forms.CheckboxSelectMultiple(),
        }


class EventAdmin(BaseEventAdmin):

    form = EventAdminForm
    inlines = [OccurrenceInline, EventDocumentInline]
    fieldsets = [['Description', {'fields': ['title', 'brief_description',
        'description', 'tags', 'category', 'calendar', 'organization',
        'person', 'location', 'activity', 'theme', 'image', 'a_la_une',
        'status',
      ]}],
    ]
    restricted_fieldsets = [['Description', {'fields': ['title', 'brief_description',
        'description', 'tags', 'category', 'calendar', 'organization',
        'person', 'location', 'activity', 'theme', 'image',
      ]}],
    ]
    list_display = ('id', 'title', 'time_str', 'status', 'a_la_une')
    list_display_links = ('title', )
    list_filter = ('status', 'a_la_une')

    class Media:
        js = ('mce_filebrowser/js/filebrowser_init.js',)

    def get_fieldsets(self, request, obj=None):
        if request.user.is_superuser:
            return super(EventAdmin, self).get_fieldsets(request, obj)
        return self.restricted_fieldsets

    def get_form(self, request, obj=None, **kwargs):
        """
        Workaround bug http://code.djangoproject.com/ticket/9360 (thanks to peritus)
        """
        return super(EventAdmin, self).get_form(request, obj, fields=flatten_fieldsets(self.get_fieldsets(request, obj)))

    def save_model(self, request, obj, form, change):
        """Send an email if just validated"""
        if change and obj.status == 'V':
            if Event.objects.get(pk=obj.pk).status != 'V':
                from ionyweb.plugin_app.plugin_contact.models import Plugin_Contact
                try:
                    sender = Plugin_Contact.objects.all()[0].email
                except IndexError:
                    sender = None
                if obj.person:
                    dests = obj.person.emails()
                else:
                    dests = []
                site = Site.objects.get_current().domain
                subject = u"Votre évènement est publié sur la plateforme %s" % site
                context = {
                    'site': site,
                    'slug': settings.REGION_SLUG,
                    'event': obj,
                }
                send_mixed_email(sender, dests, subject, 'email/event_validation', context)
        super(EventAdmin, self).save_model(request, obj, form, change)

    def save_related(self, request, form, formsets, change):
        super(EventAdmin, self).save_related(request, form, formsets, change)
        ui = connections.all()[0].get_unified_index()
        ui.get_index(Event).update_object(instance=form.instance)


class LocationAdmin(BaseLocationAdmin):

    def csv_view(self, request):
        response = HttpResponse(mimetype='text/csv')
        response['Content-Disposition'] = 'attachment; filename=lieux.csv'
        writer = csv.writer(response, delimiter=',', quotechar='"', quoting=csv.QUOTE_ALL)
        writer.writerow([s.encode('cp1252') for s in [u'organisation',
            u'libellé', u'adresse', u'complément d\'adresse',
            u'code postal', u'commune', u'type de lieu',
            u'jours et horaires d\'ouverture', u'tél.', u'fax', u'courriel']])
        for org in Organization.objects.order_by('title'):
            for loc in org.located.exclude(location__isnull=True):
                row = [org.title]
                row.append(loc.location.label or '')
                row.append(loc.location.adr1 or '')
                row.append(loc.location.adr2 or '')
                row.append(loc.location.zipcode or '')
                row.append(loc.location.city or '')
                row.append(loc.category.label if loc.category else '')
                row.append(loc.opening or '')
                tel = org.contacts.filter(contact_medium_id=1, location=loc.location)
                if tel:
                    row.append(tel[0].content)
                else:
                    row.append('')
                fax = org.contacts.filter(contact_medium_id=3, location=loc.location)
                if fax:
                    row.append(fax[0].content)
                else:
                    row.append('')
                email = org.contacts.filter(contact_medium_id=8, location=loc.location)
                if email:
                    row.append(email[0].content)
                else:
                    row.append('')
                writer.writerow([s.encode('cp1252', 'xmlcharrefreplace') for s in row])
        return response

    def get_urls(self):
        urls = super(LocationAdmin, self).get_urls()
        my_urls = patterns('',
            url(r'^csv/$', self.admin_site.admin_view(self.csv_view)),
        )
        return my_urls + urls


class NewsletterSubscriptionAdmin(admin.ModelAdmin):

    list_display = ('email', 'name', 'structure', 'active')
    search_fields = ('email', 'name', 'structure')
    list_filter = ('active', )

    def csv_view(self, request):
        emails = set()
        for s in NewsletterSubscription.objects.filter(active=True):
            emails.add(s.email)
        for org in Organization.objects.filter(newsletter_subscription=True):
            for email in org.emails():
                emails.add(email)
        response = HttpResponse(mimetype='text/csv')
        response['Content-Disposition'] = 'attachment; filename=newsletter.csv'
        writer = csv.writer(response, delimiter=',', quotechar='"', quoting=csv.QUOTE_ALL)
        for email in emails:
            writer.writerow([email])
        return response

    def get_urls(self):
        urls = super(NewsletterSubscriptionAdmin, self).get_urls()
        my_urls = patterns('',
            url(r'^csv/$', self.admin_site.admin_view(self.csv_view)),
        )
        return my_urls + urls


admin.site.unregister(Organization)
register(Guaranty, GuarantyAdmin)
register(Organization, OrganizationAdmin)
register(ClientTarget)
register(AgreementIAE)
register(Contact)
register(LegalStatus)
register(CategoryIAE)
register(DocumentType)
register(ContactMedium)
admin.site.unregister(Person)
register(Person, PersonAdmin)
register(CallForTenders, CallForTendersAdmin)
register(Offer, OfferAdmin)
admin.site.unregister(Event)
register(Event, EventAdmin)
admin.site.unregister(Location)
register(Location, LocationAdmin)
register(NewsletterSubscription, NewsletterSubscriptionAdmin)
