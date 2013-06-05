# -*- coding: utf-8 -*-
from django.db import models
from django.utils.translation import ugettext_lazy as _
from ionyweb.page.models import AbstractPageApp


class PageApp_Directory(AbstractPageApp):
    
    # Define your fields here

    def __unicode__(self):
        return u'Directory #%d' % (self.pk)

    class Meta:
        verbose_name = _(u"Directory")