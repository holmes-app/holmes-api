#!/usr/bin/python
# -*- coding: utf-8 -*-


from preggy import expect

from tornado.testing import gen_test

from holmes.models import Domain
from tests.unit.base import ApiTestCase
from tests.fixtures import DomainFactory, PageFactory


class TestDomain(ApiTestCase):

    @gen_test
    def test_can_create_domain(self):
        domain = yield DomainFactory.create()

        expect(domain._id).not_to_be_null()
        expect(domain.url).to_include('http://my-site-')
        expect(domain.name).to_include('domain-')

    @gen_test
    def test_can_get_pages_per_domain(self):
        domain = yield DomainFactory.create()
        domain2 = yield DomainFactory.create()

        yield PageFactory.create(domain=domain)
        yield PageFactory.create(domain=domain)
        yield PageFactory.create(domain=domain2)
        yield PageFactory.create(domain=domain2)
        yield PageFactory.create(domain=domain2)

        pages_per_domain = yield Domain.get_pages_per_domain()

        expect(pages_per_domain).to_be_like({
            domain._id: 2,
            domain2._id: 3
        })

    @gen_test
    def test_can_convert_to_dict(self):
        domain = yield DomainFactory.create()
        domain_dict = domain.to_dict()

        expect(domain.url).to_equal(domain_dict['url'])
        expect(domain.name).to_equal(domain_dict['name'])
