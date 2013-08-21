# -*- coding: utf-8 -*-

from django.template import RequestContext
from ionyweb.website.rendering.utils import render_view
from .forms import OrgSearch
from coop_local.models import Organization, ActivityNomenclature, Area, Location
from coop_local.models.local_models import ORGANIZATION_STATUSES
from django.core.paginator import Paginator, PageNotAnInteger, EmptyPage
from django.shortcuts import get_object_or_404
from django.http import HttpResponseRedirect
from django.conf import settings
from django.db.models import Q
from django.contrib.gis.measure import Distance

from ionyweb.website.rendering.medias import CSSMedia, JSMedia #, JSAdminMedia
MEDIAS = (
    CSSMedia('leaflet/leaflet.css', prefix_file=''),
    JSMedia('leaflet/leaflet-src.js', prefix_file=''),
    JSMedia('leaflet/leaflet.extras.js', prefix_file=''),
    CSSMedia('selectable/css/dj.selectable.css', prefix_file=''),
    JSMedia('selectable/js/jquery.dj.selectable.js', prefix_file=''),
)

def index_view(request, page_app):
    if request.GET.get('display') == 'Annuaire':
        return HttpResponseRedirect('../annuaire/?' + request.GET.urlencode())
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
            print descendants
        else:
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
            orgs = orgs.filter(pref_address__point__distance_lte=(area.polygon, Distance(km=radius)))
        orgs = orgs.distinct()
    else:
        area = None
        orgs = Organization.objects.none()
    get_params = request.GET.copy()
    if area is None:
        bounds = Area.objects.filter(label=settings.REGION_LABEL).extent()
    else:
        bounds = Location.objects.filter(pref_address_org__in=orgs).extent()
    return render_view('page_map/index.html',
                       {'object': page_app, 'form': form, 'orgs': orgs,
                        'bounds': bounds, 'get_params': get_params.urlencode()},
                       MEDIAS,
                       context_instance=RequestContext(request))
