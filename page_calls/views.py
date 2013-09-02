# -*- coding: utf-8 -*-

from django.template import RequestContext
from ionyweb.website.rendering.utils import render_view
from .forms import CallSearch, CallForm
from coop_local.models import CallForTenders, Organization
from django.core.paginator import Paginator, PageNotAnInteger, EmptyPage
from django.shortcuts import get_object_or_404
from django.http import HttpResponseRedirect, HttpResponseForbidden
from coop_local.models.local_models import ORGANIZATION_STATUSES
from django.utils.timezone import now
from datetime import timedelta
from django.db.models import Q
from django.contrib.auth.decorators import login_required

from ionyweb.website.rendering.medias import CSSMedia, JSMedia #, JSAdminMedia
MEDIAS = (
    CSSMedia('select2/select2.css', prefix_file=''),
    CSSMedia('css/select2-bootstrap3.css', prefix_file=''),
    JSMedia('select2/select2.min.js', prefix_file=''),
    CSSMedia('datetimepicker/css/datetimepicker.css', prefix_file=''),
    JSMedia('datetimepicker/js/bootstrap-datetimepicker.min.js', prefix_file=''),
    JSMedia('datetimepicker/js/locales/bootstrap-datetimepicker.fr.js', prefix_file=''),
)

def index_view(request, page_app):
    qd = request.GET.copy()
    form = CallSearch(qd)
    if form.is_valid():
        calls = CallForTenders.geo_objects.filter(organization__status=ORGANIZATION_STATUSES.VALIDATED)
        calls = calls.filter(
            Q(title__icontains=form.cleaned_data['q']) |
            Q(area__label__icontains=form.cleaned_data['q']) |
            Q(activity__path__icontains=form.cleaned_data['q']) |
            Q(organization__title__icontains=form.cleaned_data['q']) |
            Q(organization__acronym__icontains=form.cleaned_data['q']))
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
        if form.cleaned_data['period'] == 'archive':
            calls = calls.filter(deadline__lt=now())
        elif form.cleaned_data['period'] != 'tout':
            calls = calls.filter(deadline__gte=now())
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
                       (),
                       context_instance=RequestContext(request))


def detail_view(request, page_app, pk):
    call = get_object_or_404(CallForTenders, pk=pk)
    get_params = request.GET.copy()
    return render_view('page_calls/detail.html',
                       {'object': page_app, 'call': call,
                        'get_params': get_params.urlencode()},
                       (),
                       context_instance=RequestContext(request))


@login_required
def delete_view(request, page_app, pk):
    call = get_object_or_404(CallForTenders, pk=pk)
    if not call.organization.engagement_set.filter(org_admin=True, person__user=request.user).exists():
        return HttpResponseForbidden('Opération interdite')
    call.delete()
    return HttpResponseRedirect('/mon-compte/p/mes-appels-doffres/')


@login_required
def update_view(request, page_app, pk):
    call = get_object_or_404(CallForTenders, pk=pk)
    if not call.organization.engagement_set.filter(org_admin=True, person__user=request.user).exists():
        return HttpResponseForbidden('Opération interdite')
    form = CallForm(request.POST or None, instance=call)
    if form.is_valid():
        form.save()
        return HttpResponseRedirect('/mon-compte/p/mes-appels-doffres/')
    return render_view('page_calls/edit.html',
                       {'object': page_app, 'form': form},
                       MEDIAS,
                       context_instance=RequestContext(request))


@login_required
def add_view(request, page_app):
    org = Organization.mine(request)
    if org is None:
        return HttpResponseForbidden('Opération interdite')
    form = CallForm(request.POST or None)
    if form.is_valid():
        call = form.save(commit=False)
        call.organization = org
        call.save()
        return HttpResponseRedirect('/mon-compte/p/mes-appels-doffres/')
    return render_view('page_calls/edit.html',
                       {'object': page_app, 'form': form},
                       MEDIAS,
                       context_instance=RequestContext(request))
