# -*- coding:utf-8 -*-
import csv
import sys
import time
import datetime
import logging

from django.core.management.base import BaseCommand, CommandError
from django.template.defaultfilters import slugify
from django.contrib.gis.geos import Point
from coop_tag.settings import get_class
from coop_geo.models import Location
from coop.org.models import COMM_MEANS

from coop_local.models import Provider, LegalStatus, CategoryIAE, OrganizationCategory, Contact

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

current_time = datetime.datetime.now()
logging.basicConfig(filename='%(date)s_structure_migration.log' % {'date': current_time.strftime("%Y-%m-%d")},
                    level=logging.DEBUG,
                    format='%(asctime)s %(levelname)s - %(message)s',
                    datefmt='%d/%m/%Y %H:%M:%S',)

Tag = get_class('tag')

class Command(BaseCommand):
    args = '<import_file>'
    help = 'Import structure file'

    def handle(self, *args, **options):
	    
        for import_file in args:

            errors_array = []
            dest_file = csv.DictReader(open(import_file, 'rb'), delimiter=',', quotechar='"')

            for row in dest_file:
                
                title = row['Raison sociale']

                (provider, success) = Provider.objects.get_or_create(title=title);
                
                """ First import fields
                provider.acronym = row['Sigle']
                provider.description = row['Presentation generale']
                
                # csv date is JJ/MM/YYYY, but django model needs YYYY-MM-DD
                birth_date = _clean_row(row['Date de creation'])
                if _is_valid(birth_date):
                    tme_struct = time.strptime(birth_date, '%d/%m/%Y')
                    provider.birth = datetime.datetime(*tme_struct[0:3])
                    
                provider.web = row['Site web']
                provider.siret = row['N° SIRET']
                legal_status = row['Statut juridique']
                try:
                    obj = LegalStatus.objects.get(label=legal_status)
                    provider.legal_status = obj
                except LegalStatus.DoesNotExist:
                    logging.warn("Unknown Status : >" + legal_status + "<")

                
                category_iae = row['Type de structure SIAE']
                try:
                    obj = CategoryIAE.objects.get(label=category_iae)
                    provider.category_iae = [obj]
                except CategoryIAE.DoesNotExist:
                    logging.warn("Unknown IAE Category : >" + category_iae + "<")
                
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
                
                try:
                    bdis_id = row['Identifiant BDIS']
                    _set_attr_if_empty(provider, 'bdis_id', int(bdis_id))
                except Exception:
                    msg = "Unknown BDIS ID >%(bdis_id)s< for %(name)s" \
                                        % {'bdis_id': bdis_id, 'name': title}
                    logging.warn(msg)           

                # Old Fields
                _set_attr_if_empty(provider, 'acronym', row['Sigle'])
                
                ess_structures = row['Type de structure ESS']
                if _is_valid(ess_structures):
                    ess_structures_list = ess_structures.split(";")
                    for ess_structure in ess_structures_list:
                        try:
                            obj = OrganizationCategory.objects.get(slug=slugify(ess_structure))
                            provider.category.add(obj)
                        except Exception as e:
                            msg = "Unknown CategoryESS >%(ess_structure)s< for %(name)s" \
                                                % {'ess_structure': ess_structure, 'name': title}
                            logging.warn(msg)
                
                _set_attr_if_empty(provider, 'web', row['Site web'])
                _set_attr_if_empty(provider, 'description', row['Presentation generale'])

                keywords = row['mot-clés Thèmes candidats']
                if _is_valid(keywords):
                    tags_list = keywords.split(";")
                    for tag in tags_list:
                        slugified_tag = slugify(tag)
                        (obj, success) = Tag.objects.get_or_create(name=slugified_tag)
                        provider.tags.add(obj)

                address_label = row["libellé de l'adresse"]
                address_1 = row["Adresse 1"]
                address_2 = row["Adresse 2"]
                zip_code = row["Code postal"]
                city = row["Ville"]

                (location, success) = Location.objects.get_or_create(label=address_label,
                                                   adr1=address_1,
                                                   adr2=address_2,
                                                   zipcode=zip_code,
                                                   city=city)
                try:
                    latitude = longitude = ""
                    longitude = float(row["longitude"])
                    latitude = float(row["latitude"])
                    point = Point(latitude, longitude)
                    location.point = point
                    location.save()
                except Exception as e:
                    msg = "Error with lat/long >%(latitude)s/%(longitude)s<" \
                                            % {'latitude': latitude, 'longitude': longitude}
                    logging.warn(msg)

                _set_attr_if_empty(provider, 'pref_address', location)

                email = row['Email de la structure']
                if _is_valid(email):
                    _save_contact(provider, email, COMM_MEANS.MAIL, False, True, 'pref_email')

                cell_number = row['Teléphone']
                if _is_valid(cell_number):
                    _save_contact(provider, cell_number, COMM_MEANS.LAND, True, True, 'pref_phone')

                fax_number = row['Fax']
                if _is_valid(fax_number):
                    _save_contact(provider, fax_number, COMM_MEANS.FAX, True)

                mobile_number = row['mobile']
                if _is_valid(mobile_number):
                    _save_contact(provider, mobile_number, COMM_MEANS.GSM, True)

                provider.save()


def _save_contact(provider, data, category, is_tel_number, set_provider_field=False, provider_field_name=None):

    if is_tel_number:
        data = _format_number_to_bd_check(_clean_tel(data))

    try:
        Contact.objects.get(category=category, content=data)
    
    except Contact.DoesNotExist:
        # get_or_create method cannot be called because of generic Contact model relation
        # so we try get, and create it manually if does not exists
        contact = Contact(content_object=provider, category=category, content=data)
        contact.save()

        if set_provider_field:
            _set_attr_if_empty(provider, provider_field_name, contact)


# Save field only if there is no data
# to avoid overwriting client manual work on preprod
def _set_attr_if_empty(provider, field_name, data):

    if (getattr(provider, field_name) == None):
        setattr(provider, field_name, data)


def _format_number_to_bd_check(data):

    return ".".join([data[0:2], data[2:4], data[4:6], data[6:8], data[8:10]])


def _is_valid(data):

    return (data != "")


def _clean_tel(data):

    # Every tel number lacks first "0"
    data = "0" + data
    
    return data


def _clean_int(data):
    
    if _is_valid(data):
        return int(data)


def unicode_csv_reader(unicode_csv_data, dialect=csv.excel, **kwargs):

    # csv.py doesn't do Unicode; encode temporarily as UTF-8:
    csv_reader = csv.reader(utf_8_encoder(unicode_csv_data),
                            dialect=dialect, **kwargs)
    return csv_reader


def utf_8_encoder(unicode_csv_data):
    for line in unicode_csv_data:
        yield line.encode('utf-8')
