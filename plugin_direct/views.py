# -*- coding: utf-8 -*-
from django.template import RequestContext
from ionyweb.website.rendering.utils import render_view

# from ionyweb.website.rendering.medias import CSSMedia, JSMedia, JSAdminMedia
MEDIAS = (
    # App CSS
    # CSSMedia('plugin_direct.css'),
    # App JS
    # JSMedia('plugin_direct.js'),
    # Actions JSAdmin
    # JSAdminMedia('plugin_direct_actions.js'),
    )

def index_view(request, plugin):    
    return render_view('plugin_direct/index.html',
                       {'object': plugin},
                       MEDIAS,
                       context_instance=RequestContext(request))