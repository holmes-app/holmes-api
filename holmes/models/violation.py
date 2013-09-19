#!/usr/bin/python
# -*- coding: utf-8 -*-


from motorengine import Document, StringField, IntField


class Violation(Document):
    key = StringField(required=True)
    title = StringField(required=True, default="value")
    description = StringField(required=True, default="value")
    points = IntField(required=True)

    def __str__(self):
        return "%s (%d points)" % (self.key, self.points)

    def __repr__(self):
        return self.__str__()
