# -*- coding: utf-8 -*-

from django.template import RequestContext
from ionyweb.website.rendering.utils import render_view
from .forms import SubscriptionForm
from coop_local.models import NewsletterSubscription
from django.shortcuts import get_object_or_404
from django.http import HttpResponseRedirect
from django.contrib.sites.models import Site
from ionyweb.plugin_app.plugin_contact.models import Plugin_Contact
from django.utils.text import wrap
from django.template.loader import render_to_string
from coop_local.management.commands.mailing import EmailMultiRelated
from BeautifulSoup import BeautifulSoup

MEDIAS = (
)

def index_view(request, page_app):
    form = SubscriptionForm(request.POST or None)
    if form.is_valid():
        subscription = form.save()
        link = 'http://%s/newsletter/p/confirmer/%u/' % (Site.objects.get_current().domain, subscription.pk)
        context = {'link': link}
        subject = u'Confirmation de votre abonnement à la newsletter %s' % Site.objects.get_current().domain
        text = wrap(render_to_string('page_newsletter/mail.txt', context), 72)
        html = render_to_string('page_newsletter/mail.html', context)
        sender = Plugin_Contact.objects.all()[0].email
        msg = EmailMultiRelated(subject, text, sender, [subscription.email])
        msg.attach_alternative(html, 'text/html')
        soup = BeautifulSoup(html)
        msg.send()
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
