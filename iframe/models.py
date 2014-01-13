# -*- coding:utf-8 -*-

from django.db import models
from coop_local.models import Area, AgreementIAE, Organization, Tag


class IFrame(models.Model):
    title = models.CharField(u"Titre", max_length=200)
    domain = models.URLField(u"Domaine")
    area = models.ForeignKey(Area, null=True, blank=True,
                             verbose_name=u"Zone")
    network = models.ForeignKey(Organization, null=True, blank=True,
                                limit_choices_to = {'is_network': True},
                                verbose_name=u"Réseau")
    agreement_iae = models.ForeignKey(AgreementIAE, null=True, blank=True,
                                      verbose_name=u"Spécificité")
    tag= models.ForeignKey(Tag, null=True, blank=True,
                           verbose_name=u"Mot-clé")

    def __unicode__(self):
        return self.title
