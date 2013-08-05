# -*- coding: utf-8 -*-

from django.template import RequestContext
from ionyweb.website.rendering.utils import render_view
from .forms import (OrgSearch, OrganizationForm1, OrganizationForm2,
    EngagementForm)
from coop_local.models import Organization, ActivityNomenclature
from coop_local.models.local_models import ORGANIZATION_STATUSES
from django.core.paginator import Paginator, PageNotAnInteger, EmptyPage
from django.http import HttpResponseRedirect
from django.shortcuts import get_object_or_404
from django.contrib.auth.decorators import login_required


from ionyweb.website.rendering.medias import CSSMedia, JSMedia #, JSAdminMedia
MEDIAS = (
    # App CSS
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


@login_required
def add_view(request, page_app):

    if request.method == "POST":
        form1 = OrganizationForm1(request.POST)
        form2 = EngagementForm(request.POST)
        if form1.is_valid() and form2.is_valid():
            org = form1.save()
            eng = form2.save(commit=False)
            eng.person = request.user.get_profile()
            eng.organization = org
            eng.org_admin = True
            eng.save()
            return HttpResponseRedirect('../modifier2/')
    else:
        form1 = OrganizationForm1()
        form2 = EngagementForm()

    return render_view('page_directory/edit.html',
        {'form1': form1, 'form2': form2,
         'title': u'Ajouter un acheteur / Fournisseur'},
        MEDIAS,
        context_instance=RequestContext(request))


def edit1_view(request, page_app, pk):

    org = get_object_or_404(Organization, pk=pk,
        engagement__person__user=request.user, engagement__org_admin=True)

    if request.method == "POST":
        form = OrganizationForm1(request.POST, instance=org)
        if form.is_valid():
            org = form.save()
            return HttpResponseRedirect('../modifier2/')
    else:
        form = OrganizationForm1(instance=org)

    return render_view('page_directory/edit.html',
        {'form1': form, 'title': u'Modifier un acheteur / Fournisseur'},
        MEDIAS,
        context_instance=RequestContext(request))


def edit2_view(request, page_app, pk):

    org = get_object_or_404(Organization, pk=pk,
        engagement__person__user=request.user, engagement__org_admin=True)

    if request.method == "POST":
        form = OrganizationForm2(request.POST, instance=org)
        if form.is_valid():
            org = form.save()
            return HttpResponseRedirect(org.get_absolute_url())
    else:
        form = OrganizationForm2(instance=org)

    return render_view('page_directory/edit.html',
        {'form1': form, 'title': u'Modifier un acheteur / Fournisseur'},
        MEDIAS,
        context_instance=RequestContext(request))
