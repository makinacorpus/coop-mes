# -*- coding: utf-8 -*-

from coop_local.models import Contact, ContactMedium


def sync_contacts(engagement, cleaned_data):
    tel_medium = ContactMedium.objects.get(label=u'Téléphone')
    try:
        tel = engagement.contacts.get(contact_medium=tel_medium)
    except Contact.DoesNotExist:
        tel = None
    data = cleaned_data['tel']
    if data:
        if not tel:
            tel = Contact(content_object=engagement, contact_medium=tel_medium)
        tel.content = data
        tel.save()
    elif tel:
        tel.delete()
    email_medium = ContactMedium.objects.get(label=u'Courriel')
    try:
        email = engagement.contacts.get(contact_medium=email_medium)
    except Contact.DoesNotExist:
        email = None
    data = cleaned_data['email']
    if data:
        if not email:
            email = Contact(content_object=engagement, contact_medium=email_medium)
        email.content = data
        email.save()
    elif email:
        email.delete()
