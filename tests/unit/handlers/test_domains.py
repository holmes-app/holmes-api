#!/usr/bin/python
# -*- coding: utf-8 -*-

import sys
import calendar
from datetime import datetime
from ujson import loads
from preggy import expect
from tornado.testing import gen_test
from tornado.httpclient import HTTPError

from holmes.models import Domain, Request
from tests.unit.base import ApiTestCase
from tests.fixtures import DomainFactory, PageFactory, ReviewFactory, RequestFactory


class TestDomainsHandler(ApiTestCase):

    def setUp(self):
        super(TestDomainsHandler, self).setUp()
        self.db.query(Domain).delete()
        self.db.query(Request).delete()

    @gen_test
    def test_can_get_domains_info(self):
        self.clean_cache('globo.com')
        self.clean_cache('g1.globo.com')

        domain = DomainFactory.create(url="http://globo.com", name="globo.com")
        DomainFactory.create(url="http://g1.globo.com", name="g1.globo.com")

        page = PageFactory.create(domain=domain)

        ReviewFactory.create(is_active=True, domain=domain, page=page)

        RequestFactory.create(domain_name='globo.com', status_code=200, response_time=0.25)
        RequestFactory.create(domain_name='globo.com', status_code=300, response_time=0.35)
        RequestFactory.create(domain_name='globo.com', status_code=400, response_time=0.25)

        response = yield self.http_client.fetch(
            self.get_url('/domains')
        )

        expect(response.code).to_equal(200)

        domains = loads(response.body)

        expect(domains).to_length(2)

        expect(domains[0]['name']).to_equal("g1.globo.com")
        expect(domains[0]['url']).to_equal("http://g1.globo.com")
        expect(domains[0]['violationCount']).to_equal(0)
        expect(domains[0]['pageCount']).to_equal(0)
        expect(domains[0]['reviewPercentage']).to_equal(0)
        expect(domains[0]['errorPercentage']).to_equal(0)
        expect(domains[0]['averageResponseTime']).to_be_like(0)

        expect(domains[1]['name']).to_equal("globo.com")
        expect(domains[1]['url']).to_equal("http://globo.com")
        expect(domains[1]['violationCount']).to_equal(0)
        expect(domains[1]['pageCount']).to_equal(1)
        expect(domains[1]['reviewPercentage']).to_equal(100.00)
        expect(domains[1]['errorPercentage']).to_equal(33.33)
        expect(domains[1]['averageResponseTime']).to_be_like(0.3)

    @gen_test
    def test_will_return_empty_list_when_no_domains(self):
        response = yield self.http_client.fetch(
            self.get_url('/domains')
        )

        expect(response.code).to_equal(200)

        domains = loads(response.body)

        expect(domains).to_length(0)


class TestDomainDetailsHandler(ApiTestCase):

    @gen_test
    def test_can_get_domain_details(self):
        self.clean_cache('domain-details.com')

        domain = DomainFactory.create(url="http://www.domain-details.com", name="domain-details.com")

        page = PageFactory.create(domain=domain)
        page2 = PageFactory.create(domain=domain)

        ReviewFactory.create(page=page, is_active=True, is_complete=True, number_of_violations=20)
        ReviewFactory.create(page=page2, is_active=True, is_complete=True, number_of_violations=30)

        response = yield self.http_client.fetch(
            self.get_url('/domains/%s/' % domain.name)
        )

        expect(response.code).to_equal(200)

        domain_details = loads(response.body)

        expect(domain_details['name']).to_equal('domain-details.com')
        expect(domain_details['pageCount']).to_equal(2)
        expect(domain_details['violationCount']).to_equal(50)

    @gen_test
    def test_domain_not_found(self):
        name = 'haha.com.br'

        try:
            yield self.http_client.fetch(self.get_url('/domains/%s/' % name))
        except HTTPError:
            err = sys.exc_info()[1]
            expect(err).not_to_be_null()
            expect(err.code).to_equal(404)
        else:
            assert False, 'Should not have got this far'


