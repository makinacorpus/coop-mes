from django.shortcuts import render, get_object_or_404
from iframe.models import IFrame
from page_directory.views import get_index_context, paginate
from page_map.views import get_index_context as get_map_context
from django.core.urlresolvers import reverse
from django.http import HttpResponseRedirect
from coop_local.models import Organization
from coop_local.models.local_models import ORGANIZATION_STATUSES
from django.utils.timezone import now


def iframe_filter(obj, context):
    if obj.area:
        context['orgs'] = context['orgs'].filter(located__location__point__intersects=obj.area.polygon)
    if obj.network:
        context['orgs'] = context['orgs'].filter(source__relation_type_id=1, source__target=obj.network)
    if obj.agreement_iae:
        context['orgs'] = context['orgs'].filter(agreement_iae=obj.agreement_iae)
    if obj.tag:
        context['orgs'] = context['orgs'].filter(tagged_items__tag=obj.tag)


def iframe(request, pk):

    iframe = get_object_or_404(IFrame, pk=pk)
    if request.GET.get('display') == 'Cartographie':
        return HttpResponseRedirect(reverse('iframe_carto', args=[pk]) + '?' + request.GET.urlencode())
    context = get_index_context(request)
    context['iframe'] = iframe
    iframe_filter(iframe, context)
    paginate(request, context)
    response = render(request, 'iframe/index.html', context)
    response['X-Frame-Options'] = 'ALLOW-FROM %s' % iframe.domain

    return response


def detail(request, pk, org_pk):

    iframe = get_object_or_404(IFrame, pk=pk)
    org = get_object_or_404(Organization, pk=org_pk, status=ORGANIZATION_STATUSES.VALIDATED)
    calls = org.callfortenders_set.filter(deadline__gte=now()).order_by('deadline')
    get_params = request.GET.copy()
    context = {'iframe': iframe, 'org': org, 'calls': calls, 'get_params': get_params.urlencode()}
    response = render(request, 'iframe/detail.html', context)
    response['X-Frame-Options'] = 'ALLOW-FROM %s' % iframe.domain
    return response


def iframe_carto(request, pk):

    iframe = get_object_or_404(IFrame, pk=pk)
    if request.GET.get('display') == 'Annuaire':
        return HttpResponseRedirect(reverse('iframe', args=[pk]) + '?' + request.GET.urlencode())
    context = get_map_context(request, bound_area=iframe.area)
    context['iframe'] = iframe
    iframe_filter(iframe, context)
    response = render(request, 'iframe/carto.html', context)
    response['X-Frame-Options'] = 'ALLOW-FROM %s' % iframe.domain

    return response
