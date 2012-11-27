# -*- coding:utf-8 -*-
from django.db import models
from extended_choices import Choices
from coop.org.models import BaseOrganization, BaseOrganizationCategory
from django.utils.translation import ugettext_lazy as _
from django_extensions.db import fields as exfields
from django.core.validators import RegexValidator, MaxLengthValidator
from mptt.models import MPTTModel, TreeForeignKey
from coop_geo.models import AreaLink
from django.contrib.contenttypes import generic


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


class OrganizationDocument(models.Model):

    name = models.CharField(_(u'name'), blank=True, max_length=100)
    description = models.TextField(_(u'description'), blank=True)
    attachment = models.FileField(_(u'attachment'), upload_to='docs', max_length=255)
    organization = models.ForeignKey('Organization')

    class Meta:
        verbose_name = _(u'associated document')
        verbose_name_plural = _(u'associated documents')
        app_label = 'coop_local'


class OrganizationCategory(BaseOrganizationCategory):

    class Meta:
        verbose_name = _(u'organization category ESS')
        verbose_name_plural = _(u'organization categories ESS')
        app_label = 'coop_local'


ORGANISATION_GUARANTY_TYPES = Choices(
    ('LABEL', 1, _(u'Label')),
    ('AGREEMENT', 2, _(u'Agreement')),
    ('STANDARD', 3, _(u'Technical Standard')),
    ('PROCESS', 4, _(u'Process')),
    ('CERTIFICATION', 5, _(u'Certification')),
)


class OrganizationGuaranty(models.Model):

    type = models.IntegerField(_(u'type'), choices=ORGANISATION_GUARANTY_TYPES.CHOICES)
    name = models.CharField(_(u'name'), blank=True, max_length=100)
    description = models.TextField(_(u'description'), blank=True)

    def __unicode__(self):
        return ORGANISATION_GUARANTY_TYPES.CHOICES_DICT[self.type] + ' ' + self.name

    class Meta:
        verbose_name = _(u'guaranty')
        verbose_name_plural = _(u'guaranties')
        app_label = 'coop_local'


class OrganizationReference(models.Model):

    client_name = models.CharField(_(u'client name'), max_length=100)
    period = models.IntegerField(_('period'), blank=True, null=True)
    services = models.TextField(_(u'services'), blank=True)
    organization = models.ForeignKey('Organization')

    class Meta:
        verbose_name = _(u'reference')
        verbose_name_plural = _(u'references')
        app_label = 'coop_local'


class ActivityNomenclatureAvise(models.Model):

    label = models.CharField(_(u'label'), max_length=100, unique=True)

    def __unicode__(self):
        return self.label

    class Meta:
        verbose_name = _(u'AVISE activity nomenclature item')
        verbose_name_plural = _(u'AVISE activity nomenclature')
        app_label = 'coop_local'
        ordering = ['label']


class ActivityNomenclature(MPTTModel):

    label = models.CharField(_(u'label'), max_length=100)
    path = models.CharField(_(u'label'), max_length=306, editable=False) # denormalized field
    parent = TreeForeignKey('self', verbose_name=_(u'parent'), null=True, blank=True, related_name='children')
    avise = models.ForeignKey('ActivityNomenclatureAvise', verbose_name=_(u'AVISE equivalent'), blank=True, null=True)

    def __unicode__(self):
        return self.path

    def save(self, *args, **kwargs):
        labels = [item.label for item in self.parent.get_ancestors(include_self=True)] if self.parent else []
        labels.append(self.label)
        self.path = u' / '.join(labels)
        super(ActivityNomenclature, self).save(*args, **kwargs)

    class Meta:
        unique_together = ('label', 'parent')
        verbose_name = _(u'activity nomenclature item')
        verbose_name_plural = _(u'activity nomenclature')
        app_label = 'coop_local'
        ordering = ['tree_id', 'lft'] # needed for TreeEditor


class ClientTarget(models.Model):

    label = models.CharField(_(u'label'), max_length=100, unique=True)

    def __unicode__(self):
        return self.label

    class Meta:
        verbose_name = _(u'client target')
        verbose_name_plural = _(u'client targets')
        app_label = 'coop_local'


