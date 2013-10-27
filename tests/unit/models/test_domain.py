#!/usr/bin/python
# -*- coding: utf-8 -*-


from preggy import expect

from tornado.testing import gen_test

from holmes.models import Domain
from tests.unit.base import ApiTestCase
from tests.fixtures import DomainFactory, PageFactory, ReviewFactory


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
        yield DomainFactory.create()

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

    @gen_test
    def test_can_get_violations_per_domain(self):
        domain = yield DomainFactory.create()
        domain2 = yield DomainFactory.create()
        yield DomainFactory.create()

        page = yield PageFactory.create(domain=domain)
        page2 = yield PageFactory.create(domain=domain)
        page3 = yield PageFactory.create(domain=domain2)
        page4 = yield PageFactory.create(domain=domain2)
        page5 = yield PageFactory.create(domain=domain2)

        yield ReviewFactory.create(page=page, number_of_violations=40, is_active=True, is_complete=True)
        yield ReviewFactory.create(page=page2, number_of_violations=20, is_active=True, is_complete=True)
        yield ReviewFactory.create(page=page3, number_of_violations=15, is_active=True, is_complete=True)
        yield ReviewFactory.create(page=page4, number_of_violations=25, is_active=True, is_complete=True)
        yield ReviewFactory.create(page=page5, number_of_violations=50, is_active=True, is_complete=True)

        violations_per_domain = yield Domain.get_violations_per_domain()

        expect(violations_per_domain).to_be_like({
            domain._id: 60,
            domain2._id: 90
        })

    @gen_test
    def test_can_get_page_count(self):
        domain = yield DomainFactory.create()
        domain2 = yield DomainFactory.create()
        yield DomainFactory.create()

        yield PageFactory.create(domain=domain)
        yield PageFactory.create(domain=domain)
        yield PageFactory.create(domain=domain2)
        yield PageFactory.create(domain=domain2)
        yield PageFactory.create(domain=domain2)

        pages_for_domain = yield domain.get_page_count()
        pages_for_domain_2 = yield domain2.get_page_count()

        expect(pages_for_domain).to_equal(2)
        expect(pages_for_domain_2).to_equal(3)

    @gen_test
    def test_can_get_violation_count_and_points(self):
        domain = yield DomainFactory.create()
        domain2 = yield DomainFactory.create()
        yield DomainFactory.create()

        page = yield PageFactory.create(domain=domain)
        page2 = yield PageFactory.create(domain=domain)
        page3 = yield PageFactory.create(domain=domain2)

        yield ReviewFactory.create(page=page, is_active=True, number_of_violations=20)
        yield ReviewFactory.create(page=page2, is_active=True, number_of_violations=10)
        yield ReviewFactory.create(page=page3, is_active=True, number_of_violations=30)

        violation_count, violation_points = yield domain.get_violation_data()

        expect(violation_count).to_equal(30)
        expect(violation_points).to_equal(235)
