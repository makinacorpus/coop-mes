# -*- coding: utf-8 -*-

from django.template import RequestContext
from ionyweb.website.rendering.utils import render_view
from coop_local.models import Event
from .forms import EventSearch
from django.db.models import Q
from django.core.paginator import Paginator, PageNotAnInteger, EmptyPage
from ionyweb.website.rendering.medias import CSSMedia, JSMedia
from django.shortcuts import get_object_or_404


def index_view(request, page_app):
    qd = request.GET.copy()
    if not qd.get('area_0') and 'area_1' in qd:
        del qd['area_1']
    form = EventSearch(qd)
    if form.is_valid():
        events = Event.geo_objects
        events = events.filter(
            Q(title__icontains=form.cleaned_data['q']) |
            Q(description__icontains=form.cleaned_data['q']) |
            #Q(tagged_items__tag__name__icontains=form.cleaned_data['q']) |
            Q(located__location__city__icontains=form.cleaned_data['q'])
            #Q(activities__path__icontains=form.cleaned_data['q'])
        )
        sector = form.cleaned_data['sector']
        descendants = sector and sector.get_descendants(include_self=True)
        #if descendants:
            #events = events.filter(activity__in=descendants)
        area = form.cleaned_data.get('area')
        if area:
            try:
                radius = int(form.cleaned_data.get('radius'))
            except:
                radius = 0
            if radius != 0:
                center = area.polygon.centroid
                degrees = radius * 360 / 40000
                q = Q(located__location__point__dwithin=(center, degrees))
                events = events.filter(q)
            else:
                q = Q(located__location__point__contained=area.polygon)
                events = events.filter(q)
        events = events.distinct()
    else:
        area = None
        events = Event.objects.none()
    paginator = Paginator(events, 20)
    page = request.GET.get('page')
    try:
        events_page = paginator.page(page)
    except PageNotAnInteger:
        events_page = paginator.page(1)
    except EmptyPage:
        events_page = paginator.page(paginator.num_pages)
    get_params = request.GET.copy()
    if 'page' in get_params:
        del get_params['page']
    return render_view('page_pasr_agenda/index.html',
                       {'object': page_app, 'form': form, 'events': events_page,
                        'get_params': get_params.urlencode()},
                       (CSSMedia('selectable/css/dj.selectable.css', prefix_file=''),
                        JSMedia('selectable/js/jquery.dj.selectable.js', prefix_file=''),
                        CSSMedia('tagger/css/coop_tag.css', prefix_file=''),
                        JSMedia('tagger/js/jquery.autoSuggest.minified.js', prefix_file='')),
                       context_instance=RequestContext(request))


def detail_view(request, page_app, pk):
    event = get_object_or_404(Event, pk=pk)
    get_params = request.GET.copy()
    return render_view('page_pasr_agenda/detail.html',
                       {'object': page_app, 'event': event,
                        'get_params': get_params.urlencode()},
                       (),
                       context_instance=RequestContext(request))