class TestDomainReviewsHandler(ApiTestCase):

    @gen_test
    def test_can_get_domain_reviews(self):
        dt = datetime(2010, 11, 12, 13, 14, 15)
        dt_timestamp = calendar.timegm(dt.utctimetuple())

        dt2 = datetime(2011, 12, 13, 14, 15, 16)
        dt2_timestamp = calendar.timegm(dt2.utctimetuple())

        domain = DomainFactory.create(url="http://www.domain-details.com", name="domain-details.com")

        page = PageFactory.create(domain=domain, last_review_date=dt)
        page2 = PageFactory.create(domain=domain, last_review_date=dt2)

        ReviewFactory.create(page=page, is_active=True, is_complete=True, completed_date=dt, number_of_violations=20)
        ReviewFactory.create(page=page, is_active=False, is_complete=True, completed_date=dt2, number_of_violations=30)
        ReviewFactory.create(page=page2, is_active=True, is_complete=True, completed_date=dt2, number_of_violations=30)
        ReviewFactory.create(page=page2, is_active=False, is_complete=True, completed_date=dt, number_of_violations=20)

        response = yield self.http_client.fetch(
            self.get_url('/domains/%s/reviews/' % domain.name)
        )

        expect(response.code).to_equal(200)

        domain_details = loads(response.body)

        expect(domain_details['domainName']).to_equal('domain-details.com')
        expect(domain_details['domainURL']).to_equal('http://www.domain-details.com')
        expect(domain_details['pages']).to_length(2)

        expect(domain_details['pages'][1]['url']).to_equal(page2.url)
        expect(domain_details['pages'][1]['uuid']).to_equal(str(page2.uuid))
        expect(domain_details['pages'][1]['completedAt']).to_equal(dt2_timestamp)

        expect(domain_details['pages'][0]['url']).to_equal(page.url)
        expect(domain_details['pages'][0]['uuid']).to_equal(str(page.uuid))
        expect(domain_details['pages'][0]['completedAt']).to_equal(dt_timestamp)

    @gen_test
    def test_can_get_domain_reviews_for_next_page(self):
        dt = datetime(2010, 11, 12, 13, 14, 15)

        domain = DomainFactory.create(url="http://www.domain-details.com", name="domain-details.com")

        pages = []
        for page_index in range(16):
            page = PageFactory.create(domain=domain, last_review_date=dt)
            pages.append(page)

        reviews = []
        for review_index in range(16):
            review = ReviewFactory.create(
                page=pages[review_index],
                is_active=True,
                is_complete=True,
                completed_date=dt,
                number_of_violations=20
            )
            reviews.append(review)

        response = yield self.http_client.fetch(
            self.get_url('/domains/%s/reviews/?current_page=1' % domain.name)
        )

        expect(response.code).to_equal(200)

        domain_details = loads(response.body)

        expect(domain_details['pages']).to_length(10)

        for i in range(10):
            expect(domain_details['pages'][i]['url']).to_equal(pages[i].url)
            expect(domain_details['pages'][i]['uuid']).to_equal(str(pages[i].uuid))

        response = yield self.http_client.fetch(
            self.get_url('/domains/%s/reviews/?current_page=2' % domain.name)
        )

        expect(response.code).to_equal(200)

        domain_details = loads(response.body)

        expect(domain_details['pages']).to_length(6)

        for i in range(6):
            expect(domain_details['pages'][i]['url']).to_equal(pages[10 + i].url)
            expect(domain_details['pages'][i]['uuid']).to_equal(str(pages[10 + i].uuid))


class TestViolationsPerDayHandler(ApiTestCase):

    @gen_test
    def test_can_get_violations_per_day(self):
        dt = datetime(2013, 10, 10, 10, 10, 10)
        dt2 = datetime(2013, 10, 11, 10, 10, 10)
        dt3 = datetime(2013, 10, 12, 10, 10, 10)

        page = PageFactory.create()

        ReviewFactory.create(page=page, is_active=False, is_complete=True, completed_date=dt, number_of_violations=20)
        ReviewFactory.create(page=page, is_active=False, is_complete=True, completed_date=dt2, number_of_violations=10)
        ReviewFactory.create(page=page, is_active=True, is_complete=True, completed_date=dt3, number_of_violations=30)

        response = yield self.http_client.fetch(
            self.get_url('/domains/%s/violations-per-day/' % page.domain.name)
        )

        expect(response.code).to_equal(200)

        domain_details = loads(response.body)

        expect(domain_details['violations']).to_be_like([
            {
                u'completedAt': u'2013-10-10',
                u'violation_points': 190,
                u'violation_count': 20
            },
            {
                u'completedAt': u'2013-10-11',
                u'violation_points': 45,
                u'violation_count': 10
            },
            {
                u'completedAt': u'2013-10-12',
                u'violation_points': 435,
                u'violation_count': 30
            }
        ])


class TestChangeDomainStatus(ApiTestCase):

    @gen_test
    def test_can_set_domain_to_inactive(self):
        domain = DomainFactory.create(url="http://www.domain.com", name="domain.com", is_active=True)

        response = yield self.http_client.fetch(
            self.get_url(r'/domains/%s/change-status/' % domain.name),
            method='POST',
            body=''
        )
        expect(response.code).to_equal(200)
        domain_from_db = Domain.get_domain_by_name(domain.name, self.db)
        expect(domain_from_db.is_active).to_be_false()

    @gen_test
    def test_can_set_domain_to_active(self):
        domain = DomainFactory.create(url="http://www.domain.com", name="domain.com", is_active=False)

        response = yield self.http_client.fetch(
            self.get_url(r'/domains/%s/change-status/' % domain.name),
            method='POST',
            body=''
        )
        expect(response.code).to_equal(200)
        domain_from_db = Domain.get_domain_by_name(domain.name, self.db)
        expect(domain_from_db.is_active).to_be_true()
