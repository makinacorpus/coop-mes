# -*- coding:utf-8 -*-
import csv
import sys
import logging
import datetime

from django.core.management.base import BaseCommand, CommandError
from django.template.defaultfilters import slugify

from coop_local.models import Organization, LegalStatus, CategoryIAE, Person, Engagement, Role

    
# Columns are :
# 0 - ID Structures BDIS
# 1 - ID Personnes BDIS
# 2 - Fonction
# 3 - Courriel
# 4 - Nom
# 5 - Prénom

current_time = datetime.datetime.now()

logging.basicConfig(filename='%(date)s_person_migration.log' % {'date': current_time.strftime("%Y-%m-%d")},
                    level=logging.DEBUG,
                    format='%(asctime)s %(levelname)s - %(message)s',
                    datefmt='%d/%m/%Y %H:%M:%S',)

class Command(BaseCommand):
    args = '<import_file>'
    help = 'Import structure file'

    def handle(self, *args, **options):
	    
        # Slugifying one more time, to overwrite initial method which keep accents
        roles = Role.objects.all()
        for current_role in roles:
            current_role.label = current_role.label
            current_role.save()

        for import_file in args:

            dest_file = csv.DictReader(open(import_file, 'rb'), delimiter=',', quotechar='"')

            for row in dest_file:
                
                last_name = row['Nom']
                first_name = row['Prénom']

                if (_is_valid(last_name) and _is_valid(first_name)):
                    (person, success) = Person.objects.get_or_create(last_name=last_name, first_name=first_name)

                    email = row['Courriel']
                    if _is_valid(email):
                        person.email = email

                    bdis_person_id = row['ID Personnes BDIS']
                    if _is_valid(bdis_person_id):
                        person.bdis_id = bdis_person_id

                    person.save()

                    role_name = row['Fonction']
                    role_name_slug = slugify(role_name)
                    bdis_organization_id = row['ID Structures BDIS']

                    try:
                        organization = Organization.objects.get(bdis_id=bdis_organization_id)
                        role = None

                        try:
                            role = Role.objects.get(slug=role_name_slug)
                        except Role.DoesNotExist:
                            logging.warn("Role > %(role_name)s < not found for "
                                         "%(last_name)s %(first_name)s" % {'role_name': role_name,
                                                                           'last_name': last_name,
                                                                           'first_name': first_name})
        
                        Engagement.objects.get_or_create(person=person, organization=organization, role=role)
                    
                    except Organization.DoesNotExist:
                        logging.warn("BDIS Organization number > %(bdis_id)s < not found for " 
                                     "%(last_name)s %(first_name)s" % {'bdis_id': bdis_organization_id,
                                                                       'last_name': last_name,
                                                                       'first_name': first_name})
        

def _is_valid(data):

    return (data != "")


def unicode_csv_reader(unicode_csv_data, dialect=csv.excel, **kwargs):
    # csv.py doesn't do Unicode; encode temporarily as UTF-8:
    csv_reader = csv.reader(utf_8_encoder(unicode_csv_data),
                            dialect=dialect, **kwargs)
    return csv_reader


def utf_8_encoder(unicode_csv_data):
    for line in unicode_csv_data:
        yield line.encode('utf-8')
