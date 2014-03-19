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

                if bdis_id and Organization.objects.filter(bdis_id=bdis_id).exists():
                    provider = Organization.objects.get(bdis_id=bdis_id)
                    if provider.status == 'V':
                        logging.debug(u"Une organisation validée avec l'identifiant BDIS %(bdis_id)s (id %(id)u) existe déjà dans la base." % {'bdis_id': bdis_id, 'id': provider.id})
                        provider.is_provider = True
                        provider.is_bdis = True
                        provider.save()
                        continue
                    else:
                        logging.debug(u"Une organisation non validée avec l'identifiant BDIS %(bdis_id)s (id %(id)u) existe déjà dans la base." % {'bdis_id': bdis_id, 'id': provider.id})
                elif Organization.objects.filter(norm_title=normalize_text(title)).exists():
                    provider = Organization.objects.get(norm_title=normalize_text(title))
                    if provider.id > last_id:
                        logging.warn(u"L'organisation %s est en doublon dans le fichier." % title)
                    elif provider.status == 'V':
                        logging.debug(u"L'organisation %s validée existe déjà dans la base (%u, %s)." % (title, provider.id, provider.title))
                        provider.is_provider = True
                        provider.is_bdis = True
                        provider.id_bdis = bdis_id
                        provider.save()
                        continue
                    else:
                        logging.debug(u"L'organisation %s non validée existe déjà dans la base (%u, %s)." % (title, provider.id, provider.title))
                else:
                    provider = Organization(title=title)
                    provider.save()

                provider.is_provider = True
                provider.is_bdis = True
                provider.bdis_id = bdis_id

                _set_attr_if_empty(provider, 'acronym', row[u'Sigle'])
                _set_attr_if_empty(provider, 'description', row[u'Présentation libre de la structure'])
                _set_attr_if_empty(provider, 'added_value', row[u'plue value sociale'])
                
                # csv date is JJ/MM/YYYY, but django model needs YYYY-MM-DD
                _set_attr_if_empty(provider, 'birth', _clean_date(row[u'Date de création'], u'de création', title))
                
                _set_attr_if_empty(provider, 'web', row[u'Site'])
                _set_attr_if_empty(provider, 'siret', row[u'Siret'].replace(' ', '').replace(u' ', '').replace(u'?', '').replace(u'-', '').replace(u',', ''))
                legal_status = row[u'Statut juridique']
                if legal_status in (u'SARL coopérative', u'Société coopérative de production'):
                    legal_status = u'SCOP SARL'
                if legal_status in (u'SCIC', ):
                    legal_status = u'SCIC SARL'
                if legal_status and legal_status != 'Autre':
                    try:
                        obj = LegalStatus.objects.get(label=legal_status)
                        _set_attr_if_empty(provider, 'legal_status', obj)
                    except LegalStatus.DoesNotExist:
                        logging.warn(u"Statut juridique %s inconnu pour %s. Il a été ignoré" % (legal_status, title))
                
                _set_attr_if_empty(provider, 'brief_description', row[u'Description simple'])
                _set_attr_if_empty(provider, 'annual_revenue', _clean_int(row["Budget"]))
                _set_attr_if_empty(provider, 'workforce', _clean_int(row[u'Nombre de salariés (ETP)']))
                #_set_attr_if_empty(provider, 'production_workforce', _clean_int(row[u'Effectif de production (ETP)']))
                #_set_attr_if_empty(provider, 'supervision_workforce', _clean_int(row[u'Effectif d’encadrement (ETP)']))
                #_set_attr_if_empty(provider, 'integration_workforce', _clean_int(row[u'Nombre de salariés en insertion (ETP)']))
                #_set_attr_if_empty(provider, 'annual_integration_number', _clean_int(row[u'Nombre de personnes en insertion accompagnées par an']))

                # Second Import fields (january import)

                # Old Fields
                _set_attr_if_empty(provider, 'acronym', row[u'Sigle'])

                if row[u'Spécificités']:
                    categories_iae = [row[u'Spécificités']]
                else:
                    categories_iae = []
                ess_structures = row[u'type ess']
                if _is_valid(ess_structures):
                    ess_structures_list = ess_structures.split(";")
                    for ess_structure in ess_structures_list:
                        if ess_structure == u'Association intermédiaire':
                            categories_iae.append('AI')
                            continue
                        if ess_structure == u'Atelier chantier d’insertion':
                            categories_iae.append('ACI')
                            continue
                        if ess_structure == u'entreprise d’insertion':
                            categories_iae.append('EI')
                            continue
                        if "paca" in import_file:
                            ess_structure = ess_structure.replace(u"coopérative d’activité et d’emploi", u"Coopérative d’activité et d’emploi et d'entrepren-e-u-r-s")
                        ess_structure = ess_structure.replace(u"foyer de jeunes travaileurs", u"Foyer de jeunes travailleurs")
                        try:
                            obj = OrganizationCategory.objects.get(label__iexact=ess_structure)
                            _set_attr_m2m(provider, 'category', obj)
                        except Exception as e:
                            msg = u"Categorie ESS %(ess_structure)s inconnue pour %(name)s. Elle a été ignorée." \
                                                % {'ess_structure': ess_structure, 'name': title}
                            logging.warn(msg)

                for category_iae in categories_iae:
                    provider.agreement_iae.add(conventionnementIAE)
                    if category_iae == u"Conventionnement IAE":
                        continue
                    try:
                        obj = CategoryIAE.objects.get(label=category_iae)
                        _set_attr_m2m(provider, 'category_iae', obj)
                    except CategoryIAE.DoesNotExist:
                        logging.warn(u"Catégorie IAE %s inconnue pour %s" % (category_iae, title))

                keywords = row[u'mots clés']
                if _is_valid(keywords):
                    keywords = keywords.replace(u"Développement économique local Dialogue social territorial Economie sociale et solidaire Economie et emploi, Entreprises Mobilité", u"Développement économique local;Dialogue social territorial;Economie sociale et solidaire;Economie et emploi;Entreprises;Mobilité")
                    keywords = keywords.replace(',', ';')
                    tags_list = keywords.split(";")
                    for tag in tags_list:
                        slugified_tag = slugify(tag)
                        logging.debug('Get or create tag %s...' % tag)
                        (obj, created) = Tag.objects.get_or_create(name=tag)
                        _set_attr_m2m(provider, 'tags', obj)
                
                themes = row[u'Thématiques']
                if _is_valid(themes):
                    themes_list = themes.replace(u':', u';').split(";")
                    for theme in themes_list:
                        if theme in ('', u'ép*', u'monnaie solidaire', u'Mutualisation de moyens et de compétences'):
                            continue
                        theme = theme.replace(u'’', u'\'').strip()
                        theme = theme.replace(u"Circuits courts", u"Circuit court")
                        theme = theme.replace(u"éparhne et financement solidaire", u"épargne et financement solidaire")
                        theme = theme.replace(u"internet et logiciels libres", u"internet solidaire et logiciels libres")
                        theme = theme.replace(u"préservattion", u"préservation")
                        theme = theme.replace(u"protection de l'environnement", u"préservation de l'environnement")
                        try:
                            obj = TransverseTheme.objects.get(name__iexact=theme)
                        except TransverseTheme.DoesNotExist:
                            logging.warn(u"Thème %s non trouvé pour %s" % (theme, provider))
                            continue
                        _set_attr_m2m(provider, 'transverse_themes', obj)

                address_label = ""
                if ';' in row["Adresse"]:
                    address_1, address_2 = row["Adresse"].split(';', 1)
                else:
                    address_1 = row["Adresse"]
                    address_2 = ""
                zip_code = row["Code postal"].replace(' ', '').strip()
                if len(zip_code) > 5:
                    logging.warn('Code postal avec plus de 5 chiffres %s' % provider.title)
                    zip_code = ''
                city = row["Ville"]

                if not _is_valid(address_label):
                    address_label = address_1

                try:
                    logging.debug('Get or create location %s...' % address_label)
                    (location, created) = Location.objects.get_or_create(label__iexact=address_label,
                                                   adr1__iexact=address_1,
                                                   adr2__iexact=address_2,
                                                   zipcode=zip_code,
                                                   city__iexact=city)
                except Location.MultipleObjectsReturned:
                    location = Location.objects.filter(label__iexact=address_label,
                                                       adr1__iexact=address_1,
                                                       adr2__iexact=address_2,
                                                       zipcode__iexact=zip_code,
                                                       city__iexact=city)[0]
                try:
                    latitude = longitude = ""
                    longitude = float(row["longitude"])
                    latitude = float(row["latitude"])
                    point = Point(latitude, longitude)
                    _set_attr_if_empty(location, 'point', point)
                    logging.debug('Save location %s...' % location)
                    location.save()
                except Exception as e:
                    msg = u"Pas de géolocalisation pour %s" % title
                    logging.warn(msg)

                location_category = LocationCategory.objects.get(slug="siege-social")
                try:
                    located = Located.objects.get(location=location)
                    _set_attr_if_empty(located, 'category', location_category)
                    _set_attr_if_empty(located, 'opening', row[u'Jours d’ouverture'])
                    logging.debug('Save located %s...' % located)
                    located.save()
                except Located.DoesNotExist:
                    located = Located(content_object=provider,
                                      location=location,
                                      main_location=True,
                                      category=location_category,
                                      opening=row[u'Jours d’ouverture'])
                    logging.debug('Save located %s...' % located)
                    located.save()
		except Located.MultipleObjectsReturned:
		    located = Located.objects.filter(location=location)[0]
		    msg = "Location %s is not unique" % location.label
		    logging.debug(msg)
                finally:    
                    _set_attr_if_empty(provider, 'located', located)
                    _set_attr_if_empty(provider, 'pref_address', location)

                email = row[u'Courriel']
                if _is_valid(email):
                    _save_contact(provider, email, u'Courriel', False, True, 'pref_email')

                cell_number = row[u'Téléphone']
                if _is_valid(cell_number):
                    _save_contact(provider, cell_number, u'Téléphone', True, True, 'pref_phone')

                fax_number = row[u'Fax']
                if _is_valid(fax_number):
                    _save_contact(provider, fax_number, u'Fax', True)

                mobile_number = row[u'Mobile']
                if _is_valid(mobile_number):
                    _save_contact(provider, mobile_number, u'Mobile', True)

                for i in row[u'activités économiques (voir onglet activités)'].split(';'):
                    if not _is_valid(i):
                        continue
                    activities = ActivityNomenclature.objects.filter(label__iexact=ACTIVITIES[i]).order_by('-level')
                    if len(activities) == 0:
                        logging.warn(u"Secteur d'activité %s inconnu pour %s. Il a été ignoré." % (ACTIVITIES[i], provider))
                        continue
                    activity = activities[0]
                    #if activity.level != 2:
                        #logging.warn(u"Secteur d'activité %s niveau %u pour %s. Il a été ignoré." % (ACTIVITIES[i], activity.level, provider))
                        #continue
                    logging.debug('Get or create offer %s...' % activity.label)
                    offer, created = Offer.objects.get_or_create(
                        provider=provider, description=activity.label)
                    if created:
                        offer.activity.add(activity)
                        dep = zip_code and '%02u' % int(zip_code[:2])
                        if dep:
                            try:
                                offer.area.add(Area.objects.get(area_type__txt_idx='DEP', reference=dep))
                            except Area.DoesNotExist:
                                logging.warn(u"Impossible de trouver le département %s pour %s. Il a été ignoré." % (dep, provider))

                _set_attr_if_empty(provider, 'status', row[u'Code Statut de la fiche'][:1])

                mode = row[u'Mode de transmission']
                if mode == u'':
                    mode = u'Administration'
                if mode == u'Saisie sur le site':
                    _set_attr_if_empty(provider, 'transmission', 1)
                elif mode == u'Administration':
                    _set_attr_if_empty(provider, 'transmission', 2)
                elif mode == u'Import':
                    _set_attr_if_empty(provider, 'transmission', 3)
                else:
                    logging.warn(u"Mode de transmission %s inconnu pour %s" % (mode, provider))

                _set_attr_if_empty(provider, 'transmission_date', _clean_date(row[u'Date transmission'], u'de transmission', title))

                _set_attr_if_empty(provider, 'correspondence', row[u'Correspondance BDis / Structure'])

                logging.debug('Save provider %s...' % provider)
                provider.save()


