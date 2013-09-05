# -*- coding: utf-8 -*-
from django.template import RequestContext
from ionyweb.website.rendering.utils import render_view
from .forms import OrgSearch
from django.conf import settings

from ionyweb.website.rendering.medias import JSMedia
MEDIAS = (
    JSMedia('js/vendor/raphael-min.js', prefix_file=''),
)

def index_view(request, plugin):
    form = OrgSearch(request.GET)
    return render_view('plugin_home_search/index.html',
                       {'object': plugin, 'form': form,
                        'REGION_LABEL': settings.REGION_LABEL},
                       MEDIAS,
                       context_instance=RequestContext(request))
