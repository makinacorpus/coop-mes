# -*- coding:utf-8 -*-
from django.db import models
from django.contrib.auth.models import User
from extended_choices import Choices
from django.utils.translation import ugettext_lazy as _
from django_extensions.db import fields as exfields
from django.core.validators import (BaseValidator, RegexValidator,
    MaxLengthValidator)
from django.template.defaultfilters import slugify
from mptt.models import MPTTModel, TreeForeignKey
from sorl.thumbnail import ImageField
from sorl.thumbnail import default

from coop.org.models import (BaseOrganization, BaseOrganizationCategory,
    BaseRole, BaseRelation, BaseContact, BaseEngagement)
from coop.person.models import BasePerson
from coop_geo.models import Located as BaseLocated
from unidecode import unidecode
import re
from django.contrib.gis.db.models import GeoManager
from coop_local.models.fields import MultiSelectField

 
ADMIN_THUMBS_SIZE = '60x60'


# Use Choices() !
# ETAT = ((0, 'Inconnu'),
#         (1, 'Active'),
#         (2, 'En sommeil'),
#         (3, 'En projet'),
# )

# Here you can either :
# - Customize coop models by deriving from the abstract class (BaseOrganization, Baseperson...)
# - Or add your own models, providing you add in their Meta class app_label="coop_local"


class HtmlMaxLengthValidator(BaseValidator):
    compare = lambda self, a, b: a > b
    clean = lambda self, x: len(re.sub('<[^>]*>', '', x))
    message = _('Ensure this value has at most %(limit_value)d characters (it has %(show_value)d).')
    code = 'max_length'


def normalize_text(text):
    return re.sub(r'\s+', ' ', unidecode(text).lower().strip())


class Person(BasePerson):

    bdis_id = models.IntegerField(_(u'bdis identifiant'), blank=True, null=True)

    def my_organization(self):
        engagements = self.engagements.filter(org_admin=True)
        if not engagements:
            return None
        return engagements[0].organization


class LegalStatus(models.Model):

    label = models.CharField(blank=True, max_length=100)
    slug = exfields.AutoSlugField(populate_from=('label'), overwrite=True)
    description = models.TextField(_(u'description'), blank=True)

    class Meta:
        verbose_name = _(u'legal status')
        verbose_name_plural = _(u'legal statuses')
        ordering = ['label']
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


class CategoryIAE(models.Model):

    label = models.CharField(blank=True, max_length=100)
    slug = exfields.AutoSlugField(populate_from=('label'), overwrite=True)
    description = models.TextField(_(u'description'), blank=True)

    class Meta:
        verbose_name = _(u'category IAE')
        verbose_name_plural = _(u'categories IAE')
        ordering = ['label']
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

    def _can_modify_categoryiae(self, user):
        if user.is_authenticated():
            if user.is_superuser:
                return True
            else:
                return False

    def can_view_categoryiae(self, user):
        # TODO use global privacy permissions on objects
        return True

    def can_edit_categoryiae(self, user):
        return self._can_modify_categoryiae(user)


class DocumentType(models.Model):

    name = models.CharField(_(u'name'), blank=True, max_length=100)

    def __unicode__(self):
        return self.name

    class Meta:
        verbose_name = _(u'document type')
        verbose_name_plural = _(u'document types')
        ordering = ['name']
        app_label = 'coop_local'


class AbstractDocument(models.Model):

    name = models.CharField(_(u'name'), blank=True, max_length=100)
    description = models.TextField(_(u'description'), blank=True)
    attachment = models.FileField(_(u'attachment'), upload_to='docs', max_length=255)
    type = models.ForeignKey('DocumentType', verbose_name=_(u'type'), blank=True, null=True)

    class Meta:
        abstract = True
        verbose_name = _(u'associated document')
        verbose_name_plural = _(u'associated documents')
        ordering = ['name']
        app_label = 'coop_local'


class Document(AbstractDocument):

    organization = models.ForeignKey('Organization')


class OfferDocument(AbstractDocument):

    offer = models.ForeignKey('Offer')


class OrganizationCategory(BaseOrganizationCategory):

    class Meta:
        verbose_name = _(u'category ESS')
        verbose_name_plural = _(u'categories ESS')
        ordering = ['label']
        app_label = 'coop_local'


ORGANISATION_GUARANTY_TYPES = Choices(
    ('NORME', 1, _(u'Norme')),
    ('OFFICIAL_LABEL', 2, _(u'Official label')),
    ('PRIVATE_LABEL', 3, _(u'Private label')),
    ('QUALITY', 4, _(u'Quality process')),
    ('AGREEMENT', 5, _(u'Agreement')),
)

