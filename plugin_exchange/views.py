# -*- coding: utf-8 -*-
from django.template import RequestContext
from django.conf import settings
from django.utils.translation import ugettext_lazy as _
from ionyweb.website.rendering.medias import CSSMedia, JSMedia
from ionyweb.website.rendering.utils import render_view
from forms import Plugin_ExchangeForm
from coop_local.models import Person

RENDER_MEDIAS = (
    CSSMedia('plugin_contact.css'),
    CSSMedia('select2/select2.css', prefix_file=''),
    CSSMedia('css/select2-bootstrap3.css', prefix_file=''),
    JSMedia('select2/select2.min.js', prefix_file=''),
)


def index_view(request, plugin):
	
    contact_form = Plugin_ExchangeForm()
    message = None

    try:
        person = Person.objects.get(user=request.user)
    except Person.DoesNotExist:
        return render_view(
            plugin.get_templates('plugin_exchange/error.html'),
            {'object': plugin,
             'message': u'Votre compte n\'est lié à aucune organisation.'},
            RENDER_MEDIAS,
            context_instance=RequestContext(request))
    org = person.my_organization()
    if not org.pref_email:
        return render_view(
            plugin.get_templates('plugin_exchange/error.html'),
            {'object': plugin,
             'message': u"Veuillez d'abord ajouter un contact Courriel dans vos <a href=\"/annuaire/p/modifier/9/\">contacts</a>."},
            RENDER_MEDIAS,
            context_instance=RequestContext(request))

    sender = org.pref_email.content

    if request.method == "POST" and not request.is_admin_url:
        # Check if we submit this form.
        if int(request.POST['contactform']) == plugin.pk:
            contact_form = Plugin_ExchangeForm(request.POST, request.FILES)
            if contact_form.is_valid():
                n = contact_form.send(request, sender)
                message = _(u'Message envoyé à {} destinataire{}'.format(n, "s" if n > 1 else ""))
                contact_form = Plugin_ExchangeForm()
            else:
                message = _(u'The mail could not be sent')

    return render_view(
        plugin.get_templates('plugin_exchange/index.html'),
        {'object': plugin,
         'form': contact_form,
         'message': message},
        RENDER_MEDIAS,
        context_instance=RequestContext(request))
