# -*- coding: utf-8 -*-

from django.template import RequestContext
from ionyweb.website.rendering.utils import render_view
from .search_form import OrgSearch
from .forms import (OrganizationForm1, PROVIDER_FORMS,
    NOT_PROVIDER_FORMS, OfferForm, OfferDocumentsFormset, AddTargetForm)
from coop_local.models import (Organization, ActivityNomenclature, Engagement,
    Person, Location, Relation, Offer, Contact, ContactMedium)
from coop_local.models.local_models import ORGANIZATION_STATUSES
from django.core.paginator import Paginator, PageNotAnInteger, EmptyPage
from django.http import HttpResponse, HttpResponseRedirect
from django.shortcuts import get_object_or_404, render
from django.contrib.auth.decorators import login_required
from django.contrib.formtools.wizard.views import SessionWizardView
from django.core.files.storage import FileSystemStorage
from tempfile import gettempdir
from ionyweb.website.rendering.medias import CSSMedia, JSMedia
from ionyweb.page.models import Page
from django.contrib.auth.models import User
from django.db.models import Q
from django.utils.timezone import now
from django.db import transaction
from django.contrib.contenttypes.generic import BaseGenericInlineFormSet
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.views.generic import CreateView, UpdateView
from datetime import date
from django.forms.models import model_to_dict
from django.contrib.admin.models import LogEntry, ADDITION, CHANGE
from django.contrib.contenttypes.models import ContentType
from  django.utils.encoding import force_unicode
from django.utils.translation import ugettext as _
from django.utils.text import get_text_list
from django.contrib.gis.measure import Distance
from django.template import Context
from django.template.loader import get_template
from django.conf import settings
import json


def get_index_context(request, networks=False, bdis=False):
    qd = request.GET.copy()
    if not qd.get('geo'):
        qd['geo'] = '1'
    if not qd.get('area_0') and 'area_1' in qd:
        del qd['area_1']
    form = OrgSearch(qd)
    if form.is_valid():
        orgs = Organization.geo_objects.filter(status=ORGANIZATION_STATUSES.VALIDATED)
        if bdis:
            orgs = orgs.filter(is_bdis=True)
        else:
            orgs = orgs.filter(is_pasr=True)
        orgs = orgs.filter(
            Q(title__icontains=form.cleaned_data['q']) |
            Q(acronym__icontains=form.cleaned_data['q']) |
            Q(tagged_items__tag__name__icontains=form.cleaned_data['q']) |
            Q(located__location__city__icontains=form.cleaned_data['q']) |
            Q(activities__path__icontains=form.cleaned_data['q']) |
            Q(offer__activity__path__icontains=form.cleaned_data['q']))
        if form.cleaned_data['guaranty']:
            orgs = orgs.filter(guaranties=form.cleaned_data['guaranty'])
        if networks:
            orgs = orgs.filter(is_network=True)
            if form.cleaned_data['prov_type']:
                orgs = orgs.filter(agreement_iae=form.cleaned_data['prov_type'])
        elif form.cleaned_data['org_type'] == 'fournisseur':
            orgs = orgs.filter(is_provider=True)
            if form.cleaned_data['prov_type']:
                orgs = orgs.filter(agreement_iae=form.cleaned_data['prov_type'])
        elif form.cleaned_data['org_type'] == 'acheteur-public':
            orgs = orgs.filter(is_customer=True, customer_type=1)
        elif form.cleaned_data['org_type'] == 'acheteur-prive':
            orgs = orgs.filter(is_customer=True, customer_type=2)
        interim = form.cleaned_data['interim']
        if interim:
            orgs = orgs.filter(offer__activity__label__in=(u'mise à disposition de personnel', u'travail temporaire', 'Mise à disposition de personnel'))
        sector = form.cleaned_data['sector']
        subsector = form.cleaned_data['subsector']
        if subsector:
            descendants = subsector.get_descendants(include_self=True)
        elif sector:
            descendants = sector.get_descendants(include_self=True)
        else:
            descendants = None
        if descendants:
            orgs = orgs.filter(offer__activity__in=descendants)
        area = form.cleaned_data.get('area')
        geo = qd.get('geo')
        orgs = orgs.distinct()
        if area:
            if area.default_location and area.default_location.point:
                center = area.default_location.point
                print 'default_location:', center.y, center.x
            else:
                center = area.polygon.centroid
                print 'centroid:', center.y, center.x
            try:
                radius = int(form.cleaned_data.get('radius'))
            except:
                radius = 0
            if radius != 0:
                degrees = radius * 360 / 40000.
                if geo == '1':
                    orgs = orgs.filter(located__location__point__dwithin=(center, degrees))
                else:
                    orgs = orgs.filter(offer__area__polygon__dwithin=(center, degrees))
            else:
                if geo == '1':
                    orgs = orgs.filter(located__location__point__intersects=area.polygon)
                else:
                    # intersects, excluding borders
                    orgs = orgs.filter(offer__area__polygon__relate=(area.polygon, '2********'))
            if radius or geo == '2':
                orgs = list(orgs)
                for o in orgs:
                    locations = Location.objects.filter(located__organization=o)
                    if locations.exists():
                        o.nearest = locations.distance(center).order_by('distance')[0]
                    else:
                        o.nearest = None
                    if o.nearest and o.nearest.distance is not None:
                        o.distance = o.nearest.distance
                    else:
                        o.distance = None
                orgs.sort(key=lambda o: (o.distance is None, o.distance))
    else:
        area = None
        orgs = Organization.objects.none()
    return {
        'form': form,
        'geo': qd['geo'],
        'orgs': orgs,
    }


