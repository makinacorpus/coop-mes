# -*- coding:utf-8 -*-
from haystack import indexes
from coop.search_indexes import OrganizationIndex as BaseOrganizationIndex
from coop.search_indexes import EventIndex as BaseEventIndex
from coop.search_indexes import CoopIndexWithoutSite
from django.utils.timezone import now
from coop_local.models import CallForTenders, Offer
from ionyweb.page_app.page_blog.models import Entry
from ionyweb.page_app.page_text.models import PageApp_Text


class OrganizationIndex(BaseOrganizationIndex, indexes.Indexable):
    def index_queryset(self, using=None):
        return self.get_model().objects.filter(status='V')


class EventIndex(BaseEventIndex, indexes.Indexable):
    def index_queryset(self, using=None):
        return self.get_model().objects.filter(status='V', occurrence__end_time__gte=now())


class CallForTendersIndex(CoopIndexWithoutSite, indexes.Indexable):
    def get_model(self):
        return CallForTenders

    def index_queryset(self, using=None):
        return self.get_model().objects.filter(deadline__gte=now())


class EntryIndex(CoopIndexWithoutSite, indexes.Indexable):
    def get_model(self):
        return Entry

    def index_queryset(self, using=None):
        return self.get_model().objects.filter(status=Entry.STATUS_ONLINE)


class PageApp_TextIndex(CoopIndexWithoutSite, indexes.Indexable):
    def get_model(self):
        return PageApp_Text

    def index_queryset(self, using=None):
        return self.get_model().objects.filter(page__isnull=False)
