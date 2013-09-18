# -*- coding:utf-8 -*-

# Based on http://djangosnippets.org/snippets/285/
# Sending html emails with images attached in Django

# download and install BeautifulSoup from http://www.crummy.com/software/BeautifulSoup/
from BeautifulSoup import BeautifulSoup

from django.conf import settings
from django.template import loader, Context
from django.core.mail import EmailMultiAlternatives
from django.contrib.auth.models import User
from ionyweb.plugin_app.plugin_contact.models import Plugin_Contact

from email.MIMEImage import MIMEImage
import email.Charset

from django.core.management.base import BaseCommand, CommandError
from coop_local.models import Organization
import unicodedata
import re
import random
import string

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


class Command(BaseCommand):
    help = 'Mailing'

    def handle(self, *args, **options):

        sender = Plugin_Contact.objects.all()[0].email

        for org in Organization.objects.filter(is_provider=True):
            try:
                member = org.engagement_set.filter(org_admin=True)[0]
            except IndexError:
                print u'Pas de membre pour %s' % org.label()
                continue
            if member.person.user is not None:
                continue
            person = member.person
            try:
                email = member.email or org.contacts.filter(contact_medium__label='Email')[0].content
            except IndexError:
                print u'Pas d\'email pour %s' % org.label()
                continue
            username = person.first_name + '.' + person.last_name
            username = unicodedata.normalize('NFKD', unicode(username))
            username = username.encode('ASCII', 'ignore')
            username = username.lower()
            username = username.replace(' ', '_')
            username = re.sub(r'[^a-z_\.-]', '-', username)
            for i in range(0, 10):
                if i == 0:
                    _username = username
                else:
                    _username = username + '%u' % i
                if not User.objects.filter(username=_username).exists():
                    username = _username
                    break
            password = ''.join([random.choice(string.digits + string.letters) for i in range(0, 6)]).lower()
            user = User(
                first_name=person.first_name,
                last_name=person.last_name,
                email=email,
                username=username
            )
            user.set_password(password)
            user.save()
            person.user = user
            person.save()
            print u'Envoi effectué à %s, %s, %s@%s' % (email, org.label(), username, password)
            #send_html_mail(u'Accédez à votre fiche dans achetons-solidaires-paca.com', email,
                #{'username': username, 'password': password, 'sender': sender},
                #template='mailing.html', sender=sender)
