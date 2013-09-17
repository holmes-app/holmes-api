#!/usr/bin/python
# -*- coding: utf-8 -*-


from motorengine import Document, URLField, StringField, ReferenceField, DateTimeField

from holmes.models.domain import Domain


class Page(Document):
    title = StringField()
    url = URLField(required=True)
    added_date = DateTimeField(required=True, auto_now_on_insert=True)
    updated_date = DateTimeField(required=True, auto_now_on_insert=True, auto_now_on_update=True)

    domain = ReferenceField(Domain, required=True)
    #last_processing = ReferenceField(Processing, required=False)
