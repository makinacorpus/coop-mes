#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""

Whoosh backend for haystack that implements character folding, as per http://packages.python.org/Whoosh/stemming.html#character-folding .

To use, put this file on your path and add it to your haystack settings, eg.

    HAYSTACK_CONNECTIONS = {
        'default': {
            'ENGINE': 'search_backends.FoldingWhooshEngine',
            'PATH': 'path-to-whoosh-index',
        },
    }

"""


from haystack.backends.whoosh_backend import WhooshEngine, WhooshSearchBackend, WHOOSH_ID, ID, DJANGO_CT, DJANGO_ID, Schema, IDLIST, STORED, TEXT, KEYWORD, NUMERIC, BOOLEAN, DATETIME, NGRAM, NGRAMWORDS

from whoosh.analysis import CharsetFilter, StemmingAnalyzer
from whoosh.support.charset import accent_map


class FoldingWhooshSearchBackend(WhooshSearchBackend):
    def build_schema(self, fields):
        schema_fields = {
            ID: WHOOSH_ID(stored=True, unique=True),
            DJANGO_CT: WHOOSH_ID(stored=True),
            DJANGO_ID: WHOOSH_ID(stored=True),
        }
        # Grab the number of keys that are hard-coded into Haystack.
        # We'll use this to (possibly) fail slightly more gracefully later.
        initial_key_count = len(schema_fields)
        content_field_name = ''

        for field_name, field_class in fields.items():
            if field_class.is_multivalued:
                if field_class.indexed is False:
                    schema_fields[field_class.index_fieldname] = IDLIST(stored=True, field_boost=field_class.boost)
                else:
                    schema_fields[field_class.index_fieldname] = KEYWORD(stored=True, commas=True, scorable=True, field_boost=field_class.boost)
            elif field_class.field_type in ['date', 'datetime']:
                schema_fields[field_class.index_fieldname] = DATETIME(stored=field_class.stored)
            elif field_class.field_type == 'integer':
                schema_fields[field_class.index_fieldname] = NUMERIC(stored=field_class.stored, type=int, field_boost=field_class.boost)
            elif field_class.field_type == 'float':
                schema_fields[field_class.index_fieldname] = NUMERIC(stored=field_class.stored, type=float, field_boost=field_class.boost)
            elif field_class.field_type == 'boolean':
                # Field boost isn't supported on BOOLEAN as of 1.8.2.
                schema_fields[field_class.index_fieldname] = BOOLEAN(stored=field_class.stored)
            elif field_class.field_type == 'ngram':
                schema_fields[field_class.index_fieldname] = NGRAM(minsize=3, maxsize=15, stored=field_class.stored, field_boost=field_class.boost)
            elif field_class.field_type == 'edge_ngram':
                schema_fields[field_class.index_fieldname] = NGRAMWORDS(minsize=2, maxsize=15, at='start', stored=field_class.stored, field_boost=field_class.boost)
            else:
                analyzer = StemmingAnalyzer() | CharsetFilter(accent_map)
                schema_fields[field_class.index_fieldname] = TEXT(stored=True, analyzer=analyzer, field_boost=field_class.boost)

            if field_class.document is True:
                content_field_name = field_class.index_fieldname

        # Fail more gracefully than relying on the backend to die if no fields
        # are found.
        if len(schema_fields) <= initial_key_count:
            raise SearchBackendError("No fields were found in any search_indexes. Please correct this before attempting to search.")

        return (content_field_name, Schema(**schema_fields))


class FoldingWhooshEngine(WhooshEngine):
    backend = FoldingWhooshSearchBackend
