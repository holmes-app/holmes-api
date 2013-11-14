#!/usr/bin/python
# -*- coding: utf-8 -*-

import sys
from datetime import datetime
from uuid import UUID
from ujson import loads, dumps

from preggy import expect
from tornado.testing import gen_test
from tornado.httpclient import HTTPError
from mock import Mock

from holmes.models import Page
from tests.unit.base import ApiTestCase
from tests.fixtures import DomainFactory, PageFactory, ReviewFactory


class TestPageHandler(ApiTestCase):
    def mock_request(self, code, effective_url):
        def handle(*args, **kw):
            response_mock = Mock(code=code, effective_url=effective_url)
            kw['callback'](response_mock)

        client = Mock()
        self.server.application.http_client = client
        client.fetch.side_effect = handle

    @gen_test
    def test_can_save(self):
        def side_effect(*args, **kw):
            response_mock = Mock(code=200, effective_url="http://www.globo.com")
            kw['callback'](response_mock)

        self.mock_request(code=200, effective_url="http://www.globo.com")

        response = yield self.http_client.fetch(
            self.get_url('/page'),
            method='POST',
            body=dumps({
                'url': 'http://www.globo.com'
            })
        )

        expect(response.code).to_equal(200)

        page_uuid = UUID(response.body)
        page = Page.by_uuid(page_uuid, self.db)

        expect(page).not_to_be_null()
        expect(str(page_uuid)).to_equal(page.uuid)

    @gen_test
    def test_can_save_known_domain(self):
        DomainFactory.create(url='http://www.globo.com', name='globo.com')

        self.mock_request(code=200, effective_url="http://www.globo.com")

        response = yield self.http_client.fetch(
            self.get_url('/page'),
            method='POST',
            body=dumps({
                'url': 'http://www.globo.com'
            })
        )

        expect(response.code).to_equal(200)

        page_uuid = UUID(response.body)
        page = Page.by_uuid(page_uuid, self.db)

        expect(page).not_to_be_null()
        expect(str(page_uuid)).to_equal(page.uuid)

    @gen_test
    def test_error_when_invalid_url(self):
        invalid_url = ''

        try:
            yield self.http_client.fetch(
                self.get_url('/page'),
                method='POST',
                body=dumps({
                    'url': invalid_url
                })
            )
        except HTTPError:
            err = sys.exc_info()[1]
            expect(err).not_to_be_null()
            expect(err.code).to_equal(400)
            expect(err.response.reason).to_be_like('Invalid url [%s]' % invalid_url)

        else:
            assert False, 'Should not have got this far'

    @gen_test
    def test_when_url_already_exists(self):
        page = PageFactory.create(url="http://www.globo.com")

        self.mock_request(code=200, effective_url="http://www.globo.com")

        response = yield self.http_client.fetch(
            self.get_url('/page'),
            method='POST',
            body=dumps({
                'url': page.url
            })
        )

        expect(response.code).to_equal(200)
        expect(response.body).to_equal(str(page.uuid))

    @gen_test
    def test_when_url_already_exists_with_slash(self):
        page = PageFactory.create(url="http://www.globo.com/")

        self.mock_request(code=200, effective_url="http://www.globo.com")

        response = yield self.http_client.fetch(
            self.get_url('/page'),
            method='POST',
            body=dumps({
                'url': "http://www.globo.com"
            })
        )

        expect(response.code).to_equal(200)
        expect(response.body).to_equal(str(page.uuid))

        page_count = self.db.query(Page).filter(Page.url == "http://www.globo.com").count()
        expect(page_count).to_equal(0)

    @gen_test
    def test_when_url_already_exists_without_slash(self):
        page = PageFactory.create(url="http://www.globo.com")

        self.mock_request(code=200, effective_url="http://www.globo.com/")

        response = yield self.http_client.fetch(
            self.get_url('/page'),
            method='POST',
            body=dumps({
                'url': "http://www.globo.com/"
            })
        )

        expect(response.code).to_equal(200)
        expect(response.body).to_equal(str(page.uuid))

        page_count = self.db.query(Page).filter(Page.url == "http://www.globo.com/").count()
        expect(page_count).to_equal(0)

    @gen_test
    def test_get_page_not_found(self):
        try:
            yield self.http_client.fetch(
                self.get_url('/page/%s' % self.ZERO_UUID),
                method='GET'
            )
        except HTTPError:
            err = sys.exc_info()[1]
            expect(err).not_to_be_null()
            expect(err.code).to_equal(404)
            expect(err.response.reason).to_be_like('Page UUID [%s] not found' % self.ZERO_UUID)
        else:
            assert False, 'Should not have got this far'

    @gen_test
    def test_get_page_get_info(self):
        page = PageFactory.create()

        response = yield self.http_client.fetch(self.get_url('/page/%s' % page.uuid))

        expect(response.code).to_equal(200)

        returned_page = loads(response.body)

        expect(returned_page['uuid']).to_equal(str(page.uuid))
        expect(returned_page['url']).to_equal(page.url)


