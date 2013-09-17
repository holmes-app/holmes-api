#!/usr/bin/python
# -*- coding: utf-8 -*-


from motorengine import Document, URLField, StringField, ReferenceField

from holmes.models.domain import Domain


class Page(Document):
    title = StringField()
    url = URLField(required=True)
    domain = ReferenceField(Domain, required=True)
