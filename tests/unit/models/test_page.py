#!/usr/bin/python
# -*- coding: utf-8 -*-

from datetime import datetime

from preggy import expect
from tornado.testing import gen_test

from tests.unit.base import ApiTestCase
from tests.fixtures import DomainFactory, PageFactory


class TestPage(ApiTestCase):
    @gen_test
    def test_can_create_page(self):
        domain = yield DomainFactory.create()
        page = yield PageFactory.create(domain=domain)

        expect(page.uuid).not_to_be_null()
        expect(page._id).not_to_be_null()
        expect(page.url).to_include("http://my-site.com/")
        expect(page.title).to_include("page-")

        expect(page.added_date).to_be_like(datetime.now())
        expect(page.updated_date).to_be_like(datetime.now())

    @gen_test
    def test_can_convert_page_to_dict(self):
        domain = yield DomainFactory.create()
        page = yield PageFactory.create(domain=domain)

        page_dict = page.to_dict()

        expect(page_dict['uuid']).to_equal(str(page.uuid))
        expect(page_dict['title']).to_equal(page.title)
        expect(page_dict['url']).to_equal(page.url)
