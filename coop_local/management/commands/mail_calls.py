# -*- coding:utf-8 -*-

# Based on http://djangosnippets.org/snippets/285/
# Sending html emails with images attached in Django

# download and install BeautifulSoup from http://www.crummy.com/software/BeautifulSoup/
from BeautifulSoup import BeautifulSoup

from django.conf import settings
from django.template import loader, Context
from django.core.mail import EmailMultiAlternatives, SafeMIMEMultipart
from django.contrib.auth.models import User
from ionyweb.plugin_app.plugin_contact.models import Plugin_Contact

from email.MIMEImage import MIMEImage
import email.Charset

from django.core.management.base import BaseCommand, CommandError
from coop_local.models import (Organization, Engagement, Person, Contact,
    ContactMedium, ActivityNomenclature, CallForTenders)
from django.db import transaction
import unicodedata
import re
import random
import string
from django.template.loader import render_to_string
import os
from email.MIMEBase import MIMEBase
from django.utils.text import wrap
from django.db.models import Q
from django.contrib.sites.models import Site
from django.utils.timezone import now
from datetime import timedelta

CHARSET = 'utf-8'

email.Charset.add_charset(CHARSET, email.Charset.SHORTEST, None, None)

named = lambda email, name: ('%s <%s>' % (email, name)) if name else email

def image_finder(tag):
    return (tag.name == u'img' or
            tag.name == u'table' and tag.has_key('background'))

def render(context, template):
    if template:
        t = loader.get_template(template)
        return t.render(Context(context))
    return context

def send_html_mail(subject, recipient, message, template='',
                   recipient_name='', sender_name='', sender=None,
                   CHARSET=CHARSET):
    """
    If you want to use Django template system:
       use `message` and define `template`.

    If you want to use images in html message, no problem,
    it will attach automatically found files in html template.
    (image paths are relative to PROJECT_PATH)
    """

    html = render(message, template)

    # Image processing, replace the current image urls with attached images.
    soup = BeautifulSoup(html)
    images = []
    added_images = []
    for index, tag in enumerate(soup.findAll(image_finder)):
        if tag.name == u'img':
            name = 'src'
        elif tag.name == u'table':
            name = 'background'
        # If the image was already added, skip it.
        if tag[name] in added_images:
            continue
        added_images.append(tag[name])
        images.append((tag[name], 'img%d' % index))
        tag[name] = 'cid:img%d' % index
    html = str(soup)

    msg = EmailMultiAlternatives(
        subject=subject,
        body=html,
        to=[named(recipient, recipient_name)],
        from_email=named(sender, sender_name),
    )

    for filename, file_id in images:
        image_file = open(settings.PROJECT_PATH + filename, 'rb')
        msg_image = MIMEImage(image_file.read())
        image_file.close()
        msg_image.add_header('Content-ID', '<%s>' % file_id)
        msg.attach(msg_image)

    msg.content_subtype = 'html'
    msg.mixed_subtype = 'related'
    msg.send()


#-------------------------------------------------------------------------

class EmailMultiRelated(EmailMultiAlternatives):
    """
    A version of EmailMessage that makes it easy to send multipart/related
    messages. For example, including text and HTML versions with inline images.
    """
    related_subtype = 'related'

    def __init__(self, subject='', body='', from_email=None, to=None, bcc=None,
            connection=None, attachments=None, headers=None, alternatives=None):
        # self.related_ids = []
        self.related_attachments = []
        return super(EmailMultiRelated, self).__init__(subject, body, from_email, to, bcc, connection, attachments, headers, alternatives)

    def attach_related(self, filename=None, content=None, mimetype=None):
        """
        Attaches a file with the given filename and content. The filename can
        be omitted and the mimetype is guessed, if not provided.

        If the first parameter is a MIMEBase subclass it is inserted directly
        into the resulting message attachments.
        """
        if isinstance(filename, MIMEBase):
            assert content == mimetype == None
            self.related_attachments.append(filename)
        else:
            assert content is not None
            self.related_attachments.append((filename, content, mimetype))

    def attach_related_file(self, path, mimetype=None):
        """Attaches a file from the filesystem."""
        filename = os.path.basename(path)
        content = open(path, 'rb').read()
        self.attach_related(filename, content, mimetype)

    def _create_message(self, msg):
        return self._create_attachments(self._create_related_attachments(self._create_alternatives(msg)))

    def _create_alternatives(self, msg):
        for i, (content, mimetype) in enumerate(self.alternatives):
            if mimetype == 'text/html':
                for filename, _, _ in self.related_attachments:
                    content = re.sub(r'(?<!cid:)%s' % re.escape(filename), 'cid:%s' % filename, content)
                self.alternatives[i] = (content, mimetype)

        return super(EmailMultiRelated, self)._create_alternatives(msg)

    def _create_related_attachments(self, msg):
        encoding = self.encoding or settings.DEFAULT_CHARSET
        if self.related_attachments:
            body_msg = msg
            msg = SafeMIMEMultipart(_subtype=self.related_subtype, encoding=encoding)
            if self.body:
                msg.attach(body_msg)
            for related in self.related_attachments:
                msg.attach(self._create_related_attachment(*related))
        return msg

    def _create_related_attachment(self, filename, content, mimetype=None):
        """
        Convert the filename, content, mimetype triple into a MIME attachment
        object. Adjust headers to use Content-ID where applicable.
        Taken from http://code.djangoproject.com/ticket/4771
        """
        attachment = super(EmailMultiRelated, self)._create_attachment(filename, content, mimetype)
        if filename:
            mimetype = attachment['Content-Type']
            del(attachment['Content-Type'])
            del(attachment['Content-Disposition'])
            attachment.add_header('Content-Disposition', 'inline', filename=filename)
            attachment.add_header('Content-Type', mimetype, name=filename)
            attachment.add_header('Content-ID', '<%s>' % filename)
        return attachment

#-------------------------------------------------------------------------



class Command(BaseCommand):
    help = 'Mailing'

    def handle(self, *args, **options):

        self.slug = settings.REGION_SLUG
        self.sender = Plugin_Contact.objects.all()[0].email

        for org in Organization.objects.filter(is_provider=True, calls_subscription=True):
            self.mail_org(org)

    @transaction.commit_on_success
    def mail_org(self, org):

        calls = CallForTenders.objects.filter(creation=(now() - timedelta(days=1)).date())
        activities = ActivityNomenclature.objects.filter(offer__provider=org)
        calls = calls.filter(activity__in=activities)

        if len(calls) == 0:
            return

        engagements = org.engagement_set.filter(org_admin=True)
        if not engagements:
            return
        person = engagements[0].person

        sender = self.sender
        site = Site.objects.get_current().domain
        context = {'person': person, 'calls': calls, 'sender': sender, 'site': site}
        subject = u'Nouvel appel d\'offre sur %s' % site
        text = wrap(render_to_string('mailing-calls-%s.txt' % self.slug, context), 72)
        html = render_to_string('mailing-calls-%s.html' % self.slug, context)
        email = org.pref_email.content
        msg = EmailMultiRelated(subject, text, sender, [email])
        msg.attach_alternative(html, 'text/html')
        soup = BeautifulSoup(html)
        for index, tag in enumerate(soup.findAll(image_finder)):
            if tag.name == u'img':
                name = 'src'
            msg.attach_related_file(settings.PROJECT_PATH + '/coop_local/static/img/' + tag[name])
        msg.send()
        print u'Envoi effectué à %s, %s, %s' % (email, sender, org.label())
