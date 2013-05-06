# -*- coding: utf-8 -*-
from django.template import RequestContext
from ionyweb.website.rendering.utils import render_view
from coop_local.models import Organization
from coop_local.models.local_models import ORGANIZATION_STATUSES
from ionyweb.page_app.page_blog.models import Entry

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
    providers = Organization.objects.filter(is_provider=True, status=ORGANIZATION_STATUSES.VALIDATED).order_by('-validation')[:6]
    customers = Organization.objects.filter(is_customer=True, status=ORGANIZATION_STATUSES.VALIDATED).order_by('-validation')[:6]
    actus = Entry.objects.filter(status=Entry.STATUS_ONLINE).order_by('-publication_date')[:6]
    return render_view('plugin_direct/index.html',
                       {'object': plugin, 'providers': providers, 'customers': customers, 'actus': actus},
                       MEDIAS,
                       context_instance=RequestContext(request))