# -*- coding: utf-8 -*-
import floppyforms as forms
from ionyweb.forms import ModuloModelForm
from .models import Plugin_Search


class Plugin_SearchForm(ModuloModelForm):

    class Meta:
        model = Plugin_Search


class OrgSearch(forms.Form):

    org_type = forms.ChoiceField(choices=(('', u'Tout voir'),), required=False)
    sector = forms.ChoiceField(choices=(('', u'Tout voir'),), required=False)
    area  = forms.ChoiceField(choices=(('', u'Tout voir'),), required=False)
    q = forms.CharField(required=False)
