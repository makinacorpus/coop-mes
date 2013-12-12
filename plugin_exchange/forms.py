# -*- coding: utf-8 -*-

from django.conf import settings
from django.core.mail import EmailMessage
from django.utils.translation import ugettext_lazy as _

from ionyweb.forms import ModuloModelForm, IonywebContentForm

import floppyforms as forms

from models import Plugin_Exchange
from crispy_forms.helper import FormHelper
from crispy_forms.layout import Layout, Fieldset, HTML, Field
from coop_local.models import ActivityNomenclature, Organization


class Plugin_ExchangeForm(IonywebContentForm, forms.Form):
    """
    Exchange form use to display the plugin
    """
    QUALITE_CHOICES = (
        (u'', u'------'),
        (u'PUB', u'Acheteur public'),
        (u'PRI', u'Acheteur privé'),
        (u'FOU', u'Fournisseur'),
        (u'NET', u'Réseau'),
    )

    qualite_from = forms.ChoiceField(label=u'Qualité', choices=QUALITE_CHOICES)
    subject = forms.CharField(label=_(u'Objet'))
    message = forms.CharField(label=_(u"Message"), widget=forms.Textarea)
    attachment = forms.FileField(label=_(u"Pièce-Jointe"), required=False)
    qualite_to = forms.ChoiceField(label=u'Qualité', choices=QUALITE_CHOICES)
    activity = forms.ModelChoiceField(queryset=ActivityNomenclature.objects.all(), label=u'Secteur d\'activité')

    def __init__(self, *args, **kwargs):
        super(Plugin_ExchangeForm, self).__init__(*args, **kwargs)
        choices = [(None, '------')]
        for level1 in ActivityNomenclature.objects.filter(level=settings.ACTIVITY_NOMENCLATURE_LOOKUP_LEVEL-1).order_by('label'):
            choices.append((level1.label, [(level2.id, level2.label) for level2 in level1.children.order_by('label')]))
        self.fields['activity'].choices = choices
        self.helper = FormHelper()
        self.helper.form_tag = False
        self.helper.layout = Layout(
            Fieldset(u"Expéditeur", 'qualite_from'),
            Fieldset(u"Destinataires", 'qualite_to', 'activity'),
            Fieldset(u"Message", 'subject', 'message', 'attachment'),
        )

    def send(self, request, sender):

        if self.is_valid():
            subject = u'[%s] %s' % (settings.SITE_NAME,
                                    self.cleaned_data['subject'])

            if self.cleaned_data['qualite_to'] in ('PUB', 'PRI'):
                orgs = Organization.objects.filter(status='V', is_customer=True, activities=self.cleaned_data['activity'])
                if self.cleaned_data['qualite_to'] == 'PUB':
                    orgs = orgs.filter(customer_type=1)
                else:
                    orgs = orgs.filter(customer_type=2)
            elif self.cleaned_data['qualite_to'] == 'FOU':
                orgs = Organization.objects.filter(status='V', is_provider=True, offer__activity=self.cleaned_data['activity'])
            elif self.cleaned_data['qualite_to'] == 'NET':
                orgs = Organization.objects.filter(status='V', is_network=True, offer__activity=self.cleaned_data['activity'])
            orgs = orgs.filter(exchanges_subscription=True)

            mails = [email for email in orgs.values_list('pref_email__content', flat=True) if email is not None]

            message = u"Qualité: %s\n\n" % dict(self.QUALITE_CHOICES)[self.cleaned_data['qualite_from']]
            message += self.cleaned_data['message']

            attachment = self.cleaned_data['attachment']

            ok = True
            for mail in mails:
                msg = EmailMessage(subject, message, sender, [mail])
                if attachment:
                    msg.attach(attachment.name,
                               attachment.read(),
                               attachment.content_type)
                try:
                    msg.send()
                except:
                    ok = False
                    raise

            return ok and len(mails)

        return False

class Plugin_ExchangeFormAdmin(ModuloModelForm):
    """
    Exchange form to edit the plugin
    """

    class Meta:
        model = Plugin_Exchange