def paginate(request, context):
    get_params = request.GET.copy()
    paginator = Paginator(context['orgs'], 20)
    page = request.GET.get('page')
    try:
        orgs_page = paginator.page(page)
    except PageNotAnInteger:
        orgs_page = paginator.page(1)
    except EmptyPage:
        orgs_page = paginator.page(paginator.num_pages)
    if 'page' in get_params:
        del get_params['page']
    context['orgs'] = orgs_page
    context['get_params'] = get_params.urlencode()


def index_view(request, page_app):
    if request.GET.get('display') == 'Cartographie':
        return HttpResponseRedirect('../cartographie/?' + request.GET.urlencode())
    context = get_index_context(request, page_app.networks, page_app.bdis)
    paginate(request, context)
    context['object'] = page_app
    return render_view('page_directory/index.html',
                       context,
                       (CSSMedia('selectable/css/dj.selectable.css', prefix_file=''),
                        JSMedia('selectable/js/jquery.dj.selectable.js', prefix_file=''),
                        CSSMedia('tagger/css/coop_tag.css', prefix_file=''),
                        JSMedia('tagger/js/jquery.autoSuggest.minified.js', prefix_file='')),
                       context_instance=RequestContext(request))


def detail_view(request, page_app, pk):
    org = get_object_or_404(Organization, pk=pk)
    if org.status != ORGANIZATION_STATUSES.VALIDATED:
        return render_view('page_directory/not_validated.html', {'object': page_app},
                           (), context_instance=RequestContext(request))
    calls = org.callfortenders_set.filter(deadline__gte=now()).order_by('deadline')
    get_params = request.GET.copy()
    return render_view('page_directory/detail.html',
                       {'object': page_app, 'org': org, 'calls': calls,
                        'get_params': get_params.urlencode()},
                       (),
                       context_instance=RequestContext(request))


PROVIDER_TITLES = (
    u'Identification',
    u'Type d\'organisation',
    u'Description',
    u'Classification',
    u'Données économiques',
    u'Témoignage',
    u'Documents',
    u'Partenaires',
    u'Localisation',
    u'Contacts',
    u'Membres',
    u'Références',
)

NOT_PROVIDER_TITLES = (
    u'Identification',
    u'Type d\'organisation',
    u'Description',
    u'Classification',
    u'Témoignage',
    u'Documents',
    u'Partenaires',
    u'Localisation',
    u'Contacts',
    u'Membres',
)

ORGANIZATION_MEDIA = (
    CSSMedia('tagger/css/coop_tag.css', prefix_file=''),
    JSMedia('tagger/js/jquery.autoSuggest.minified.js', prefix_file=''),
    CSSMedia('select2/select2.css', prefix_file=''),
    CSSMedia('css/select2-bootstrap3.css', prefix_file=''),
    JSMedia('select2/select2.min.js', prefix_file=''),
    JSMedia('../_tinymce/compressor/', prefix_file=''),
)

