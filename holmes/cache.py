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
    def increment_page_count(self, domain_name, increment=1, callback=None):
        self.increment_count('page-count', domain_name, increment, callback)

    def increment_count(self, key, domain_name, increment=1, callback=None):
        key = '%s-%s' % (self.get_domain_name(domain_name), key)
        self.redis.incrby(key, increment, callback=callback)

    @return_future
    def get_page_count(self, domain_name, callback=None):
        self.get_count(
            'page-count',
            domain_name,
            int(self.config.PAGE_COUNT_EXPIRATION_IN_SECONDS),
            lambda domain: domain.get_page_count(self.db),
            callback
        )

    @return_future
    def get_violation_count(self, domain_name, callback=None):
        self.get_count(
            'violation-count',
            domain_name,
            int(self.config.PAGE_COUNT_EXPIRATION_IN_SECONDS),
            lambda domain: domain.get_violation_data(self.db),
            callback
        )

    @return_future
    def get_review_count(self, domain_name, callback=None):
        self.get_count(
            'active-review-count',
            domain_name,
            int(self.config.ACTIVE_REVIEW_COUNT_EXPIRATION_IN_SECONDS),
            lambda domain: domain.get_active_review_count(self.db),
            callback
        )

    def get_count(self, key, domain_name, expiration, get_count_method, callback=None):
        cache_key = '%s-%s' % (self.get_domain_name(domain_name), key)
        self.redis.get(cache_key, callback=self.handle_get_count(key, domain_name, expiration, get_count_method, callback))

    def handle_get_count(self, key, domain_name, expiration, get_count_method, callback):
        def handle(count):
            if count is not None:
                callback(int(count))
                return

            domain = domain_name
            if domain and not isinstance(domain, Domain):
                domain = Domain.get_domain_by_name(domain_name, self.db)

            if not domain:
                callback(None)
                return

            count = get_count_method(domain)

            cache_key = '%s-%s' % (domain.name, key)

            self.redis.setex(
                key=cache_key,
                value=int(count),
                seconds=expiration,
                callback=self.handle_set_count(count, callback)
            )

        return handle

    def handle_set_count(self, count, callback):
        def handle(*args, **kw):
            callback(count)

        return handle