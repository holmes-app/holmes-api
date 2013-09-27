#!/usr/bin/python
# -*- coding: utf-8 -*-

from preggy import expect
from tornado.testing import gen_test

#from holmes.models import Page
from tests.base import ApiTestCase


class TestPageHandler(ApiTestCase):
    
    @gen_test
    def test_can_save(self):
        pass
        # response = yield self.http_client.fetch(
        #     self.get_url('/page'),
        #     method='POST',
        #     body='url=%s' % "http://globo.com"
        # )

        # expect(response.code).to_equal(200)
        # expect(response.body).to_equal("ok")
