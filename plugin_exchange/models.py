# -*- coding: utf-8 -*-
from django.db import models
from django.utils.translation import ugettext_lazy as _
from ionyweb.plugin.models import AbstractPlugin


class Plugin_Exchange(AbstractPlugin):

    # Define your fields here

    def __unicode__(self):
        return u'Exchange #%d' % (self.pk)


    def get_admin_form(self):
        from forms import Plugin_ExchangeFormAdmin
        return Plugin_ExchangeFormAdmin

    class Meta:
        verbose_name = _(u"Exchange")
