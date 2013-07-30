# -*- coding: utf-8 -*-

from django.template import RequestContext
from ionyweb.website.rendering.utils import render_view
from .forms import CallSearch
from coop_local.models import CallForTenders, Organization
from django.core.paginator import Paginator, PageNotAnInteger, EmptyPage
from django.shortcuts import get_object_or_404
from django.http import HttpResponseRedirect
from coop_local.models.local_models import ORGANIZATION_STATUSES

from ionyweb.website.rendering.medias import CSSMedia, JSMedia #, JSAdminMedia
MEDIAS = (
    # App CSS
    CSSMedia('page_calls/bootstrap.min.css'),
    # App JS
    # Actions JSAdmin
    # JSAdminMedia('page_calls_actions.js'),
    )

def index_view(request, page_app):
    qd = request.GET.copy()
    form = CallSearch(qd)
    if form.is_valid():
        calls = CallForTenders.geo_objects.filter(organization__status=ORGANIZATION_STATUSES.VALIDATED)
        if form.cleaned_data['org_type'] == 'public':
            calls = calls.filter(organization__is_customer=True, organization__customer_type=1)
        if form.cleaned_data['org_type'] == 'prive':
            calls = calls.filter(organization__is_customer=True, organization__customer_type=2)
        sector = form.cleaned_data['sector']
        descendants = sector and sector.get_descendants(include_self=True)
        if descendants:
            calls = calls.filter(activity__in=descendants)
        if form.cleaned_data['area']:
            calls = calls.filter(area__polygon__intersects=form.cleaned_data['area'].polygon)
        calls = calls.distinct()
    else:
        calls = Organization.objects.none()
    paginator = Paginator(calls, 20)
    page = request.GET.get('page')
    try:
        calls_page = paginator.page(page)
    except PageNotAnInteger:
        calls_page = paginator.page(1)
    except EmptyPage:
        calls_page = paginator.page(paginator.num_pages)
    get_params = request.GET.copy()
    if 'page' in get_params:
        del get_params['page']
    return render_view('page_calls/index.html',
                       {'object': page_app, 'form': form, 'calls': calls_page,
                        'get_params': get_params.urlencode()},
                       MEDIAS,
                       context_instance=RequestContext(request))


def detail_view(request, page_app, pk):
    call = get_object_or_404(CallForTenders, pk=pk)
    get_params = request.GET.copy()
    return render_view('page_calls/detail.html',
                       {'object': page_app, 'call': call,
                        'get_params': get_params.urlencode()},
                       MEDIAS,
                       context_instance=RequestContext(request))