def _save_contact(provider, data, medium_label, is_tel_number, set_provider_field=False, provider_field_name=None):

    if is_tel_number:
        data = _format_number_to_bd_check(_clean_tel(data))

    contacts = Contact.objects.filter(contact_medium__label=medium_label, content=data, organization=provider)

    if (contacts.count() == 0):
        # get_or_create method cannot be called because of generic Contact model relation
        # so we try get, and create it manually if does not exists
        medium = ContactMedium.objects.get(label=medium_label)
        contact = Contact(content_object=provider, contact_medium=medium, content=data)
        logging.debug('Save contact %s...' % contact)
        contact.save()
    else:
        if (contacts.count() > 1):
            logging.warn("Contact > %(data)s < of medium %(medium)s for %(title)s has duplicated entries" 
                        % {'data': data, 'medium': medium_label, 'title': provider.title})
        contact = contacts[0]
        contact.content_object = provider
        logging.debug('Save contact %s...' % contact)
        contact.save()

    if set_provider_field:
        _set_attr_if_empty(provider, provider_field_name, contact)


# Save field only if there is no data
# to avoid overwriting client manual work on preprod
def _set_attr_if_empty(obj, field_name, data):

    field_value = getattr(obj, field_name)
    if ((field_value == None) or (field_value == '')):
        setattr(obj, field_name, data)


