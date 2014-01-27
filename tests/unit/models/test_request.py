#!/usr/bin/python
# -*- coding: utf-8 -*-

from datetime import datetime
from preggy import expect

from tests.unit.base import ApiTestCase
from tests.fixtures import RequestFactory


class TestDomain(ApiTestCase):

    def test_can_create_request(self):
        request = RequestFactory.create()

        expect(request.id).not_to_be_null()
        expect(request.domain_name).to_equal('g1.globo.com')
        expect(request.url).to_equal('http://g1.globo.com')
        expect(request.effective_url).to_equal('http://g1.globo.com/')
        expect(request.status_code).to_equal(301)
        expect(request.response_time).to_equal(0.23)
        expect(request.completed_date).to_equal(datetime(2013, 2, 12, 0, 0))
