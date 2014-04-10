#!/usr/bin/python
# -*- coding: utf-8 -*-

import sys
import calendar
from datetime import datetime
from ujson import loads
from preggy import expect
from tornado.testing import gen_test
from tornado.httpclient import HTTPError

from holmes.models import Domain, Key
from tests.unit.base import ApiTestCase
from tests.fixtures import DomainFactory, PageFactory, ReviewFactory, RequestFactory


class TestDomainsHandler(ApiTestCase):

    @gen_test
    def test_can_get_domains_info(self):
        DomainFactory.create(url="http://globo.com", name="globo.com")
        DomainFactory.create(url="http://g1.globo.com", name="g1.globo.com")

        response = yield self.http_client.fetch(
            self.get_url('/domains')
        )

        expect(response.code).to_equal(200)

        domains = loads(response.body)

        expect(domains).to_length(2)

        expect(domains[0]['name']).to_equal("g1.globo.com")
        expect(domains[0]['url']).to_equal("http://g1.globo.com")
        expect(domains[0]['is_active']).to_be_true()

        expect(domains[1]['name']).to_equal("globo.com")
        expect(domains[1]['url']).to_equal("http://globo.com")
        expect(domains[1]['is_active']).to_be_true()

    @gen_test
    def test_will_return_empty_list_when_no_domains(self):
        response = yield self.http_client.fetch(
            self.get_url('/domains')
        )

        expect(response.code).to_equal(200)

        domains = loads(response.body)

        expect(domains).to_length(0)


class TestDomainsFullDataHandler(ApiTestCase):

    @gen_test
    def test_can_get_domains_full_data(self):
        domains = []
        for i in xrange(3):
            domains.append(DomainFactory.create(name='domain-%d.com' % i))

        pages = []
        for i, domain in enumerate(domains):
            pages.append([])
            for j in xrange(3):
                pages[i].append(PageFactory.create(domain=domain))

        requests = reviews = []
        for i, (domain, page) in enumerate(zip(domains, pages)):
            for j in xrange(i + 1):
                reviews.append(ReviewFactory.create(
                    domain=domain,
                    page=page[j],
                    is_active=True,
                    number_of_violations=(5 + 2 * j)
                ))
                requests.append(RequestFactory.create(
                    status_code=200 if j % 2 == 0 else 404,
                    domain_name=domain.name,
                    response_time=0.25 * (i + 1)
                ))

        self.server.application.violation_definitions = {
            'key.%s' % i: {
                'title': 'title.%s' % i,
                'category': 'category.%s' % (i % 3),
                'key': Key.get_or_create(self.db, 'key.%d' % i, 'category.%d' % (i % 3))
            } for i in xrange(9)
        }

        response = yield self.http_client.fetch(
            self.get_url('/domains-details')
        )

        expect(response.code).to_equal(200)

        full_data = loads(response.body)

        expect(full_data).to_length(3)
        expect(full_data[0].keys()).to_length(10)

        expect(map(lambda d: d['name'], full_data)).to_be_like(['domain-0.com', 'domain-1.com', 'domain-2.com'])
        expect(map(lambda d: d['pageCount'], full_data)).to_be_like([3, 3, 3])
        expect(map(lambda d: d['reviewCount'], full_data)).to_be_like([1, 2, 3])
        expect(map(lambda d: d['violationCount'], full_data)).to_be_like([5, 12, 21])
        expect(map(lambda d: d['reviewPercentage'], full_data)).to_be_like([33.33, 66.67, 100.0])
        expect(map(lambda d: d['errorPercentage'], full_data)).to_be_like([0.0, 50.0, 33.33])
        expect(map(lambda d: d['averageResponseTime'], full_data)).to_be_like([0.25, 0.5, 0.75])


