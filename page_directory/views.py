# -*- coding: utf-8 -*-

from django.template import RequestContext
from ionyweb.website.rendering.utils import render_view
from .forms import OrgSearch
from coop_local.models import Organization, ActivityNomenclature
from coop_local.models.local_models import ORGANIZATION_STATUSES
from django.core.paginator import Paginator, PageNotAnInteger, EmptyPage
from django.shortcuts import get_object_or_404
from django.http import HttpResponseRedirect

from ionyweb.website.rendering.medias import CSSMedia, JSMedia #, JSAdminMedia
MEDIAS = (
    # App CSS
    CSSMedia('page_directory/bootstrap.min.css'),
    CSSMedia('leaflet/leaflet.css', prefix_file=''),
    # App JS
    JSMedia('leaflet/leaflet-src.js', prefix_file=''),
    JSMedia('leaflet/leaflet.extras.js', prefix_file=''),
    # Actions JSAdmin
    # JSAdminMedia('page_directory_actions.js'),
    )

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
            print descendants
        else:
            sector = form.cleaned_data['sector']
            descendants = sector and sector.get_descendants(include_self=True)
        if descendants:
            orgs = orgs.filter(offer__activity__in=descendants)
        if form.cleaned_data['area']:
            orgs = orgs.filter(offer__area__polygon__intersects=form.cleaned_data['area'].polygon)
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
                       MEDIAS,
                       context_instance=RequestContext(request))


def detail_view(request, page_app, pk):
    org = get_object_or_404(Organization, pk=pk)
    get_params = request.GET.copy()
    return render_view('page_directory/detail.html',
                       {'object': page_app, 'org': org,
                        'get_params': get_params.urlencode()},
                       MEDIAS,
                       context_instance=RequestContext(request))


def add_view(request, page_app):
    return render_view('page_directory/add.html',
                       {'object': page_app},
                       MEDIAS,
                       context_instance=RequestContext(request))
