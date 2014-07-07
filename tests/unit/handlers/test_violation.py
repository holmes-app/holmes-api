#!/usr/bin/python
# -*- coding: utf-8 -*-

import sys
import calendar

from ujson import loads
from tests.unit.base import ApiTestCase
from preggy import expect
from tornado.testing import gen_test
from tornado.httpclient import HTTPError
from datetime import datetime

from tests.fixtures import ReviewFactory, PageFactory, DomainFactory, KeyFactory, ViolationFactory
from holmes.models import Key, Violation


class TestMostCommonViolationsHandler(ApiTestCase):

    @gen_test
    def test_can_get_most_common_violations(self):
        self.db.query(Violation).delete()

        review = ReviewFactory.create()

        for i in range(5):
            key = Key.get_or_create(self.db, 'violation.0')
            review.add_violation(key, 'value', 100, review.domain)

        for j in range(2):
            key = Key.get_or_create(self.db, 'violation.1')
            review.add_violation(key, 'value', 300, review.domain)

        self.server.application.violation_definitions = {
            'violation.%d' % i: {
                'title': 'title.%s' % i,
                'category': 'category.%s' % i,
                'key': Key.get_or_create(self.db, 'violation.%d' % i, 'category.%d' % i)
            } for i in range(3)
        }

        self.db.flush()

        response = yield self.http_client.fetch(
            self.get_url('/most-common-violations/')
        )

        violations = loads(response.body)

        expect(response.code).to_equal(200)
        expect(violations).to_be_like([
            {'count': 5, 'name': 'title.0', 'category': 'category.0', 'key': 'violation.0'},
            {'count': 2, 'name': 'title.1', 'category': 'category.1', 'key': 'violation.1'},
            {'count': 0, 'name': 'title.2', 'category': 'category.2', 'key': 'violation.2'},
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
    def test_can_get_violation_by_key_name_using_no_external_search_provider(self):
        self.use_no_external_search_provider()

        domains = [DomainFactory.create(
            name='g%s.com' % chr(i),
            url='http://g%s.com' % chr(i)
        ) for i in range(ord('a'), ord('d'))]

        pages = [PageFactory.create(
            domain=domains[i % 3],
            url='%s/%d' % (domains[i % 3].url, i % 2)
        ) for i in range(6)]

        for i, page in enumerate(pages):
            review = ReviewFactory.create(
                page=page,
                is_active=True,
                number_of_violations=i,
                created_date=datetime(2014, 04, 15, 11, 44, i),
                completed_date=datetime(2014, 04, 15, 11, 44, i * 2)
            )
            review.page.last_review_id = review.id
            review.page.last_review_uuid = review.uuid
            review.page.last_review_date = review.completed_date

        self.db.flush()

        self.server.application.violation_definitions = {
            'key.%s' % i: {
                'title': 'title.%s' % i,
                'category': 'category.%s' % (i % 3),
                'generic_description': 'description.%s' % (i % 3),
                'key': Key.get_or_create(self.db, 'key.%d' % i, 'category.%d' % (i % 3))
            } for i in range(6)
        }

        dt = datetime(2014, 04, 15, 11, 44, 4)
        dt_timestamp = calendar.timegm(dt.utctimetuple())

        response = yield self.http_client.fetch(
            self.get_url('/violation/key.1')
        )
        violations = loads(response.body)
        expect(response.code).to_equal(200)
        expect(violations).to_length(3)
        expect(violations['title']).to_equal('title.1')
        expect(violations['reviews']).to_length(4)
        expect(violations['reviewsCount']).to_equal(4)
        expect(violations['reviews'][3]['domain']).to_equal('gc.com')
        expect(violations['reviews'][3]['page']['url']).to_equal('http://gc.com/0')
        expect(violations['reviews'][3]['page']['completedAt']).to_equal(dt_timestamp)

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
        expect(violations['reviews']).to_length(4)
        expect(violations['reviewsCount']).to_be_null()

        response = yield self.http_client.fetch(
            self.get_url('/violation/key.1?domain_filter=gc.com')
        )
        violations = loads(response.body)
        expect(response.code).to_equal(200)
        expect(violations).to_length(3)
        expect(violations['title']).to_equal('title.1')
        expect(violations['reviews']).to_length(2)
        expect(violations['reviewsCount']).to_be_null()

        response = yield self.http_client.fetch(
            self.get_url('/violation/key.1?domain_filter=gc.com&page_filter=1')
        )
        violations = loads(response.body)
        expect(response.code).to_equal(200)
        expect(violations).to_length(3)
        expect(violations['title']).to_equal('title.1')
        expect(violations['reviews']).to_length(1)
        expect(violations['reviewsCount']).to_be_null()

        try:
            response = yield self.http_client.fetch(
                self.get_url('/violation/foobar')
            )
        except HTTPError:
            err = sys.exc_info()[1]
            expect(err).not_to_be_null()
            expect(err.code).to_equal(404)
            expect(err.response.reason).to_be_like('Invalid violation key foobar')
        else:
            assert False, 'Should not get this far'

        try:
            response = yield self.http_client.fetch(
                self.get_url('/violation/key.1?domain_filter=foobar')
            )
        except HTTPError:
            err = sys.exc_info()[1]
            expect(err).not_to_be_null()
            expect(err.code).to_equal(404)
            expect(err.response.reason).to_be_like('Domain foobar not found')
        else:
            assert False, 'Should not get this far'

    @gen_test
    def test_can_get_violation_by_key_name_using_elastic_search_provider(self):
        self.use_elastic_search_provider()

        domains = [DomainFactory.create(
            name='g%s.com' % chr(i),
            url='http://g%s.com' % chr(i)
        ) for i in range(ord('a'), ord('d'))]

        pages = [PageFactory.create(
            domain=domains[i % 3],
            url='%s/%d' % (domains[i % 3].url, i % 2)
        ) for i in range(6)]

        for i, page in enumerate(pages):
            review = ReviewFactory.create(
                page=page,
                is_active=True,
                number_of_violations=6 - i,
                created_date=datetime(2014, 04, 15, 11, 44, i),
                completed_date=datetime(2014, 04, 15, 11, 44, i * 2),
            )
            self.server.application.search_provider.index_review(review)

        self.db.flush()
        self.server.application.search_provider.refresh()

        self.server.application.violation_definitions = {
            'key.%s' % i: {
                'title': 'title.%s' % i,
                'category': 'category.%s' % (i % 3),
                'key': Key.get_or_create(self.db, 'key.%d' % i, 'category.%d' % (i % 3))
            } for i in range(6)
        }

        dt = datetime(2014, 04, 15, 11, 44, 2)  # [4, 3, 2, 1, 0]
        dt_timestamp = calendar.timegm(dt.utctimetuple())

        response = yield self.http_client.fetch(
            self.get_url('/violation/key.1')
        )
        violations = loads(response.body)
        expect(response.code).to_equal(200)
        expect(violations).to_length(3)
        expect(violations['title']).to_equal('title.1')
        expect(violations['reviews']).to_length(5)
        expect(violations['reviewsCount']).to_equal(5)
        expect(violations['reviews'][3]['domain']).to_equal('gb.com')
        expect(violations['reviews'][3]['page']['url']).to_equal('http://gb.com/1')
        expect(violations['reviews'][3]['page']['completedAt']).to_equal(dt_timestamp)

        response = yield self.http_client.fetch(
            self.get_url('/violation/key.1?page_size=2&current_page=1')
        )
        violations = loads(response.body)
        expect(response.code).to_equal(200)
        expect(violations).to_length(3)
        expect(violations['title']).to_equal('title.1')
        expect(violations['reviews']).to_length(2)
        expect(violations['reviewsCount']).to_equal(5)

        response = yield self.http_client.fetch(
            self.get_url('/violation/key.1?page_filter=1')
        )
        violations = loads(response.body)
        expect(response.code).to_equal(200)
        expect(violations).to_length(3)
        expect(violations['title']).to_equal('title.1')
        expect(violations['reviews']).to_length(5)
        expect(violations['reviewsCount']).to_equal(5)

        response = yield self.http_client.fetch(
            self.get_url('/violation/key.1?domain_filter=gb.com')
        )
        violations = loads(response.body)
        expect(response.code).to_equal(200)
        expect(violations).to_length(3)
        expect(violations['title']).to_equal('title.1')
        expect(violations['reviews']).to_length(2)
        expect(violations['reviewsCount']).to_equal(2)

        response = yield self.http_client.fetch(
            self.get_url('/violation/key.1?domain_filter=gb.com&page_filter=1')
        )
        violations = loads(response.body)
        expect(response.code).to_equal(200)
        expect(violations).to_length(3)
        expect(violations['title']).to_equal('title.1')
        expect(violations['reviews']).to_length(1)
        expect(violations['reviewsCount']).to_equal(1)

        try:
            response = yield self.http_client.fetch(
                self.get_url('/violation/foobar')
            )
        except HTTPError:
            err = sys.exc_info()[1]
            expect(err).not_to_be_null()
            expect(err.code).to_equal(404)
            expect(err.response.reason).to_be_like('Invalid violation key foobar')
        else:
            assert False, 'Should not get this far'

        try:
            response = yield self.http_client.fetch(
                self.get_url('/violation/key.1?domain_filter=foobar')
            )
        except HTTPError:
            err = sys.exc_info()[1]
            expect(err).not_to_be_null()
            expect(err.code).to_equal(404)
            expect(err.response.reason).to_be_like('Domain foobar not found')
        else:
            assert False, 'Should not get this far'

    @gen_test
    def test_can_get_blacklist_domains(self):
        key = KeyFactory.create(name='blacklist.domains')

        for i in range(3):
            for j in range(i + 1):
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
                'generic_description': '',
                'key': key
            }
        }

        response = yield self.http_client.fetch(
            self.get_url('/violation/blacklist.domains/domains')
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
    def test_fails_by_invalid_key_name_domains(self):
        try:
            yield self.http_client.fetch(
                self.get_url('/violation/foobar/domains')
            )
        except HTTPError:
            err = sys.exc_info()[1]
            expect(err).not_to_be_null()
            expect(err.code).to_equal(404)
            expect(err.response.reason).to_be_like('Invalid violation key foobar')
        else:
            assert False, 'Should not get this far'

    @gen_test
    def test_can_get_by_key_name_domains(self):
        domains = [DomainFactory.create(name='g%d.com' % i) for i in range(2)]
        keys = [KeyFactory.create(name='random.fact.%s' % i) for i in range(3)]

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
                'generic_description': 'Desc',
                'key': keys[i]
            } for i in range(3)
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
            'title': 'SEO',
            'category': 'SEO',
            'description': 'Desc'
        }

        expect(response.code).to_equal(200)
        expect(violation).to_length(5)
        expect(violation['domains']).to_length(2)
        expect(violation).to_be_like(expected_violation)