def _set_attr_m2m(obj, field_name, data):

    field_value = getattr(obj, field_name)
    field_value.add(data)


def _format_number_to_bd_check(data):

    return ".".join([data[0:2], data[2:4], data[4:6], data[6:8], data[8:10]])


def _is_valid(data):

    return (data != "")


def _clean_tel(data):

    data = re.sub(r'[^\d]', '', data)

    # Some tel number lacks first "0"
    if data[0] != '0':
        data = "0" + data

    return data


def _clean_int(data):
    
    if _is_valid(data):
        if '.' in data:
            data = data.split('.')[0]
        return int(data.replace(' ', '').replace(u' ', '').replace(u'?', ''))
    else:
        return None

def _clean_date(data, field, title):

    if data == '-':
        return None
    elif _is_valid(data):
        try:
            tme_struct = time.strptime(data, '%d/%m/%Y')
        except ValueError:
            try: 
                tme_struct = time.strptime(data, '%d/%m/%y')
            except ValueError:
                logging.warn("Format de la date %s incorrect pour %s" % (field, title));
                return None
        return datetime.datetime(*tme_struct[0:3])
    return None


def unicode_csv_reader(unicode_csv_data, dialect=csv.excel, **kwargs):

    # csv.py doesn't do Unicode; encode temporarily as UTF-8:
    csv_reader = csv.reader(utf_8_encoder(unicode_csv_data),
                            dialect=dialect, **kwargs)
    return csv_reader


