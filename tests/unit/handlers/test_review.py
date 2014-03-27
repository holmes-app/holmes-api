#!/usr/bin/python
# -*- coding: utf-8 -*-

import sys
import calendar
from datetime import datetime, timedelta

from preggy import expect
from tornado.testing import gen_test
from tornado.httpclient import HTTPError
from ujson import loads

from tests.unit.base import ApiTestCase
from tests.fixtures import PageFactory, ReviewFactory, KeyFactory


class TestReviewHandler(ApiTestCase):

    @gen_test
    def test_invalid_review_returns_404(self):
        page = PageFactory.create()

        url = self.get_url('/page/%s/review/invalid' % page.uuid)

        try:
            yield self.http_client.fetch(
                url,
                method='GET'
            )
        except HTTPError:
            err = sys.exc_info()[1]
            expect(err).not_to_be_null()
            expect(err.code).to_equal(404)
            expect(err.response.reason).to_be_like('Review with uuid of invalid not found!')
        else:
            assert False, 'Should not have got this far'

    @gen_test
    def test_can_get_review(self):
        dt = datetime(2010, 11, 12, 13, 14, 15)
        dt_timestamp = calendar.timegm(dt.utctimetuple())
        review = ReviewFactory.create(created_date=dt)

        key1 = KeyFactory.create(name='fact')
        review.add_fact(key1, 'value')
        key2 = KeyFactory.create(name='violation')
        review.add_violation(key2, 'value', 100, review.domain)

        self.db.flush()

        url = self.get_url(
            '/page/%s/review/%s' % (
                review.page.uuid,
                review.uuid
            )
        )

        response = yield self.http_client.fetch(url)

        expect(response.code).to_equal(200)

        expected = {
            'domain': review.domain.name,
            'page': review.page.to_dict(),
            'uuid': str(review.uuid),
            'isComplete': False,
            'facts': [
                {u'key': u'fact', u'value': u'value', u'title': u'unknown',
                 u'unit': u'value', u'category': u'unknown'}
            ],
            'violations': [
                {u'points': 100, u'description': u'value',
                 u'key': u'violation', u'title': u'undefined', u'category': 'undefined'}
            ],
            'createdAt': dt_timestamp,
            'completedAt': None,
            'violationPoints': 100,
            'violationCount': 1,
        }

        expect(loads(response.body)).to_be_like(expected)


class TestLastReviewsHandler(ApiTestCase):

    @gen_test
    def test_can_get_last_reviews(self):
        page = PageFactory.create()

        date_now = datetime(2013, 11, 12, 13, 25, 27)

        review = ReviewFactory.create(
            page=page,
            is_active=True,
            is_complete=False,
            completed_date=date_now,
            created_date=date_now)

        key1 = KeyFactory.create(name='fact')
        review.add_fact(key1, 'value')
        key2 = KeyFactory.create(name='violation')
        review.add_violation(key2, 'value', 100, page.domain)
        review.is_complete = True
        self.db.flush()

        url = self.get_url('/last-reviews')
        response = yield self.http_client.fetch(url, method='GET')

        expect(response.code).to_equal(200)

        dt = calendar.timegm(date_now.utctimetuple())

        expected = [{
            'domain': review.domain.name,
            'page': page.to_dict(),
            'uuid': str(review.uuid),
            'isComplete': True,
            'facts': [
                {u'key': u'fact', u'unit': u'value', u'value': u'value',
                 u'title': u'unknown', u'category': u'unknown'}
            ],
            'violations': [
                {u'points': 100, u'description': u'value',
                 u'key': u'violation', u'title': u'undefined', u'category': 'undefined'}
            ],
            'createdAt': dt,
            'completedAt': dt,
            'violationCount': 1,
        }]

        expect(loads(response.body)).to_be_like(expected)


class TestLastReviewsInLastHourHandler(ApiTestCase):

    @gen_test
    def test_can_get_last_reviews_count_in_last_hour(self):
        ReviewFactory.create(is_active=True,
                             completed_date=datetime.today() - timedelta(minutes=61))
        ReviewFactory.create(is_active=True,
                             completed_date=datetime.today() - timedelta(minutes=59))
        ReviewFactory.create(is_active=True,
                             completed_date=datetime.today() - timedelta(minutes=5))
        ReviewFactory.create(is_active=True,
                             completed_date=datetime.today() - timedelta(minutes=1))

        self.db.flush()

        url = self.get_url('/reviews-in-last-hour')
        response = yield self.http_client.fetch(url, method='GET')

        expect(response.code).to_equal(200)

        expect(loads(response.body)).to_be_like({'count': 3})
