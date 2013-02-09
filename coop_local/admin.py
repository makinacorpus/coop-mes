# -*- coding:utf-8 -*-
from django import forms
from django.contrib import admin
from django.core.exceptions import ImproperlyConfigured
from django.db.models.loading import get_model
from django.contrib.contenttypes.models import ContentType
from django.db import models
from django.db.models import Q
from django.utils.translation import ugettext as _
from django.contrib.contenttypes.generic import generic_inlineformset_factory
from django.conf.urls.defaults import patterns, url
from django.shortcuts import get_object_or_404
from django.http import HttpResponse
from django.template.defaultfilters import slugify
from django.contrib.admin.widgets import RelatedFieldWidgetWrapper

from chosen import widgets as chosenwidgets
from selectable.base import ModelLookup
from selectable.registry import registry
from mptt.admin import MPTTModelAdmin
from sorl.thumbnail.admin import AdminImageMixin
from djappypod.response import OdtTemplateResponse
import csv

from coop.org.admin import (OrganizationAdmin, OrganizationAdminForm, RelationInline,
    LocatedInline, ContactInline as BaseContactInline, EngagementInline as BaseEngagementInline,
    OrgInline)
from coop.person.admin import PersonAdmin as BasePersonAdmin
from coop.utils.autocomplete_admin import FkAutocompleteAdmin, InlineAutocompleteAdmin, AutoComboboxSelectEditWidget, register

from coop_geo.models import Location
from coop_local.models.local_models import normalize_text
from coop_local.models import (LegalStatus, CategoryIAE, Document, Guaranty, Reference, ActivityNomenclature,
    ActivityNomenclatureAvise, Offer, TransverseTheme, Client, Network, DocumentType, AgreementIAE,
    Location, Engagement, ContactMedium)

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
        provider_id = request.GET.get('provider')
        if provider_id:
            provider = Provider.objects.get(id=provider_id)
            print provider
            print provider.located.all()
            results = results.filter(id__in=provider.located.all().values_list('location_id', flat=True))
        return results


class MediumLookup(ModelLookup):
    model = ContactMedium
    search_fields = ('label', )


registry.register(LocationLookup)
registry.register(MediumLookup)


def make_contact_form(provider, admin_site):
    class ContactForm(forms.ModelForm):
        def __init__(self, *args, **kwargs):
            super(ContactForm, self).__init__(*args, **kwargs)
            location_rel = Contact._meta.get_field_by_name('location')[0].rel
            medium_rel = Contact._meta.get_field_by_name('contact_medium')[0].rel
            self.fields['location'].widget = AutoComboboxSelectEditWidget(location_rel, admin_site, LocationLookup)
            if provider:
                self.fields['location'].widget.update_query_parameters({'provider': provider.pk})
            self.fields['location'].widget.choices = None
            self.fields['location'].widget = RelatedFieldWidgetWrapper(self.fields['location'].widget, location_rel, admin_site, True)
            self.fields['contact_medium'].widget = RelatedFieldWidgetWrapper(self.fields['contact_medium'].widget, medium_rel, admin_site, True)
        class Meta:
            model = Contact
            fields = ('contact_medium', 'content', 'details', 'location', 'display')
    return ContactForm


class ContactInline(BaseContactInline):
    fields = ('contact_medium', 'content', 'details', 'location', 'display')
    def get_formset(self, request, obj=None, **kwargs):
        return generic_inlineformset_factory(Contact, form=make_contact_form(obj, self.admin_site))


class EngagementInline(BaseEngagementInline):
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


class ReferenceInline(InlineAutocompleteAdmin):

    model = Reference
    verbose_name = _(u'reference')
    verbose_name_plural = _(u'references')
    fk_name = 'target'
    readonly_fields = ('created',)
    fields = ('source', 'from_year', 'to_year', 'services', 'created')
    related_search_fields = {'source': ('title', 'subtitle', 'acronym',), }
    extra = 1

    def queryset(self, request):
        queryset = super(ReferenceInline, self).queryset(request)
        return queryset.filter(relation_type_id=2)


