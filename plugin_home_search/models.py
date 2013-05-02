# -*- coding: utf-8 -*-
from django.db import models
from django.utils.translation import ugettext_lazy as _
from ionyweb.plugin.models import AbstractPlugin


class Plugin_HomeSearch(AbstractPlugin):
    
    # Define your fields here

    def __unicode__(self):
        return u'HomeSearch #%d' % (self.pk)

    class Meta:
        verbose_name = _(u"HomeSearch")