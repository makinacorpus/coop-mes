# -*- coding:utf-8 -*-
import csv
import os
import shutil

from django.core.management.base import BaseCommand, CommandError
from django.conf import settings

from coop_local.models import Organization


class Command(BaseCommand):
    args = '<import_file> <import_dir>'
    help = 'Import logos'

    def handle(self, *args, **options):

        bdis2logo = {}
        with open(args[0], 'rb') as f:
            reader = csv.reader(f, delimiter=',', quotechar='"')
            reader.next()
            for row in reader:
                bdis2logo[row[0]] = row[1]

        for org in Organization.objects.filter(is_bdis=True, bdis_id__isnull=False).order_by('bdis_id'):
            if str(org.bdis_id) not in bdis2logo:
                print u"ERROR Pas de correspondance pour %u" % org.bdis_id
                continue
            id_logo = bdis2logo[str(org.bdis_id)]
            if not id_logo:
                #print u"ERROR Correspondance vide pour %u" % org.bdis_id
                continue
            path = args[1] + '/' + id_logo + '/img.'
            if os.path.exists(path + 'png'):
                path = path + 'png'
            elif os.path.exists(path + 'jpg'):
                path = path + 'jpg'
            else:
                print u"ERROR Pas de fichier %s.(png|jpg)" % path
                continue
            path2 = 'logos/bdis%u.png' % org.bdis_id
            shutil.copyfile(path, settings.MEDIA_ROOT + '/' + path2)
            org.logo = path2
            org.save()
            print 'OK    ->', path2
