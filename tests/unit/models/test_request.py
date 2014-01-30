#!/usr/bin/python
# -*- coding: utf-8 -*-

from datetime import datetime
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
        expect(request.completed_date).to_equal(datetime(2013, 2, 12, 0, 0))
        expect(request.review_url).to_equal('http://globo.com/')

    def test_can_get_status_code_info(self):
        request = RequestFactory.create(domain_name='g1.globo.com')

        loaded = Request.get_status_code_info('g1.globo.com', self.db)

        expect(loaded[0].get('code')).to_equal(request.status_code)
        expect(loaded[0].get('total')).to_equal(1)

        invalid_domain = Request.get_status_code_info('g2.globo.com', self.db)
        expect(invalid_domain).to_equal([])
