#!/usr/bin/python
# -*- coding: utf-8 -*-

import sys
import calendar
from datetime import datetime, timedelta

from preggy import expect
from tornado.testing import gen_test
from tornado.httpclient import HTTPError
from ujson import loads

from holmes.models import Review, Page, Domain
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


class TestCompleteReviewHandler(ApiTestCase):

    @gen_test
    def test_invalid_review_returns_404(self):
        page = PageFactory.create()

        url = self.get_url('/page/%s/review/invalid/complete' % page.uuid)

        try:
            yield self.http_client.fetch(
                url,
                method='POST',
                body=''
            )
        except HTTPError:
            err = sys.exc_info()[1]
            expect(err).not_to_be_null()
            expect(err.code).to_equal(404)
            expect(err.response.reason).to_be_like('Review with uuid of invalid not found!')
        else:
            assert False, 'Should not have got this far'

    @gen_test
    def test_can_complete_review(self):
        dt = datetime.now()
        review = ReviewFactory.create()

        url = self.get_url(
            '/page/%s/review/%s/complete' % (
                review.page.uuid,
                review.uuid
            )
        )

        response = yield self.http_client.fetch(url, method='POST', body='')

        expect(response.code).to_equal(200)

        review = self.db.query(Review).get(review.id)

        expect(review.is_complete).to_be_true()
        expect(review.is_active).to_be_true()
        expect(review.completed_date).to_be_greater_or_equal_to(dt)
        expect(review.page.last_review.id).to_equal(review.id)

    @gen_test
    def test_completing_reviews_inactivates_old_reviews(self):
        dt = datetime.now()
        domain = DomainFactory.create()
        page = PageFactory.create(domain=domain)
        page2 = PageFactory.create(domain=domain)

        review = ReviewFactory.create(
            page=page,
            is_complete=True,
            is_active=True,
            created_date=dt-timedelta(days=1))

        review2 = ReviewFactory.create(page=page, is_complete=False, is_active=False)
        review3 = ReviewFactory.create(page=page2, is_complete=True, is_active=True)

        url = self.get_url(
            '/page/%s/review/%s/complete' % (
                page.uuid,
                review2.uuid
            )
        )

        response = yield self.http_client.fetch(url, method='POST', body='')

        expect(response.code).to_equal(200)

        loaded_review = self.db.query(Review).get(review2.id)

        expect(loaded_review).not_to_be_null()
        expect(loaded_review.is_complete).to_be_true()
        expect(loaded_review.is_active).to_be_true()
        expect(loaded_review.completed_date).to_be_greater_or_equal_to(dt)
        expect(loaded_review.page.last_review.id).to_equal(review2.id)

        loaded_review = self.db.query(Review).get(review.id)
        expect(loaded_review).not_to_be_null()
        expect(loaded_review.is_complete).to_be_true()
        expect(loaded_review.is_active).to_be_false()

        loaded_review = self.db.query(Review).get(review3.id)
        expect(loaded_review).not_to_be_null()
        expect(loaded_review.is_complete).to_be_true()
        expect(loaded_review.is_active).to_be_true()

    @gen_test
    def test_cant_complete_review_twice(self):
        review = ReviewFactory.create(is_complete=True)

        url = self.get_url(
            '/page/%s/review/%s/complete' % (
                review.page.uuid,
                review.uuid
            )
        )

        try:
            yield self.http_client.fetch(
                url,
                method='POST',
                body=''
            )
        except HTTPError:
            err = sys.exc_info()[1]
            expect(err).not_to_be_null()
            expect(err.code).to_equal(400)
            expect(err.response.reason).to_be_like('Review with uuid %s is already completed!' % str(review.uuid))
        else:
            assert False, 'Should not have got this far'

    @gen_test
    def test_same_day_review_removes_older(self):
        dt = datetime.now()

        page = PageFactory.create()
        review_yesterday = ReviewFactory.create(page=page, created_date=(dt-timedelta(days=1)))
        review_old = ReviewFactory.create(page=page, created_date=dt)

        url = self.get_url(
            '/page/%s/review/%s/complete' % (
                page.uuid,
                str(review_old.uuid)
            )
        )
        response = yield self.http_client.fetch(url, method='POST', body='')
        expect(response.code).to_equal(200)

        review_new = ReviewFactory.create(page=page, created_date=dt)

        url = self.get_url(
            '/page/%s/review/%s/complete' % (
                page.uuid,
                str(review_new.uuid)
            )
        )
        response = yield self.http_client.fetch(url, method='POST', body='')
        expect(response.code).to_equal(200)

        reviews = self.db.query(Review).filter(Review.page_id == page.id).all()

        reviews_uuids = []
        for review in reviews:
            reviews_uuids.append(str(review.uuid))

        expect(reviews).to_length(2)
        expect(reviews_uuids).to_include(str(review_yesterday.uuid))
        expect(reviews_uuids).to_include(str(review_new.uuid))
        expect(reviews_uuids).not_to_include(str(review_old.uuid))


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
