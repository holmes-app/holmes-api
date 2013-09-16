#!/usr/bin/python
# -*- coding: utf-8 -*-


from preggy import expect

from tests.base import ApiTestCase
from tornado.testing import gen_test

from holmes.models import Domain


class TestDomain(ApiTestCase):
    @gen_test
    def test_can_create_domain(self):
        domain = yield Domain.objects.create(url="http://www.globo.com/", name="Globo.com")

        expect(domain._id).not_to_be_null()
        expect(domain.url).to_equal("http://www.globo.com/")
        expect(domain.name).to_equal("Globo.com")
