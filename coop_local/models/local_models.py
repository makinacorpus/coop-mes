# -*- coding:utf-8 -*-
from django.db import models
from extended_choices import Choices
from coop.org.models import BaseOrganization, BaseOrganizationCategory
from django.utils.translation import ugettext_lazy as _
from django_extensions.db import fields as exfields
from django.core.validators import RegexValidator

# Use Choices() !
# ETAT = ((0, 'Inconnu'),
#         (1, 'Active'),
#         (2, 'En sommeil'),
#         (3, 'En projet'),
# )

# Here you can either :
# - Customize coop models by deriving from the abstract class (BaseOrganization, Baseperson...)
# - Or add your own models, providing you add in their Meta class app_label="coop_local"

class LegalStatus(models.Model):

    label = models.CharField(blank=True, max_length=100)
    slug = exfields.AutoSlugField(populate_from=('label'), overwrite=True)
    description = models.TextField(_(u'description'), blank=True)

    class Meta:
        verbose_name = _(u'legal status')
        verbose_name_plural = _(u'legal statuses')
        app_label = 'coop_local'

    def __unicode__(self):
        return self.label

    #@models.permalink
    def get_absolute_url(self):
        return reverse('org_legalstatus_detail', args=[self.slug])

    def get_edit_url(self):
        return reverse('org_legalstatus_edit', args=[self.slug])

    def get_cancel_url(self):
        return reverse('org_legalstatus_edit_cancel', args=[self.slug])

    def _can_modify_legalstatus(self, user):
        if user.is_authenticated():
            if user.is_superuser:
                return True
            else:
                return False

    def can_view_legalstatus(self, user):
        # TODO use global privacy permissions on objects
        return True

    def can_edit_legalstatus(self, user):
        return self._can_modify_legalstatus(user)


class OrganizationCategoryIAE(models.Model):

    label = models.CharField(blank=True, max_length=100)
    slug = exfields.AutoSlugField(populate_from=('label'), overwrite=True)
    description = models.TextField(_(u'description'), blank=True)

    class Meta:
        verbose_name = _(u'organization category IAE')
        verbose_name_plural = _(u'organization categories IAE')
        app_label = 'coop_local'

    def __unicode__(self):
        return self.label

    #@models.permalink
    def get_absolute_url(self):
        return reverse('org_categoryiae_detail', args=[self.slug])

    def get_edit_url(self):
        return reverse('org_categoryiae_edit', args=[self.slug])

    def get_cancel_url(self):
        return reverse('org_categoryiae_edit_cancel', args=[self.slug])

    def _can_modify_organizationcategoryiae(self, user):
        if user.is_authenticated():
            if user.is_superuser:
                return True
            else:
                return False

    def can_view_organizationcategoryiae(self, user):
        # TODO use global privacy permissions on objects
        return True

    def can_edit_organizationcategoryiae(self, user):
        return self._can_modify_organizationcategoryiae(user)


class OrganizationCategory(BaseOrganizationCategory):

    class Meta:
        verbose_name = _(u'organization category ESS')
        verbose_name_plural = _(u'organization categories ESS')
        app_label = 'coop_local'


class Organization(BaseOrganization):

    # Key data
    siret = models.CharField(_(u'No. SIRET'), max_length=14, blank=True,
        validators=[RegexValidator(regex='^\d{14}$', message=_(u'No. SIRET has 14 digits'))])
    legal_status = models.ForeignKey('LegalStatus', blank=True, null=True,
        verbose_name=_(u'legal status'))
    category_iae = models.ManyToManyField('OrganizationCategoryIAE', blank=True, null=True,
        verbose_name=_(u'organization category IAE'))
    agreement_iae = models.BooleanField(_(u'agreement IAE'))

    # Description
    brief_description = models.TextField(_(u'brief description'), blank=True)
    added_value = models.TextField(_(u'added value'), blank=True)

    # Economic data
    annual_revenue = models.IntegerField(_(u'annual revenue'), blank=True, null=True)
    workforce = models.IntegerField(_(u'workforce'), blank=True, null=True)
    production_workforce = models.IntegerField(_(u'production workforce'), blank=True, null=True)
    supervision_workforce = models.IntegerField(_(u'supervision workforce'), blank=True, null=True)
    integration_workforce = models.IntegerField(_(u'integration workforce'), blank=True, null=True)
    annual_integration_number = models.IntegerField(_(u'annual integration number'), blank=True, null=True)

    class Meta:
        ordering = ['title']
        verbose_name = _(u'Provider')
        verbose_name_plural = _(u'Providers')
        app_label = 'coop_local'

Organization._meta.get_field('title').verbose_name = _(u'corporate name')
Organization._meta.get_field('category').verbose_name = _(u'organization category ESS')
Organization._meta.get_field('description').verbose_name = _(u'general presentation')
Organization._meta.get_field('description').max_length = 3000
