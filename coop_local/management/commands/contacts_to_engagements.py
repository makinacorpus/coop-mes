# -*- coding:utf-8 -*-

from django.core.management.base import BaseCommand, CommandError
from coop_local.models import Person


class Command(BaseCommand):
    help = 'Copy contacts to engagements'

    def handle(self, *args, **options):

        for person in Person.objects.filter(contacts__isnull=False).order_by('last_name', 'first_name'):
            print person
            for engagement in person.engagements.all():
                try:
                    engagement.email = person.contacts.filter(contact_medium__label=u'Email')[0].content
                except IndexError:
                    pass
                try:
                    engagement.tel = person.contacts.filter(contact_medium__label=u'Téléphone')[0].content
                except IndexError:
                    pass
                engagement.save()
