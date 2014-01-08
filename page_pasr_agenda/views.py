# -*- coding: utf-8 -*-

from django.template import RequestContext
from ionyweb.website.rendering.utils import render_view
from coop_local.models import Event, Occurrence, Organization, Calendar
from .forms import (EventSearch, FrontEventForm, OccurrencesForm,
    LocationForm, DocumentsForm)
from django.db.models import Q, Min
from django.core.paginator import Paginator, PageNotAnInteger, EmptyPage
from ionyweb.website.rendering.medias import CSSMedia, JSMedia
from django.shortcuts import get_object_or_404
from datetime import datetime, date, timedelta
from django.contrib.auth.decorators import login_required
from django.contrib.admin.models import LogEntry, ADDITION, CHANGE, DELETION
from django.contrib.contenttypes.models import ContentType
from  django.utils.encoding import force_unicode
from django.utils.text import get_text_list
from django.utils.translation import ugettext as _
from django.shortcuts import get_object_or_404
from django.http import HttpResponseRedirect, HttpResponseForbidden
from django.conf import settings
from django.contrib.sites.models import Site


EDIT_MEDIA = [
    CSSMedia('tagger/css/coop_tag.css', prefix_file=''),
    JSMedia('tagger/js/jquery.autoSuggest.minified.js', prefix_file=''),
    JSMedia('../_tinymce/compressor/', prefix_file=''),
    CSSMedia('select2/select2.css', prefix_file=''),
    CSSMedia('css/select2-bootstrap3.css', prefix_file=''),
    JSMedia('select2/select2.min.js', prefix_file=''),
    CSSMedia('css/datepicker.css', prefix_file=''),
    JSMedia('js/bootstrap-datepicker.js', prefix_file=''),
    JSMedia('js/bootstrap-datepicker.fr.js', prefix_file=''),
]


def index_view(request, page_app):
    qd = request.GET.copy()
    if not qd.get('area_0') and 'area_1' in qd:
        del qd['area_1']
    if not qd.get('date'):
        qd['date'] = date.today().strftime('%d/%m/%Y')
    if not qd.get('interval') or not qd['interval'].isdigit:
        qd['interval'] = '9999'
    form = EventSearch(qd)
    if form.is_valid():
        events = Event.geo_objects
        events = events.filter(status='V')
        start = form.cleaned_data['date']
        end = form.cleaned_data['date'] + timedelta(days=int(form.cleaned_data['interval']))
        events = events.filter(occurrence__end_time__gte=start, occurrence__start_time__lt=end)
        events = events.filter(
            Q(title__icontains=form.cleaned_data['q']) |
            Q(description__icontains=form.cleaned_data['q']) |
            Q(tagged_items__tag__name__icontains=form.cleaned_data['q']) |
            Q(located__location__city__icontains=form.cleaned_data['q']) |
            Q(activity__path__icontains=form.cleaned_data['q'])
        )
        sector = form.cleaned_data['sector']
        descendants = sector and sector.get_descendants(include_self=True)
        if descendants:
            events = events.filter(activity__in=descendants)
        if qd.get('organization'):
            events = events.filter(organization=qd['organization'])
        area = form.cleaned_data.get('area')
        if area:
            try:
                radius = int(form.cleaned_data.get('radius'))
            except:
                radius = 0
            if radius != 0:
                center = area.polygon.centroid
                degrees = radius * 360 / 40000.
                q = Q(location__point__dwithin=(center, degrees))
                events = events.filter(q)
            else:
                q = Q(location__point__contained=area.polygon)
                events = events.filter(q)
    else:
        area = None
        events = Event.objects.none()
    events = events.annotate(start_time=Min('occurrence__start_time'))
    events = events.distinct()
    events = events.order_by('start_time')
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
    if event.status != 'V':
        return render_view('page_pasr_agenda/not_validated.html', {'object': page_app},
                           (), context_instance=RequestContext(request))
    get_params = request.GET.copy()
    return render_view('page_pasr_agenda/detail.html',
                       {'object': page_app, 'event': event,
                        'get_params': get_params.urlencode()},
                       (),
                       context_instance=RequestContext(request))


