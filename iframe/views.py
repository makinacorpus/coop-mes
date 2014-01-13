from django.shortcuts import render, get_object_or_404
from iframe.models import IFrame
from page_directory.views import get_index_context, paginate
from page_map.views import get_index_context as get_map_context
from django.core.urlresolvers import reverse
from django.http import HttpResponseRedirect


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

    obj = get_object_or_404(IFrame, pk=pk)
    if request.GET.get('display') == 'Cartographie':
        return HttpResponseRedirect(reverse('iframe_carto', args=[pk]) + '?' + request.GET.urlencode())
    context = get_index_context(request)
    iframe_filter(obj, context)
    paginate(request, context)
    response = render(request, 'iframe/index.html', context)
    response['X-Frame-Options'] = 'ALLOW-FROM %s' % obj.domain

    return response


def iframe_carto(request, pk):

    obj = get_object_or_404(IFrame, pk=pk)
    if request.GET.get('display') == 'Annuaire':
        return HttpResponseRedirect(reverse('iframe', args=[pk]) + '?' + request.GET.urlencode())
    context = get_map_context(request, bound_area=obj.area)
    iframe_filter(obj, context)
    response = render(request, 'iframe/carto.html', context)
    response['X-Frame-Options'] = 'ALLOW-FROM %s' % obj.domain

    return response
