#!/usr/bin/python
# -*- coding: utf-8 -*-


from motorengine import Document, URLField, StringField


class Domain(Document):
    url = URLField(required=True)
    name = StringField(required=True)
