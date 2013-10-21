# -*- coding: utf-8 -*-

from django.template import RequestContext
from ionyweb.website.rendering.utils import render_view
from .forms import (OrgSearch, OrganizationForm1, ORGANIZATION_FORMS, OfferForm)
from coop_local.models import (Organization, ActivityNomenclature, Engagement,
    Person, Location, Relation, Offer)
from coop_local.models.local_models import ORGANIZATION_STATUSES
from django.core.paginator import Paginator, PageNotAnInteger, EmptyPage
from django.http import HttpResponseRedirect
from django.shortcuts import get_object_or_404
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


def index_view(request, page_app):
    if request.GET.get('display') == 'Cartographie':
        return HttpResponseRedirect('../cartographie/?' + request.GET.urlencode())
    qd = request.GET.copy()
    if not qd.get('area_0') and 'area_1' in qd:
        del qd['area_1']
    form = OrgSearch(qd)
    if form.is_valid():
        orgs = Organization.geo_objects.filter(status=ORGANIZATION_STATUSES.VALIDATED)
        orgs = orgs.filter(
            Q(title__icontains=form.cleaned_data['q']) |
            Q(acronym__icontains=form.cleaned_data['q']) |
            Q(tagged_items__tag__name__icontains=form.cleaned_data['q']) |
            Q(located__location__city__icontains=form.cleaned_data['q']) |
            Q(activities__path__icontains=form.cleaned_data['q']) |
            Q(offer__activity__path__icontains=form.cleaned_data['q']))
        if form.cleaned_data['org_type'] == 'fournisseur':
            orgs = orgs.filter(is_provider=True)
            if form.cleaned_data['prov_type']:
                orgs = orgs.filter(agreement_iae=form.cleaned_data['prov_type'])
        if form.cleaned_data['org_type'] == 'acheteur-public':
            orgs = orgs.filter(is_customer=True, customer_type=1)
        if form.cleaned_data['org_type'] == 'acheteur-prive':
            orgs = orgs.filter(is_customer=True, customer_type=2)
        interim = form.cleaned_data['interim']
        if interim:
            orgs = orgs.filter(offer__activity__label__in=(u'mise à disposition de personnel', u'travail temporaire'))
        sector = form.cleaned_data['sector']
        descendants = sector and sector.get_descendants(include_self=True)
        if descendants:
            orgs = orgs.filter(offer__activity__in=descendants)
        area = form.cleaned_data.get('area')
        if area:
            try:
                radius = int(form.cleaned_data.get('radius'))
            except:
                radius = 0
            if radius != 0:
                center = area.polygon.centroid
                degrees = radius * 360 / 40000.
                q = Q(located__location__point__dwithin=(center, degrees))
                q |= Q(offer__area__polygon__dwithin=(center, degrees))
                orgs = orgs.filter(q)
            else:
                q = Q(located__location__point__contained=area.polygon)
                q |= Q(offer__area__polygon__intersects=area.polygon)
                orgs = orgs.filter(q)
        orgs = orgs.distinct()
    else:
        area = None
        orgs = Organization.objects.none()
    paginator = Paginator(orgs, 20)
    page = request.GET.get('page')
    try:
        orgs_page = paginator.page(page)
    except PageNotAnInteger:
        orgs_page = paginator.page(1)
    except EmptyPage:
        orgs_page = paginator.page(paginator.num_pages)
    get_params = request.GET.copy()
    if 'page' in get_params:
        del get_params['page']
    return render_view('page_directory/index.html',
                       {'object': page_app, 'form': form, 'orgs': orgs_page,
                        'get_params': get_params.urlencode()},
                       (CSSMedia('selectable/css/dj.selectable.css', prefix_file=''),
                        JSMedia('selectable/js/jquery.dj.selectable.js', prefix_file=''),
                        CSSMedia('tagger/css/coop_tag.css', prefix_file=''),
                        JSMedia('tagger/js/jquery.autoSuggest.minified.js', prefix_file='')),
                       context_instance=RequestContext(request))


def detail_view(request, page_app, pk):
    org = get_object_or_404(Organization, pk=pk, status=ORGANIZATION_STATUSES.VALIDATED)
    calls = org.callfortenders_set.filter(deadline__gte=now()).order_by('deadline')
    get_params = request.GET.copy()
    return render_view('page_directory/detail.html',
                       {'object': page_app, 'org': org, 'calls': calls,
                        'get_params': get_params.urlencode()},
                       (),
                       context_instance=RequestContext(request))


class OrganizationEditView(SessionWizardView):

    file_storage = FileSystemStorage(location=gettempdir() + '/django-coop/')
    template_name = 'page_directory/edit.html'

    def get_form_kwargs(self, step):
        cleaned_data1 = self.storage.get_step_data('1') or {}
        cleaned_data2 = self.storage.get_step_data('2') or {}
        is_customer = '1-is_customer' in cleaned_data1 or '2-is_customer' in cleaned_data2
        is_provider = '1-is_provider' in cleaned_data1 or '2-is_provider' in cleaned_data2
        return {
            'step': step,
            'is_customer': is_customer,
            'is_provider': is_provider,
        }

    def get_form(self, step=None, data=None, files=None):
        if step is None:
            step = self.steps.current
        kwargs = self.get_form_kwargs(step)
        kwargs.update({
            'data': data,
            'files': files,
            'prefix': self.get_form_prefix(step, self.form_list[step]),
        })
        initial = self.get_form_initial(step)
        if initial:
            kwargs['initial'] = initial
        kwargs.setdefault('instance', self.get_form_instance(step))
        return self.form_list[step](**kwargs)


