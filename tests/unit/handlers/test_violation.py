#!/usr/bin/python
# -*- coding: utf-8 -*-

from ujson import loads
from tests.unit.base import ApiTestCase
from preggy import expect
from tornado.testing import gen_test

from tests.fixtures import ReviewFactory
from holmes.models import Key, Violation


class TestMostCommonViolationsHandler(ApiTestCase):

    def clean_cache(self, domain_name=None, cache_keys=[]):
        if domain_name:
            super(TestMostCommonViolationsHandler, self).clean_cache(domain_name)

        do_nothing = lambda *args, **kw: None
        for cache_key in cache_keys:
            self.server.application.redis.delete(cache_key, callback=do_nothing)

    @gen_test
    def test_can_get_most_common_violations(self):
        self.db.query(Violation).delete()
        self.clean_cache(cache_keys=['most-common-violations'])

        review = ReviewFactory.create()

        for i in range(5):
            key = Key.get_or_create(self.db, 'violation1')
            review.add_violation(key, 'value', 100)

        for j in range(2):
            key = Key.get_or_create(self.db, 'violation2')
            review.add_violation(key, 'value', 300)

        self.db.flush()

        response = yield self.http_client.fetch(
            self.get_url('/most-common-violations/')
        )

        violations = loads(response.body)

        expect(response.code).to_equal(200)
        expect(violations).to_be_like([
            {'count': 5, 'name': 'undefined', 'category': 'undefined'},
            {'count': 2, 'name': 'undefined', 'category': 'undefined'}
        ])

        self.db.query(Violation).delete()

        response = yield self.http_client.fetch(
            self.get_url('/most-common-violations/')
        )

        violations_from_cache = loads(response.body)

        expect(response.code).to_equal(200)
        expect(violations_from_cache).to_be_like(violations)