class Guaranty(models.Model):

    type = models.IntegerField(_(u'type'), choices=ORGANISATION_GUARANTY_TYPES.CHOICES)
    name = models.CharField(_(u'name'), blank=True, max_length=100)
    description = models.TextField(_(u'description'), blank=True)
    logo = ImageField(upload_to='guaranty_logos/', null=True, blank=True)

    def __unicode__(self):
        return self.name

    def logo_list_display(self):
        try:
            if self.logo:
                thumb = default.backend.get_thumbnail(self.logo.file, ADMIN_THUMBS_SIZE)
                return '<img width="%s" src="%s" />' % (thumb.width, thumb.url)
            else:
                return _(u"No Image")
        except IOError:
            raise
            return _(u"No Image")

    logo_list_display.short_description = _(u"logo")
    logo_list_display.allow_tags = True

    class Meta:
        verbose_name = _(u'guaranty')
        verbose_name_plural = _(u'guaranties')
        ordering = ['name']
        app_label = 'coop_local'


class Relation(BaseRelation):

    pass


class Reference(Relation):

    from_year = models.IntegerField(_('from year'), blank=True, null=True)
    to_year = models.IntegerField(_('to year'), blank=True, null=True)
    services = models.TextField(_(u'services'), blank=True)

    class Meta:
        verbose_name = _(u'reference')
        verbose_name_plural = _(u'references')
        app_label = 'coop_local'

Reference._meta.get_field('source').verbose_name = _(u'customer')


class ClientTarget(models.Model):

    label = models.CharField(_(u'label'), max_length=100, unique=True)

    def __unicode__(self):
        return self.label

    class Meta:
        verbose_name = _(u'customer target')
        verbose_name_plural = _(u'customer targets')
        ordering = ['label']
        app_label = 'coop_local'


class AgreementIAE(models.Model):

    label = models.CharField(_(u'label'), max_length=100, unique=True)

    def __unicode__(self):
        return self.label

    class Meta:
        verbose_name = _(u'agreement IAE')
        verbose_name_plural = _(u'agreements IAE')
        ordering = ['label']
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


CUSTOMER_TYPES = Choices(
    ('PUBLIC', 1, _(u'Public')),
    ('PRIVATE', 2, _(u'Private')),
)


class Engagement(BaseEngagement):

    tel = models.CharField(_(u'tél.'), max_length=100, blank=True, null=True)
    email = models.EmailField(_(u'email'), max_length=100, blank=True, null=True)


CLAUSE_CHOICES = (('14', '14'), ('15', '15'), ('30', '30'), ('53', '53'))


class CallForTenders(models.Model):

    title = models.CharField(_(u'title'), max_length=200)
    activity = models.ManyToManyField('coop_local.ActivityNomenclature', verbose_name=_(u'activity sector'))
    organization = models.ForeignKey('Organization', verbose_name=_('organization'))
    areas = models.ManyToManyField('coop_local.Area', verbose_name=_(u'execution locations'), blank=True, null=True)
    allotment = models.BooleanField(_(u'allotment'))
    lot_numbers = models.CharField(_(u'lot numbers'), max_length=200, blank=True, help_text=u'Séparés par une virgule')
    deadline = models.DateTimeField(_(u'deadline'))
    clauses = MultiSelectField(_(u'clauses (si marché public)'), max_length=200, choices=CLAUSE_CHOICES, blank=True)
    url = models.URLField(u'URL', blank=True, null=True, max_length=250)
    en_direct = models.BooleanField(u'en direct', default=False)
    description = models.TextField(u'description synthétique', blank=True)

    objects = models.Manager()
    geo_objects = GeoManager()

    def __unicode__(self):

        return self.title

    def get_absolute_url(self):
        return '/appels-doffres/p/%u/' % self.id

    def activities(self):
        return ", ".join(self.activity.values_list('label', flat=True))

    class Meta:
        verbose_name = _(u'Call for tenders')
        verbose_name_plural = _(u'Calls for tenders')
        app_label = 'coop_local'


