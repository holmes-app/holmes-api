#!/usr/bin/python
# -*- coding: utf-8 -*-

import sys

from preggy import expect
from tornado.testing import gen_test
from tornado.httpclient import HTTPError

from holmes.models import Review
from tests.unit.base import ApiTestCase
from tests.fixtures import PageFactory, ReviewFactory


class TestFactHandler(ApiTestCase):

    @gen_test
    def test_invalid_review_returns_404(self):
        page = PageFactory.create()

        url = self.get_url(
            '/page/%s/review/invalid/fact' % page.uuid
        )

        try:
            yield self.http_client.fetch(
                url,
                method='POST',
                body='key=test.fact&unit=kb&title=test&value=10'
            )
        except HTTPError:
            err = sys.exc_info()[1]
            expect(err).not_to_be_null()
            expect(err.code).to_equal(404)
            expect(err.response.reason).to_be_like('Review with uuid of invalid not found!')
        else:
            assert False, 'Should not have got this far'

    @gen_test
    def test_can_save_fact(self):
        review = ReviewFactory.create()

        url = self.get_url(
            '/page/%s/review/%s/fact' % (
                review.page.uuid,
                review.uuid
            )
        )

        response = yield self.http_client.fetch(
            url,
            method='POST',
            body='key=test.fact&unit=kb&title=test&value=10'
        )

        expect(response.code).to_equal(200)
        expect(response.body).to_equal('OK')

        review = Review.by_uuid(review.uuid, self.db)

        expect(review).not_to_be_null()
        expect(review.facts).to_length(1)

        fact = review.facts[0]
        expect(fact.key).to_equal('test.fact')
        expect(fact.unit).to_equal('kb')
        expect(fact.value).to_equal('10')
        expect(fact.title).to_equal('test')
