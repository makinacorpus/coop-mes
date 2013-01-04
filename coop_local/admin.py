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

from chosen import widgets as chosenwidgets
from mptt.admin import MPTTModelAdmin
from sorl.thumbnail.admin import AdminImageMixin

from coop.org.admin import (OrganizationAdmin, OrganizationAdminForm, RelationInline,
    LocatedInline, ContactInline as BaseContactInline, EngagementInline)
from coop.utils.autocomplete_admin import FkAutocompleteAdmin, InlineAutocompleteAdmin

from coop_geo.models import Location
from coop_local.models import (LegalStatus, CategoryIAE, Document, Guaranty, Reference, ActivityNomenclature,
    ActivityNomenclatureAvise, Offer, TransverseTheme, Client, Network, DocumentType, AgreementIAE,
    Location)

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


def make_contact_form(organization):
    class ContactForm(forms.ModelForm):
        location = forms.ModelChoiceField(label=_(u'location'), required=False,
            queryset=organization.locations())
        class Meta:
            model = Contact
            fields = ('contact_medium', 'content', 'details', 'location', 'display')
    return ContactForm


class ContactInline(BaseContactInline):
    fields = ('contact_medium', 'content', 'details', 'location', 'display')
    def get_formset(self, request, obj=None, **kwargs):
        return generic_inlineformset_factory(Contact, form=make_contact_form(obj))


class DocumentInline(admin.TabularInline):

    model = Document
    verbose_name = _(u'document')
    verbose_name_plural = _(u'documents')
    extra = 1


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
            'legal_status': chosenwidgets.ChosenSelect(),
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
        self.fields['pref_email'].queryset = org_contacts.filter(category=8)
        self.fields['pref_phone'].queryset = org_contacts.filter(category__in=phone_categories)
        self.fields['category'].help_text = None

        member_locations_id = [m.location.id for m in
            Person.objects.filter(id__in=members_id).exclude(location=None)]  # limit SQL to location field

        self.fields['pref_address'].queryset = Location.objects.filter(
            Q(id__in=self.instance.located.all().values_list('location_id', flat=True))
          | Q(id__in=member_locations_id)
            )


class ProviderAdmin(OrganizationAdmin):

    form = ProviderAdminForm
    readonly_fields = ['creation', 'modification']
    list_filter = ['active', 'agreement_iae']
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

    def get_actions(self, request):
        """ Remove actions set by OrganizationAdmin class without removing ModelAdmin ones."""
        return super(OrganizationAdmin, self).get_actions(request)

    def save_related(self, request, form, formsets, change):
        super(ProviderAdmin, self).save_related(request, form, formsets, change)
        if not change:
            form.instance.authors.add(request.user)

    def save_formset(self, request, form, formset, change):
        instances = formset.save(commit=False)
        for instance in instances:
            if isinstance(instance, Reference):
                instance.relation_type_id = 2
                try:
                    instance.target.client
                except Client.DoesNotExist:
                    client = Client(organization_ptr_id=instance.target.pk)
                    client.__dict__.update(instance.target.__dict__)
                    client.save()
            instance.save()

ProviderAdmin.formfield_overrides[models.ManyToManyField] = {'widget': forms.CheckboxSelectMultiple}

admin.site.unregister(Organization)
admin.site.register(Provider, ProviderAdmin)

admin.site.register(LegalStatus)
admin.site.register(CategoryIAE)

class GuarantyAdmin(AdminImageMixin, admin.ModelAdmin):

    list_display = ('logo_list_display', 'type', 'name')
    list_display_links = ('name', )
    list_filter = ('type', )
    search_fields = ('type', 'name')

admin.site.register(Guaranty, GuarantyAdmin)


class ActivityNomenclatureAdmin(MPTTModelAdmin, FkAutocompleteAdmin):

    related_search_fields = {'avise': ('label',), 'parent': ('path',)}
    mptt_indent_field = 'label'
    mptt_level_indent = 50
    list_display = ('label', )

admin.site.register(ActivityNomenclature, ActivityNomenclatureAdmin)
admin.site.register(ActivityNomenclatureAvise)
admin.site.register(ClientTarget)
admin.site.register(TransverseTheme)
admin.site.register(Organization, OrganizationAdmin)
admin.site.register(Client, OrganizationAdmin)
admin.site.register(Network, OrganizationAdmin)
admin.site.register(DocumentType)
admin.site.register(AgreementIAE)
