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
from coop.utils.autocomplete_admin import (FkAutocompleteAdmin,
    InlineAutocompleteAdmin, SelectableAdminMixin,
    AutoComboboxSelectEditWidget, AutoCompleteSelectEditWidget, register)

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
        if 'pks' in request.GET:
            if request.GET['pks']:
                pks = request.GET['pks'].split(',')
                results = results.filter(pk__in=pks)
            else:
                results = results.none()
        return results


class MediumLookup(ModelLookup):
    model = ContactMedium
    search_fields = ('label__icontains', )


class ActivityLookup(ModelLookup):
    model = ActivityNomenclature
    search_fields = ('path__icontains', )
    filters = {'level': 2}


registry.register(LocationLookup)
registry.register(MediumLookup)
registry.register(ActivityLookup)


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


class ActivityWidget(AutoCompleteSelectEditWidget):

    def render(self, name, value, attrs=None):
        markup = super(ActivityWidget, self).render(name, value, attrs)
        related_url = '/admin/coop_local/provider/activity_list/'
        related_url = reverse('admin:coop_local_offer_activity_list', current_app=self.admin_site.name)
        markup += u'&nbsp;<a href="%s" class="activity-lookup" id="lookup_id_%s" onclick="return showActivityLookupPopup(this);">' % (related_url, name)
        markup += u'<img src="%s" width="16" height="16"></a>' % static('admin/img/selector-search.gif')
        return mark_safe(markup)


def make_offer_form(admin_site, request):
    class OfferAdminForm(forms.ModelForm):
        class Meta:
            model = get_model('coop_local', 'Offer')
        def __init__(self, *args, **kwargs):
            super(OfferAdminForm, self).__init__(*args, **kwargs)
            activity_rel = Offer._meta.get_field_by_name('activity')[0].rel
            related_modeladmin = admin_site._registry.get(activity_rel.to)
            can_change_related = bool(related_modeladmin and
                related_modeladmin.has_change_permission(request))
            can_add_related = bool(related_modeladmin and
                related_modeladmin.has_add_permission(request))
            activity_widget = ActivityWidget(activity_rel, admin_site, ActivityLookup, can_change_related=can_change_related)
            activity_widget.choices = None
            self.fields['activity'].widget = RelatedFieldWidgetWrapper(activity_widget, activity_rel, admin_site, can_add_related=can_add_related)
            targets_rel = Offer._meta.get_field_by_name('targets')[0].rel
            targets_widget = forms.CheckboxSelectMultiple(attrs={'class': 'multiple_checkboxes'}, choices=self.fields['targets'].choices)
            self.fields['targets'].widget = RelatedFieldWidgetWrapper(targets_widget, targets_rel, admin_site, can_add_related=False)
    return OfferAdminForm


class OfferInline(SelectableAdminMixin, admin.StackedInline):

    model = Offer
    verbose_name = _(u'offer')
    verbose_name_plural = _(u'offers')
    formfield_overrides = {models.ManyToManyField: {'widget': forms.CheckboxSelectMultiple(attrs={'class':'multiple_checkboxes'})}}

    def get_formset(self, request, obj=None, **kwargs):
        return forms.models.inlineformset_factory(Provider, Offer, form=make_offer_form(self.admin_site, request), extra=1)

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

        for field_name in ('workforce', 'production_workforce', 'supervision_workforce',
            'integration_workforce', 'annual_integration_number'):
            self.fields[field_name].localize = True

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

    def change_view(self, request, object_id, form_url='', extra_context={}):
        obj = self.get_object(request, unquote(object_id))
        if request.user.has_perm('coop_local.change_provider'):
            has_object_change_permission = True
        elif request.user.has_perm('coop_local.change_its_provider'):
            has_object_change_permission = request.user in obj.authors.all()
        else:
            has_object_change_permission = False
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
        return super(ProviderAdmin, self).change_view(request, object_id, form_url, extra_context)

    def add_view(self, request, form_url='', extra_context={}):
        extra_context['has_object_change_permission'] = True
        return super(ProviderAdmin, self).add_view(request, form_url, extra_context)

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
            url(r'^activity_list/$', self.activity_list_view, name='coop_local_offer_activity_list')
        )
        return my_urls + urls

    def activity_list_view(self, request):
        activities = ActivityNomenclature.objects.all()
        return render(request, 'admin/activity_list.html', {'activities': activities, 'is_popup': True})

    def has_change_permission(self, request, obj=None):
        return request.user.has_perm('coop_local.view_provider')

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
