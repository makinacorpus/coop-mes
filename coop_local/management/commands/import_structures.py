# -*- coding:utf-8 -*-
import csv
import sys
import time
import datetime

from django.core.management.base import BaseCommand, CommandError
from django.template.defaultfilters import slugify
from django.contrib.gis.geos import Point
from coop_tag.models import Tag
from coop_geo.models import Location
from coop.org.models import BaseContact

from coop_local.models import Provider, LegalStatus, CategoryIAE, CategoryESS

# The purpose of this script is to import human-made data (csv file) for MES providers
# Columns are :
# 0 - Identifiant BDIS
# 1 - Raison sociale
# 2 - Sigle
# 3 - Date de creation
# 4 - Statut juridique
# 5 - Type de structure ESS 
# 6 - Type de structure SIAE
# 7 - Site web
# 8 - N° SIRET
# 9 - Chiffre d'affaires annuel
# 10 - plue value sociale et environ-nementale
# 11 - Description succincte
# 12 - Presentation generale
# 13 - Effectif total (ETP)
# 14 - Effectif de production (ETP)
# 15 - Effectif d’encadrement (ETP)
# 16 - Nombre de salariés en insertion (ETP)
# 17 - Nombre de personnes en insertion accompagnées par an 
# 18 - "mot-clés Thèmes candidats"
# 19 - libellé de l'adresse
# 20 - Adresse 1
# 21 - Adresse 2
# 22 - Code postal
# 23 - Ville
# 24 - Jours d’ouverture
# 25 - longitude
# 26 - latitude 
# 27 - Email de la structure
# 28 - Teléphone
# 29 - Fax
# 30 - mobile

class Command(BaseCommand):
    args = '<import_file>'
    help = 'Import structure file'

    def handle(self, *args, **options):
	    
        for import_file in args:


            dest_file = csv.DictReader(open(import_file, 'rb'), delimiter=',', quotechar='"')

            for row in dest_file:
                
                title = row['Raison sociale']

                (provider, success) = Provider.objects.get_or_create(title=title);
                
                """ First import fields
                provider.acronym = row['Sigle']
                provider.description = row['Presentation generale']
                
                # csv date is JJ/MM/YYYY, but django model needs YYYY-MM-DD
                birth_date = _clean_row(row['Date de creation'])
                if (birth_date is not None):
                    tme_struct = time.strptime(birth_date, '%d/%m/%Y')
                    provider.birth = datetime.datetime(*tme_struct[0:3])
                    
                provider.web = row['Site web']
                provider.siret = row['N° SIRET']
                legal_status = row['Statut juridique']
                try:
                    obj = LegalStatus.objects.get(label=legal_status)
                    provider.legal_status = obj
                except LegalStatus.DoesNotExist:
                    print "Unknown Status : >" + legal_status + "<"

                
                category_iae = row['Type de structure SIAE']
                try:
                    obj = CategoryIAE.objects.get(label=category_iae)
                    provider.category_iae = [obj]
                except CategoryIAE.DoesNotExist:
                    print "Unknown IAE Category : >" + category_iae + "<"
                
                provider.brief_description = row['Description succincte']
                provider.added_value = row['plue value sociale et environ-nementale']
                provider.annual_revenue = _clean_int(row["Chiffre d'affaires annuel"])
                provider.workforce = _clean_int(row['Effectif total (ETP)'])
                provider.production_workforce = _clean_int(row['Effectif de production (ETP)'])
                provider.supervision_workforce = _clean_int(row['Effectif d’encadrement (ETP)'])
                provider.integration_workforce = _clean_int(row['Nombre de salariés en insertion (ETP)'])
                provider.annual_integration_number = _clean_int(row['Nombre de personnes en insertion accompagnées par an'])
                """

                """ Second Import fields"""
                
                # New Fields
                provider.bdis_id = row['Identifiant BDIS']

                # Old Fields
                provider.acronym = row['Sigle']
                
                ess_structures_list = row['Type de structure ESS'].split(";")
                for ess_structure in ess_structures_list:
                    try:
                        obj = CategoryESS.objects.get(slug=slugify(ess_structure))
                        provider.category.add(obj)
                    except CategoryESS.DoesNotExist:
                        errors_array.append("Unknown CategoryESS >%(ess_structure)s< for %(name)s" 
                                            % {'ess_structure': ess_structure, 'name': name})

                provider.web = row['Site web']
                provider.birth = row['Date de creation']
                provider.description = row['Presentation generale']

                tags_list = row['mot-clés Thèmes candidats'].split(";")
                for tag in tags_list:
                    (obj, success) = Tag.objects.get_or_create(slugify(tag))
                    provider.tags.add(obj)

                address_label = row["libellé de l'adresse"]
                address_1 = row["Adresse 1"]
                address_2 = row["Adresse 2"]
                zip_code = row["Code postal"]
                city = row["Ville"]

                (location, success) = Location.objects.get_or_create(label=address_label,
                                                   adr1=address_1,
                                                   adr2=address_2,
                                                   zipcode=zipcode,
                                                   city=city)
                
                try:
                    longitude = float(row["longitude"])
                    latitude = float(row["latitude"])
                    point = Point(latitude, longitude)
                    location.point(point)
                    location.save()
                except:
                    errors_array.append("Error with lat/long >%(latitude)s/%(longitude)s<" 
                                            % {'latitude': latitude, 'longitude': longitude})

                provider.pref_address = location

                email = row["Email de la structure"]
                provider.email = email

                #provider.category_iae = ? 
                #provider.agreement_iae = ?

                #provider.transverse_themes = ?
                #provider.guaranties = ?
                
                #provider.modification = ?

                #provider.correspondence = ?
                #provider.transmission = ?
                #provider.author = ?
                #provider.validation = ?
                
                provider.save()
                #sys.exit()


def _clean_int(data):
    
    if (_clean_row(data) is not None):
        return int(data)

def _clean_row(data):
    
    if (data != ''):
        return data
    else:
        return None

def unicode_csv_reader(unicode_csv_data, dialect=csv.excel, **kwargs):
    # csv.py doesn't do Unicode; encode temporarily as UTF-8:
    csv_reader = csv.reader(utf_8_encoder(unicode_csv_data),
                            dialect=dialect, **kwargs)
    return csv_reader


def utf_8_encoder(unicode_csv_data):
    for line in unicode_csv_data:
        yield line.encode('utf-8')