class Organization(BaseOrganization):

    # COMMON Organization type
    is_provider = models.BooleanField(_('is a provider'))
    is_customer = models.BooleanField(_('is a customer'))
    is_network = models.BooleanField(_('is a network'))

    # CUSTOMER
    customer_type = models.IntegerField(_('Customer type'), choices=CUSTOMER_TYPES.CHOICES, blank=True, null=True)
    testimony = models.TextField(_(u'testimony'), blank=True)

    # PROVIDER Key data
    siret = models.CharField(_(u'No. SIRET'), max_length=14, blank=True,
        validators=[RegexValidator(regex='^\d{14}$', message=_(u'No. SIRET has 14 digits'))])
    legal_status = models.ForeignKey('LegalStatus', blank=True, null=True,
        verbose_name=_(u'legal status'))
    category_iae = models.ManyToManyField('CategoryIAE', blank=True, null=True,
        verbose_name=_(u'category IAE'))
    agreement_iae = models.ManyToManyField('AgreementIAE', blank=True, null=True,
        verbose_name=_(u'specifics'))
    bdis_id = models.IntegerField(_(u'bdis identifiant'), blank=True, null=True)

    # PROVIDER Description
    brief_description = models.TextField(_(u'brief description'), blank=True)
    added_value = models.TextField(_(u'added value'), blank=True)

    # PROVIDER Economic data
    annual_revenue = models.IntegerField(_(u'annual revenue'), blank=True, null=True)
    workforce = models.DecimalField(_(u'workforce'), blank=True, null=True, max_digits=10, decimal_places=1)
    production_workforce = models.DecimalField(_(u'production workforce'), blank=True, null=True, max_digits=10, decimal_places=1)
    supervision_workforce = models.DecimalField(_(u'supervision workforce'), blank=True, null=True, max_digits=10, decimal_places=1)
    integration_workforce = models.DecimalField(_(u'integration workforce'), blank=True, null=True, max_digits=10, decimal_places=1)
    annual_integration_number = models.DecimalField(_(u'annual integration number'), blank=True, null=True, max_digits=10, decimal_places=1)

    # PROVIDER Guaranties
    guaranties = models.ManyToManyField(Guaranty, verbose_name=_(u'guaranties'), blank=True, null=True)

    # PROVIDER Management
    creation = models.DateField(_(u'creation date'), auto_now_add=True)
    modification = models.DateField(_(u'modification date'), auto_now=True)
    status = models.CharField(_(u'status'), max_length=1, choices=ORGANIZATION_STATUSES.CHOICES, default='I')
    correspondence = models.TextField(_(u'correspondence'), blank=True)
    transmission = models.IntegerField(_(u'transmission mode'), choices=TRANSMISSION_MODES.CHOICES, blank=True, null=True)
    transmission_date = models.DateField(_(u'transmission date'), blank=True, null=True)
    authors = models.ManyToManyField(User, blank=True, null=True, verbose_name=_('authors'))
    validation = models.DateField(_(u'validation date'), blank=True, null=True)

    # COMMON Search
    norm_title = models.CharField(max_length=250, unique=True)

    en_direct = models.BooleanField(u'en direct', default=False)
    a_la_une = models.BooleanField(u'à la une', default=False)

    geo_objects = GeoManager()

    def save(self, *args, **kwargs):
        self.norm_title = normalize_text(self.title)
        super(Organization, self).save(*args, **kwargs)

    def brief_description_xhtml(self):
        return self.brief_description.replace('\n', '<br/>').encode('ascii', 'xmlcharrefreplace')

    def added_value_xhtml(self):
        return self.added_value.replace('\n', '<br/>').encode('ascii', 'xmlcharrefreplace')

    def unchecked_agreements_iae(self):
        return AgreementIAE.objects.exclude(id__in=self.agreement_iae.all().values_list('id', flat=True))

    def unchecked_transverse_themes(self):
        return models.get_model('coop_local', 'TransverseTheme').objects.exclude(id__in=self.transverse_themes.all().values_list('id', flat=True))

    def references(self):
        return Reference.objects.filter(target=self)

    def source_relations(self):
        return Relation.objects.filter(source=self)

    def target_relations(self):
        return Relation.objects.filter(target=self)

    def reseaux(self):
        return Relation.objects.filter(source=self, relation_type__id=1)

    def non_reseaux(self):
        return Relation.objects.filter(source=self).exclude(relation_type__id=1)

    def part_eco(self):
        return Relation.objects.filter(source=self, relation_type__id__in=(2, 3, 5))

    def part_tech(self):
        return Relation.objects.filter(source=self, relation_type__id=4)

    def part_fin(self):
        return Relation.objects.filter(source=self, relation_type__id=5)

    def images(self):
        return self.document_set.filter(attachment__iregex=r'\.(jpe?g|gif|png)$')

    def documents(self):
        return self.document_set.exclude(attachment__iregex=r'\.(jpe?g|gif|png)$')

    def other_contacts(self):
        return self.contacts.filter(location__isnull=True)

    def engagements(self):
        return Engagement.objects.filter(organization=self)

    def offer_activities(self):
        return ", ".join(self.offer_set.values_list('activity__label', flat=True).distinct())

    def category_iae_desc(self):
        return ", ".join([cat.description or cat.label for cat in self.category_iae.all()])

    def offer_areas(self):
        areas = set()
        for offer in self.offer_set.all():
            areas |= set([unicode(a) for a in offer.area.all()])
        return ", ".join(areas)

    def future_calls(self):
        return self.callfortenders_set.order_by('deadline')

    def types(self):
        t = []
        if self.is_provider:
            t.append(u'Fournisseur')
        if self.is_customer:
            t.append(u'Acheteur %s' % self.get_customer_type_display())
        if self.is_network:
            t.append(u'Réseau')
        return u' - '.join(t)

    @classmethod
    def mine(klass, request):
        if not request.user:
            return None
        try:
            person = request.user.get_profile()
        except:
            return None
        return person.my_organization()

    def get_absolute_url(self):
        return '/annuaire/p/%u/' % self.id

    class Meta:
        ordering = ['title']
        verbose_name = _(u'Organization')
        verbose_name_plural = _(u'Organizations')
        app_label = 'coop_local'
        permissions = (
            ('view_organization', 'Can view organization'),
            ('change_only_his_organization', 'Can change only his organization'),
            ('delete_only_his_organization', 'Can delete only his organization'),
        )