OFFER_MEDIA = (
    CSSMedia('tagger/css/coop_tag.css', prefix_file=''),
    JSMedia('tagger/js/jquery.autoSuggest.minified.js', prefix_file=''),
    CSSMedia('select2/select2.css', prefix_file=''),
    CSSMedia('css/select2-bootstrap3.css', prefix_file=''),
    JSMedia('select2/select2.min.js', prefix_file=''),
)


class OrganizationCreateView(CreateView):

    template_name = 'page_directory/create.html'
    model = Organization
    form_class = OrganizationForm1
    success_url = '/annuaire/p/modifier/1/'

    def dispatch(self, request, *args, **kwargs):
        if settings.REGION_SLUG == 'npdc' and request.method == 'GET' and request.META.get('HTTP_REFERER') != 'http://apes.sloli.fr/ls/index.php/survey/index':
            return HttpResponseRedirect('http://apes.sloli.fr/ls/index.php/survey/index/sid/28943/newtest/Y/lang/fr')
        if request.user.is_authenticated():
            return render_view('page_directory/should_logout.html',
                {}, (), context_instance=RequestContext(request))
        return super(OrganizationCreateView, self).dispatch(request, args, **kwargs)

    def get_initial(self):
        return {
            'first_name': self.request.GET.get('prenom'),
            'last_name': self.request.GET.get('nom'),
            'title': self.request.GET.get('structure'),
        }

    def get_form_kwargs(self):
        kwargs = super(OrganizationCreateView, self).get_form_kwargs()
        kwargs['propose'] = False
        kwargs['request'] = self.request
        return kwargs

    def render_to_response(self, context, **response_kwargs):
        assert response_kwargs == {}
        context['titles'] = NOT_PROVIDER_TITLES
        try:
            context['charte'] = Page.objects.get(title='Charte', website=self.request.website).app.text
        except Page.DoesNotExist:
            context['charte'] = u'<p>La page « Charte » n\'existe pas.</p>'
        return render_view(self.get_template_names(),
            context,
            ORGANIZATION_MEDIA,
            context_instance=RequestContext(self.request))

    def form_valid(self, form):
        response = super(OrganizationCreateView, self).form_valid(form)
        LogEntry.objects.log_action(
            user_id         = self.request.user.pk,
            content_type_id = ContentType.objects.get_for_model(self.object).pk,
            object_id       = self.object.pk,
            object_repr     = force_unicode(self.object),
            action_flag     = ADDITION
        )
        return response


add_view = OrganizationCreateView.as_view()


def propose_url(org, default_url):
    if org.is_provider and (not org.birth or not org.legal_status or not org.siret):
        return '/annuaire/p/modifier/1/?propose'
    if org.is_customer and not org.customer_type:
        return '/annuaire/p/modifier/1/?propose'
    if not org.brief_description:
        return '/annuaire/p/modifier/2/?propose'
    if org.is_customer and not org.activities.exists():
        return '/annuaire/p/modifier/3/?propose'
    if org.is_provider and not org.workforce:
        return '/annuaire/p/modifier/4/?propose'
    if org.is_provider and org.agreement_iae.filter(label=u'Conventionnement IAE').exists() and not (org.integration_workforce or org.annual_integration_number):
        return '/annuaire/p/modifier/4/?propose'
    if org.is_provider and not org.offer_set.exists():
        return '/annuaire/p/offre/ajouter/?propose'
    if org.status == 'I':
        org.status = 'P'
    org.transmission_date = date.today()
    org.save()
    return default_url


def propose_view(request, page_app):
    try:
        person = Person.objects.get(user=request.user)
    except Person.DoesNotExist:
        raise PermissionDenied
    org = person.my_organization()
    return HttpResponseRedirect(propose_url(org, '/mon-compte/'))


