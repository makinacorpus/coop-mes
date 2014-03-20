# -*- coding: utf-8 -*-
from django.db import models
from django.utils.translation import ugettext_lazy as _
from ionyweb.page.models import AbstractPageApp
from coop_local.models import Area, AgreementIAE, Organization, Tag


class IFrame(models.Model):
    title = models.CharField(u"Titre", max_length=200)
    domain = models.URLField(u"Domaine", help_text=u"Nom de domaine du site qui contiendra cette IFrame (nécessaire pour des raisons de sécurité)")
    area = models.ForeignKey(Area, null=True, blank=True,
                             verbose_name=u"Zone")
    network = models.ForeignKey(Organization, null=True, blank=True,
                                limit_choices_to = {'is_network': True},
                                verbose_name=u"Réseau")
    agreement_iae = models.ForeignKey(AgreementIAE, null=True, blank=True,
                                      verbose_name=u"Spécificité")
    tag= models.ForeignKey(Tag, null=True, blank=True,
                           verbose_name=u"Mot-clé")
    top_content = models.TextField(u'Contenu du haut', blank=True)

    def __unicode__(self):
        return self.title


class PageApp_Iframe(AbstractPageApp):

    # Define your fields here
    bdis = models.BooleanField(u'Afficher la BDIS plutôt que la PASR')
    right_content = models.TextField(u'Contenu de droite', blank=True)

    def __unicode__(self):
        return u'Iframe #%d' % (self.pk)

    class Meta:
        verbose_name = _(u"Iframe")