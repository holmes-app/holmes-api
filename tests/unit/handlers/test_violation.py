#!/usr/bin/python
# -*- coding: utf-8 -*-

from ujson import loads
from tests.unit.base import ApiTestCase
from preggy import expect
from tornado.testing import gen_test

from tests.fixtures import ReviewFactory, PageFactory, DomainFactory, KeyFactory, ViolationFactory
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
        domains = [DomainFactory.create(
            name='g%s.com' % chr(i),
            url='http://g%s.com/' % chr(i)
        ) for i in xrange(ord('a'), ord('d'))]

        pages = [PageFactory.create(
            domain=domains[i % 3],
            url='%s%d' % (domains[i % 3].url, i % 2)
        ) for i in xrange(6)]

        for i, page in enumerate(pages):
            ReviewFactory.create(page=page, is_active=True, number_of_violations=i)

        self.db.flush()

        self.server.application.violation_definitions = {
            'key.%s' % i: {
                'title': 'title.%s' % i,
                'category': 'category.%s' % (i % 3),
                'key': Key.get_or_create(self.db, 'key.%d' % i, 'category.%d' % (i % 3))
            } for i in xrange(6)
        }

        response = yield self.http_client.fetch(
            self.get_url('/violation/key.1')
        )
        violations = loads(response.body)
        expect(response.code).to_equal(200)
        expect(violations).to_length(3)
        expect(violations['title']).to_equal('title.1')
        expect(violations['reviews']).to_length(4)
        expect(violations['reviewsCount']).to_equal(4)

        response = yield self.http_client.fetch(
            self.get_url('/violation/key.1?page_size=2&current_page=1')
        )
        violations = loads(response.body)
        expect(response.code).to_equal(200)
        expect(violations).to_length(3)
        expect(violations['title']).to_equal('title.1')
        expect(violations['reviews']).to_length(2)
        expect(violations['reviewsCount']).to_equal(4)

        response = yield self.http_client.fetch(
            self.get_url('/violation/key.1?page_filter=1')
        )
        violations = loads(response.body)
        expect(response.code).to_equal(200)
        expect(violations).to_length(3)
        expect(violations['title']).to_equal('title.1')
        expect(violations['reviews']).to_length(2)
        expect(violations['reviewsCount']).to_equal(2)

        response = yield self.http_client.fetch(
            self.get_url('/violation/key.1?domain_filter=gc.com')
        )
        violations = loads(response.body)
        expect(response.code).to_equal(200)
        expect(violations).to_length(3)
        expect(violations['title']).to_equal('title.1')
        expect(violations['reviews']).to_length(2)
        expect(violations['reviewsCount']).to_equal(8)

        response = yield self.http_client.fetch(
            self.get_url('/violation/key.1?domain_filter=foobar')
        )
        violations = loads(response.body)
        expect(response.code).to_equal(200)
        expect(violations).to_length(3)
        expect(violations['title']).to_equal('title.1')
        expect(violations['reviews']).to_length(4)
        expect(violations['reviewsCount']).to_equal(4)

        response = yield self.http_client.fetch(
            self.get_url('/violation/key.1?domain_filter=gc.com&page_filter=1')
        )
        violations = loads(response.body)
        expect(response.code).to_equal(200)
        expect(violations).to_length(3)
        expect(violations['title']).to_equal('title.1')
        expect(violations['reviews']).to_length(1)
        expect(violations['reviewsCount']).to_equal(1)

    @gen_test
    def test_can_get_blacklist_domains(self):
        key = KeyFactory.create(name='blacklist.domains')

        for i in xrange(3):
            for j in xrange(i + 1):
                ViolationFactory.create(
                    key=key,
                    value=[
                        'http://www.blacklist-domain-%d.com/' % i,
                        'http://blacklist-domain-%d.com/' % i
                    ]
                )
                ViolationFactory.create(
                    key=key,
                    value=['http://www.blacklist-domain-%d.com/' % i]
                )

        self.db.flush()

        self.server.application.violation_definitions = {
            'blacklist.domains': {
                'title': 'title',
                'category': 'category',
                'key': key
            }
        }

        response = yield self.http_client.fetch(
            self.get_url('/violation/blacklist.domains')
        )
        expect(response.code).to_equal(200)

        violation = loads(response.body)
        expect(violation['details']).to_length(3)
        expect(violation['details']).to_be_like([
            {'count': 9, 'domain': 'blacklist-domain-2.com'},
            {'count': 6, 'domain': 'blacklist-domain-1.com'},
            {'count': 3, 'domain': 'blacklist-domain-0.com'}
        ])


class TestViolationDomainsHandler(ApiTestCase):

    @gen_test
    def test_can_get_by_key_name_domains(self):
        domains = [DomainFactory.create(name='g%d.com' % i) for i in xrange(2)]
        keys = [KeyFactory.create(name='random.fact.%s' % i) for i in xrange(3)]

        for i in range(3):
            for j in range(i + 1):
                ViolationFactory.create(
                    key=keys[i],
                    domain=domains[j % 2]
                )

        self.db.flush()

        self.server.application.violation_definitions = {
            'random.fact.%s' % i: {
                'title': 'SEO',
                'category': 'SEO',
                'key': keys[i]
            } for i in xrange(3)
        }

        response = yield self.http_client.fetch(
            self.get_url('/violation/%s/domains' % keys[2].name)
        )

        violation = loads(response.body)

        expected_violation = {
            'domains': [
                {'name': 'g0.com', 'count': 2},
                {'name': 'g1.com', 'count': 1}
            ],
            'total': 3,
            'title': 'SEO'
        }

        expect(response.code).to_equal(200)
        expect(violation).to_length(3)
        expect(violation['domains']).to_length(2)
        expect(violation).to_be_like(expected_violation)