class OrganizationChangeView(UpdateView):

    template_name = 'page_directory/edit.html'
    success_url  = '/mon-compte/'
    model = Organization

    def dispatch(self, request, *args, **kwargs):
        try:
            self.step = int(kwargs['step'])
        except:
            self.step = 0
        self.propose = 'propose' in request.REQUEST
        return super(OrganizationChangeView, self).dispatch(request, args, **kwargs)

    def get_form_class(self):
        return self.forms[self.step]

    def get_object(self, queryset=None):
        try:
            person = Person.objects.get(user=self.request.user)
        except Person.DoesNotExist:
            raise PermissionDenied
        self.org = person.my_organization()
        if self.org and self.org.status == 'V':
            self.propose = True
        if self.org and self.org.is_provider:
            self.forms = PROVIDER_FORMS
            self.titles = PROVIDER_TITLES
        else:
            self.forms = NOT_PROVIDER_FORMS
            self.titles = NOT_PROVIDER_TITLES
        self.last_step = len(self.forms) - 1
        if self.step > self.last_step:
            self.step = self.last_step
        return self.org

    def get_form_kwargs(self):
        kwargs = super(OrganizationChangeView, self).get_form_kwargs()
        kwargs['propose'] = self.propose
        if self.step == 0:
            kwargs['request'] = self.request
        return kwargs

    def get_form(self, form_class):
        """ Force form bounding to set fields as required
        """
        kwargs = self.get_form_kwargs()
        if not 'data' in kwargs and self.propose and self.step in (1, 2, 3, 4):
            data = model_to_dict(self.object)
            if not data.get('tags'):
                data['tags'] = None
            kwargs['data'] = data
        return form_class(**kwargs)

    def get_context_data(self, **kwargs):
        kwargs.update({
            'step': {
                'current': self.step,
                'prev': str(self.step - 1) if self.step > 0 else None,
                'next': str(self.step + 1) if self.step < self.last_step else None,
                'count': self.last_step + 1,
            },
        })
        if self.step == 3 and self.org and self.org.is_provider:
            kwargs['message'] = u"Si vous souhaitez ajouter des termes dans les listes proposées (type de structures ESS, thématiques, garanties) faites parvenir un message à travers le <a href=\"/contact\">formulaire contact</a>"
        if self.step == self.last_step - int(self.org and self.org.is_provider):
            kwargs['message'] = u"Les interlocuteurs de votre structure : direction générale, service commercial…"
        if self.step == 11:
            kwargs['message'] = u"Références de clients professionnels permettant de valoriser la capacité de votre structure à répondre aux besoins d’acheteurs professionnels"
        return super(OrganizationChangeView, self).get_context_data(**kwargs)

    def get_success_url(self):
        if self.propose or self.step == self.last_step:
            default_url = self.success_url
        else:
            default_url = '/annuaire/p/modifier/%u/' % (self.step + 1)
        if self.propose:
            return propose_url(self.org, default_url)
        else:
            return default_url

    def render_to_response(self, context, **response_kwargs):
        assert response_kwargs == {}
        context['titles'] = self.titles
        context['title'] = context['titles'][self.step]
        return render_view(self.get_template_names(),
            context,
            ORGANIZATION_MEDIA,
            context_instance=RequestContext(self.request))

    def construct_change_message(self, form):
        """
        Construct a change message from a changed object.
        """
        change_message = []

        if hasattr(form, 'forms'):
            for added_object in form.new_objects:
                change_message.append(_('Added %(name)s "%(object)s".')
                                        % {'name': force_unicode(added_object._meta.verbose_name),
                                            'object': force_unicode(added_object)})
            for changed_object, changed_fields in form.changed_objects:
                change_message.append(_('Changed %(list)s for %(name)s "%(object)s".')
                                        % {'list': get_text_list(changed_fields, _('and')),
                                            'name': force_unicode(changed_object._meta.verbose_name),
                                            'object': force_unicode(changed_object)})
            for deleted_object in form.deleted_objects:
                change_message.append(_('Deleted %(name)s "%(object)s".')
                                        % {'name': force_unicode(deleted_object._meta.verbose_name),
                                            'object': force_unicode(deleted_object)})
        elif form.changed_data:
            change_message.append(_('Changed %s.') % get_text_list(form.changed_data, _('and')))

        change_message = ' '.join(change_message)
        return change_message or _('No fields changed.')

    def form_valid(self, form):
        response = super(OrganizationChangeView, self).form_valid(form)
        message = ''
        LogEntry.objects.log_action(
            user_id         = self.request.user.pk,
            content_type_id = ContentType.objects.get_for_model(Organization).pk,
            object_id       = self.org.pk,
            object_repr     = force_unicode(self.org),
            action_flag     = CHANGE,
            change_message  = self.construct_change_message(form)
        )
        return response

change_view = login_required(OrganizationChangeView.as_view())


