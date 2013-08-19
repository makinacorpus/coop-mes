# -*- coding: utf-8 -*-

from django.template import RequestContext
from ionyweb.website.rendering.utils import render_view
from .forms import (OrgSearch,  OrganizationForm0, OrganizationForm1,
    OrganizationForm2, OrganizationForm3, OrganizationForm4)
from coop_local.models import Organization, ActivityNomenclature
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


def index_view(request, page_app):
    if request.GET.get('display') == 'Cartographie':
        return HttpResponseRedirect('../cartographie/?' + request.GET.urlencode())
    qd = request.GET.copy()
    if 'interim' not in qd:
        qd['interim'] = '2'
    form = OrgSearch(qd)
    if form.is_valid():
        orgs = Organization.geo_objects.filter(status=ORGANIZATION_STATUSES.VALIDATED)
        orgs = orgs.filter(title__icontains=form.cleaned_data['q'])
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
                       (),
                       context_instance=RequestContext(request))


def detail_view(request, page_app, pk):
    org = get_object_or_404(Organization, pk=pk)
    get_params = request.GET.copy()
    return render_view('page_directory/detail.html',
                       {'object': page_app, 'org': org,
                        'get_params': get_params.urlencode()},
                       (),
                       context_instance=RequestContext(request))

organization_forms = (
    OrganizationForm0,
    OrganizationForm1,
    OrganizationForm2,
    OrganizationForm3,
    OrganizationForm4,
)

class OrganizationView(SessionWizardView):

    file_storage = FileSystemStorage(location=gettempdir() + '/django-coop/')

    def get_form_instance(self, step):
        if not 'pk' in self.kwargs:
            return None
        pk = self.kwargs['pk']
        instance = get_object_or_404(Organization, pk=pk)
        return instance

    def get_template_names(self):
        return 'page_directory/edit%s.html' % self.steps.current

    def done(self, form_list, **kwargs):
        #do_something_with_the_form_data(form_list)
        return HttpResponseRedirect('/')

    def render_to_response(self, context, **response_kwargs):
        assert response_kwargs == {}
        if self.steps.current == '0':
            try:
                context['charte'] = Page.objects.get(title='Charte').app.text
            except Page.DoesNotExist:
                context['charte'] = u'<p>La page « Charte » n\'existe pas.</p>'
        return render_view(self.get_template_names(),
            context,
            (CSSMedia('tagger/css/coop_tag.css', prefix_file=''), JSMedia('tagger/js/jquery.autoSuggest.minified.js', prefix_file='')),
            context_instance=RequestContext(self.request))

add_view = login_required(OrganizationView.as_view(organization_forms))
change_view = login_required(OrganizationView.as_view(organization_forms))
