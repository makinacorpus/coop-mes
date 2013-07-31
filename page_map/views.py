# -*- coding: utf-8 -*-

from django.template import RequestContext
from ionyweb.website.rendering.utils import render_view
from .forms import OrgSearch
from coop_local.models import Organization, ActivityNomenclature, Area
from coop_local.models.local_models import ORGANIZATION_STATUSES
from django.core.paginator import Paginator, PageNotAnInteger, EmptyPage
from django.shortcuts import get_object_or_404
from django.http import HttpResponseRedirect
from django.conf import settings

from ionyweb.website.rendering.medias import CSSMedia, JSMedia #, JSAdminMedia
MEDIAS = (
    # App CSS
    CSSMedia('leaflet/leaflet.css', prefix_file=''),
    # App JS
    JSMedia('leaflet/leaflet-src.js', prefix_file=''),
    JSMedia('leaflet/leaflet.extras.js', prefix_file=''),
    # Actions JSAdmin
    # JSAdminMedia('page_map_actions.js'),
    )

def index_view(request, page_app):
    if request.GET.get('display') == 'Annuaire':
        return HttpResponseRedirect('../annuaire/?' + request.GET.urlencode())
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
    get_params = request.GET.copy()
    coords = Area.objects.get(label=settings.REGION_LABEL).polygon.envelope.coords[0]
    print coords
    bounds = (coords[0][1], coords[0][0], coords[2][1], coords[2][0])
    return render_view('page_map/index.html',
                       {'object': page_app, 'form': form, 'orgs': orgs,
                        'bounds': bounds, 'get_params': get_params.urlencode()},
                       MEDIAS,
                       context_instance=RequestContext(request))
