#!/usr/bin/python
# -*- coding: utf-8 -*-


from motorengine import Document, ReferenceField, DateTimeField


class Processing(Document):
    page = ReferenceField("holmes.models.page.Page", required=True)
    #facts = ListField(EmbeddedDocumentField(Fact))
    #violation = ListField(EmbeddedDocumentField(Violation))

    created_date = DateTimeField(required=True, auto_now_on_insert=True)
