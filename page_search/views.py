# -*- coding: utf-8 -*-

from django.template import RequestContext
from ionyweb.website.rendering.utils import render_view
from page_account.views import make_ionyweb_view
from haystack.forms import SearchForm as BaseSearchForm
from haystack.views import basic_search
from django.http import HttpResponseRedirect

#index_view = make_ionyweb_view(SearchView())


class SearchForm(BaseSearchForm):
    def __init__(self, *args, **kwargs):
        super(SearchForm, self).__init__(*args, **kwargs)
        self.fields['q'].widget.attrs['class'] = 'form-control'


def index_view(request, page_app):

    response = basic_search(request, form_class=SearchForm, template='page_search/index.html')
    if isinstance(response, HttpResponseRedirect):
        return response
    return render_view('content.html', {'content': response.content}, (),
            context_instance=RequestContext(request))
