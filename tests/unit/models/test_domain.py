#!/usr/bin/python
# -*- coding: utf-8 -*-

import sys
from datetime import datetime

from preggy import expect
from tornado.testing import gen_test
from tornado.web import HTTPError

from holmes.models import Domain, Page, Review
from tests.unit.base import ApiTestCase
from tests.fixtures import DomainFactory, PageFactory, ReviewFactory


class TestDomain(ApiTestCase):

    def test_can_create_domain(self):
        domain = DomainFactory.create()

        expect(domain.id).not_to_be_null()
        expect(domain.url).to_include('http://my-site-')
        expect(domain.name).to_include('domain-')

    def test_can_get_pages_per_domain(self):
        domain = DomainFactory.create()
        domain2 = DomainFactory.create()
        DomainFactory.create()

        PageFactory.create(domain=domain)
        PageFactory.create(domain=domain)
        PageFactory.create(domain=domain2)
        PageFactory.create(domain=domain2)
        PageFactory.create(domain=domain2)

        pages_per_domain = Domain.get_pages_per_domain(self.db)

        expect(pages_per_domain).to_be_like({
            domain.id: 2,
            domain2.id: 3
        })

    def test_can_convert_to_dict(self):
        domain = DomainFactory.create()

        domain_dict = domain.to_dict()

        expect(domain_dict['url']).to_equal(domain.url)
        expect(domain_dict['name']).to_equal(domain.name)

    def test_can_get_violations_per_domain(self):
        domain = DomainFactory.create()
        domain2 = DomainFactory.create()
        DomainFactory.create()

        page = PageFactory.create(domain=domain)
        page2 = PageFactory.create(domain=domain)
        page3 = PageFactory.create(domain=domain2)
        page4 = PageFactory.create(domain=domain2)
        page5 = PageFactory.create(domain=domain2)

        ReviewFactory.create(domain=domain, page=page, number_of_violations=40, is_active=True, is_complete=True)
        ReviewFactory.create(domain=domain, page=page2, number_of_violations=20, is_active=True, is_complete=True)
        ReviewFactory.create(domain=domain2, page=page3, number_of_violations=15, is_active=True, is_complete=True)
        ReviewFactory.create(domain=domain2, page=page4, number_of_violations=25, is_active=True, is_complete=True)
        ReviewFactory.create(domain=domain2, page=page5, number_of_violations=50, is_active=True, is_complete=True)

        violations_per_domain = Domain.get_violations_per_domain(self.db)

        expect(violations_per_domain).to_be_like({
            domain.id: 60,
            domain2.id: 90
        })

    def test_can_get_page_count(self):
        domain = DomainFactory.create()
        domain2 = DomainFactory.create()
        DomainFactory.create()

        PageFactory.create(domain=domain)
        PageFactory.create(domain=domain)
        PageFactory.create(domain=domain2)
        PageFactory.create(domain=domain2)
        PageFactory.create(domain=domain2)

        pages_for_domain = domain.get_page_count(self.db)
        pages_for_domain_2 = domain2.get_page_count(self.db)

        expect(pages_for_domain).to_equal(2)
        expect(pages_for_domain_2).to_equal(3)

    def test_can_get_violation_count_and_points(self):
        domain = DomainFactory.create()
        domain2 = DomainFactory.create()
        DomainFactory.create()

        page = PageFactory.create(domain=domain)
        page2 = PageFactory.create(domain=domain)
        page3 = PageFactory.create(domain=domain2)

        ReviewFactory.create(domain=domain, page=page, is_active=True, number_of_violations=20)
        ReviewFactory.create(domain=domain, page=page2, is_active=True, number_of_violations=10)
        ReviewFactory.create(domain=domain2, page=page3, is_active=True, number_of_violations=30)

        violation_count, violation_points = domain.get_violation_data(self.db)

        expect(violation_count).to_equal(30)
        expect(violation_points).to_equal(235)

    def test_can_get_violations_per_day(self):
        dt = datetime(2013, 10, 10, 10, 10, 10)
        dt2 = datetime(2013, 10, 11, 10, 10, 10)
        dt3 = datetime(2013, 10, 12, 10, 10, 10)

        domain = DomainFactory.create()

        page = PageFactory.create(domain=domain)

        ReviewFactory.create(domain=domain, page=page, is_active=False, is_complete=True, completed_date=dt, number_of_violations=20)
        ReviewFactory.create(domain=domain, page=page, is_active=False, is_complete=True, completed_date=dt2, number_of_violations=10)
        ReviewFactory.create(domain=domain, page=page, is_active=True, is_complete=True, completed_date=dt3, number_of_violations=30)

        violations = domain.get_violations_per_day(self.db)

        expect(violations["2013-10-10"]).to_be_like({
            "violation_count": 20,
            "violation_points": 190
        })

        expect(violations["2013-10-11"]).to_be_like({
            "violation_count": 10,
            "violation_points": 45
        })

        expect(violations["2013-10-12"]).to_be_like({
            "violation_count": 30,
            "violation_points": 435
        })

    @gen_test
    def test_can_get_reviews_for_domain(self):
        dt = datetime(2013, 10, 10, 10, 10, 10)
        dt2 = datetime(2013, 10, 11, 10, 10, 10)
        dt3 = datetime(2013, 10, 12, 10, 10, 10)

        domain = DomainFactory.create()

        page = PageFactory.create(domain=domain)

        ReviewFactory.create(page=page, is_active=False, is_complete=True, completed_date=dt, number_of_violations=20)
        ReviewFactory.create(page=page, is_active=False, is_complete=True, completed_date=dt2, number_of_violations=10)
        review = ReviewFactory.create(
            page=page, is_active=True, is_complete=True,
            completed_date=dt3, number_of_violations=30)

        reviews = domain.get_active_reviews(self.db)

        expect(reviews).to_length(1)

        expect(reviews[0].id).to_equal(review.id)

    def test_invalid_domain_returns_None(self):
        domain_name = 'domain-details.com'
        domain = Domain.get_domain_by_name(domain_name, self.db)

        expect(domain).to_be_null()

    def test_can_get_domain_by_name(self):
        domain = DomainFactory.create()

        loaded_domain = Domain.get_domain_by_name(domain.name, self.db)

        expect(loaded_domain.id).to_equal(domain.id)
