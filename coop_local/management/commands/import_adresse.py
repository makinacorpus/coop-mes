# -*- coding:utf-8 -*-
import csv
import sys
import time
import datetime
import logging
import re

from django.core.management.base import BaseCommand, CommandError
from django.template.defaultfilters import slugify
from django.contrib.gis.geos import Point
from coop_tag.settings import get_class
from coop_geo.models import LocationCategory
from coop.org.models import COMM_MEANS
from django.db.utils import IntegrityError
from unidecode import unidecode
from django.db.models import Max

from coop_local.models import (Organization, LegalStatus, CategoryIAE, OrganizationCategory, AgreementIAE,
    Contact, Location, ContactMedium, Located, TransverseTheme, ActivityNomenclature, Offer, Area)

current_time = datetime.datetime.now()
logging.basicConfig(filename='%(date)s_structure_migration.log' % {'date': current_time.strftime("%Y-%m-%d")},
                    level=logging.WARNING,
                    format='%(asctime)s %(levelname)s - %(message)s',
                    datefmt='%d/%m/%Y %H:%M:%S',)

Tag = get_class('tag')

def normalize_text(text):
    return re.sub(r'\s+', ' ', unidecode(text).lower().strip())

class Command(BaseCommand):
    args = '<import_file>'
    help = 'Import structure file'

    def handle(self, *args, **options):

        for import_file in args:

            errors_array = []
            dest_file = csv.DictReader(open(import_file, 'rb'), delimiter=',', quotechar='"')
            #print 'HEADER:'
            #for f in dest_file.fieldnames:
                #print f.decode('utf8')

            conventionnementIAE =  AgreementIAE.objects.get(label=u"Conventionnement IAE")
            last_id = Organization.objects.aggregate(id=Max('id'))['id']

            for i, row in enumerate(dest_file):

                print 'Line %u' % (i + 2)
                logging.debug('Line %u' % (i + 2))

                row = dict([(k.decode('utf8'), v.decode('utf8')) for k, v in row.iteritems()])

                title = row[u'Nom']
                bdis_id = int(row[u'Numéro BDIS']) if row[u'Numéro BDIS'] else None
                address_label = ""
                if ';' in row["Adresse"]:
                    address_1, address_2 = row["Adresse"].split(';', 1)
                else:
                    address_1 = row["Adresse"]
                    address_2 = ""
                zip_code = row["Code postal"].replace(' ', '').strip()
                zip_code = '%05u' % int(zip_code) if zip_code else ''
                if len(zip_code) > 5:
                    logging.warn('Code postal avec plus de 5 chiffres %s' % provider.title)
                    zip_code = ''
                city = row["Ville"]

                try:
                    provider = Organization.objects.get(norm_title=normalize_text(title))
                except Organization.DoesNotExist:
                    logging.error('no org %s (bdis %u)' % (title, bdis_id))
                    continue
                if provider.bdis_id != bdis_id:
                    logging.warn('wrong bdis_id for %s' % title)
                    continue
                    #provider.bdis_id = bdis_id
                    #provider.save()

                location_category = LocationCategory.objects.get(slug="siege-social")
                locateds = Located.objects.filter(organization=provider, category=location_category).order_by('-id')
                save_located = False
                if len(locateds) == 0:
                    logging.error('No located for bdis_id=%u' % bdis_id)
                    location = Location()
                    located = Located(content_object=provider, opening=row[u'Jours d’ouverture'], category=location_category)
                    save_located = True
                else:
                    located = locateds[0]
                    if located.location:
                        location = located.location
                    else:
                        location = Location()
                        save_located = True

                location.adr1 = address_1
                location.adr2 = address_2
                location.zipcode = zip_code
                location.city = city

                try:
                    latitude = longitude = ""
                    longitude = float(row["longitude"])
                    latitude = float(row["latitude"])
                    point = Point(longitude, latitude)
                except Exception as e:
                    msg = u"Pas de géolocalisation pour %s" % title
                    logging.warn(msg)
                    point = None
                location.point = point
                location.save()

                if save_located:
                    located.location = location
                    located.save()
