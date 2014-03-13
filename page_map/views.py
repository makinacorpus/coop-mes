# -*- coding: utf-8 -*-

from django.template import RequestContext
from ionyweb.website.rendering.utils import render_view
from page_directory.search_form import OrgSearch
from coop_local.models import Organization, ActivityNomenclature, Area, Location
from coop_local.models.local_models import ORGANIZATION_STATUSES
from django.core.paginator import Paginator, PageNotAnInteger, EmptyPage
from django.shortcuts import get_object_or_404
from django.http import HttpResponseRedirect
from django.conf import settings
from django.db.models import Q
from django.contrib.gis.geos import Point, MultiPoint
from ionyweb.page.models import Page

from ionyweb.website.rendering.medias import CSSMedia, JSMedia #, JSAdminMedia
MEDIAS = (
    CSSMedia('leaflet/leaflet.css', prefix_file=''),
    CSSMedia('leaflet/MarkerCluster.css', prefix_file=''),
    CSSMedia('leaflet/MarkerCluster.Default.css', prefix_file=''),
    JSMedia('leaflet/leaflet-src.js', prefix_file=''),
    JSMedia('leaflet/leaflet.extras.js', prefix_file=''),
    JSMedia('leaflet/leaflet.markercluster.js', prefix_file=''),
    CSSMedia('selectable/css/dj.selectable.css', prefix_file=''),
    JSMedia('selectable/js/jquery.dj.selectable.js', prefix_file=''),
)

def get_index_context(request, bound_area=None, bdis=False):
    qd = request.GET.copy()
    if not qd.get('geo'):
        qd['geo'] = '1'
    if not qd.get('area_0') and 'area_1' in qd:
        del qd['area_1']
    if 'dep' in qd:
        try:
            area = Area.objects.get(reference=qd['dep'], area_type__txt_idx='DEP')
        except Area.DoesNotExist:
            pass
        else:
            qd['area_0'] = area.label
            qd['area_1'] = area.pk
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
            orgs = orgs.filter(
                Q(offer__activity__label__iexact=(u'mise à disposition de personnel')) |
                Q(offer__activity__label__iexact=(u'travail temporaire')))
        sector = form.cleaned_data['sector']
        descendants = sector and sector.get_descendants(include_self=True)
        if descendants:
            orgs = orgs.filter(offer__activity__in=descendants)
        geo = qd.get('geo')
        area = form.cleaned_data.get('area')
        if area:
            try:
                radius = int(form.cleaned_data.get('radius'))
            except:
                radius = 0
            if radius != 0:
                center = area.polygon.centroid
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
        orgs = orgs.distinct()
    else:
        area = None
        orgs = Organization.objects.none()
    get_params = request.GET.copy()
    if area is None or geo == '2':
        if bound_area:
            bounds = bound_area.polygon.extent
        else:
            bounds = Area.objects.filter(label=settings.REGION_LABEL).extent()
    elif area and radius:
        bounds = MultiPoint(Point(center.x - degrees, center.y - degrees), Point(center.x + degrees, center.y + degrees)).extent
    else:
        bounds = area.polygon.extent
    return {
        'form': form,
        'geo': qd['geo'],
        'orgs': orgs,
        'area': area,
        'bounds': bounds,
        'get_params': get_params.urlencode()
    }


def index_view(request, page_app):
    if request.GET.get('display') == 'Annuaire':
        return HttpResponseRedirect('../annuaire/?' + request.GET.urlencode())
    context = get_index_context(request, bdis=page_app.bdis)
    context['object'] = page_app
    if page_app.bdis:
        context['iframe'] = Page.objects.get(slug='iframe', website=request.website).app
    return render_view('page_map/index.html',
                       context,
                       MEDIAS,
                       context_instance=RequestContext(request))