class TestDomainDetailsHandler(ApiTestCase):

    @gen_test
    def test_can_get_domain_details(self):
        domain = DomainFactory.create(url="http://www.domain-details.com", name="domain-details.com")

        page = PageFactory.create(domain=domain, url=domain.url)
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
        expect(domain_details['reviewCount']).to_equal(2)
        expect(domain_details['violationCount']).to_equal(50)
        expect(domain_details['reviewPercentage']).to_equal(100.00)
        expect(domain_details['errorPercentage']).to_equal(0)
        expect(domain_details['averageResponseTime']).to_equal(0)
        expect(domain_details['is_active']).to_be_true()
        expect(domain_details['homepageId']).to_equal(str(page.uuid))
        expect(domain_details['homepageReviewId']).to_equal(str(page.last_review_uuid))

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


class TestDomainViolationsPerDayHandler(ApiTestCase):

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


class TestDomainReviewsHandler(ApiTestCase):

    @gen_test
    def test_can_get_domain_reviews_using_no_external_search_provider(self):
        self.use_no_external_search_provider()

        dt = datetime(2010, 11, 12, 13, 14, 15)
        dt_timestamp = calendar.timegm(dt.utctimetuple())

        dt2 = datetime(2011, 12, 13, 14, 15, 16)
        dt2_timestamp = calendar.timegm(dt2.utctimetuple())

        domain = DomainFactory.create(url="http://www.domain-details.com", name="domain-details.com")

        page = PageFactory.create(domain=domain, last_review_date=dt)
        page2 = PageFactory.create(domain=domain, last_review_date=dt2)

        ReviewFactory.create(page=page, is_active=True, is_complete=True, completed_date=dt, number_of_violations=13)
        ReviewFactory.create(page=page, is_active=False, is_complete=True, completed_date=dt2, number_of_violations=12)
        ReviewFactory.create(page=page2, is_active=True, is_complete=True, completed_date=dt2, number_of_violations=11)
        ReviewFactory.create(page=page2, is_active=False, is_complete=True, completed_date=dt, number_of_violations=10)

        response = yield self.http_client.fetch(
            self.get_url('/domains/%s/reviews/' % domain.name)
        )

        expect(response.code).to_equal(200)

        domain_details = loads(response.body)

        expect(domain_details['pages']).to_length(2)

        expect(domain_details['pages'][1]['url']).to_equal(page2.url)
        expect(domain_details['pages'][1]['uuid']).to_equal(str(page2.uuid))
        expect(domain_details['pages'][1]['completedAt']).to_equal(dt2_timestamp)

        expect(domain_details['pages'][0]['url']).to_equal(page.url)
        expect(domain_details['pages'][0]['uuid']).to_equal(str(page.uuid))
        expect(domain_details['pages'][0]['completedAt']).to_equal(dt_timestamp)

    @gen_test
    def test_can_get_domain_reviews_using_elastic_search_provider(self):
        self.use_elastic_search_provider()

        dt = datetime(2010, 11, 12, 13, 14, 15)
        dt_timestamp = calendar.timegm(dt.utctimetuple())

        dt2 = datetime(2011, 12, 13, 14, 15, 16)
        dt2_timestamp = calendar.timegm(dt2.utctimetuple())

        domain = DomainFactory.create(url="http://www.domain-details.com", name="domain-details.com")

        page = PageFactory.create(domain=domain, last_review_date=dt)
        page2 = PageFactory.create(domain=domain, last_review_date=dt2)

        review = ReviewFactory.create(page=page, is_active=False, is_complete=True, completed_date=dt, number_of_violations=13)
        self.server.application.search_provider.index_review(review)
        review = ReviewFactory.create(page=page, is_active=True, is_complete=True, completed_date=dt, number_of_violations=12)
        self.server.application.search_provider.index_review(review)
        review = ReviewFactory.create(page=page2, is_active=False, is_complete=True, completed_date=dt2, number_of_violations=11)
        self.server.application.search_provider.index_review(review)
        review = ReviewFactory.create(page=page2, is_active=True, is_complete=True, completed_date=dt2, number_of_violations=10)
        self.server.application.search_provider.index_review(review)

        self.server.application.search_provider.refresh()

        response = yield self.http_client.fetch(
            self.get_url('/domains/%s/reviews/' % domain.name)
        )

        expect(response.code).to_equal(200)

        domain_details = loads(response.body)

        expect(domain_details['pages']).to_length(2)

        expect(domain_details['pages'][0]['url']).to_equal(page.url)
        expect(domain_details['pages'][0]['uuid']).to_equal(str(page.uuid))
        expect(domain_details['pages'][0]['completedAt']).to_equal(dt_timestamp)
        expect(domain_details['pages'][0]['violationCount']).to_equal(12)

        expect(domain_details['pages'][1]['url']).to_equal(page2.url)
        expect(domain_details['pages'][1]['uuid']).to_equal(str(page2.uuid))
        expect(domain_details['pages'][1]['completedAt']).to_equal(dt2_timestamp)
        expect(domain_details['pages'][1]['violationCount']).to_equal(10)

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


