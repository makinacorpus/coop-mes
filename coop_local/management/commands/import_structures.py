# -*- coding:utf-8 -*-
import csv
import sys
import time
import datetime

from django.core.management.base import BaseCommand, CommandError

from coop_local.models import Provider, LegalStatus, CategoryIAE

    
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
                
                provider = Provider()
                provider.title = row['Raison sociale']
                provider.acronym = row['Sigle']
                provider.description = row['Presentation generale']
                
                # csv date is JJ/MM/YYYY, but django model needs YYYY-MM-DD
                birth_date = _clean_row(row['Date de creation'])
                if (birth_date is not None):
                    tme_struct = time.strptime(birth_date, '%d/%m/%Y')
                    provider.birth = datetime.datetime(*tme_struct[0:3])
                    
                provider.email = row['Email de la structure']
                provider.web = row['Site web']

                provider.siret = row['N° SIRET']
                legal_status = row['Statut juridique']
                try:
                    obj = LegalStatus.objects.get(label=legal_status)
                    provider.legal_status = obj
                except LegalStatus.DoesNotExist:
                    print "Unknown Status : >" + legal_status + "<"

                """
                category_iae = row['Type de structure SIAE']
                try:
                    obj = CategoryIAE.objects.get(label=category_iae)
                    provider.category_iae = obj
                except CategoryIAE.DoesNotExist:
                    print "Unknown IAE Category : >" + category_iae + "<"
                """
                    
                #provider.category_iae = ? 
                #provider.agreement_iae = ?
                #provider.brief_description = row['Description succincte']
                #provider.added_value = row['plue value sociale et environ-nementale']
                #provider.transverse_themes = ?
                #provider.annual_revenue = _clean_int(row["Chiffre d'affaires annuel"])
                #provider.workforce = _clean_int(row['Effectif total (ETP)'])
                #provider.production_workforce = _clean_int(row['Effectif de production (ETP)'])
                #provider.supervision_workforce = _clean_int(row['Effectif d’encadrement (ETP)'])
                #provider.integration_workforce = _clean_int(row['Nombre de salariés en insertion (ETP)'])
                #provider.annual_integration_number = _clean_int(row['Nombre de personnes en insertion accompagnées par an'])
                #provider.guaranties = ?
                
                #provider.modification = ?
                #provider.status = row['Statut juridique']
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