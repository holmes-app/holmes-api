#!/usr/bin/python
# -*- coding: utf-8 -*-


from motorengine import Document, UUIDField, DateTimeField, ReferenceField


class Worker(Document):
    uuid = UUIDField(required=True)
    last_ping = DateTimeField(auto_now_on_update=True)
    current_page = ReferenceField(reference_document_type='holmes.models.page.Page')

    def __str__(self):
        return "Worker %s" % str(self.uuid)

    def __repr__(self):
        return str(self)
