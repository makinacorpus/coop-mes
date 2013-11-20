# -*- coding: utf-8 -*-

import floppyforms as forms
from ionyweb.forms import ModuloModelForm
from .models import PageApp_Guaranties

from coop_local.models.local_models import ORGANISATION_GUARANTY_TYPES

class PageApp_GuarantiesForm(ModuloModelForm):

    class Meta:
        model = PageApp_Guaranties


class GuarantySearch(forms.Form):
    type = forms.ChoiceField(choices=(('', u'Tout voir'), ) + ORGANISATION_GUARANTY_TYPES.CHOICES, required=False)
    q = forms.CharField(required=False)

    def __init__(self, *args, **kwargs):
        super(GuarantySearch, self).__init__(*args, **kwargs)
        for field in self.fields.itervalues():
            field.widget.attrs['class'] = 'form-control'
