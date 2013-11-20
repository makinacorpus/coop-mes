# -*- coding: utf-8 -*-

from django.template import RequestContext
from ionyweb.website.rendering.utils import render_view
from .forms import GuarantySearch
from coop_local.models import Guaranty
from django.db.models import Q
from django.core.paginator import Paginator, PageNotAnInteger, EmptyPage


def index_view(request, page_app):
    form = GuarantySearch(request.GET)
    if form.is_valid():
        guaranties = Guaranty.objects.filter(
            Q(name__icontains=form.cleaned_data['q']) |
            Q(description__icontains=form.cleaned_data['q']))
        if form.cleaned_data['type']:
            guaranties = guaranties.filter(type=form.cleaned_data['type'])
    else:
        guaranties = Guaranty.objects.none()
    paginator = Paginator(guaranties, 20)
    page = request.GET.get('page')
    try:
        guaranties_page = paginator.page(page)
    except PageNotAnInteger:
        guaranties_page = paginator.page(1)
    except EmptyPage:
        guaranties_page = paginator.page(paginator.num_pages)
    get_params = request.GET.copy()
    if 'page' in get_params:
        del get_params['page']
    return render_view('page_guaranties/index.html',
                       {'object': page_app, 'form': form,
                        'guaranties': guaranties_page,
                        'get_params': get_params.urlencode()},
                       (),
                       context_instance=RequestContext(request))
