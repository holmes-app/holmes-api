#!/usr/bin/python
# -*- coding: utf-8 -*-

import sys
import calendar
from datetime import datetime, timedelta

from preggy import expect
from tornado.testing import gen_test
from tornado.httpclient import HTTPError
from ujson import loads

from holmes.models import Review, Page
from tests.unit.base import ApiTestCase
from tests.fixtures import DomainFactory, PageFactory, ReviewFactory


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
        review = ReviewFactory.create()

        review.add_fact('fact', 'value', 'title', 'kb')
        review.add_violation('violation', 'title', 'description', 100)

        self.db.flush()

        url = self.get_url(
            '/page/%s/review/%s' % (
                review.page.uuid,
                review.uuid
            )
        )

        response = yield self.http_client.fetch(url)

        expect(response.code).to_equal(200)

        dt = calendar.timegm(datetime.now().utctimetuple())

        expected = {
            'domain': review.domain.name,
            'page': review.page.to_dict(),
            'uuid': str(review.uuid),
            'isComplete': False,
            'facts': [
                {u'key': u'fact', u'value': u'value', u'title': u'title', u'unit': u'kb'}
            ],
            'violations': [
                {u'points': 100, u'description': u'description', u'key': u'violation', u'title': u'title'}
            ],
            'createdAt': dt,
            'completedAt': None,
            'violationPoints': 100,
            'violationCount': 1,
            'completedDateISO': None
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

        review.add_fact('fact', 'value', 'title', 'kb')
        review.add_violation('violation', 'title', 'description', 100)
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
                {u'key': u'fact', u'value': u'value', u'title': u'title',
                 u'unit': u'kb'}
            ],
            'violations': [
                {u'points': 100, u'description': u'description',
                 u'key': u'violation', u'title': u'title'}
            ],
            'createdAt': dt,
            'completedAt': dt,
            'violationCount': 1,
            'completedDateISO': date_now.isoformat()
        }]

        expect(loads(response.body)).to_be_like(expected)
