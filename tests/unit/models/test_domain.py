#!/usr/bin/python
# -*- coding: utf-8 -*-

from datetime import datetime

from preggy import expect
from tornado.testing import gen_test

from holmes.models import Domain, Request, Violation
from tests.unit.base import ApiTestCase
from tests.fixtures import DomainFactory, PageFactory, ReviewFactory, RequestFactory


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

        violation_count = domain.get_violation_data(self.db)

        expect(violation_count).to_equal(30)

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

        expect(violations).to_be_like([
            {
                "completedAt": "2013-10-10",
                "violation_count": 20,
                "violation_points": 190
            },
            {
                "completedAt": "2013-10-11",
                "violation_count": 10,
                "violation_points": 45
            },
            {
                "completedAt": "2013-10-12",
                "violation_count": 30,
                "violation_points": 435
            }
        ])

    @gen_test
    def test_can_get_reviews_for_domain(self):
        dt = datetime(2013, 10, 10, 10, 10, 10)
        dt2 = datetime(2013, 10, 11, 10, 10, 10)
        dt3 = datetime(2013, 10, 12, 10, 10, 10)

        domain = DomainFactory.create()

        page = PageFactory.create(domain=domain, last_review_date=dt3)

        ReviewFactory.create(page=page, is_active=False, is_complete=True, completed_date=dt, number_of_violations=20)
        ReviewFactory.create(page=page, is_active=False, is_complete=True, completed_date=dt2, number_of_violations=10)
        review = ReviewFactory.create(
            page=page, is_active=True, is_complete=True,
            completed_date=dt3, number_of_violations=30)

        reviews = domain.get_active_reviews(self.db)

        expect(reviews).to_length(1)

        expect(reviews[0].last_review_uuid).to_equal(str(review.uuid))

    def test_invalid_domain_returns_None(self):
        domain_name = 'domain-details.com'
        domain = Domain.get_domain_by_name(domain_name, self.db)

        expect(domain).to_be_null()

    def test_can_get_domain_by_name(self):
        domain = DomainFactory.create()

        loaded_domain = Domain.get_domain_by_name(domain.name, self.db)

        expect(loaded_domain.id).to_equal(domain.id)

    def test_get_domain_names(self):
        self.db.query(Domain).delete()

        DomainFactory.create(name="g1.globo.com")
        DomainFactory.create(name="globoesporte.globo.com")

        domain_names = Domain.get_domain_names(self.db)

        expect(domain_names).to_be_like([
            'g1.globo.com',
            'globoesporte.globo.com'
        ])

    def test_can_get_good_request_count(self):
        self.db.query(Request).delete()

        domain = DomainFactory.create()

        good = domain.get_good_request_count(self.db)
        expect(good).to_equal(0)

        RequestFactory.create(status_code=200, domain_name=domain.name)
        RequestFactory.create(status_code=304, domain_name=domain.name)

        good = domain.get_good_request_count(self.db)
        expect(good).to_equal(2)

        RequestFactory.create(status_code=400, domain_name=domain.name)
        RequestFactory.create(status_code=403, domain_name=domain.name)
        RequestFactory.create(status_code=404, domain_name=domain.name)

        good = domain.get_good_request_count(self.db)
        expect(good).to_equal(2)

    def test_can_get_bad_request_count(self):
        self.db.query(Request).delete()

        domain = DomainFactory.create()

        bad = domain.get_bad_request_count(self.db)
        expect(bad).to_equal(0)

        RequestFactory.create(status_code=200, domain_name=domain.name)
        RequestFactory.create(status_code=304, domain_name=domain.name)

        bad = domain.get_bad_request_count(self.db)
        expect(bad).to_equal(0)

        RequestFactory.create(status_code=400, domain_name=domain.name)
        RequestFactory.create(status_code=403, domain_name=domain.name)
        RequestFactory.create(status_code=404, domain_name=domain.name)

        bad = domain.get_bad_request_count(self.db)
        expect(bad).to_equal(3)

    def test_can_get_response_time_avg(self):
        self.db.query(Request).delete()

        domain = DomainFactory.create()

        avg = domain.get_response_time_avg(self.db)
        expect(avg).to_be_like(0)

        RequestFactory.create(status_code=200, domain_name=domain.name, response_time=0.25)
        RequestFactory.create(status_code=304, domain_name=domain.name, response_time=0.35)

        avg = domain.get_response_time_avg(self.db)
        expect(avg).to_be_like(0.3)

        RequestFactory.create(status_code=400, domain_name=domain.name, response_time=0.25)
        RequestFactory.create(status_code=403, domain_name=domain.name, response_time=0.35)
        RequestFactory.create(status_code=404, domain_name=domain.name, response_time=0.25)

        avg = domain.get_response_time_avg(self.db)
        expect(avg).to_be_like(0.3)

    def test_can_get_domains_details(self):
        self.db.query(Domain).delete()

        details = Domain.get_domains_details(self.db)

        expect(details).to_length(0)

        domain = DomainFactory.create(name='domain-1.com', url='http://domain-1.com/')
        domain2 = DomainFactory.create(name='domain-2.com', url='http://domain-2.com/')
        DomainFactory.create()

        page = PageFactory.create(domain=domain)
        page2 = PageFactory.create(domain=domain)
        page3 = PageFactory.create(domain=domain2)

        ReviewFactory.create(domain=domain, page=page, is_active=True, number_of_violations=20)
        ReviewFactory.create(domain=domain, page=page2, is_active=True, number_of_violations=10)
        ReviewFactory.create(domain=domain2, page=page3, is_active=True, number_of_violations=30)

        RequestFactory.create(status_code=200, domain_name=domain.name, response_time=0.25)
        RequestFactory.create(status_code=304, domain_name=domain.name, response_time=0.35)
        RequestFactory.create(status_code=400, domain_name=domain.name, response_time=0.25)
        RequestFactory.create(status_code=403, domain_name=domain.name, response_time=0.35)
        RequestFactory.create(status_code=404, domain_name=domain.name, response_time=0.25)

        details = Domain.get_domains_details(self.db)

        expect(details).to_length(3)
        expect(details[0]).to_length(10)
        expect(details[0]['url']).to_equal('http://domain-1.com/')
        expect(details[0]['name']).to_equal('domain-1.com')
        expect(details[0]['violationCount']).to_equal(30)
        expect(details[0]['pageCount']).to_equal(2)
        expect(details[0]['reviewCount']).to_equal(2)
        expect(details[0]['reviewPercentage']).to_equal(100.0)
        expect(details[0]['errorPercentage']).to_equal(60.0)
        expect(details[0]['is_active']).to_be_true()
        expect(details[0]['averageResponseTime']).to_equal(0.3)

    def test_can_get_active_domains(self):
        self.db.query(Domain).delete()

        domain = DomainFactory(is_active=True)
        DomainFactory(is_active=False)

        domains = Domain.get_active_domains(self.db)

        expect(domains).to_length(1)
        expect(domains[0].id).to_equal(domain.id)
