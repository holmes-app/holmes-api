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
from tests.fixtures import DelimiterFactory, UserFactory

from holmes.models import Delimiter, User


class TestDelimiterHandler(ApiTestCase):
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
    def test_can_get_delimiters(self):
        self.db.query(Delimiter).delete()

        DelimiterFactory.create(url='http://test.com/', value=100)
        DelimiterFactory.create(url='http://globo.com/', value=2)

        response = yield self.http_client.fetch(
            self.get_url('/delimiters')
        )

        expect(response.code).to_equal(200)

        delimiters = loads(response.body)

        expect(delimiters).to_length(2)

        expect(delimiters[0]['url']).to_equal('http://test.com/')
        expect(delimiters[0]['value']).to_equal(100)

        expect(delimiters[1]['url']).to_equal('http://globo.com/')
        expect(delimiters[1]['value']).to_equal(2)

    @gen_test
    def test_will_return_empty_list_when_no_delimiters(self):
        self.db.query(Delimiter).delete()

        response = yield self.http_client.fetch(
            self.get_url('/delimiters')
        )

        expect(response.code).to_equal(200)

        delimiters = loads(response.body)

        expect(delimiters).to_length(0)

    @gen_test
    def test_can_save_delimiters_without_access_token(self):
        self.db.query(Delimiter).delete()

        try:
            yield self.http_client.fetch(
                self.get_url('/delimiters'),
                method='POST',
                body=dumps({
                    'url': 'http://globo.com/',
                    'value': 10
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
    def test_can_save_delimiters_with_access_token(self):
        self.db.query(Delimiter).delete()
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
            self.get_url('/delimiters'),
            method='POST',
            body=dumps({
                'url': 'http://globo.com/',
                'value': 10
            }),
            headers={'X-AUTH-HOLMES': '111'}
        )

        loaded_delimiter = Delimiter.by_url('http://globo.com/', self.db)
        expect(loaded_delimiter).not_to_be_null()

    @gen_test
    def test_can_save_delimiters_with_empty_values(self):
        self.db.query(Delimiter).delete()
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
                self.get_url('/delimiters'),
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
    def test_can_save_delimiters_with_not_authorized_user(self):
        self.db.query(Delimiter).delete()
        self.db.query(User).delete()

        UserFactory(email='test@test.com')

        user_data = dumps({
            'reason': 'Unauthorized user',
        })

        self.mock_request(code=402, body=user_data)

        try:
            yield self.http_client.fetch(
                self.get_url('/delimiters'),
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
