#!/usr/bin/python
# -*- coding: utf-8 -*-

from datetime import date
from preggy import expect

from tests.unit.base import ApiTestCase
from tests.fixtures import RequestFactory

from holmes.models import Request


class TestRequest(ApiTestCase):

    def test_can_create_request(self):
        request = RequestFactory.create()

        expect(request.id).not_to_be_null()
        expect(request.domain_name).to_equal('g1.globo.com')
        expect(request.url).to_equal('http://g1.globo.com')
        expect(request.effective_url).to_equal('http://g1.globo.com/')
        expect(request.status_code).to_equal(301)
        expect(request.response_time).to_equal(0.23)
        expect(request.completed_date).to_equal(date(2013, 2, 12))
        expect(request.review_url).to_equal('http://globo.com/')

    def test_can_get_status_code_info(self):
        request = RequestFactory.create(domain_name='g1.globo.com')

        loaded = Request.get_status_code_info('g1.globo.com', self.db)

        expect(loaded[0].get('code')).to_equal(request.status_code)
        expect(loaded[0].get('total')).to_equal(1)

        invalid_domain = Request.get_status_code_info('g2.globo.com', self.db)
        expect(invalid_domain).to_equal([])

    def test_can_get_requests_by_status_code(self):
        request = RequestFactory.create(
            domain_name='globo.com',
            status_code=200
        )

        loaded = Request.get_requests_by_status_code('globo.com', 200, self.db)

        expect(loaded[0].url).to_equal(request.url)
        expect(loaded[0].review_url).to_equal(request.review_url)
        expect(loaded[0].completed_date).to_equal(request.completed_date)

        invalid_domain = Request.get_requests_by_status_code(
            'g1.globo.com',
            200,
            self.db
        )
        expect(invalid_domain).to_equal([])

        invalid_code = Request.get_requests_by_status_code(
            'globo.com',
            2300,
            self.db
        )
        expect(invalid_code).to_equal([])

    def test_can_get_requests_by_status_count(self):
        for i in range(4):
            RequestFactory.create(domain_name='globo.com', status_code=200)

        total = Request.get_requests_by_status_count(
            'globo.com',
            200,
            self.db
        )
        expect(total).to_equal(4)

        invalid_domain = Request.get_requests_by_status_code(
            'g1.globo.com',
            200,
            self.db
        )
        expect(invalid_domain).to_equal([])

        invalid_code = Request.get_requests_by_status_code(
            'globo.com',
            2300,
            self.db
        )
        expect(invalid_code).to_equal([])
