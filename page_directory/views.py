# -*- coding: utf-8 -*-

from django.template import RequestContext
from ionyweb.website.rendering.utils import render_view
from .forms import (OrgSearch,  OrganizationForm0, OrganizationForm1,
    OrganizationForm2, OrganizationForm3, OrganizationForm4)
from coop_local.models import (Organization, ActivityNomenclature, Engagement,
    Person, Location)
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
from django.contrib.auth import login, authenticate
from django.db.models import Q
from django.utils.timezone import now
from django.contrib.gis.measure import Distance


def index_view(request, page_app):
    if request.GET.get('display') == 'Cartographie':
        return HttpResponseRedirect('../cartographie/?' + request.GET.urlencode())
    qd = request.GET.copy()
    if 'interim' not in qd:
        qd['interim'] = '2'
    if not qd.get('area_0') and 'area_1' in qd:
        del qd['area_1']
    form = OrgSearch(qd)
    if form.is_valid():
        orgs = Organization.geo_objects.filter(status=ORGANIZATION_STATUSES.VALIDATED)
        orgs = orgs.filter(
            Q(title__icontains=form.cleaned_data['q']) |
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
        if interim == '1':
            descendants = ActivityNomenclature.objects.filter(label__in=(u'mise à disposition de personnel', u'travail temporaire'))
        else:
            sector = form.cleaned_data['sector']
            descendants = sector and sector.get_descendants(include_self=True)
        if descendants:
            orgs = orgs.filter(offer__activity__in=descendants)
        if form.cleaned_data['area']:
            try:
                radius = int(form.cleaned_data.get('radius'))
            except:
                radius = 0
            if radius != 0:
                orgs = orgs.filter(pref_address__point__distance_lte=(form.cleaned_data['area'].polygon, Distance(km=radius)))
            else:
                orgs = orgs.filter(pref_address__point__contained=form.cleaned_data['area'].polygon)
        orgs = orgs.distinct()
    else:
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
                        JSMedia('selectable/js/jquery.dj.selectable.js', prefix_file='')),
                       context_instance=RequestContext(request))


def detail_view(request, page_app, pk):
    org = get_object_or_404(Organization, pk=pk)
    calls = org.callfortenders_set.filter(deadline__gte=now()).order_by('deadline')
    get_params = request.GET.copy()
    return render_view('page_directory/detail.html',
                       {'object': page_app, 'org': org, 'calls': calls,
                        'get_params': get_params.urlencode()},
                       (),
                       context_instance=RequestContext(request))

organization_create_forms = (
    OrganizationForm0,
    OrganizationForm1,
    OrganizationForm2,
    OrganizationForm3,
    OrganizationForm4,
)

class OrganizationCreateView(SessionWizardView):

    file_storage = FileSystemStorage(location=gettempdir() + '/django-coop/')
    template_name = 'page_directory/edit.html'

    def get_form_kwargs(self, step):
        return {'step': step}

    def done(self, forms, **kwargs):
        # User
        user = forms[0].save()
        user = authenticate(username=user.username, password=forms[0].cleaned_data['password1'])
        login(self.request, user)
        # Person
        person = forms[1].save(commit=False)
        person.user = user
        person.username = user.username
        person.save()
        # Organization
        organization = forms[2].save()
        for form in forms[3:]:
            for field, value in form.cleaned_data.iteritems():
                setattr(organization, field, value)
        organization.save()
        # Engagement
        engagement = Engagement()
        engagement.person = person
        engagement.organization = organization
        engagement.org_admin = True
        engagement.tel = forms[1].cleaned_data['tel']
        engagement.email = forms[1].cleaned_data['email']
        engagement.role = forms[1].cleaned_data['role']
        engagement.save()
        return HttpResponseRedirect('/mon-compte/')

    def render_to_response(self, context, **response_kwargs):
        assert response_kwargs == {}
        context['titles'] = (
            u'Codes d\'accès',
            u'Données personelles',
            u'Type d\'organisation',
            u'Description',
            u'Catégories',
        )
        if self.steps.current == '0':
            try:
                context['charte'] = Page.objects.get(title='Charte').app.text
            except Page.DoesNotExist:
                context['charte'] = u'<p>La page « Charte » n\'existe pas.</p>'
        return render_view(self.get_template_names(),
            context,
            (CSSMedia('tagger/css/coop_tag.css', prefix_file=''),
            JSMedia('tagger/js/jquery.autoSuggest.minified.js', prefix_file=''),
            CSSMedia('select2/select2.css', prefix_file=''),
            JSMedia('select2/select2.min.js', prefix_file='')),
            context_instance=RequestContext(self.request))

add_view = OrganizationCreateView.as_view(organization_create_forms)


organization_change_forms = (
    OrganizationForm1,
    OrganizationForm2,
    OrganizationForm3,
    OrganizationForm4,
)

class OrganizationChangeView(SessionWizardView):

    file_storage = FileSystemStorage(location=gettempdir() + '/django-coop/')
    template_name = 'page_directory/edit.html'

    def get_form_instance(self, step):
        if step == '0':
            return self.person
        else:
            return self.organization

    def get_form_kwargs(self, step):
        return {'step': step}

    def get_form_initial(self, step):
        pk = self.kwargs['pk']
        self.organization = get_object_or_404(Organization, pk=pk)
        self.person = Person.objects.get(user=self.request.user)
        self.engagement = Engagement.objects.get(person=self.person, organization=self.organization)
        if step == '0':
            return {'tel': self.engagement.tel, 'role': self.engagement.role}
        return {}

    def done(self, forms, **kwargs):
        # Person
        forms[0].save()
        # Organization
        for form in forms[1:]:
            form.save()
        # Engagement
        self.engagement.tel = forms[0].cleaned_data['tel']
        self.engagement.email = forms[0].cleaned_data['email']
        self.engagement.role = forms[0].cleaned_data['role']
        self.engagement.save()
        return HttpResponseRedirect('/mon-compte/')

    def render_to_response(self, context, **response_kwargs):
        assert response_kwargs == {}
        context['titles'] = (
            u'Données personelles',
            u'Type d\'organisation',
            u'Description',
            u'Catégories',
        )
        return render_view(self.get_template_names(),
            context,
            (CSSMedia('tagger/css/coop_tag.css', prefix_file=''),
            JSMedia('tagger/js/jquery.autoSuggest.minified.js', prefix_file=''),
            CSSMedia('select2/select2.css', prefix_file=''),
            JSMedia('select2/select2.min.js', prefix_file='')),
            context_instance=RequestContext(self.request))

change_view = login_required(OrganizationChangeView.as_view(organization_change_forms))
