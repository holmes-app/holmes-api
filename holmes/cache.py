#!/usr/bin/python
# -*- coding: utf-8 -*-

from tornado.concurrent import return_future

from holmes.models import Domain


class Cache(object):
    def __init__(self, application):
        self.application = application
        self.redis = self.application.redis
        self.db = self.application.db
        self.config = self.application.config

    def get_domain_name(self, domain_name):
        if isinstance(domain_name, Domain):
            return domain_name.name

        return domain_name

    @return_future
    def get_page_count(self, domain_name, callback=None):
        key = '%s-page-count' % self.get_domain_name(domain_name)
        self.redis.get(key, callback=self.handle_get_page_count(domain_name, callback))

    def handle_get_page_count(self, domain_name, callback):
        def handle(page_count):
            if page_count is not None:
                callback(int(page_count))
                return

            domain = domain_name
            if domain and not isinstance(domain, Domain):
                domain = Domain.get_domain_by_name(domain_name, self.db)

            if not domain:
                callback(None)
                return

            page_count = domain.get_page_count(self.db)

            key = '%s-page-count' % domain.name

            self.redis.setex(
                key=key,
                value=int(page_count),
                seconds=int(self.config.PAGE_COUNT_EXPIRATION_IN_SECONDS),
                callback=self.handle_set_page_count(page_count, callback)
            )

        return handle

    def handle_set_page_count(self, page_count, callback):
        def handle(*args, **kw):
            callback(page_count)

        return handle

    @return_future
    def get_violation_count(self, domain_name, callback=None):
        key = '%s-violation-count' % self.get_domain_name(domain_name)
        self.redis.get(key, callback=self.handle_get_violation_count(domain_name, callback))

    def handle_get_violation_count(self, domain_name, callback):
        def handle(violation_count):
            if violation_count is not None:
                callback(int(violation_count))
                return

            domain = domain_name
            if domain and not isinstance(domain, Domain):
                domain = Domain.get_domain_by_name(domain_name, self.db)

            if not domain:
                callback(None)
                return

            violation_count = domain.get_violation_data(self.db)

            key = '%s-violation-count' % domain.name

            self.redis.setex(
                key=key,
                value=int(violation_count),
                seconds=int(self.config.VIOLATION_COUNT_EXPIRATION_IN_SECONDS),
                callback=self.handle_set_violation_count(violation_count, callback)
            )

        return handle

    def handle_set_violation_count(self, violation_count, callback):
        def handle(*args, **kw):
            callback(violation_count)

        return handle
