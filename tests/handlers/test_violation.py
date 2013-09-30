#!/usr/bin/python
# -*- coding: utf-8 -*-

import sys

from preggy import expect
from tornado.testing import gen_test
from tornado.httpclient import HTTPError

from holmes.models import Review
from tests.base import ApiTestCase
from tests.fixtures import DomainFactory, PageFactory, ReviewFactory


class TestViolationHandler(ApiTestCase):

    @gen_test
    def test_invalid_review_returns_404(self):
        domain = yield DomainFactory.create()
        page = yield PageFactory.create(domain=domain)

        url = self.get_url(
            '/page/%s/review/invalid/violation' % page.uuid
        )

        try:
            yield self.http_client.fetch(
                url,
                method='POST',
                body='key=test.violation&title=title&description=description&points=20'
            )
        except HTTPError:
            err = sys.exc_info()[1]
            expect(err).not_to_be_null()
            expect(err.code).to_equal(404)
            expect(err.response.reason).to_be_like("Review with uuid of invalid not found!")
        else:
            assert False, "Should not have got this far"

    @gen_test
    def test_can_save_fact(self):
        domain = yield DomainFactory.create()
        page = yield PageFactory.create(domain=domain)
        review = yield ReviewFactory.create(page=page)

        url = self.get_url(
            '/page/%s/review/%s/violation' % (
                page.uuid,
                review.uuid
            )
        )

        response = yield self.http_client.fetch(
            url,
            method='POST',
            body='key=test.violation&title=title&description=description&points=20'
        )

        expect(response.code).to_equal(200)
        expect(response.body).to_equal("OK")

        review = yield Review.objects.get(uuid=review.uuid)

        expect(review).not_to_be_null()
        expect(review.violations).to_length(1)

        violation = review.violations[0]
        expect(violation.key).to_equal('test.violation')
        expect(violation.title).to_equal('title')
        expect(violation.description).to_equal('description')
        expect(violation.points).to_equal(20)
