#!/usr/bin/python
# -*- coding: utf-8 -*-

from ujson import loads
from tests.unit.base import ApiTestCase
from preggy import expect
from tornado.testing import gen_test

from tests.fixtures import ReviewFactory, PageFactory, DomainFactory
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
            review.add_violation(key, 'value', 100, review.domain)

        for j in range(2):
            key = Key.get_or_create(self.db, 'violation2')
            review.add_violation(key, 'value', 300, review.domain)

        self.db.flush()

        response = yield self.http_client.fetch(
            self.get_url('/most-common-violations/')
        )

        violations = loads(response.body)

        expect(response.code).to_equal(200)
        expect(violations).to_be_like([
            {'count': 5, 'name': 'undefined', 'category': 'undefined', 'key': 'violation1'},
            {'count': 2, 'name': 'undefined', 'category': 'undefined', 'key': 'violation2'}
        ])

        self.db.query(Violation).delete()

        response = yield self.http_client.fetch(
            self.get_url('/most-common-violations/')
        )

        violations_from_cache = loads(response.body)

        expect(response.code).to_equal(200)
        expect(violations_from_cache).to_be_like(violations)


class TestViolationHandler(ApiTestCase):

    @gen_test
    def test_can_get_violation_by_key_name(self):
        self.db.query(Violation).delete()

        domain = DomainFactory.create(name='g.com')
        page = PageFactory.create(uuid='some-uuid', domain=domain, url='http://g.com/1')
        review = ReviewFactory.create(is_active=True, uuid='some-uuid', page=page)

        key1 = Key.get_or_create(self.db, 'random.fact.1')
        review.add_violation(key1, 'value', 100)

        key2 = Key.get_or_create(self.db, 'random.fact.2')
        review.add_violation(key2, 'value', 300)

        self.db.flush()

        self.server.application.violation_definitions = {
            'random.fact.1': {
                'title': 'SEO',
                'category': 'SEO',
                'key': key1
            },
            'random.fact.2': {
                'title': 'HTTP',
                'category': 'HTTP',
                'key': key2
            }
        }

        response = yield self.http_client.fetch(
            self.get_url('/violation/random.fact.1')
        )

        violations = loads(response.body)

        expected_violations = {
            'reviews': [{
                'page': {
                    'url': 'http://g.com/1',
                    'uuid': 'some-uuid',
                    'completedAt': None
                },
                'domain_name': 'g.com',
                'uuid': 'some-uuid'
            }],
            'title': 'SEO'
        }

        expect(response.code).to_equal(200)
        expect(violations).to_length(2)
        expect(violations['reviews']).to_length(1)
        expect(violations).to_be_like(expected_violations)