@login_required
def add_view(request, page_app):
    org = Organization.mine(request)
    if org is None:
        return HttpResponseForbidden('Votre compte n\'est pas attaché à une organisation.')
    form = FrontEventForm(request.POST or None, request.FILES or None)
    form2 = OccurrencesForm(request.POST or None, instance=form.instance)
    form3 = LocationForm(request.POST or None)
    form4 = DocumentsForm(request.POST or None, request.FILES or None, instance=form.instance)
    if form.is_valid() and form2.is_valid() and form3.is_valid() and form4.is_valid():
        location = form3.save()
        event = form.save(commit=False)
        if 'propose' in request.POST and event.status == 'I':
            event.status = 'P'
        event.calendar = Calendar.objects.all()[0]
        event.organization = org
        event.person = request.user.get_profile()
        event.location = location
        event.save()
        form.save_m2m()
        form2.save()
        form4.save()
        LogEntry.objects.log_action(
            user_id         = request.user.pk,
            content_type_id = ContentType.objects.get_for_model(Event).pk,
            object_id       = event.pk,
            object_repr     = force_unicode(event),
            action_flag     = ADDITION,
        )
        if 'propose' in request.POST:
            return HttpResponseRedirect('/agenda/p/mes-evenements/feedback/')
        else:
            return HttpResponseRedirect('/agenda/p/mes-evenements/')
    return render_view('page_pasr_agenda/edit.html',
                       {'object': page_app, 'form': form, 'form2': form2, 'form3': form3, 'form4': form4},
                       EDIT_MEDIA,
                       context_instance=RequestContext(request))


@login_required
def delete_view(request, page_app, pk):
    org = Organization.mine(request)
    if org is None:
        return HttpResponseForbidden('Votre compte n\'est pas attaché à une organisation.')
    event = get_object_or_404(Event, pk=pk, organization=org)
    LogEntry.objects.log_action(
        user_id         = request.user.pk,
        content_type_id = ContentType.objects.get_for_model(Event).pk,
        object_id       = event.pk,
        object_repr     = force_unicode(event),
        action_flag     = DELETION,
        change_message  = u'Evénement "%s" supprimé.' % force_unicode(event)
    )
    event.delete()
    return HttpResponseRedirect('/agenda/p/mes-evenements/')


@login_required
def update_view(request, page_app, pk):
    org = Organization.mine(request)
    if org is None:
        return HttpResponseForbidden('Votre compte n\'est pas attaché à une organisation.')
    event = get_object_or_404(Event, pk=pk, organization=org)
    form = FrontEventForm(request.POST or None, request.FILES or None, instance=event)
    form2 = OccurrencesForm(request.POST or None, instance=event)
    form3 = LocationForm(request.POST or None, instance=event.location)
    form4 = DocumentsForm(request.POST or None, request.FILES or None, instance=event)
    if form.is_valid() and form2.is_valid() and form3.is_valid() and form4.is_valid():
        location = form3.save()
        event = form.save(commit=False)
        if 'propose' in request.POST and event.status == 'I':
            event.status = 'P'
        event.location = location
        event.save()
        form.save_m2m()
        form2.save()
        form4.save()
        LogEntry.objects.log_action(
            user_id         = request.user.pk,
            content_type_id = ContentType.objects.get_for_model(Event).pk,
            object_id       = event.pk,
            object_repr     = force_unicode(event),
            action_flag     = CHANGE,
            change_message  = u'%s modifié pour l\'événement "%s".' % (get_text_list(form.changed_data, _('and')), force_unicode(event))
        )
        if 'propose' in request.POST:
            return HttpResponseRedirect('/agenda/p/mes-evenements/feedback/')
        else:
            return HttpResponseRedirect('/agenda/p/mes-evenements/')
    return render_view('page_pasr_agenda/edit.html',
                       {'object': page_app, 'form': form, 'form2': form2, 'form3': form3, 'form4': form4},
                       EDIT_MEDIA,
                       context_instance=RequestContext(request))


@login_required
def my_view(request, page_app):
    org = Organization.mine(request)
    if org is None:
        return HttpResponseForbidden('Votre compte n\'est pas attaché à une organisation.')
    events = Event.objects.filter(organization=org)
    events = events.annotate(start_time=Min('occurrence__start_time'))
    events = events.filter(Q(occurrence__end_time=None) | Q(occurrence__end_time__gte=datetime.now()))
    events = events.order_by('start_time')
    return render_view('page_pasr_agenda/my_events.html',
                       {'object': page_app, 'events': events},
                       [],
                       context_instance=RequestContext(request))


def feedback_view(request, page_app):
    return render_view('page_pasr_agenda/feedback.html',
                       {'object': page_app, 'slug': settings.REGION_SLUG, 'site': Site.objects.get_current().domain},
                       [],
                       context_instance=RequestContext(request))
