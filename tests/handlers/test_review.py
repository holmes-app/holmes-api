#!/usr/bin/python
# -*- coding: utf-8 -*-

import sys
import calendar
from datetime import datetime

from preggy import expect
from tornado.testing import gen_test
from tornado.httpclient import HTTPError
from ujson import loads

from holmes.models import Review
from tests.base import ApiTestCase
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
            expect(err.response.reason).to_be_like("Review with uuid of invalid not found!")
        else:
            assert False, "Should not have got this far"

    @gen_test
    def test_can_get_review(self):
        domain = yield DomainFactory.create()
        page = yield PageFactory.create(domain=domain)
        review = yield ReviewFactory.create(page=page)

        review.add_fact("fact", "kb", "value")
        review.add_violation("violation", "title", "description", 100)
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
            "domain": domain.name,
            "pageId": str(page.uuid),
            "reviewId": str(review.uuid),
            "isComplete": False,
            'facts': [
                {'key': 'fact', 'unit': 'value', 'value': 'kb'}
            ],
            'violations': [
                {u'points': 100, u'description': u'description', u'key': u'violation', u'title': u'title'}
            ],
            "createdAt": dt,
            "completedAt": None
        }

        expect(loads(response.body)).to_be_like(expected)

    @gen_test
    def test_invalid_review_returns_404_on_post(self):
        domain = yield DomainFactory.create()
        page = yield PageFactory.create(domain=domain)

        url = self.get_url('/page/%s/review/invalid' % page.uuid)

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
            expect(err.response.reason).to_be_like("Review with uuid of invalid not found!")
        else:
            assert False, "Should not have got this far"

    @gen_test
    def test_can_finish_review(self):
        domain = yield DomainFactory.create()
        page = yield PageFactory.create(domain=domain)
        review = yield ReviewFactory.create(page=page)

        dt = datetime.now()

        url = self.get_url(
            '/page/%s/review/%s' % (
                page.uuid,
                review.uuid
            )
        )

        response = yield self.http_client.fetch(url, method="POST", body="")

        expect(response.code).to_equal(200)

        loaded_review = yield Review.objects.get(uuid=review.uuid)

        expect(loaded_review).not_to_be_null()
        expect(loaded_review.is_complete).to_be_true()
        expect(loaded_review.completed_date).to_be_like(dt)
