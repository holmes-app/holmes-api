#!/usr/bin/python
# -*- coding: utf-8 -*-

import calendar
from datetime import datetime, timedelta
from preggy import expect
from ujson import loads
from tests.unit.base import ApiTestCase
from tests.fixtures import RequestFactory, DomainFactory
from tornado.testing import gen_test

from holmes.models import Request


class TestLastRequestsHandler(ApiTestCase):
    @property
    def cache(self):
        return self.server.application.cache

    @gen_test
    def test_get_last_requests(self):
        self.db.query(Request).delete()

        dt1 = datetime(2013, 11, 12)
        dt1_timestamp = calendar.timegm(dt1.utctimetuple())

        domain1 = DomainFactory.create()
        domain2 = DomainFactory.create()
        request = RequestFactory.create(domain_name=domain1.name,
                                        completed_date=dt1)

        response = yield self.http_client.fetch(self.get_url('/last-requests/'))

        expect(response.code).to_equal(200)

        expect(loads(response.body)).to_be_like({
            u'requests': [{
                u'url': request.url,
                u'status_code': request.status_code,
                u'completed_date': dt1_timestamp,
                u'domain_name': request.domain_name,
                u'effective_url': request.effective_url,
                u'review_url': request.review_url,
                u'response_time': request.response_time
            }]
        })

        request = RequestFactory.create(domain_name=domain2.name,
                                        completed_date=dt1)

        response = yield self.http_client.fetch(self.get_url('/last-requests/'))
        expect(response.code).to_equal(200)
        expect(len(loads(response.body)['requests'])).to_be_like(2)

        response = yield self.http_client.fetch(self.get_url('/last-requests/?domain_filter=%s' % domain2.name))
        expect(response.code).to_equal(200)
        response_body = loads(response.body)
        expect(len(response_body['requests'])).to_be_like(1)
        expect(response_body['requests'][0]['domain_name']).to_be_like(domain2.name)

    @gen_test
    def test_get_last_requests_filter_by_staus_code(self):
        for i in range(3):
            RequestFactory.create(
                status_code=200,
                domain_name='globo.com'
            )
            RequestFactory.create(
                status_code=404,
                domain_name='g1.globo.com'
            )

        response = yield self.http_client.fetch(self.get_url('/last-requests/?status_code_filter=200'))

        expect(response.code).to_equal(200)

        response_body = loads(response.body)
        expect(response_body['requests']).to_length(3)
        expect(response_body['requests'][0]['domain_name']).to_be_like('globo.com')


class TestRequestsInLastDayHandler(ApiTestCase):
    @gen_test
    def test_get_requests_in_last_day(self):
        utcnow = datetime.utcnow()

        DomainFactory.create(name='globo.com')
        DomainFactory.create(name='globoesporte.com')
        DomainFactory.create(name='domain3.com')

        for i in range(3):
            RequestFactory.create(
                status_code=200,
                completed_date=utcnow.date() - timedelta(days=i),
                domain_name='globo.com'
            )
            RequestFactory.create(
                status_code=404,
                completed_date=utcnow.date() - timedelta(days=i),
                domain_name='globo.com'
            )
            RequestFactory.create(
                status_code=404,
                completed_date=utcnow.date() - timedelta(days=i),
                domain_name='globoesporte.com'
            )
            RequestFactory.create(
                status_code=599,
                completed_date=utcnow.date() - timedelta(days=i),
                domain_name='g1.globo.com'
            )

        self.db.flush()

        response = yield self.http_client.fetch(self.get_url('/requests-in-last-day/'))
        expect(response.code).to_equal(200)
        expect(loads(response.body)).to_be_like([
            {u'count': 2, u'statusCodeTitle': u'OK', u'statusCode': 200},
            {u'count': 4, u'statusCodeTitle': u'Not Found', u'statusCode': 404}
        ])

        response = yield self.http_client.fetch(self.get_url('/requests-in-last-day/?domain_filter=globo.com'))
        expect(response.code).to_equal(200)
        expect(loads(response.body)).to_be_like([
            {u'count': 2, u'statusCodeTitle': u'OK', u'statusCode': 200},
            {u'count': 2, u'statusCodeTitle': u'Not Found', u'statusCode': 404}
        ])

        response = yield self.http_client.fetch(self.get_url('/requests-in-last-day/?domain_filter=globoesporte.com'))
        expect(response.code).to_equal(200)
        expect(loads(response.body)).to_be_like([
            {u'count': 2, u'statusCodeTitle': u'Not Found', u'statusCode': 404}
        ])

        response = yield self.http_client.fetch(self.get_url('/requests-in-last-day/?domain_filter=g1.globo.com'))
        expect(response.code).to_equal(200)
        expect(loads(response.body)).to_be_like([])

        response = yield self.http_client.fetch(self.get_url('/requests-in-last-day/?domain_filter=domain3.com'))
        expect(response.code).to_equal(200)
        expect(loads(response.body)).to_be_like([])


class TestLastRequestsStatusCodeHandler(ApiTestCase):
    @gen_test
    def test_can_get_all_status_code(self):
        for i in range(3):
            for j in range(4):
                RequestFactory.create(
                    url='http://m.com/page-%d' % j,
                    domain_name='m.com',
                    status_code=200 + (100*j),
                )

        self.db.flush()

        response = yield self.http_client.fetch(self.get_url('/last-requests/status-code/'))

        expect(response.code).to_equal(200)

        expect(loads(response.body)).to_be_like([
            {
                u'statusCodeTitle': u'OK',
                u'statusCode': 200
            }, {
                u'statusCodeTitle': u'Multiple Choices',
                u'statusCode': 300
            }, {
                u'statusCodeTitle': u'Bad Request',
                u'statusCode': 400
            }, {
                u'statusCodeTitle': u'Internal Server Error',
                u'statusCode': 500
            }
        ])
