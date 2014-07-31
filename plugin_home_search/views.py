# -*- coding: utf-8 -*-
from django.template import RequestContext
from ionyweb.website.rendering.utils import render_view
from django.conf import settings
from coop_local.models import ActivityNomenclature

from ionyweb.website.rendering.medias import JSMedia
MEDIAS = (
    JSMedia('js/vendor/raphael-min.js', prefix_file=''),
)

def index_view(request, plugin):
    univers = ActivityNomenclature.objects.filter(level=0).order_by('label')
    middle = (len(univers) + 1) // 2
    univers1 = univers[:middle]
    univers2 = univers[middle:]
    return render_view('plugin_home_search/index.html',
                       {'object': plugin, 'univers1': univers1, 'univers2': univers2,
                        'REGION_LABEL': settings.REGION_LABEL},
                       MEDIAS,
                       context_instance=RequestContext(request))
