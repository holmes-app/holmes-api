#!/usr/bin/python
# -*- coding: utf-8 -*-

import calendar
from datetime import datetime, timedelta
from preggy import expect
from ujson import loads
from tests.unit.base import ApiTestCase
from tests.fixtures import RequestFactory
from tornado.testing import gen_test

from holmes.models import Request


class TestLastRequestsHandler(ApiTestCase):
    @property
    def cache(self):
        return self.server.application.cache

    @gen_test
    def test_get_last_requests(self):
        self.db.query(Request).delete()
        self.cache.redis.delete('requests-count')

        dt1 = datetime(2013, 11, 12)
        dt1_timestamp = calendar.timegm(dt1.utctimetuple())

        request = RequestFactory.create(completed_date=dt1)

        response = yield self.http_client.fetch(self.get_url('/last-requests/'))

        expect(response.code).to_equal(200)

        expect(loads(response.body)).to_be_like({
            u'requestsCount': 1,
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


class TestRequestsInLastDayHandler(ApiTestCase):
    @gen_test
    def test_get_requests_in_last_day(self):
        utcnow = datetime.utcnow().date()

        for i in range(3):
            RequestFactory.create(
                status_code=200,
                completed_date=utcnow - timedelta(days=1)
            )
            RequestFactory.create(
                status_code=404,
                completed_date=utcnow - timedelta(days=i)
            )
            RequestFactory.create(
                status_code=599,
                completed_date=utcnow - timedelta(days=i + 1)
            )

        self.db.flush()

        response = yield self.http_client.fetch(self.get_url('/requests-in-last-day/'))

        expect(response.code).to_equal(200)

        expect(loads(response.body)).to_be_like([
            {
                'statusCode': 200,
                'statusCodeTitle': 'OK',
                'count': 3
            }, {
                'statusCode': 404,
                'statusCodeTitle': 'Not Found',
                'count': 2
            }, {
                'statusCode': 599,
                'statusCodeTitle': 'Tornado Timeout',
                'count': 1
            }
        ])