def utf_8_encoder(unicode_csv_data):
    for line in unicode_csv_data:
        yield line.encode('utf-8')

ACTIVITIES = {
    u'AGR.c.01': u'maraîchage',
    u'AGR.c.02': u'Elevage',
    u'AGR.c.03': u'autres activités liées à l\'agriculture',
    u'AGR.c.04': u'autres activités liées à l\'agriculture',
    u'AGR.c.05': u'production des grandes cultures',
    u'AGR.c.06': u'production des grandes cultures',
    u'AGR.c.08': u'espaces verts',
    u'AGR.c.09': u'sylviculture',
    u'AGR.c.10': u'jardins',
    u'AGR.c.11': u'soutien à l’agriculture',
    u'AGR.c.12': u'autres activités liées à l\'agriculture',
    u'ARG.c.07': u'sylviculture',
    u'ART.c.01': u'bijoux artisanaux',
    u'ART.c.02': u'autres activités liées à habillement, textiles, artisanat',
    u'ART.c.03': u'travail du bois',
    u'ART.c.04': u'autres activités liées à habillement, textiles, artisanat',
    u'AUT.c.01': u'Cosmétiques',
    u'AUT.c.02': u'produits d\'entretien',
    u'AUT.c.03': u'autres activités liées à santé, social, emploi',
    u'AUT.c.04': u'autres activités liées à santé, social, emploi',
    u'AUT.c.05': u'autres activités liées à l’industrie',
    u'AUT.c.06': u'autres activités liées à l’industrie',
    u'AUT.c.07': u'autres activités liées à l’industrie',
    u'BAT.c.01': u'démolition',
    u'BAT.c.02': u'maçonnerie, construction',
    u'BAT.c.03': u'travaux de voirie et d’assainissement',
    u'BAT.c.04': u'entretien et restauration du patrimoine bâti',
    u'BAT.c.05': u'peinture et revêtement',
    u'BAT.c.06': u'maçonnerie, construction',
    u'BAT.c.07': u'menuiserie, charpentes',
    u'BAT.c.08': u'peinture et revêtement',
    u'BAT.c.09': u'plomberie',
    u'BAT.c.10': u'architecture et dessin industriel',
    u'BAT.c.11': u'autres activités de construction',
    u'BNQ.c.01': u'Assurances',
    u'BNQ.c.02': u'financement',
    u'BNQ.c.03': u'autres activités liées à Finances et banque',
    u'CLT.c.01': u'évènements et spectacles',
    u'CLT.c.02': u'Théâtre, danse, musique',
    u'CLT.c.03': u'cinéma',
    u'CLT.c.04': u'Musique',
    u'CLT.c.05': u'Dessin, peinture, sculpture, arts plastiques',
    u'CLT.c.06': u'littérature',
    u'CLT.c.07': u'Arts plastiques',
    u'CLT.c.08': u'patrimoine, musées',
    u'CLT.c.09': u'patrimoine, musées',
    u'CLT.c.10': u'autres activités liées à culture, art…',
    u'COM.c.01': u'édition',
    u'COM.c.02': u'journalisme, rédaction',
    u'COM.c.03': u'multimédia, web',
    u'COM.c.04': u'Marketing',
    u'COM.c.05': u'imprimerie, reprographie',
    u'COM.c.06': u'PAO, infographie, graphisme',
    u'COM.c.07': u'télévision et radio',
    u'COM.c.08': u'autres activités liées à la communication',
    u'COO.c.01': u'coopération internationale',
    u'COO.c.02': u'coopération internationale',
    u'COO.c.03': u'coopération européenne',
    u'COO.c.04': u'autres activités non classées',
    u'COO.c.05': u'coopération internationale',
    u'DIS.c.01': u'distribution de produits alimentaires et de boissons',
    u'DIS.c.02': u'artisanat',
    u'DIS.c.03': u'habillement',
    u'DIS.c.04': u'autres activités non classées',
    u'ELC.c.01': u'production d’énergie renouvelable',
    u'ELC.c.02': u'électronique',
    u'ELC.c.03': u'autres activités dans l’énergie renouvelable et les économies d’énergie',
    u'FOR.c.01': u'enseignement',
    u'FOR.c.02': u'enseignement',
    u'FOR.c.03': u'études/conseil',
    u'FOR.c.04': u'activités de soutien à l’enseignement',
    u'For.c.05': u'Recherche',
    u'FOR.c.06': u'autres activités liées à formation et études',
    u'GES.c.01': u'comptabilité',
    u'GES.c.02': u'Secrétariat',
    u'GES.c.03': u'ressources humaines',
    u'GES.c.04': u'activités juridiques',
    u'GES.c.05': u'autres activités liées à gestion, management, activités de bureau',
    u'HEB.c.01': u'Hôtellerie',
    u'HEB.c.02': u'Gîte, camping, chambre d’hôte',
    u'HEB.c.03': u'Gîte, camping, chambre d’hôte',
    u'HEB.c.04': u'restauration collective',
    u'HEB.c.05': u'restauration individuelle',
    u'HEB.c.06': u'Traiteur',
    u'HEB.c.07': u'autres activités dans la restauration',
    u'HEB.c.08': u'autres activités dans la restauration',
    u'INF.c.01': u'fabrication d’équipements informatiques',
    u'INF.c.02': u'Vente de matériels informatiques',
    u'INF.c.03': u'maintenance et réparation de matériels informatique',
    u'INF.c.04': u'développement informatique',
    u'INF.c.05': u'autres activités liées à informatique et télécommunications',
    u'INF.c.06': u'autres activités liées à informatique et télécommunications',
    u'LSR.c.01': u'sport',
    u'LSR.c.02': u'Animation',
    u'LSR.c.03': u'Tourisme',
    u'LSR.c.04': u'autres activités liées à Loisir et sports, tourisme, hébergement',
    u'NAT.c.01': u'espaces naturels',
    u'NAT.c.02': u'espaces naturels',
    u'NAT.c.03': u'collecte, traitement, recyclage déchets et autres',
    u'NAT.c.04': u'Gestion écologique de l’eau',
    u'NAT.c.05': u'prévention contre les pollutions',
    u'NAT.c.06': u'prévention contre les pollutions',
    u'NAT.c.07': u'autres activités liées à l’environnement',
    u'REP.c.01': u'réparation de véhicules',
    u'REP.c.02': u'Petit électroménager;Gros électroménager',
    u'REP.c.03': u'nettoyage de locaux',
    u'REP.c.04': u'blanchisserie',
    u'REP.c.05': u'habillement',
    u'REP.c.06': u'autres activités liées au transports, entretien et logistique',
    u'SAN.c.01': u'Emploi',
    u'SAN.c.02': u'handicap',
    u'SAN.c.03': u'petite enfance',
    u'SAN.c.04': u'personnes âgées',
    u'SAN.c.05': u'services à la personne',
    u'SAN.c.06': u'Centres médicaux',
    u'SAN.c.07': u'Activités médico-sociales',
    u'SAN.c.08': u'autres activités liées à santé, social, emploi',
    u'TEX.c.01': u'mobilier',
    u'TEX.c.02': u'confection textile',
    u'TEX.c.03': u'habillement',
    u'TEX.c.04': u'travail du cuir',
    u'TEX.c.05': u'autres activités liées à habillement, textiles, artisanat',
    u'TRA.c.01': u'déplacement en véhicules motorisés',
    u'TRA.c.02': u'autres activités liées au transports, entretien et logistique',
    u'TRA.c.03': u'Déménagement',
    u'TRA.c.04': u'autres activités liées au transports, entretien et logistique',
    u'URB.c.01': u'location immobilière',
    u'URB.c.02': u'vente immobilière',
    u'URB.c.03': u'Aménagement',
    u'URB.c.04': u'logement',
    u'URB.c.05': u'autres activités liées à l’habitat',
}