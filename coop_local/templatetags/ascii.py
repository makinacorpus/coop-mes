from django import template
from BeautifulSoup import BeautifulStoneSoup
import unicodedata

register = template.Library()

@register.filter
def ascii(str):
    nfkd_form = unicodedata.normalize('NFKD', unicode(str))
    only_ascii = nfkd_form.encode('ASCII', 'ignore')
    return only_ascii

@register.filter
def html2text(str):
    #print str[:20]
    #print '-> ' + ''.join(BeautifulStoneSoup(str, convertEntities=BeautifulStoneSoup.ALL_ENTITIES).findAll(text=True))[:20]
    return ''.join(BeautifulStoneSoup(str, convertEntities=BeautifulStoneSoup.ALL_ENTITIES).findAll(text=True))

