#!/usr/bin/python
# -*- coding: utf-8 -*-

import sys
from uuid import UUID
from ujson import loads

from preggy import expect
from tornado.testing import gen_test
from tornado.httpclient import HTTPError


from holmes.models import Page
from tests.base import ApiTestCase
from tests.fixtures import DomainFactory, PageFactory


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
        page = yield Page.objects.get(uuid=page_uuid)

        expect(page).not_to_be_null()
        expect(page_uuid).to_equal(page.uuid)

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

    @gen_test
    def test_when_url_already_exists(self):
        domain = yield DomainFactory.create()
        page = yield PageFactory.create(domain=domain)

        try:
            yield self.http_client.fetch(
                self.get_url('/page'),
                method='POST',
                body='url=%s' % page.url
            )
        except HTTPError:
            err = sys.exc_info()[1]
            expect(err).not_to_be_null()
            expect(err.code).to_equal(409)
            expect(err.response.reason).to_be_like("Duplicate entry for page [%s]" % page.url)
        else:
            assert False, "Should not have got this far"

    @gen_test
    def test_get_page_not_found(self):
        invalid_page_uuid = "00000000-0000-0000-0000-000000000000"

        try:
            yield self.http_client.fetch(
                self.get_url('/page/%s' % invalid_page_uuid),
                method='GET'
            )
        except HTTPError:
            err = sys.exc_info()[1]
            expect(err).not_to_be_null()
            expect(err.code).to_equal(404)
            expect(err.response.reason).to_be_like("Page UUID [%s] not found" % invalid_page_uuid)
        else:
            assert False, "Should not have got this far"

    @gen_test
    def test_get_page_get_info(self):
        domain = yield DomainFactory.create()
        page = yield PageFactory.create(domain=domain)

        response = yield self.http_client.fetch(self.get_url('/page/%s' % page.uuid))

        expect(response.code).to_equal(200)

        returned_page = loads(response.body)

        expect(returned_page['uuid']).to_equal(str(page.uuid))
        expect(returned_page['url']).to_equal(page.url)
