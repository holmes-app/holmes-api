#!/usr/bin/python
# -*- coding: utf-8 -*-

from tornado.concurrent import return_future
from motorengine import Document, URLField, StringField, DESCENDING

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

    def handle_get_page_count(self, callback):
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

    def handle_get_violation_data(self, callback):
        def handle(*arguments, **kwargs):
            if len(arguments) > 1 and arguments[1]:
                raise arguments[1]

            if not arguments[0]:
                callback((0, 0))
                return

            callback((arguments[0][0]['count'], arguments[0][0]['points']))

        return handle

    @return_future
    def get_violation_data(self, callback=None):
        Review.objects.aggregate.raw([
            {"$match": {"domain": self._id, "is_active": True}},
            {"$unwind": "$violations"},
            {"$group": {"_id": "$domain", "count": {"$sum": 1}, "points": {"$sum": "$violations.points"}}}
        ]).fetch(callback=self.handle_get_violation_data(callback))

    def handle_get_violations_per_day(self, callback):
        def handle(*arguments, **kwargs):
            if len(arguments) > 1 and arguments[1]:
                raise arguments[1]

            if not arguments[0]:
                callback([])
                return

            result = {}

            for day in arguments[0]:
                dt = "%d-%d-%d" % (day['year'], day['month'], day['day'])
                result[dt] = {
                    "violation_count": day['count'],
                    "violation_points": day['points']
                }

            callback(result)

        return handle

    @return_future
    def get_violations_per_day(self, callback=None):
        Review.objects.aggregate.raw([
            {"$match": {"domain": self._id, "is_complete": True}},
            {"$project": {
                "domain": 1,
                "violations": 1,
                "year": {"$year": "$completed_date"},
                "month": {"$month": "$completed_date"},
                "day": {"$dayOfMonth": "$completed_date"},
            }},
            {"$unwind": "$violations"},
            {
                "$group": {
                    "_id": {
                        "domain": "$domain", "year": "$year", "month": "$month", "day": "$day"
                    },
                    "count": {"$sum": 1},
                    "points": {"$sum": "$violations.points"}
                }
            }
        ]).fetch(callback=self.handle_get_violations_per_day(callback))

    def handle_get_active_reviews(self, callback):
        def handle(*arguments, **kwargs):
            if len(arguments) > 1 and arguments[1]:
                raise arguments[1]

            if not arguments[0]:
                callback([])
                return

            callback(arguments[0])

        return handle

    @return_future
    def get_active_reviews(self, current_page=1, page_size=10, callback=None):
        skip = (current_page - 1) * page_size
        Review.objects \
              .filter(is_active=True, domain=self) \
              .order_by(Review.violation_count, DESCENDING) \
              .skip(skip) \
              .limit(page_size) \
              .find_all(lazy=False, callback=self.handle_get_active_reviews(callback))

    def handle_get_active_review_count(self, callback):
        def handle(*arguments, **kwargs):
            if len(arguments) > 1 and arguments[1]:
                raise arguments[1]

            if not arguments[0]:
                callback(0)
                return

            callback(arguments[0])

        return handle

    @return_future
    def get_active_review_count(self, callback=None):
        Review.objects.filter(is_active=True, domain=self).count(callback=self.handle_get_active_review_count(callback))

    @classmethod
    def handle_get_domain_by_name(self, domain_name, callback):
        def handle(*arguments, **kwargs):
            if len(arguments) > 1 and arguments[1]:
                raise arguments[1]

            if not arguments[0]:
                from tornado import web
                raise web.HTTPError(404, reason='Domain with name "%s" was not found!' % domain_name)

            callback(arguments[0])

        return handle

    @classmethod
    @return_future
    def get_domain_by_name(self, domain_name, callback=None):
        Domain.objects.get(name=domain_name, callback=self.handle_get_domain_by_name(domain_name, callback))