Organization._meta.get_field('category').verbose_name = _(u'category ESS')
Organization._meta.get_field('title').verbose_name = _(u'corporate name')
Organization._meta.get_field('description').verbose_name = _(u'general presentation')
Organization._meta.get_field('description').validators = [HtmlMaxLengthValidator(3000)]
Organization._meta.get_field('pref_label')._choices = ((1, _(u'corporate name')), (2, _(u'acronym')))


class Offer(models.Model):

    provider = models.ForeignKey('Organization', verbose_name=_('provider'))
    activity = models.ManyToManyField('coop_local.ActivityNomenclature', verbose_name=_(u'activity sector'))
    description = models.TextField(_(u'description'), blank=True, validators = [MaxLengthValidator(400)], help_text=u'400 caractères maximum.')
    targets = models.ManyToManyField('ClientTarget', verbose_name=_(u'customer targets'))
    technical_means = models.TextField(_(u'technical means'), blank=True, validators = [MaxLengthValidator(400)], help_text=u'400 caractères maximum.')
    workforce = models.IntegerField(_(u'available workforce'), blank=True, null=True)
    practical_modalities = models.TextField(_(u'practical modalities'), blank=True, validators = [MaxLengthValidator(400)], help_text=u'400 caractères maximum.')
    area = models.ManyToManyField('coop_local.Area', verbose_name=_(u'coverage'))

    def __unicode__(self):

        return self.activities()

    def get_absolute_url(self):
        return '/annuaire/p/offre/%u/' % self.id

    def unchecked_targets(self):
        return ClientTarget.objects.exclude(id__in=self.targets.all().values_list('id', flat=True))

    def activities(self):
        return ", ".join(self.activity.all().values_list('label', flat=True))

    def image(self):
        try:
            return self.offerdocument_set.filter(attachment__iregex=r'\.(jpe?g|gif|png)$')[0].attachment
        except IndexError:
            return None

    class Meta:
        verbose_name = _(u'Offer')
        verbose_name_plural = _(u'Offers')
        app_label = 'coop_local'


class Role(BaseRole):

    class Meta:
        verbose_name = _('Role')
        verbose_name_plural = _('Roles')
        ordering = ['label']
        app_label = 'coop_local'

# Slugifying method is specified to avoid accents in final slug
# See http://packages.python.org/django-autoslug/settings.html 
# for slugify method order in Django AutoSlugField
Role._meta.get_field('slug').slugify = slugify


class Located(BaseLocated):

    opening = models.CharField(_(u'opening days and hours'), blank=True, max_length=200)

    def map_id(self):
        return 'located%u' % self.id

    class Meta:
        verbose_name = _(u'Located item')
        verbose_name_plural = _(u'Located items')
        app_label = 'coop_local'


class Contact(BaseContact):

    location = models.ForeignKey('Location', verbose_name=_(u'location'),
                   blank=True, null=True, on_delete=models.SET_NULL)

    class Meta:
        ordering = ['category']
        verbose_name = _(u'Contact')
        verbose_name_plural = _(u'Contacts')
        app_label = 'coop_local'


# WORKAROUND to fix problem with model inheritance and django-coop post delete signal
from django.db.models.signals import post_delete
from coop.signals import post_delete_callback
post_delete.disconnect(receiver=post_delete_callback)
