#!/usr/bin/python
# -*- coding: utf-8 -*-

import sys
from datetime import datetime

from preggy import expect
from tornado.testing import gen_test
from tornado.web import HTTPError

from holmes.models import Domain
from tests.unit.base import ApiTestCase
from tests.fixtures import DomainFactory, PageFactory, ReviewFactory


class TestDomain(ApiTestCase):

    def test_can_create_domain(self):
        domain = DomainFactory.create()
        self.db.flush()

        expect(domain.id).not_to_be_null()
        expect(domain.url).to_include('http://my-site-')
        expect(domain.name).to_include('domain-')

    def test_can_get_pages_per_domain(self):
        domain = DomainFactory.create()
        domain2 = DomainFactory.create()
        DomainFactory.create()
        self.db.flush()

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
        self.db.flush()

        domain_dict = domain.to_dict()

        expect(domain_dict['url']).to_equal(domain.url)
        expect(domain_dict['name']).to_equal(domain.name)

    #@gen_test
    #def test_can_get_violations_per_domain(self):
        #domain = yield DomainFactory.create()
        #domain2 = yield DomainFactory.create()
        #yield DomainFactory.create()

        #page = yield PageFactory.create(domain=domain)
        #page2 = yield PageFactory.create(domain=domain)
        #page3 = yield PageFactory.create(domain=domain2)
        #page4 = yield PageFactory.create(domain=domain2)
        #page5 = yield PageFactory.create(domain=domain2)

        #yield ReviewFactory.create(page=page, number_of_violations=40, is_active=True, is_complete=True)
        #yield ReviewFactory.create(page=page2, number_of_violations=20, is_active=True, is_complete=True)
        #yield ReviewFactory.create(page=page3, number_of_violations=15, is_active=True, is_complete=True)
        #yield ReviewFactory.create(page=page4, number_of_violations=25, is_active=True, is_complete=True)
        #yield ReviewFactory.create(page=page5, number_of_violations=50, is_active=True, is_complete=True)

        #violations_per_domain = yield Domain.get_violations_per_domain()

        #expect(violations_per_domain).to_be_like({
            #domain._id: 60,
            #domain2._id: 90
        #})

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

    #@gen_test
    #def test_can_get_violation_count_and_points(self):
        #domain = yield DomainFactory.create()
        #domain2 = yield DomainFactory.create()
        #yield DomainFactory.create()

        #page = yield PageFactory.create(domain=domain)
        #page2 = yield PageFactory.create(domain=domain)
        #page3 = yield PageFactory.create(domain=domain2)

        #yield ReviewFactory.create(page=page, is_active=True, number_of_violations=20)
        #yield ReviewFactory.create(page=page2, is_active=True, number_of_violations=10)
        #yield ReviewFactory.create(page=page3, is_active=True, number_of_violations=30)

        #violation_count, violation_points = yield domain.get_violation_data()

        #expect(violation_count).to_equal(30)
        #expect(violation_points).to_equal(235)

    #@gen_test
    #def test_can_get_violations_per_day(self):
        #dt = datetime(2013, 10, 10, 10, 10, 10)
        #dt2 = datetime(2013, 10, 11, 10, 10, 10)
        #dt3 = datetime(2013, 10, 12, 10, 10, 10)

        #domain = yield DomainFactory.create()

        #page = yield PageFactory.create(domain=domain)

        #yield ReviewFactory.create(page=page, is_active=False, is_complete=True, completed_date=dt, number_of_violations=20)
        #yield ReviewFactory.create(page=page, is_active=False, is_complete=True, completed_date=dt2, number_of_violations=10)
        #yield ReviewFactory.create(page=page, is_active=True, is_complete=True, completed_date=dt3, number_of_violations=30)

        #violations = yield domain.get_violations_per_day()

        #expect(violations["2013-10-10"]).to_be_like({
            #"violation_count": 20,
            #"violation_points": 190
        #})

        #expect(violations["2013-10-11"]).to_be_like({
            #"violation_count": 10,
            #"violation_points": 45
        #})

        #expect(violations["2013-10-12"]).to_be_like({
            #"violation_count": 30,
            #"violation_points": 435
        #})

    #@gen_test
    #def test_can_get_reviews_for_domain(self):
        #dt = datetime(2013, 10, 10, 10, 10, 10)
        #dt2 = datetime(2013, 10, 11, 10, 10, 10)
        #dt3 = datetime(2013, 10, 12, 10, 10, 10)

        #domain = yield DomainFactory.create()

        #page = yield PageFactory.create(domain=domain)

        #yield ReviewFactory.create(page=page, is_active=False, is_complete=True, completed_date=dt, number_of_violations=20)
        #yield ReviewFactory.create(page=page, is_active=False, is_complete=True, completed_date=dt2, number_of_violations=10)
        #review = yield ReviewFactory.create(
            #page=page, is_active=True, is_complete=True,
            #completed_date=dt3, number_of_violations=30)

        #reviews = yield domain.get_active_reviews()

        #expect(reviews).to_length(1)

        #expect(reviews[0]._id).to_equal(review._id)

    #@gen_test
    #def test_invalid_domain_returns_404(self):
        #try:
            #domain_name = 'domain-details.com'
            #yield Domain.get_domain_by_name(domain_name)
        #except HTTPError:
            #err = sys.exc_info()[1]
            #expect(err).not_to_be_null()
            #expect(err.status_code).to_equal(404)
            #expect(err.reason).to_be_like('Domain with name "%s" was not found!' % domain_name)
        #else:
            #assert False, 'Should not have got this far'
