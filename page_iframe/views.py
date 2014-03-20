# -*- coding: utf-8 -*-

from django.template import RequestContext
from ionyweb.website.rendering.utils import render_view
from .models import IFrame
from page_directory.views import get_index_context, paginate
from page_map.views import get_index_context as get_map_context
from django.shortcuts import get_object_or_404
from django.http import HttpResponseRedirect
from coop_local.models import Organization
from coop_local.models.local_models import ORGANIZATION_STATUSES
from django.utils.timezone import now

# from ionyweb.website.rendering.medias import CSSMedia, JSMedia, JSAdminMedia
MEDIAS = (
    # App CSS
    # CSSMedia('page_iframe.css'),
    # App JS
    # JSMedia('page_iframe.js'),
    # Actions JSAdmin
    # JSAdminMedia('page_iframe_actions.js'),
)


def iframe_filter(page_app, obj, context):
    context['target'] = 'target="_blank"'
    if page_app.bdis:
        context['orgs'] = context['orgs'].filter(is_bdis=True)
    else:
        context['orgs'] = context['orgs'].filter(is_pasr=True)
    if obj.area:
        context['orgs'] = context['orgs'].filter(located__location__point__intersects=obj.area.polygon)
    if obj.network:
        context['orgs'] = context['orgs'].filter(source__relation_type_id=1, source__target=obj.network)
    if obj.agreement_iae:
        context['orgs'] = context['orgs'].filter(agreement_iae=obj.agreement_iae)
    if obj.tag:
        context['orgs'] = context['orgs'].filter(tagged_items__tag=obj.tag)


def list_view(request, page_app, pk):

    iframe = get_object_or_404(IFrame, pk=pk)
    if request.GET.get('display') == 'Cartographie':
        return HttpResponseRedirect('/iframe/p/%u/carto/?%s' % (iframe.pk, request.GET.urlencode()))
    context = get_index_context(request)
    context['object'] = page_app
    context['iframe'] = iframe
    iframe_filter(page_app, iframe, context)
    paginate(request, context)
    http_headers = {'X-Frame-Options': 'ALLOW-FROM %s' % iframe.domain}
    return render_view('page_iframe/list.html', context, MEDIAS,
                       context_instance=RequestContext(request),
                       http_headers=http_headers,
                       global_context={'home_url': '/iframe/p/%u/' % iframe.pk,
                                       'top_content': iframe.top_content})


def detail_view(request, page_app, pk, org_pk):

    iframe = get_object_or_404(IFrame, pk=pk)
    org = get_object_or_404(Organization, pk=org_pk, status=ORGANIZATION_STATUSES.VALIDATED)
    calls = org.callfortenders_set.filter(deadline__gte=now()).order_by('deadline')
    get_params = request.GET.copy()
    context = {'object': page_app, 'iframe': iframe, 'org': org, 'calls': calls, 'get_params': get_params.urlencode()}
    http_headers = {'X-Frame-Options': 'ALLOW-FROM %s' % iframe.domain}
    return render_view('page_iframe/detail.html', context, MEDIAS,
                       context_instance=RequestContext(request),
                       http_headers=http_headers,
                       global_context={'home_url': '/iframe/p/%u/' % iframe.pk,
                                       'top_content': iframe.top_content})


def carto_view(request, page_app, pk):

    iframe = get_object_or_404(IFrame, pk=pk)
    if request.GET.get('display') == 'Annuaire':
        return HttpResponseRedirect('/iframe/p/%u/?%s' % (iframe.pk, request.GET.urlencode()))
    context = get_map_context(request, bound_area=iframe.area)
    context['object'] = page_app
    context['iframe'] = iframe
    iframe_filter(page_app, iframe, context)
    http_headers = {'X-Frame-Options': 'ALLOW-FROM %s' % iframe.domain}
    return render_view('page_iframe/carto.html', context, MEDIAS,
                       context_instance=RequestContext(request),
                       http_headers=http_headers,
                       global_context={'home_url': '/iframe/p/%u/' % iframe.pk,
                                       'top_content': iframe.top_content})


def index_view(request, page_app):
    return render_view('page_iframe/index.html',
                       { 'object': page_app },
                       MEDIAS,
                       context_instance=RequestContext(request))
