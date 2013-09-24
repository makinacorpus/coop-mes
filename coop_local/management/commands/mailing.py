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
    ContactMedium)
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

    def handle(self, slug, *args, **options):

        self.slug = slug
        self.sender = Plugin_Contact.objects.all()[0].email

        orgs = Organization.objects.filter(is_provider=True)

        if slug == 'npdc':
            emails = (
                'abcdubonpain@yahoo.fr',
                'contact@asah-asso.fr',
                'afp2i@afp2i.fr',
                'gerard.trebacz@aism-eve.fr',
                'afichelle@altereos.fr',
                'arche.gerard@free.fr',
                'contact@cliss21.com',
                'christophe.louage@groupevitaminet.com',
                'gerard.trebacz@aism-eve.fr',
                'ac.delvinquiere@sfr.fr',
                'p.vincent@aideadom.fr',
                'nadia.oudin@groupevitaminet.com',
                'contact@fermedusens.com',
                'f.leroy@saveursetsaisons.com',
                'lerelaisvermellois@wanadoo.fr',
                'clambert@lilas-autopartage.com',
                'mediapole@groupevitaminet.com',
                'momlille@momartre.com',
                'partenaires.contact@free.fr',
                'elizabeth.dinsdale@pocheco.com',
                'lille@vitame.fr',
                'sapih@wanadoo.fr',
                'amelie@ayin.fr',
                'marc.sockeel@abbayedebelval.fr',
                'cedric.houbart@scil.coop',
                'remy.oulouna@groupevitaminet.com',
                'contact@toerana-habitat.fr',
                'adelin.delassus@groupevitaminet.com',
                'direction@groupetandem.fr',
            )
            orgs = orgs.filter(Q(contacts__content__in=emails) | Q(engagement__email__in=emails)).distinct()

        #orgs = orgs.filter(id=231) BAT MP

        for org in orgs:
            self.mail_org(org)

    @transaction.commit_on_success
    def mail_org(self, org):

        members = org.engagement_set.filter(org_admin=True)
        if members:
            member = org.engagement_set.filter(org_admin=True)[0]
            if member.person.user is not None:
                return
            person = member.person
            username = (person.first_name.strip() + '.' + person.last_name.strip())[:30]
        else:
            #print u'Pas de membre pour %s' % org.label()
            person = None
            username = org.label().lower().strip()
            username = username.replace('association ', '')
            username = username.replace('assoc ', '')
            username = username[:12]
        try:
            email = (person and member.email) or org.contacts.filter(contact_medium__label='Email')[0].content
        except IndexError:
            #print u'Pas d\'email pour %s' % org.label()
            return
        username = unicodedata.normalize('NFKD', unicode(username))
        username = username.encode('ASCII', 'ignore')
        username = username.lower()
        username = username.replace(' ', '_')
        username = re.sub(r'[^a-z0-9_\.-]', '-', username)
        username = re.sub(r'[_.-]+$', '', username)
        username = username.replace('_-_', '-')
        for i in range(0, 10):
            if i == 0:
                _username = username
            else:
                _username = username + '%u' % i
            if not User.objects.filter(username=_username).exists() and not Person.objects.filter(username=_username).exists():
                username = _username
                break
            #print 'L\'identifiant %s existe déjà' % _username
        password = ''.join([random.choice(string.digits + string.letters) for i in range(0, 6)]).lower()
        if person is None:
            person = Person.objects.create(last_name=u'Votre nom',
                first_name=u'Votre prénom', username=username)
            person.contacts.add(Contact(contact_medium=ContactMedium.objects.get(label='Email'), content=email))
            member = Engagement.objects.create(person=person,
                organization=org, org_admin = True)
        user = User(
            first_name=person.first_name[:30],
            last_name=person.last_name[:30],
            email=email,
            username=username
        )
        user.set_password(password)
        user.save()
        person.user = user
        person.username = username
        person.save()
        #print '%s;%s' % (username, password)
        if self.slug == 'mp':
            try:
                sender = org.authors.all()[0].email
            except IndexError:
                sender = self.sender
            if self.slug == 'mp' and sender not in ('carole.donaty@adepes.org', 'ndelcour.cooracemp@orange.fr', 'urei-mp@live.fr'):
                return
        else:
            sender = self.sender
        context = {'username': username, 'password': password, 'sender': sender}
        subject = u'Accédez à votre fiche dans achetons-solidaires-paca.com'
        text = wrap(render_to_string('mailing-%s.txt' % self.slug, context), 72)
        html = render_to_string('mailing-%s.html' % self.slug, context)
        #send_html_mail(subject, email, context, template='mailing.html', sender=sender)
        msg = EmailMultiRelated(subject, text, sender, [email])
        msg.attach_alternative(html, 'text/html')
        soup = BeautifulSoup(html)
        for index, tag in enumerate(soup.findAll(image_finder)):
            if tag.name == u'img':
                name = 'src'
            msg.attach_related_file(settings.PROJECT_PATH + '/coop_local/static/img/' + tag[name])
        msg.send()
        print u'Envoi effectué à %s, %s, %s, %s:%s' % (email, sender, org.label(), username, password)
