#!/usr/bin/python
# -*- coding: utf-8 -*-

from tornado.concurrent import return_future
from motorengine import Document, URLField, StringField

from holmes.models.page import Page
from holmes.models.review import Review


class Domain(Document):
    url = URLField(required=True)
    name = StringField(required=True)

    def to_dict(self):
        return {
            "url": self.url,
            "name": self.name
        }

    @classmethod
    def handle_get_violations_per_domain(cls, callback):
        def handle(*arguments, **kwargs):
            if len(arguments) > 1 and arguments[1]:
                raise arguments[1]

            domains = {}
            for domain in arguments[0]:
                domains[domain['domain']] = domain['count']
            callback(domains)

        return handle

    @classmethod
    @return_future
    def get_violations_per_domain(cls, callback=None):
        Review.objects.aggregate.raw([
            {"$match": {"is_active": True}},
            {"$unwind": "$violations"},
            {"$group": {"_id": {"domain": "$domain"}, "count": {"$sum": 1}}}
        ]).fetch(callback=cls.handle_get_violations_per_domain(callback))

    @classmethod
    def handle_get_pages_per_domain(cls, callback):
        def handle(*arguments, **kwargs):
            if len(arguments) > 1 and arguments[1]:
                raise arguments[1]

            domains = {}
            for domain in arguments[0]:
                domains[domain['_id']] = domain['count']
            callback(domains)

        return handle

    @classmethod
    @return_future
    def get_pages_per_domain(cls, callback=None):
        Page.objects.aggregate.raw([
            {"$group": {"_id": "$domain", "count": {"$sum": 1}}}
        ]).fetch(callback=cls.handle_get_pages_per_domain(callback))

    @classmethod
    def handle_get_page_count(cls, callback):
        def handle(*arguments, **kwargs):
            if len(arguments) > 1 and arguments[1]:
                raise arguments[1]

            if not arguments[0]:
                callback(0)

            callback(arguments[0][0]['count'])

        return handle

    @return_future
    def get_page_count(self, callback=None):
        Page.objects.aggregate.raw([
            {"$match": {"domain": self._id}},
            {"$group": {"_id": "$domain", "count": {"$sum": 1}}}
        ]).fetch(callback=self.handle_get_page_count(callback))

    @classmethod
    def handle_get_violation_data(cls, callback):
        def handle(*arguments, **kwargs):
            if len(arguments) > 1 and arguments[1]:
                raise arguments[1]

            if not arguments[0]:
                callback(0, 0)

            callback((arguments[0][0]['count'], arguments[0][0]['points']))

        return handle

    @return_future
    def get_violation_data(self, callback=None):
        Review.objects.aggregate.raw([
            {"$match": {"domain": self._id, "is_active": True}},
            {"$unwind": "$violations"},
            {"$group": {"_id": "$domain", "count": {"$sum": 1}, "points": {"$sum": "$violations.points"}}}
        ]).fetch(callback=self.handle_get_violation_data(callback))
