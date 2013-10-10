#!/usr/bin/python
# -*- coding: utf-8 -*-


from motorengine import Document, StringField, IntField


class Violation(Document):
    key = StringField(required=True)
    title = StringField(required=True, default="value")
    description = StringField(required=True, default="value")
    points = IntField(required=True)

    def __str__(self):
        return "%s: %s (%d points)\n%s" % (self.key, self.title, self.points, self.description)

    def __repr__(self):
        return self.__str__()

    def to_dict(self):
        return {
            "key": self.key,
            "title": self.title,
            "description": self.description,
            "points": self.points
        }
