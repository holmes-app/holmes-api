#!/usr/bin/python
# -*- coding: utf-8 -*-

from tornado.concurrent import return_future
from motorengine import Document, StringField, IntField

from holmes.models.review import Review


class Violation(Document):
    key = StringField(required=True)
    title = StringField(required=True, default='value')
    description = StringField(required=True, default='value')
    points = IntField(required=True)

    def __str__(self):
        return '%s: %s (%d points)\n%s' % (self.key, self.title, self.points, self.description)

    def __repr__(self):
        return self.__str__()

    def to_dict(self):
        return {
            'key': self.key,
            'title': self.title,
            'description': self.description,
            'points': self.points
        }

    @classmethod
    def handle_get_most_common_violations(cls, callback):
        def handle(*arguments, **kwargs):
            if len(arguments) > 1 and arguments[1]:
                raise arguments[1]

            violations = {}
            for violation in arguments[0]:
                violations[violation['_id']] = violation['count']
            callback(violations)

        return handle

    @classmethod
    @return_future
    def get_most_common_violations(cls, callback=None, limit=5):
        Review.objects.aggregate.raw([
            {"$unwind": "$violations" },
            {"$group": {"_id": "$violations.title", "count": {"$sum": 1}}},
            {"$sort": {"count": -1}},
            {"$limit": limit}
        ]).fetch(callback=cls.handle_get_most_common_violations(callback))
