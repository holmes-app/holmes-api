#!/usr/bin/python
# -*- coding: utf-8 -*-

import sys

from preggy import expect
from tornado.testing import gen_test
from tornado.httpclient import HTTPError
from ujson import loads

from holmes.models import Review
from tests.unit.base import ApiTestCase
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
            expect(err.response.reason).to_be_like('Review with uuid of invalid not found!')
        else:
            assert False, 'Should not have got this far'

    @gen_test
    def test_can_save_violation(self):
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
        expect(response.body).to_equal('OK')

        review = yield Review.objects.get(uuid=review.uuid)

        expect(review).not_to_be_null()
        expect(review.violations).to_length(1)

        violation = review.violations[0]
        expect(violation.key).to_equal('test.violation')
        expect(violation.title).to_equal('title')
        expect(violation.description).to_equal('description')
        expect(violation.points).to_equal(20)

    @gen_test
    def test_can_save_violation_will_round_float_points(self):
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
            body='key=test.violation&title=title&description=description&points=1.1'
        )

        response = yield self.http_client.fetch(
            url,
            method='POST',
            body='key=test.violation&title=title&description=description&points=1.9'
        )

        expect(response.code).to_equal(200)
        expect(response.body).to_equal('OK')

        review = yield Review.objects.get(uuid=review.uuid)

        expect(review).not_to_be_null()
        expect(review.violations).to_length(2)

        violation = review.violations[0]
        expect(violation.key).to_equal('test.violation')
        expect(violation.title).to_equal('title')
        expect(violation.description).to_equal('description')
        expect(violation.points).to_equal(1)

        violation = review.violations[1]
        expect(violation.key).to_equal('test.violation')
        expect(violation.title).to_equal('title')
        expect(violation.description).to_equal('description')
        expect(violation.points).to_equal(2)

    @gen_test
    def test_can_save_violation_will_add_zero_when_invalid(self):
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
            body='key=test.violation&title=title&description=description&points='
        )

        response = yield self.http_client.fetch(
            url,
            method='POST',
            body='key=test.violation&title=title&description=description&points=a'
        )

        expect(response.code).to_equal(200)
        expect(response.body).to_equal('OK')

        review = yield Review.objects.get(uuid=review.uuid)

        expect(review).not_to_be_null()
        expect(review.violations).to_length(2)

        violation = review.violations[0]
        expect(violation.key).to_equal('test.violation')
        expect(violation.title).to_equal('title')
        expect(violation.description).to_equal('description')
        expect(violation.points).to_equal(0)

        violation = review.violations[1]
        expect(violation.key).to_equal('test.violation')
        expect(violation.title).to_equal('title')
        expect(violation.description).to_equal('description')
        expect(violation.points).to_equal(0)


class TestMostCommonViolationsHandler(ApiTestCase):

    @gen_test
    def test_can_get_most_common_violations(self):
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
        expect(response.body).to_equal('OK')

        review = yield Review.objects.get(uuid=review.uuid)

        expect(review).not_to_be_null()
        expect(review.violations).to_length(1)

        response = yield self.http_client.fetch(
            self.get_url('/most-common-violations')
        )
        expect(response.code).to_equal(200)

        returned_json = loads(response.body)
        expect(returned_json).to_length(len(review.violations))
        expect(returned_json[0]['name']).to_equal('title')
        expect(returned_json[0]['count']).to_equal(1)