ORGANIZATION_TITLES = (
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

ORGANIZATION_MEDIA = (
    CSSMedia('tagger/css/coop_tag.css', prefix_file=''),
    JSMedia('tagger/js/jquery.autoSuggest.minified.js', prefix_file=''),
    CSSMedia('select2/select2.css', prefix_file=''),
    CSSMedia('css/select2-bootstrap3.css', prefix_file=''),
    JSMedia('select2/select2.min.js', prefix_file=''),
    JSMedia('../_tinymce/compressor/', prefix_file=''),
)

OFFER_MEDIA = (
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
        if request.user.is_authenticated():
            return render_view('page_directory/should_logout.html',
                {}, (), context_instance=RequestContext(request))
        return super(OrganizationCreateView, self).dispatch(request, args, **kwargs)

    def get_form_kwargs(self):
        kwargs = super(OrganizationCreateView, self).get_form_kwargs()
        kwargs['propose'] = False
        kwargs['request'] = self.request
        return kwargs

    def render_to_response(self, context, **response_kwargs):
        assert response_kwargs == {}
        context['titles'] = ORGANIZATION_TITLES[:-1]
        try:
            context['charte'] = Page.objects.get(title='Charte').app.text
        except Page.DoesNotExist:
            context['charte'] = u'<p>La page « Charte » n\'existe pas.</p>'
        return render_view(self.get_template_names(),
            context,
            ORGANIZATION_MEDIA,
            context_instance=RequestContext(self.request))

add_view = OrganizationCreateView.as_view()


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
            self.forms = ORGANIZATION_FORMS
            self.titles = ORGANIZATION_TITLES
        else:
            self.forms = ORGANIZATION_FORMS[:-1]
            self.titles = ORGANIZATION_TITLES[:-1]
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
        kwargs = self.get_form_kwargs()
        if not 'data' in kwargs and self.propose and self.step in (1, 2, 4):
            kwargs['data'] = model_to_dict(self.object)
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
        return super(OrganizationChangeView, self).get_context_data(**kwargs)

    def get_success_url(self):
        if self.propose:
            if not self.org.birth or not self.org.legal_status or not self.org.siret:
                return '/annuaire/p/modifier/1/?propose'
            if not self.org.brief_description:
                return '/annuaire/p/modifier/2/?propose'
            if not self.org.workforce:
                return '/annuaire/p/modifier/4/?propose'
            if self.org.agreement_iae.filter(label=u'Conventionnement IAE').exists() and not (self.org.integration_workforce or self.org.annual_integration_number):
                return '/annuaire/p/modifier/4/?propose'
            if self.org.is_provider and not self.org.offer_set.exists():
                return '/annuaire/p/offre/ajouter/?propose'
            if self.org.status == 'I':
                self.org.status = 'P'
            self.org.transmission_date = date.today()
            self.org.save()
        if self.propose or self.step == self.last_step:
            return self.success_url
        return '/annuaire/p/modifier/%u/' % (self.step + 1)

    def render_to_response(self, context, **response_kwargs):
        assert response_kwargs == {}
        context['titles'] = self.titles
        context['title'] = context['titles'][self.step]
        return render_view(self.get_template_names(),
            context,
            ORGANIZATION_MEDIA,
            context_instance=RequestContext(self.request))

change_view = login_required(OrganizationChangeView.as_view())


@login_required
def offer_delete_view(request, page_app, pk):
    offer = get_object_or_404(Offer, pk=pk)
    if not offer.provider.engagement_set.filter(org_admin=True, person__user=request.user).exists():
        return HttpResponseForbidden('Opération interdite')
    offer.delete()
    return HttpResponseRedirect('/mon-compte/p/mes-offres/')


@login_required
def offer_update_view(request, page_app, pk):
    offer = get_object_or_404(Offer, pk=pk)
    if not offer.provider.engagement_set.filter(org_admin=True, person__user=request.user).exists():
        return HttpResponseForbidden('Opération interdite')
    form = OfferForm(request.POST or None, instance=offer)
    if form.is_valid():
        form.save()
        return HttpResponseRedirect('/mon-compte/p/mes-offres/')
    return render_view('page_directory/offer_edit.html',
                       {'object': page_app, 'form': form, 'org': offer.provider},
                       OFFER_MEDIA,
                       context_instance=RequestContext(request))


@login_required
def offer_add_view(request, page_app):
    org = Organization.mine(request)
    if org is None:
        return HttpResponseForbidden('Opération interdite')
    form = OfferForm(request.POST or None)
    if form.is_valid():
        offer = form.save(commit=False)
        offer.provider = org
        offer.save()
        form.save_m2m()
        return HttpResponseRedirect('/mon-compte/p/mes-offres/')
    return render_view('page_directory/offer_edit.html',
                       {'object': page_app, 'form': form, 'org': org, 'propose': 'propose' in request.GET},
                       OFFER_MEDIA,
                       context_instance=RequestContext(request))
