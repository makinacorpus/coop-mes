# -*- coding:utf-8 -*-
from django import forms
from django.contrib import admin
from django.core.exceptions import ImproperlyConfigured
from coop.org.admin import OrganizationAdmin, OrganizationAdminForm, RelationInline, LocatedInline, ContactInline, EngagementInline
from coop_local.models import (LegalStatus, OrganizationCategoryIAE, OrganizationDocument,
    OrganizationGuaranty, OrganizationReference, ActivityNomenclature, ActivityNomenclatureAvise, Offer)
from django.db.models.loading import get_model
from chosen import widgets as chosenwidgets
from django.utils.translation import ugettext as _
from mptt.admin import MPTTModelAdmin
from coop.utils.autocomplete_admin import FkAutocompleteAdmin, InlineAutocompleteAdmin
from django.db import models

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


class DocumentInline(admin.TabularInline):

    model = OrganizationDocument
    verbose_name = _(u'document')
    verbose_name_plural = _(u'documents')
    extra = 1


class ReferenceInline(admin.TabularInline):

    model = OrganizationReference
    verbose_name = _(u'reference')
    verbose_name_plural = _(u'references')
    extra = 1


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


class MyOrganizationAdminForm(OrganizationAdminForm):

    class Meta:
        model = get_model('coop_local', 'Organization')
        widgets = {
            'category': chosenwidgets.ChosenSelectMultiple(),
            'category_iae': chosenwidgets.ChosenSelectMultiple(),
        }

    def __init__(self, *args, **kwargs):
        super(MyOrganizationAdminForm, self).__init__(*args, **kwargs)
        self.fields['category_iae'].help_text = None


class MyOrganizationAdmin(OrganizationAdmin):

    form = MyOrganizationAdminForm
    readonly_fields = ['creation', 'modification']
    fieldsets = (
        (_(u'Key info'), {
            'fields': ['title', ('acronym', 'pref_label'), 'logo', ('birth', 'active',),
                       'legal_status', 'category', 'category_iae', 'agreement_iae',
                       'web', 'siret']
            }),
        (_(u'Economic info'), {
            'fields': [('annual_revenue', 'workforce'), ('production_workforce', 'supervision_workforce'),
                       ('integration_workforce', 'annual_integration_number')]
            }),
        (_(u'Description'), {
            'fields': ['brief_description', 'description', 'added_value', 'tags']
            }),
        (_(u'Guaranties'), {
            'fields': ['guaranties']
            }),
        (_(u'Management'), {
            'fields': ['creation', 'modification', 'status', 'correspondence', 'transmission',
                       'author', 'validation']
            }),
        (_(u'Preferences'), {
            'fields': ['pref_email', 'pref_phone', 'pref_address', 'notes',]
        })
    )
    inlines = [DocumentInline, ReferenceInline, RelationInline, LocatedInline, ContactInline, EngagementInline, OfferInline]

MyOrganizationAdmin.formfield_overrides[models.ManyToManyField] = {'widget': forms.CheckboxSelectMultiple}

admin.site.unregister(Organization)
admin.site.register(Organization, MyOrganizationAdmin)

admin.site.register(LegalStatus)
admin.site.register(OrganizationCategoryIAE)
admin.site.register(OrganizationGuaranty)


class ActivityNomenclatureAdmin(MPTTModelAdmin, FkAutocompleteAdmin):

    related_search_fields = {'avise': ('label',), 'parent': ('path',)}
    mptt_indent_field = 'label'
    mptt_level_indent = 50
    list_display = ('label', )

admin.site.register(ActivityNomenclature, ActivityNomenclatureAdmin)
admin.site.register(ActivityNomenclatureAvise)
admin.site.register(ClientTarget)