class TransverseTheme(models.Model):

    name = models.CharField(_(u'name'), blank=True, max_length=100)
    description = models.TextField(_(u'description'), blank=True)

    def __unicode__(self):
        return self.name

    class Meta:
        verbose_name = _(u'transverse theme')
        verbose_name_plural = _(u'transverse themes')
        app_label = 'coop_local'


ORGANIZATION_STATUSES = Choices(
    ('PROPOSED', 'P', _(u'Proposed')),
    ('VALIDATED', 'V', _(u'Validated')),
    ('TRANSMITTED', 'T', _(u'Transmitted for validation')),
    ('INCOMPLETE', 'I', _(u'Incomplete')),
)


TRANSMISSION_MODES = Choices(
    ('ONLINE', 1, _(u'Keboarded online')),
    ('ADMINISTRATION', 2, _(u'Administration')),
    ('IMPORT', 3, _('Import')),
)

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
    transverse_themes = models.ManyToManyField('TransverseTheme', verbose_name=_(u'transverse themes'), blank=True, null=True)

    # Economic data
    annual_revenue = models.IntegerField(_(u'annual revenue'), blank=True, null=True)
    workforce = models.IntegerField(_(u'workforce'), blank=True, null=True)
    production_workforce = models.IntegerField(_(u'production workforce'), blank=True, null=True)
    supervision_workforce = models.IntegerField(_(u'supervision workforce'), blank=True, null=True)
    integration_workforce = models.IntegerField(_(u'integration workforce'), blank=True, null=True)
    annual_integration_number = models.IntegerField(_(u'annual integration number'), blank=True, null=True)

    # Guaranties
    guaranties = models.ManyToManyField(OrganizationGuaranty, verbose_name=_(u'guaranties'), blank=True, null=True)

    # Management
    creation = models.DateField(_(u'creation date'), auto_now_add=True)
    modification = models.DateField(_(u'modification date'), auto_now=True)
    status = models.CharField(_(u'status'), max_length=1, choices=ORGANIZATION_STATUSES.CHOICES, blank=True)
    correspondence = models.TextField(_(u'correspondence'), blank=True)
    transmission = models.IntegerField(_(u'transmission mode'), choices=TRANSMISSION_MODES.CHOICES, blank=True, null=True)
    author = models.CharField(_(u'author'), max_length=100, blank=True)
    validation = models.DateField(_(u'validation date'), blank=True, null=True)

    class Meta:
        ordering = ['title']
        verbose_name = _(u'Provider')
        verbose_name_plural = _(u'Providers')
        app_label = 'coop_local'

Organization._meta.get_field('title').verbose_name = _(u'corporate name')
Organization._meta.get_field('category').verbose_name = _(u'organization category ESS')
Organization._meta.get_field('description').verbose_name = _(u'general presentation')
Organization._meta.get_field('description').validators = [MaxLengthValidator(3000)]
Organization._meta.get_field('pref_label')._choices = ((1, _(u'corporate name')), (2, _(u'acronym')))


class Offer(models.Model):

    activity = models.ForeignKey('ActivityNomenclature', verbose_name=_(u'activity sector'))
    description = models.TextField(_(u'description'), blank=True, validators = [MaxLengthValidator(400)])
    target = models.ForeignKey('ClientTarget', verbose_name=_(u'client target'))
    valuation = models.TextField(_(u'product or service valuation'), blank=True)
    technical_means = models.TextField(_(u'technical means'), blank=True, validators = [MaxLengthValidator(400)])
    workforce = models.IntegerField(_(u'available workforce'), blank=True, null=True)
    practical_modalities = models.TextField(_(u'practical modalities'), blank=True, validators = [MaxLengthValidator(400)])
    #framed = generic.GenericRelation('AreaLink')
    provider = models.ForeignKey('Organization', verbose_name=_('provider'))

    def __unicode__(self):

        return unicode(self.activity)

    class Meta:
        verbose_name = _(u'Offer')
        verbose_name_plural = _(u'Offers')
        app_label = 'coop_local'
