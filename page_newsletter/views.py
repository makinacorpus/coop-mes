# -*- coding: utf-8 -*-

from django.template import RequestContext
from ionyweb.website.rendering.utils import render_view
from .forms import SubscriptionForm
from coop_local.models import NewsletterSubscription
from django.shortcuts import get_object_or_404
from django.http import HttpResponseRedirect
from django.contrib.sites.models import Site
from ionyweb.plugin_app.plugin_contact.models import Plugin_Contact
from django.conf import settings
from coop_local.mixed_email import send_mixed_email

MEDIAS = ()

def index_view(request, page_app):
    form = SubscriptionForm(request.POST or None)
    if form.is_valid():
        subscription = form.save()
        sender = Plugin_Contact.objects.all()[0].email
        site = Site.objects.get_current().domain
        context = {
            'site': site,
            'slug': settings.REGION_SLUG,
            'subscription': subscription,
        }
        subject = u'Confirmation de votre abonnement à la newsletter %s' % site
        template = 'email/newsletter'
        send_mixed_email(sender, subscription.email, subject, template, context)
        return HttpResponseRedirect('/newsletter/p/a-confirmer/')
    return render_view('page_newsletter/index.html',
                       { 'object': page_app, 'form': form },
                       MEDIAS,
                       context_instance=RequestContext(request))

def to_confirm_view(request, page_app):
    return render_view('page_newsletter/to-confirm.html',
                       { 'object': page_app },
                       MEDIAS,
                       context_instance=RequestContext(request))

def confirm_view(request, page_app, pk):
    subscription = get_object_or_404(NewsletterSubscription, pk=pk)
    subscription.active = True
    subscription.save()
    return render_view('page_newsletter/confirmed.html',
                       { 'object': page_app },
                       MEDIAS,
                       context_instance=RequestContext(request))
