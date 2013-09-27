#!/usr/bin/python
# -*- coding: utf-8 -*-

import sys
from uuid import UUID

from preggy import expect
from tornado.testing import gen_test
from tornado.httpclient import HTTPError

from holmes.models import Page
from tests.base import ApiTestCase


class TestPageHandler(ApiTestCase):
    
    @gen_test
    def test_can_save(self):
        response = yield self.http_client.fetch(
            self.get_url('/page'),
            method='POST',
            body='url=%s' % "http://globo.com"
        )

        expect(response.code).to_equal(200)

        page_uuid = UUID(response.body)
        page = yield Page.objects.filter(uuid=page_uuid).find_all()

        expect(page).not_to_be_null()
        expect(page).to_length(1)
        expect(page_uuid).to_equal(page[0].uuid)

    @gen_test
    def test_error_when_invalid_url(self):
        invalid_url = ""

        try:
            yield self.http_client.fetch(
                self.get_url('/page'),
                method='POST',
                body='url=%s' % invalid_url
            )
        except HTTPError:
            err = sys.exc_info()[1]
            expect(err).not_to_be_null()
            expect(err.code).to_equal(400)
            expect(err.response.reason).to_be_like("Invalid url [%s]" % invalid_url)

        else:
            assert False, "Should not have got this far"
            