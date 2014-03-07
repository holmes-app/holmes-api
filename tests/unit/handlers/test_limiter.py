#!/usr/bin/python
# -*- coding: utf-8 -*-

import sys
from datetime import datetime
from preggy import expect
from tornado.testing import gen_test
from tornado.httpclient import HTTPError
from ujson import loads, dumps
from mock import Mock

from tests.unit.base import ApiTestCase
from tests.fixtures import LimiterFactory, UserFactory

from holmes.models import Limiter, User


class TestLimiterHandler(ApiTestCase):
    def mock_request(self, code, body):
        def handle(*args, **kw):
            response_mock = Mock(code=code, body=body)
            if 'callback' in kw:
                kw['callback'](response_mock)
            else:
                args[-1](response_mock)

        client = Mock()
        self.server.application.http_client = client
        client.fetch.side_effect = handle

    @gen_test
    def test_can_get_limiters(self):
        self.db.query(Limiter).delete()

        LimiterFactory.create(url='http://test.com/', value=100)
        LimiterFactory.create(url='http://globo.com/', value=2)

        response = yield self.http_client.fetch(
            self.get_url('/limiters')
        )

        expect(response.code).to_equal(200)

        limiters = loads(response.body)

        expect(limiters).to_length(2)

        expect(limiters[0]['url']).to_equal('http://test.com/')
        expect(limiters[0]['maxValue']).to_equal(100)

        expect(limiters[1]['url']).to_equal('http://globo.com/')
        expect(limiters[1]['maxValue']).to_equal(2)

    @gen_test
    def test_will_return_empty_list_when_no_limiters(self):
        self.db.query(Limiter).delete()

        response = yield self.http_client.fetch(
            self.get_url('/limiters')
        )

        expect(response.code).to_equal(200)

        limiters = loads(response.body)

        expect(limiters).to_length(0)

    @gen_test
    def test_can_save_limiters_without_access_token(self):
        self.db.query(Limiter).delete()

        try:
            yield self.http_client.fetch(
                self.get_url('/limiters'),
                method='POST',
                body=dumps({
                    'url': 'http://globo.com/',
                    'maxValue': 10
                })
            )
        except HTTPError:
            err = sys.exc_info()[1]
            expect(err).not_to_be_null()
            expect(err.code).to_equal(403)
            expect(err.response.reason).to_be_like('Forbidden')
        else:
            assert False, 'Should not have got this far'

    @gen_test
    def test_can_save_limiters_with_access_token(self):
        self.db.query(Limiter).delete()
        self.db.query(User).delete()

        dt = datetime(2014, 2, 14, 15, 0, 30)

        UserFactory(email='test@test.com')

        user_data = dumps({
            'is_superuser': True,
            'fullname': u'Marcelo Jorge Vieira',
            'last_login': dt,
            'email': u'test@test.com'
        })

        self.mock_request(code=200, body=user_data)

        yield self.http_client.fetch(
            self.get_url('/limiters'),
            method='POST',
            body=dumps({
                'url': 'http://globo.com/',
                'maxValue': 10
            }),
            headers={'X-AUTH-HOLMES': '111'}
        )

        loaded_limiter = Limiter.by_url('http://globo.com/', self.db)
        expect(loaded_limiter).not_to_be_null()

    @gen_test
    def test_can_save_limiters_with_empty_values(self):
        self.db.query(Limiter).delete()
        self.db.query(User).delete()

        dt = datetime(2014, 2, 14, 15, 0, 30)

        UserFactory(email='test@test.com')

        user_data = dumps({
            'is_superuser': True,
            'fullname': u'Marcelo Jorge Vieira',
            'last_login': dt,
            'email': u'test@test.com'
        })

        self.mock_request(code=200, body=user_data)

        try:
            yield self.http_client.fetch(
                self.get_url('/limiters'),
                method='POST',
                body='{}',
                headers={'X-AUTH-HOLMES': '111'}
            )
        except HTTPError:
            err = sys.exc_info()[1]
            expect(err).not_to_be_null()
            expect(err.code).to_equal(400)
            expect(err.response.body).to_equal(
                '{"reason":"Not url or value"}'
            )

    @gen_test
    def test_can_save_limiters_with_not_authorized_user(self):
        self.db.query(Limiter).delete()
        self.db.query(User).delete()

        UserFactory(email='test@test.com')

        user_data = dumps({
            'reason': 'Unauthorized user',
        })

        self.mock_request(code=402, body=user_data)

        try:
            yield self.http_client.fetch(
                self.get_url('/limiters'),
                method='POST',
                body='{}',
                headers={'X-AUTH-HOLMES': '111'}
            )
        except HTTPError:
            err = sys.exc_info()[1]
            expect(err).not_to_be_null()
            expect(err.code).to_equal(403)
            expect(err.response.reason).to_be_like('Forbidden')
            expect(err.response.body).to_equal(
                '{"reason":"Not authorized user."}'
            )
        else:
            assert False, 'Should not have got this far'
