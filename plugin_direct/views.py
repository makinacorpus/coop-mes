# -*- coding: utf-8 -*-
from django.template import RequestContext
from ionyweb.website.rendering.utils import render_view
from coop_local.models import Organization, CallForTenders
from coop_local.models.local_models import ORGANIZATION_STATUSES
from ionyweb.page_app.page_blog.models import Entry
from django.utils.timezone import now

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
    tab = request.GET.get('tab')
    if tab not in ('appels-doffres', 'fournisseurs', 'acheteurs', 'agenda', 'actualites'):
        tab = 'appels-doffres'
    calls = CallForTenders.objects.filter(en_direct=True, organization__status=ORGANIZATION_STATUSES.VALIDATED, deadline__gt=now()).order_by('deadline')[:plugin.max_item]
    providers = Organization.objects.filter(is_provider=True, en_direct=True, status=ORGANIZATION_STATUSES.VALIDATED).order_by('-validation')[:plugin.max_item]
    customers = Organization.objects.filter(is_customer=True, en_direct=True, status=ORGANIZATION_STATUSES.VALIDATED).order_by('-validation')[:plugin.max_item]
    actus = Entry.objects.filter(status=Entry.STATUS_ONLINE).order_by('-publication_date')[:plugin.max_item]
    return render_view('plugin_direct/index.html',
                       {'object': plugin, 'providers': providers, 'customers': customers, 'actus': actus, 'calls': calls, 'tab': tab},
                       MEDIAS,
                       context_instance=RequestContext(request))