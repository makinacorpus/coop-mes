
import csv
import sys

from django.core.management.base import BaseCommand, CommandError

from coop_local.models import Provider

    
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
	
	#for import_file in args:

    try:
	    file_="import_structures.csv" 
        dest_file = csv.DictReader(open(file_, 'rb'), delimiter=',', quotechar='"')

     
        for row in dest_file:

    	    provider = Provider()
            provider.label = row[1]
        	provider.siret = row[8]
            #provider.legal_status = ?
            #provider.category_iae = ?
            #provider.agreement_iae = ?
        	provider.brief_description = row[11]
            provider.added_value = row[10]
            provider.transverse_themes = ?
            provider.annual_revenue = row[9]
        	provider.workforce = row[13]
            provider.production_workforce = row[14]
            provider.supervision_workforce = row[15]
            provider.integration_workforce = row[16]
    	    provider.annual_integration_number = row[8]
            #provider.guaranties = ?
            provider.creation = row[3]
            #provider.modification = ?
            provider.status = row[4]
            #provider.correspondence = ?
            #provider.transmission = ?
    	    #provider.author = ?
            #provider.validation = ?
            
    	    self.stdout = row[0].decode(encoding='UTF-8')
    	    #print row
            sys.exit()
    except Exception e:
        throw Exception()

def unicode_csv_reader(unicode_csv_data, dialect=csv.excel, **kwargs):
    # csv.py doesn't do Unicode; encode temporarily as UTF-8:
    csv_reader = csv.reader(utf_8_encoder(unicode_csv_data),
                            dialect=dialect, **kwargs)
    return csv_reader


def utf_8_encoder(unicode_csv_data):
    for line in unicode_csv_data:
        #yield line
        yield line.encode('utf-8')