class OfferAdminForm(forms.ModelForm):

    class Meta:
        model = get_model('coop_local', 'Offer')

    def __init__(self, *args, **kwargs):
        super(OfferAdminForm, self).__init__(*args, **kwargs)
        self.fields['activity'].help_text = None


class OfferInline(admin.StackedInline, InlineAutocompleteAdmin):

    model = Offer
    form = OfferAdminForm
    verbose_name = _(u'offer')
    verbose_name_plural = _(u'offers')
    extra = 1
    related_search_fields = {'activity': ('path',)}
    formfield_overrides = {models.ManyToManyField: {'widget': forms.CheckboxSelectMultiple(attrs={'class':'multiple_checkboxes'})}}


class ProviderAdminForm(OrganizationAdminForm):

    class Meta:
        model = get_model('coop_local', 'Provider')
        widgets = {
            'category': chosenwidgets.ChosenSelectMultiple(),
            'category_iae': chosenwidgets.ChosenSelectMultiple(),
            'guaranties': chosenwidgets.ChosenSelectMultiple(),
            'authors': chosenwidgets.ChosenSelectMultiple(),
        }

    def __init__(self, *args, **kwargs):

        # We do not call just super class, but super super class, because of redefinition of all parent logic
        super(OrganizationAdminForm, self).__init__(*args, **kwargs)
        self.fields['category_iae'].help_text = None

        engagements = self.instance.engagement_set.all()
        members_id = engagements.values_list('person_id', flat=True)
        org_contacts = Contact.objects.filter(
            Q(content_type=ContentType.objects.get(model='provider'), object_id=self.instance.id)
          | Q(content_type=ContentType.objects.get(model='person'), object_id__in=members_id)
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

    def clean_title(self):
        title = self.cleaned_data['title']
        norm_title = normalize_text(title)
        if Provider.objects.filter(norm_title=norm_title).exclude(pk=self.instance.pk).exists():
            raise forms.ValidationError(_('A provider with this title already exists.'))
        return title


class ProviderAdmin(OrganizationAdmin):

    form = ProviderAdminForm
    list_display = ['logo_list_display', 'title', 'acronym', 'active', 'has_description', 'has_location']
    list_display_links = ['title', 'acronym']
    readonly_fields = ['creation', 'modification']
    list_filter = ['active', 'agreement_iae', 'authors']
    fieldsets = (
        (_(u'Key info'), {
            'fields': ['title', ('acronym', 'pref_label'), 'logo', ('birth', 'active',),
                       'legal_status', 'category', 'category_iae', 'agreement_iae',
                       'web', 'siret', 'bdis_id']
            }),
        (_(u'Economic info'), {
            'fields': [('annual_revenue', 'workforce'), ('production_workforce', 'supervision_workforce'),
                       ('integration_workforce', 'annual_integration_number')]
            }),
        (_(u'Description'), {
            'fields': ['brief_description', 'description', 'added_value', 'tags', 'transverse_themes']
            }),
        (_(u'Guaranties'), {
            'fields': ['guaranties']
            }),
        (_(u'Management'), {
            'fields': ['creation', 'modification', 'status', 'correspondence', 'transmission',
                       'transmission_date', 'authors', 'validation']
            }),
        (_(u'Preferences'), {
            'fields': ['pref_email', 'pref_phone', 'pref_address', 'notes',]
        })
    )
    inlines = [DocumentInline, ReferenceInline, RelationInline, LocatedInline, ContactInline, EngagementInline, OfferInline]
    change_form_template = 'admin/coop_local/provider/tabbed_change_form.html'
    search_fields = ['norm_title', 'acronym']
    related_search_fields = {'legal_status': ('label', )}
    related_combobox = ('legal_status', )

    def changelist_view(self, request, extra_context=None):
        query_dict = request.GET.copy()
        if 'q' in query_dict:
            query_dict['q'] = normalize_text(query_dict['q'])
        request.GET = query_dict
        return super(ProviderAdmin, self).changelist_view(request, extra_context)

    def get_actions(self, request):
        """ Remove actions set by OrganizationAdmin class without removing ModelAdmin ones."""
        return super(OrganizationAdmin, self).get_actions(request)

    def save_related(self, request, form, formsets, change):
        super(ProviderAdmin, self).save_related(request, form, formsets, change)
        if not change:
            form.instance.authors.add(request.user)

    def save_formset(self, request, form, formset, change):
        if formset.model != Reference:
            return super(ProviderAdmin, self).save_formset(request, form, formset, change)
        instances = formset.save(commit=False)
        for instance in instances:
            instance.relation_type_id = 2
            try:
                instance.target.client
            except Client.DoesNotExist:
                client = Client(organization_ptr_id=instance.target.pk)
                client.__dict__.update(instance.target.__dict__)
                client.save()
            instance.save()

    def odt_view(self, request, pk, format):
        provider = get_object_or_404(Provider, pk=pk)
        themes = TransverseTheme.objects.all()
        client_targets = ClientTarget.objects.all()
        content_type = {
            'odt': 'application/vnd.oasis.opendocument.text',
            'doc': 'application/ms-word',
            'pdf': 'application/pdf',
        }[format]
        response = OdtTemplateResponse(request,
            'export/provider.odt', {'provider': provider, 'themes': themes,
            'client_targets': client_targets, 'content_type': content_type},
            content_type=content_type)
        response['Content-Disposition'] = 'attachment; filename=%s.%s' % (slugify(provider.title), format)
        response.render()
        return response

    def csv_view(self, request):
        response = HttpResponse(mimetype='text/csv')
        response['Content-Disposition'] = 'attachment; filename=%s.csv' % _('providers')
        writer = csv.writer(response, delimiter=',', quotechar='"', quoting=csv.QUOTE_ALL)
        writer.writerow([s.encode('cp1252') for s in [
            _('corporate name'), _('acronym'), _('Preferred label'), _('creation date'),
            _('legal status'), _('category ESS'), _('category IAE'),
            _('agreement IAE'), _('web site'), _('No. SIRET')
        ]])
        for provider in Provider.objects.order_by('title'):
            row  = [provider.title, provider.acronym, provider.get_pref_label_display()]
            row += [provider.birth.strftime('%d/%m/%Y') if provider.birth else '']
            row += [unicode(provider.legal_status) if provider.legal_status else '']
            row += [', '.join([unicode(c) for c in provider.category.all()])]
            row += [', '.join([unicode(c) for c in provider.category_iae.all()])]
            row += [', '.join([unicode(a) for a in provider.agreement_iae.all()])]
            row += [provider.web, provider.siret]
            writer.writerow([s.encode('cp1252') for s in row])
        return response

    def get_urls(self):
        urls = super(ProviderAdmin, self).get_urls()
        my_urls = patterns('',
            url(r'^(?P<pk>\d+)/(?P<format>(odt|doc|pdf))/$', self.admin_site.admin_view(self.odt_view), name='provider_odt'),
            url(r'^csv/$', self.admin_site.admin_view(self.csv_view), name='providers_csv'),
        )
        return my_urls + urls

ProviderAdmin.formfield_overrides[models.ManyToManyField] = {'widget': forms.CheckboxSelectMultiple}


class GuarantyAdmin(AdminImageMixin, admin.ModelAdmin):

    list_display = ('logo_list_display', 'type', 'name')
    list_display_links = ('name', )
    list_filter = ('type', )
    search_fields = ('type', 'name')


class ActivityNomenclatureAdmin(MPTTModelAdmin, FkAutocompleteAdmin):

    related_search_fields = {'avise': ('label',), 'parent': ('path',)}
    mptt_indent_field = 'label'
    mptt_level_indent = 50
    list_display = ('label', )


class PersonAdmin(BasePersonAdmin):
    inlines = [ContactInline, OrgInline]


admin.site.unregister(Organization)
register(Guaranty, GuarantyAdmin)
register(Provider, ProviderAdmin)
register(ActivityNomenclature, ActivityNomenclatureAdmin)
register(ActivityNomenclatureAvise)
register(ClientTarget)
register(TransverseTheme)
register(Organization, OrganizationAdmin)
register(Client, OrganizationAdmin)
register(Network, OrganizationAdmin)
register(AgreementIAE)
register(Contact)
register(LegalStatus)
register(CategoryIAE)
register(DocumentType)
register(ContactMedium)
admin.site.unregister(Person)
register(Person, PersonAdmin)