@login_required
def offer_delete_view(request, page_app, pk):
    offer = get_object_or_404(Offer, pk=pk)
    if not offer.provider.engagement_set.filter(org_admin=True, person__user=request.user).exists():
        return HttpResponseForbidden('Opération interdite')
    LogEntry.objects.log_action(
        user_id         = request.user.pk,
        content_type_id = ContentType.objects.get_for_model(Organization).pk,
        object_id       = offer.provider.pk,
        object_repr     = force_unicode(offer.provider),
        action_flag     = CHANGE,
        change_message  = u'Offre "%s" supprimée.' % force_unicode(offer)
    )
    offer.delete()
    offer.provider.save() # Update modification date
    return HttpResponseRedirect('/mon-compte/p/mes-offres/')


@login_required
def offer_update_view(request, page_app, pk):
    offer = get_object_or_404(Offer, pk=pk)
    if not offer.provider.engagement_set.filter(org_admin=True, person__user=request.user).exists():
        return HttpResponseForbidden('Opération interdite')
    form = OfferForm(request.POST or None, instance=offer)
    form2 = OfferDocumentsFormset(request.POST or None, request.FILES or None, instance=offer)
    if form.is_valid() and form2.is_valid():
        offer = form.save()
        form2.save()
        offer.provider.save() # Update modification date
        LogEntry.objects.log_action(
            user_id         = request.user.pk,
            content_type_id = ContentType.objects.get_for_model(Organization).pk,
            object_id       = offer.provider.pk,
            object_repr     = force_unicode(offer.provider),
            action_flag     = CHANGE,
            change_message  = u'%s modifié pour l\'offre "%s".' % (get_text_list(form.changed_data, _('and')), force_unicode(offer))
        )
        return HttpResponseRedirect('/mon-compte/p/mes-offres/')
    return render_view('page_directory/offer_edit.html',
                       {'object': page_app, 'form': form, 'form2': form2, 'org': offer.provider},
                       OFFER_MEDIA,
                       context_instance=RequestContext(request))


@login_required
def offer_add_view(request, page_app):
    org = Organization.mine(request)
    if org is None:
        return HttpResponseForbidden('Opération interdite')
    form = OfferForm(request.POST or None)
    form2 = OfferDocumentsFormset(request.POST or None, request.FILES or None, instance=form.instance)
    if form.is_valid() and form2.is_valid():
        offer = form.save(commit=False)
        offer.provider = org
        offer.save()
        form.save_m2m()
        form2.save()
        org.save() # Update modification date
        LogEntry.objects.log_action(
            user_id         = request.user.pk,
            content_type_id = ContentType.objects.get_for_model(Organization).pk,
            object_id       = offer.provider.pk,
            object_repr     = force_unicode(offer.provider),
            action_flag     = CHANGE,
            change_message  = u'Offre "%s" ajoutée.' % force_unicode(offer)
        )
        return HttpResponseRedirect('/mon-compte/p/mes-offres/')
    return render_view('page_directory/offer_edit.html',
                       {'object': page_app, 'form': form, 'form2': form2, 'org': org, 'propose': 'propose' in request.GET},
                       OFFER_MEDIA,
                       context_instance=RequestContext(request))


#@login_required
def add_target_view(request):
    if 'title' in request.GET:
        form = AddTargetForm(request.GET)
    else:
        form = AddTargetForm()
    if form.is_valid():
        org = form.save(commit=False)
        org.save()
        if form.cleaned_data['tel']:
            Contact.objects.create(
                content_object=org,
                contact_medium=ContactMedium.objects.get(label=u'Téléphone'),
                content=form.cleaned_data['tel'])
        if form.cleaned_data['email']:
            Contact.objects.create(
                content_object=org,
                contact_medium=ContactMedium.objects.get(label=u'Courriel'),
                content=form.cleaned_data['email'])
        pk = org.pk
        form = AddTargetForm()
        status= 'OK'
    else:
        status = 'Error'
        pk = None
    t = get_template('page_directory/add_target.html')
    c = Context({'form': form})
    html = t.render(c)
    response = {'status': status, 'html': html, 'pk': pk}
    if 'html' in request.GET:
        return HttpResponse(html)
    else:
        return HttpResponse(json.dumps(response), content_type='application/json')


def subsectors_view(request, pk):
    sector = get_object_or_404(ActivityNomenclature, pk=pk)
    subsectors = sector.get_children()
    return render(request, 'page_directory/subsectors.html', {'subsectors': subsectors})
