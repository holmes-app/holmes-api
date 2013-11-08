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
        domain = yield DomainFactory.create()
        page = yield PageFactory.create(domain=domain)

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
        domain = yield DomainFactory.create()
        page = yield PageFactory.create(domain=domain)
        review = yield ReviewFactory.create(page=page)

        review.add_fact('fact', 'value', 'title', 'kb')
        review.add_violation('violation', 'title', 'description', 100)
        yield review.save()

        url = self.get_url(
            '/page/%s/review/%s' % (
                page.uuid,
                review.uuid
            )
        )

        response = yield self.http_client.fetch(url)

        expect(response.code).to_equal(200)

        dt = calendar.timegm(datetime.now().utctimetuple())

        expected = {
            'domain': domain.name,
            'page': page.to_dict(),
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
            'violationCount': 1
        }

        expect(loads(response.body)).to_be_like(expected)


class TestCompleteReviewHandler(ApiTestCase):

    @gen_test
    def test_invalid_review_returns_404(self):
        domain = yield DomainFactory.create()
        page = yield PageFactory.create(domain=domain)

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
        domain = yield DomainFactory.create()
        page = yield PageFactory.create(domain=domain)
        review = yield ReviewFactory.create(page=page)

        url = self.get_url(
            '/page/%s/review/%s/complete' % (
                page.uuid,
                review.uuid
            )
        )

        response = yield self.http_client.fetch(url, method='POST', body='')

        expect(response.code).to_equal(200)

        review = yield Review.objects.get(review._id)
        yield review.load_references(['page'])
        yield review.page.load_references(['last_review'])

        expect(review.is_complete).to_be_true()
        expect(review.is_active).to_be_true()
        expect(review.completed_date).to_be_greater_or_equal_to(dt)
        expect(review.page.last_review._id).to_equal(review._id)

    @gen_test
    def test_completing_reviews_inactivates_old_reviews(self):
        dt = datetime.now()
        domain = yield DomainFactory.create()
        page = yield PageFactory.create(domain=domain)
        page2 = yield PageFactory.create(domain=domain)

        review = yield ReviewFactory.create(
            page=page,
            is_complete=True,
            is_active=True,
            created_date=dt-timedelta(days=1))

        review2 = yield ReviewFactory.create(page=page, is_complete=False, is_active=False)
        review3 = yield ReviewFactory.create(page=page2, is_complete=True, is_active=True)

        url = self.get_url(
            '/page/%s/review/%s/complete' % (
                page.uuid,
                review2.uuid
            )
        )

        response = yield self.http_client.fetch(url, method='POST', body='')

        expect(response.code).to_equal(200)

        loaded_review = yield Review.objects.get(review2._id)
        yield loaded_review.load_references(['page'])
        yield loaded_review.page.load_references(['last_review'])

        expect(loaded_review).not_to_be_null()
        expect(loaded_review.is_complete).to_be_true()
        expect(loaded_review.is_active).to_be_true()
        expect(loaded_review.completed_date).to_be_greater_or_equal_to(dt)
        expect(loaded_review.page.last_review._id).to_equal(review2._id)

        loaded_review = yield Review.objects.get(review._id)
        expect(loaded_review).not_to_be_null()
        expect(loaded_review.is_complete).to_be_true()
        expect(loaded_review.is_active).to_be_false()

        loaded_review = yield Review.objects.get(review3._id)
        expect(loaded_review).not_to_be_null()
        expect(loaded_review.is_complete).to_be_true()
        expect(loaded_review.is_active).to_be_true()

    @gen_test
    def test_cant_complete_review_twice(self):
        domain = yield DomainFactory.create()
        page = yield PageFactory.create(domain=domain)
        review = yield ReviewFactory.create(page=page, is_complete=True)

        url = self.get_url(
            '/page/%s/review/%s/complete' % (
                page.uuid,
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

        yield Page.objects.delete()
        yield Domain.objects.delete()
        yield Review.objects.delete()

        domain = yield DomainFactory.create()
        page = yield PageFactory.create(domain=domain)
        review_yesterday = yield ReviewFactory.create(page=page, created_date=(dt-timedelta(days=1)))
        review_old = yield ReviewFactory.create(page=page, created_date=dt)

        url = self.get_url(
            '/page/%s/review/%s/complete' % (
                page.uuid,
                str(review_old.uuid)
            )
        )
        response = yield self.http_client.fetch(url, method='POST', body='')
        expect(response.code).to_equal(200)

        review_new = yield ReviewFactory.create(page=page, created_date=dt)

        url = self.get_url(
            '/page/%s/review/%s/complete' % (
                page.uuid,
                str(review_new.uuid)
            )
        )
        response = yield self.http_client.fetch(url, method='POST', body='')
        expect(response.code).to_equal(200)

        reviews = yield Review.objects.filter(page=page).find_all()

        reviews_uuids = []
        for review in reviews:
            reviews_uuids.append(str(review.uuid))

        expect(reviews).to_length(2)
        expect(reviews_uuids).to_include(str(review_yesterday.uuid))
        expect(reviews_uuids).to_include(str(review_new.uuid))
        expect(reviews_uuids).not_to_include(str(review_old.uuid))
