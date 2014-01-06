# -*- coding:utf-8 -*-

from datetime import timedelta

from django.contrib.sites.models import Site
from django.db import transaction
from django.db.models import Q
from django.utils.timezone import now
from django.conf import settings
from django.contrib.auth.models import User
from django.core.management.base import BaseCommand, CommandError

from coop_local.mixed_email import send_mixed_email
from coop_local.models import (Organization, ActivityNomenclature,
    CallForTenders)

from ionyweb.plugin_app.plugin_contact.models import Plugin_Contact


class Command(BaseCommand):
    help = 'Mailing'

    def handle(self, *args, **options):

        self.slug = settings.REGION_SLUG
        self.sender = Plugin_Contact.objects.all()[0].email

        for org in Organization.objects.filter(is_provider=True, calls_subscription=True):
            self.mail_org(org)

    @transaction.commit_on_success
    def mail_org(self, org):

        calls = CallForTenders.objects.filter(creation=(now() - timedelta(days=1)).date())
        activities = ActivityNomenclature.objects.filter(offer__provider=org)
        calls = calls.filter(activity__in=activities)

        if len(calls) == 0:
            return

        engagements = org.engagement_set.filter(org_admin=True)
        if not engagements:
            return
        person = engagements[0].person

        sender = self.sender
        site = Site.objects.get_current().domain
        context = {'person': person, 'calls': calls, 'sender': sender, 'site': site}
        subject = u'Nouvel appel d\'offre sur %s' % site
        template = 'mailing-calls-%s' % self.slug
        email = org.pref_email.content
        send_mixed_email(sender, email, subject, template, context)
        print u'Envoi effectué à %s, %s, %s' % (email, sender, org.label())
