# -*- coding: utf-8 -*-
from django.template import RequestContext
from ionyweb.website.rendering.utils import render_view
from ionyweb.page_app.page_blog.models import Entry
from coop_local.models import Organization, Event
from coop_local.models.local_models import ORGANIZATION_STATUSES

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
    news = Entry.objects.filter(status=Entry.STATUS_ONLINE)
    news = news.filter(a_la_une=True).order_by('-publication_date')
    events = Event.objects.filter(status='V')
    events = events.filter(a_la_une=True)
    orgs = Organization.objects.filter(status=ORGANIZATION_STATUSES.VALIDATED)
    orgs = orgs.filter(a_la_une=True).order_by('-validation')
    return render_view('plugin_last_news/index.html',
                       {'object': plugin, 'news': news, 'events': events, 'orgs': orgs},
                       MEDIAS,
                       context_instance=RequestContext(request))
