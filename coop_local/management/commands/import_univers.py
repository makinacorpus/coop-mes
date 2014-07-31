# -*- coding:utf-8 -*-

import csv
from coop_local.models import ActivityNomenclature, Offer, CallForTenders, Event
from django.core.management.base import BaseCommand



class Command(BaseCommand):

    def convert(self, model, corresp, adefinir):
        for obj in model.objects.all():
            activities = list(obj.activity.all())
            obj.activity.clear()
            for activity in activities:
                if activity.parent is None:
                    key = (activity.label, '', '')
                elif activity.parent.parent is None:
                    key = (activity.parent.label, activity.label, '')
                else:
                    key = (activity.parent.parent.label, activity.parent.label, activity.label)
                try:
                    x = corresp[key]
                except:
                    self.stdout.write((' // '.join(key) + ' not found\n').encode('utf8'))
                    continue
                for y in x:
                    if y[0] == u'A définir':
                        try:
                            new = ActivityNomenclature.objects.get(parent=adefinir, label=activity.label)
                        except ActivityNomenclature.DoesNotExist:
                            new = ActivityNomenclature(parent=adefinir, label=activity.label)
                            new.save()
                    else:
                        try:
                            new = ActivityNomenclature.objects.get(parent__label=y[0], label=y[1])
                        except:
                            self.stdout.write(('failed to find univers ' + ' // '.join(y) + '\n').encode('utf8'))
                            continue
                    obj.activity.add(new)

    def handle(self, *args, **options):
        max_pk = ActivityNomenclature.objects.order_by('-pk')[0].pk
        self.stdout.write('Max pk = %u\n' % max_pk)
        with open(args[0], 'rb') as f:
            reader = csv.reader(f, delimiter=';')
            for row in reader:
                row = [(i.decode('utf8')) for i in row]
                try:
                    level1 = ActivityNomenclature.objects.get(label__iexact=row[0], level=0)
                except ActivityNomenclature.DoesNotExist:
                    level1 = ActivityNomenclature(label=row[0])
                    level1.save()
                    self.stdout.write((u'level1 created ' + unicode(level1) + '\n').encode('utf8'))
                else:
                    self.stdout.write((u'level1 found   ' + unicode(level1) + '\n').encode('utf8'))
                try:
                    level2 = ActivityNomenclature.objects.get(label__iexact=row[1], parent=level1, level=1)
                except ActivityNomenclature.DoesNotExist:
                    level2 = ActivityNomenclature(label=row[1], parent=level1)
                    level2.save()
                    self.stdout.write((u'level2 created ' + unicode(level2) + '\n').encode('utf8'))
                else:
                    self.stdout.write((u'level2 found   ' + unicode(level2) + '\n').encode('utf8'))
        try:
            adefinir = ActivityNomenclature.objects.get(label=u'A définir', level=0)
        except ActivityNomenclature.DoesNotExist:
            adefinir = ActivityNomenclature(label=u'A définir')
            adefinir.save()
            self.stdout.write((u'adefinir created ' + unicode(adefinir) + '\n').encode('utf8'))
        with open(args[1], 'rb') as f:
            reader = csv.reader(f, delimiter=';')
            corresp = {}
            for row in reader:
                row = [(i.decode('utf8')) for i in row]
                if row[5]:
                    to = [row[3:5], row[5:7]]
                else:
                    to = [row[3:5]]
                corresp[tuple(row[0:3])] = to
        self.convert(Offer, corresp, adefinir)
        self.convert(CallForTenders, corresp, adefinir)
        self.convert(Event, corresp, adefinir)
        ActivityNomenclature.objects.filter(pk__lte=max_pk).delete()
