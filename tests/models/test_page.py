#!/usr/bin/python
# -*- coding: utf-8 -*-


from preggy import expect

from tests.base import ApiTestCase
from tornado.testing import gen_test

from tests.fixtures import DomainFactory, PageFactory


class TestPage(ApiTestCase):
    @gen_test
    def test_can_create_page(self):
        domain = yield DomainFactory.create()
        page = yield PageFactory.create(domain=domain)

        expect(page._id).not_to_be_null()
        expect(page.url).to_include("http://my-site.com/")
        expect(page.title).to_include("page-")
