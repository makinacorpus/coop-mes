# -*- coding: utf-8 -*-

from django.template import RequestContext
from ionyweb.website.rendering.utils import render_view
from .forms import CallSearch
from coop_local.models import CallForTenders, Organization
from django.core.paginator import Paginator, PageNotAnInteger, EmptyPage
from django.shortcuts import get_object_or_404
from django.http import HttpResponseRedirect
from coop_local.models.local_models import ORGANIZATION_STATUSES
from django.utils.timezone import now
from datetime import timedelta

from ionyweb.website.rendering.medias import CSSMedia, JSMedia #, JSAdminMedia
MEDIAS = (
    # App CSS
    #CSSMedia('page_calls/bootstrap.min.css'),
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
        if form.cleaned_data['clause']:
            calls = calls.filter(clauses__contains=form.cleaned_data['clause'])
        if form.cleaned_data['organization']:
            calls = calls.filter(organization=form.cleaned_data['organization'])
        sector = form.cleaned_data['sector']
        descendants = sector and sector.get_descendants(include_self=True)
        if descendants:
            calls = calls.filter(activity__in=descendants)
        calls = calls.distinct()
        if form.cleaned_data['period2'] == 'archive':
            calls = calls.filter(deadline__lt=now())
            if form.cleaned_data['period']:
                calls = calls.filter(deadline__gte=now()-timedelta(days=int(form.cleaned_data['period'])))
        elif form.cleaned_data['period2'] != 'tout':
            calls = calls.filter(deadline__gte=now())
            if form.cleaned_data['period']:
                calls = calls.filter(deadline__lt=now()+timedelta(days=int(form.cleaned_data['period'])))
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
