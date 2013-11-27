# -*- coding:utf-8 -*-

from django.shortcuts import render_to_response, redirect
from coop_local.models import Organization
from django.template import RequestContext
from haystack.views import SearchView
from page_account.views import make_ionyweb_view


search = make_ionyweb_view(SearchView())
