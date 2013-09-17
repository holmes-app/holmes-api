#!/usr/bin/python
# -*- coding: utf-8 -*-


from preggy import expect

from tests.base import ApiTestCase
from tornado.testing import gen_test

from tests.fixtures import DomainFactory


class TestDomain(ApiTestCase):

    @gen_test
    def test_can_create_domain(self):
        domain = yield DomainFactory.create()

        expect(domain._id).not_to_be_null()
        expect(domain.url).to_include("http://my-site-")
        expect(domain.name).to_include("domain-")
