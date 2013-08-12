from django import template
import unicodedata

register = template.Library()

@register.filter
def ascii(str):
    nfkd_form = unicodedata.normalize('NFKD', unicode(str))
    only_ascii = nfkd_form.encode('ASCII', 'ignore')
    return only_ascii
