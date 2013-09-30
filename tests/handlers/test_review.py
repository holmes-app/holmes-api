#!/usr/bin/python
# -*- coding: utf-8 -*-

import sys
import calendar
from datetime import datetime

from preggy import expect
from tornado.testing import gen_test
from tornado.httpclient import HTTPError
from ujson import dumps

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
            "facts": [],
            "violations": [],
            "createdAt": dt
        }

        expect(response.body).to_be_like(dumps(expected))
