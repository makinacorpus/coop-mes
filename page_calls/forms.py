# -*- coding: utf-8 -*-

import floppyforms as forms
from ionyweb.forms import ModuloModelForm
from .models import PageApp_Calls
from coop_local.models import CallForTenders, ActivityNomenclature, Organization
from coop_local.models.local_models import CLAUSE_CHOICES, ORGANIZATION_STATUSES
from django.conf import settings
from crispy_forms.helper import FormHelper
from crispy_forms.layout import Layout, Fieldset, HTML, Field
from crispy_forms.bootstrap import InlineCheckboxes, FormActions, StrictButton, AppendedText
from coop_local.widgets import SplitDateTimeWidget
from django.forms.util import flatatt
from django.utils.safestring import mark_safe


ORG_TYPE_CHOICES = (
    ('tout', u'Public ou privé'),
    ('prive', u'Privé'),
    ('public', u'Public'),
)

PERIOD_CHOICES = (
    ('current', u'En cours'),
    ('archive', u'Archivé'),
    ('tout', u'Tout voir'),
)

class MyCheckboxSelectMultiple(forms.CheckboxSelectMultiple):
    def __init__(self, attrs=None, ul_attrs=None):
        self.ul_attrs = ul_attrs
        super(MyCheckboxSelectMultiple, self).__init__(attrs)

    def render(self, *args, **kwargs):
        html = super(MyCheckboxSelectMultiple, self).render(*args, **kwargs)
        final_attrs = self.build_attrs(self.ul_attrs)
        return mark_safe(html.replace('<ul>','<ul%s>' % flatatt(final_attrs)))

class CallSearch(forms.Form):
    org_type = forms.ChoiceField(choices=ORG_TYPE_CHOICES, required=False)
    clauses = forms.MultipleChoiceField(choices=CLAUSE_CHOICES, required=False, widget=MyCheckboxSelectMultiple(ul_attrs={'class': 'dropdown-menu'}))
    organization = forms.ModelChoiceField(queryset=Organization.objects.filter(is_customer=True, status=ORGANIZATION_STATUSES.VALIDATED), required=False, empty_label=u'Toutes')
    sectors = forms.ModelMultipleChoiceField(queryset=ActivityNomenclature.objects.filter(level=0), required=False, widget=MyCheckboxSelectMultiple(ul_attrs={'class': 'dropdown-menu'}))
    period = forms.ChoiceField(choices=PERIOD_CHOICES, required=False)
    q = forms.CharField(required=False)

    def __init__(self, *args, **kwargs):
        super(CallSearch, self).__init__(*args, **kwargs)
        for field in self.fields.itervalues():
            field.widget.attrs['class'] = 'form-control'


class CallForm(forms.ModelForm):

    class Meta:
        model = CallForTenders
        fields = (
            'title',
            'activity',
            'areas',
            'allotment',
            'lot_numbers',
            'clauses',
            'deadline',
            'url',
            'description',
        )

    def __init__(self, *args, **kwargs):
        super(CallForm, self).__init__(*args, **kwargs)
        self.fields['deadline'].widget = SplitDateTimeWidget(time_format='%H:%M')
        self.fields['deadline'].label = u'Date et heure limite'
        self.fields['deadline'].help_text = u'Date au format jj/mm/aaaa. Heure au format hh:mm.'
        self.fields['activity'].help_text = u''
        self.fields['areas'].help_text = u''
        self.helper = FormHelper()
        self.helper.form_tag = False
        self.helper.layout = Layout(
            'title',
            'activity',
            'areas',
            'allotment',
            'lot_numbers',
            InlineCheckboxes('clauses'),
            'deadline',
            'url',
            'description',
        )