class TestPagesHandler(ApiTestCase):

    @gen_test
    def test_can_save_with_no_urls(self):
        response = yield self.http_client.fetch(
            self.get_url('/pages'),
            method='POST',
            body=''
        )

        expect(response.code).to_equal(200)
        expect(int(response.body)).to_equal(0)

    @gen_test
    def test_can_save(self):
        urls = ['http://%d.globo.com/%d.html' % (num, num) for num in range(1000)]

        response = yield self.http_client.fetch(
            self.get_url('/pages'),
            method='POST',
            body='&'.join(['url=%s' % url for url in urls])
        )

        expect(response.code).to_equal(200)
        expect(int(response.body)).to_equal(1000)

    @gen_test
    def test_saves_only_new_pages(self):
        domain = DomainFactory.create(name='globo.com', url='http://globo.com')
        page = PageFactory.create(domain=domain, url='http://www.globo.com/')

        urls = ['http://%d.globo.com/%d.html' % (num, num) for num in range(10)]
        urls.append(page.url)

        response = yield self.http_client.fetch(
            self.get_url('/pages'),
            method='POST',
            body='&'.join(['url=%s' % url for url in urls])
        )

        expect(response.code).to_equal(200)
        expect(int(response.body)).to_equal(10)

    @gen_test
    def test_saves_does_nothing_if_all_pages_already_there(self):
        domain = DomainFactory.create(name='globo.com', url='http://globo.com')
        page = PageFactory.create(domain=domain, url='http://www.globo.com/')

        urls = [page.url, page.url]

        response = yield self.http_client.fetch(
            self.get_url('/pages'),
            method='POST',
            body='&'.join(['url=%s' % url for url in urls])
        )

        expect(response.code).to_equal(200)
        expect(int(response.body)).to_equal(0)

        pages = self.db.query(Page).filter(Page.url == 'http://www.globo.com/').all()
        expect(pages).to_length(1)
        expect(pages[0].id).to_equal(page.id)

    @gen_test
    def test_cant_save_invalid_urls(self):
        urls = ['/%d.html' % num for num in range(1000)]

        try:
            yield self.http_client.fetch(
                self.get_url('/pages'),
                method='POST',
                body="&".join(['url=%s' % url for url in urls])
            )
        except HTTPError:
            err = sys.exc_info()[1]
            expect(err.code).to_equal(400)
            expect(err.response.reason).to_equal('In the urls you posted there is an invalid URL: /0.html')
        else:
            assert False, 'Should not have gotten this far'

    def test_page_will_return_options(self):
        response = yield self.http_client.fetch(
            self.get_url('/page'),
            method='OPTIONS'
        )

        expect(response.code).to_equal(200)
        expect('Access-Control-Allow-Origin' in response.headers).to_be_true()
        expect('Access-Control-Allow-Methods' in response.headers).to_be_true()
        expect('Access-Control-Allow-Headers' in response.headers).to_be_true()
        expect(response.headers['Access-Control-Allow-Origin']).to_be_like('*')
        expect(response.headers['Access-Control-Allow-Methods']).to_be_like('GET, POST, PUT')
        expect(response.headers['Access-Control-Allow-Headers']).to_be_like('Accept, Content-Type')

    @gen_test
    def test_pages_will_return_options(self):
        response = yield self.http_client.fetch(
            self.get_url('/pages'),
            method='OPTIONS'
        )

        expect(response.code).to_equal(200)
        expect('Access-Control-Allow-Origin' in response.headers).to_be_true()
        expect(response.headers['Access-Control-Allow-Origin']).to_be_like('*')


class TestPageReviewsHandler(ApiTestCase):

    @gen_test
    def test_can_get_page_reviews(self):
        dt1 = datetime(2010, 11, 12, 13, 14, 15)
        dt2 = datetime(2011, 12, 13, 14, 15, 16)

        domain = DomainFactory.create(url="http://www.domain-details.com", name="domain-details.com")

        page = PageFactory.create(domain=domain)

        review1 = ReviewFactory.create(page=page, is_active=False, is_complete=True, completed_date=dt1, number_of_violations=20)
        review2 = ReviewFactory.create(page=page, is_active=False, is_complete=True, completed_date=dt2, number_of_violations=30)

        response = yield self.http_client.fetch(
            self.get_url('/page/%s/reviews/' % page.uuid)
        )

        expect(response.code).to_equal(200)

        page_details = loads(response.body)

        expect(page_details[0]['violationCount']).to_equal(30)
        expect(page_details[0]['uuid']).to_equal(str(review2.uuid))
        expect(page_details[0]['completedDate']).to_equal(dt2.isoformat())

        expect(page_details[1]['violationCount']).to_equal(20)
        expect(page_details[1]['uuid']).to_equal(str(review1.uuid))
        expect(page_details[1]['completedDate']).to_equal(dt1.isoformat())


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
            self.get_url('/page/%s/violations-per-day/' % page.uuid)
        )

        expect(response.code).to_equal(200)

        violations = loads(response.body)

        expect(violations['violations']).to_be_like({
            u'2013-10-10': {
                u'violation_points': 190,
                u'violation_count': 20
            },
            u'2013-10-11': {
                u'violation_points': 45,
                u'violation_count': 10
            },
            u'2013-10-12': {
                u'violation_points': 435,
                u'violation_count': 30
            }
        })
