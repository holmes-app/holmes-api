#!/usr/bin/python
# -*- coding: utf-8 -*-


from preggy import expect

from tests.base import ApiTestCase


class HealthcheckHandlerTest(ApiTestCase):
    def test_healthcheck(self):
        response = self.fetch('/healthcheck')
        expect(response.code).to_equal(200)
        expect(response.body).to_be_like('WORKING')
