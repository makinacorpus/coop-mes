# -*- coding: utf-8 -*-
from django.template import RequestContext
from ionyweb.website.rendering.utils import render_view
from ionyweb.page_app.page_blog.models import Entry

# from ionyweb.website.rendering.medias import CSSMedia, JSMedia, JSAdminMedia
MEDIAS = (
    # App CSS
    # CSSMedia('plugin_last_news.css'),
    # App JS
    # JSMedia('plugin_last_news.js'),
    # Actions JSAdmin
    # JSAdminMedia('plugin_last_news_actions.js'),
    )

def index_view(request, plugin):
    entries = Entry.objects.filter(status=Entry.STATUS_ONLINE)
    entries = entries.order_by('-publication_date')
    entries = entries[:1]
    return render_view('plugin_last_news/index.html',
                       {'object': plugin, 'entries': entries},
                       MEDIAS,
                       context_instance=RequestContext(request))