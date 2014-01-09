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
    CallForTenders, SentCall, Event, SentEvent, Area)

from ionyweb.plugin_app.plugin_contact.models import Plugin_Contact


class Command(BaseCommand):
    help = 'Mailing'

    def handle(self, *args, **options):

        self.slug = settings.REGION_SLUG
        self.sender = Plugin_Contact.objects.all()[0].email

        for org in Organization.objects.filter(is_provider=True, calls_subscription=True):
            self.mail_org_for_calls(org)

        for org in Organization.objects.filter(events_subscription__isnull=False):
            self.mail_org_for_events(org)

    def mail_org_for_calls(self, org):

        calls = CallForTenders.objects.filter(deadline__gte=now().date())
        calls = calls.filter(Q(organization__status='V') | Q(force_publication=True))
        activities = ActivityNomenclature.objects.filter(offer__provider=org)
        calls = calls.filter(activity__in=activities)
        sent = SentCall.objects.filter(organization=org, call__in=calls).values_list('call__id', flat=True)
        calls = calls.exclude(id__in=sent)

        if len(calls) == 0:
            return

        engagements = org.engagement_set.filter(org_admin=True)
        if not engagements:
            return
        person = engagements[0].person

        sender = self.sender
        site = Site.objects.get_current().domain
        context = {
            'person': person,
            'calls': calls,
            'sender': sender,
            'site': site,
            'slug': self.slug,
            'region': settings.REGION_NAME,
        }
        subject = u'Nouvel appel d\'offre sur %s' % site
        template = 'email/calls'
        email = org.pref_email.content
        if not org.pref_email:
            return
        send_mixed_email(sender, email, subject, template, context)
        print u'%u appels d\'offres envoyé à %s, %s, %s' % (len(calls), email, sender, org.label())
        for call in calls:
            SentCall.objects.create(call=call, organization=org)

    def mail_org_for_events(self, org):

        events = Event.geo_objects.filter(occurrence__start_time__gte=now())
        events = events.filter(status='V')
        try:
            org_location = org.locations()[0]
            if org_location and org_location.point:
                area = Area.objects.get(area_type=org.events_subscription, polygon__intersects=org_location.point)
                if area and area.polygon:
                    events = events.filter(location__point__intersects=area.polygon)
        except:
            pass
        sent = SentEvent.objects.filter(organization=org, event__in=events).values_list('event__id', flat=True)
        events = events.exclude(id__in=sent)

        if len(events) == 0:
            return

        engagements = org.engagement_set.filter(org_admin=True)
        if not engagements:
            return
        person = engagements[0].person

        sender = self.sender
        site = Site.objects.get_current().domain
        context = {
            'person': person,
            'events': events,
            'sender': sender,
            'site': site,
            'slug': self.slug,
            'region': settings.REGION_NAME,
        }
        subject = u'Nouvel événement sur %s' % site
        template = 'email/events'
        if not org.pref_email:
            return
        email = org.pref_email.content
        send_mixed_email(sender, email, subject, template, context)
        print u'%u événements envoyé à %s, %s, %s' % (len(events), email, sender, org.label())
        for event in events:
            SentEvent.objects.create(event=event, organization=org)