class TestDomainGroupedViolationsHandler(ApiTestCase):

    @gen_test
    def test_can_get_domain_grouped_violations(self):
        domain1 = DomainFactory.create()
        domain2 = DomainFactory.create()

        page1 = PageFactory.create(domain=domain1)
        page2 = PageFactory.create(domain=domain1)
        page3 = PageFactory.create(domain=domain2)

        ReviewFactory.create(domain=domain1, page=page1, is_active=True, number_of_violations=5)
        ReviewFactory.create(domain=domain1, page=page2, is_active=True, number_of_violations=7)
        ReviewFactory.create(domain=domain2, page=page3, is_active=True, number_of_violations=9)

        self.server.application.violation_definitions = {
            'key.%s' % i: {
                'title': 'title.%s' % i,
                'category': 'category.%s' % (i % 3),
                'key': Key.get_or_create(self.db, 'key.%d' % i, 'category.%d' % (i % 3))
            } for i in xrange(9)
        }

        response = yield self.http_client.fetch(
            self.get_url('/domains/%s/violations' % domain1.name)
        )

        expect(response.code).to_equal(200)

        domain_violations = loads(response.body)

        expect(domain_violations).to_length(5)
        expect(domain_violations.keys()).to_be_like(['domainName', 'violations', 'total', 'domainURL', 'domainId'])
        expect(domain_violations['total']).to_equal(12)
        expect(domain_violations['violations']).to_length(3)

        counts = map(lambda v: v['count'], domain_violations['violations'])
        expect(counts).to_be_like([5, 4, 3])


class DomainTopCategoryViolationsHandler(ApiTestCase):

    @gen_test
    def test_can_get_domain_top_category_violations(self):
        domain1 = DomainFactory.create()
        domain2 = DomainFactory.create()

        page1 = PageFactory.create(domain=domain1)
        page2 = PageFactory.create(domain=domain1)
        page3 = PageFactory.create(domain=domain2)

        ReviewFactory.create(domain=domain1, page=page1, is_active=True, number_of_violations=5)
        ReviewFactory.create(domain=domain1, page=page2, is_active=True, number_of_violations=7)
        ReviewFactory.create(domain=domain2, page=page3, is_active=True, number_of_violations=9)

        self.server.application.violation_definitions = {
            'key.%s' % i: {
                'title': 'title.%s' % i,
                'category': 'category.%s' % (i % 3),
                'key': Key.get_or_create(self.db, 'key.%d' % i, 'category.%d' % (i % 3))
            } for i in xrange(9)
        }

        key = Key.get_or_create(self.db, 'key.0')

        response = yield self.http_client.fetch(
            self.get_url('/domains/%s/violations/%d/' % (domain1.name, key.category_id))
        )

        expect(response.code).to_equal(200)

        domain_top_category = loads(response.body)

        expect(domain_top_category).to_length(5)
        expect(domain_top_category.keys()).to_be_like(['violations', 'domainId', 'categoryId', 'domainURL', 'domainName'])
        expect(domain_top_category['violations']).to_length(3)

        counts = map(lambda v: v['count'], domain_top_category['violations'])
        expect(counts).to_be_like([2, 1, 1])


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
