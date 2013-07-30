# -*- coding: utf-8 -*-
from django.db import models
from django.utils.translation import ugettext_lazy as _
from ionyweb.page.models import AbstractPageApp


class PageApp_Account(AbstractPageApp):
    
    # Define your fields here

    def __unicode__(self):
        return u'Account #%d' % (self.pk)

    class Meta:
        verbose_name = _(u"Account")