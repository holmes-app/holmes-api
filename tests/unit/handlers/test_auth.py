#!/usr/bin/python
# -*- coding: utf-8 -*-

from preggy import expect
from tornado.testing import gen_test
from tornado import gen
from tornado.httpclient import HTTPError
from ujson import dumps, loads
from mock import Mock, patch

from tests.unit.base import ApiTestCase
from tests.fixtures import UserFactory

from holmes.models import User
from holmes.handlers.auth import AuthenticateHandler


class TestAuthenticateHandler(ApiTestCase):

    @gen_test
    def test_can_verify_authenticated_request_with_inexistent_user(self):
        response = yield self.authenticated_fetch('/authenticate')
        expect(response.code).to_equal(200)
        response_body = loads(response.body)
        expect(response_body['authenticated']).to_be_false()
        expect(response_body['isSuperUser']).to_be_false()

    @gen_test
    def test_can_verify_authenticated_request_as_valid_user(self):
        self.db.query(User).delete()
        user = UserFactory(email='test@test.com', is_superuser=False)
        response = yield self.authenticated_fetch('/authenticate', user_email=user.email)
        expect(response.code).to_equal(200)
        response_body = loads(response.body)
        expect(response_body['authenticated']).to_be_true()
        expect(response_body['isSuperUser']).to_be_false()

    @gen_test
    def test_can_verify_not_authenticated_request(self):
        response = yield self.anonymous_fetch('/authenticate')
        expect(response.code).to_equal(200)
        response_body = loads(response.body)
        expect(response_body['authenticated']).to_be_false()
        expect(response_body['isSuperUser']).to_be_false()

    @gen_test
    def test_can_verify_authenticated_request_as_superuser(self):
        self.db.query(User).delete()
        user = UserFactory(email='test@test.com', is_superuser=True)
        response = yield self.authenticated_fetch('/authenticate', user_email=user.email)
        expect(response.code).to_equal(200)
        response_body = loads(response.body)
        expect(response_body['authenticated']).to_be_true()
        expect(response_body['isSuperUser']).to_be_true()

    @gen_test
    def test_cannot_authenticate_a_user_with_invalid_google_plus_token(self):
        with patch.object(AuthenticateHandler, '_fetch_google_userinfo') as auth_mock:
            result = gen.Future()
            response_mock = Mock(code=401, body=('Unauthorized'))
            result.set_result(response_mock)
            auth_mock.return_value = result

            try:
                response = yield self.anonymous_fetch(
                    '/authenticate', method='POST', body=dumps({
                        'provider': 'GooglePlus',
                        'access_token': 'INVALID-TOKEN',
                    })
                )
            except HTTPError, e:
                response = e.response

        expect(response.code).to_equal(401)
        expect(response.body).to_equal('Unauthorized')

    @gen_test
    def test_can_authenticate_a_user_with_valid_google_plus_token(self):
        with patch.object(AuthenticateHandler, '_fetch_google_userinfo') as auth_mock:
            result = gen.Future()
            response_mock = Mock(code=200, body=(
                '{"email":"test@gmail.com", "name":"Teste", "id":"56789"}'
            ))
            result.set_result(response_mock)
            auth_mock.return_value = result
            try:
                response = yield self.anonymous_fetch(
                    '/authenticate', method='POST', body=dumps({
                        'provider': 'GooglePlus',
                        'access_token': 'VALID-TOKEN',
                    })
                )
            except HTTPError, e:
                response = e.response

            expect(response.code).to_equal(200)
            expect(loads(response.body)['first_login']).to_be_true()
            expect(loads(response.body)['authenticated']).to_be_true()

    def test_can_authenticate_inexistent_user(self):
        with patch.object(AuthenticateHandler, 'authenticate_on_google') as auth_mock:
            result = gen.Future()
            result.set_result({
                'email': 'test@test.com',
                'fullname': 'Test',
                'id': '12345'
            })
            auth_mock.return_value = result
            try:
                response = yield self.anonymous_fetch(
                    '/authenticate', method='POST', body=dumps({
                        'provider': 'GooglePlus',
                        'access_token': 'VALID-TOKEN',
                    })
                )
            except HTTPError, e:
                response = e.response

            user = User.by_email('test@test.com', self.db)
            expect(response.code).to_equal(200)
            expect(loads(response.body)['first_login']).to_be_true()
            expect(loads(response.body)['authenticated']).to_be_true()
            expect(user).not_to_be_null()

    @gen_test
    def test_can_authenticate_existent_user(self):
        self.db.query(User).delete()
        user = UserFactory(email='test@test.com')
        with patch.object(AuthenticateHandler, 'authenticate_on_google') as auth_mock:
            result = gen.Future()
            result.set_result({
                'email': 'test@test.com',
                'fullname': 'Test',
                'id': '12345'
            })
            auth_mock.return_value = result
            try:
                response = yield self.anonymous_fetch(
                    '/authenticate', method='POST', body=dumps({
                        'provider': 'GooglePlus',
                        'access_token': 'VALID-TOKEN',
                    })
                )
            except HTTPError, e:
                response = e.response

            expect(response.code).to_equal(200)
            expect(loads(response.body)['first_login']).to_be_false()
            expect(loads(response.body)['authenticated']).to_be_true()
            expect(user).not_to_be_null()

    @gen_test
    def test_cant_authenticate_with_invalid_provider(self):
        try:
            response = yield self.anonymous_fetch(
                '/authenticate', method='POST', body=dumps({
                    'provider': 'INVALID-PROVIDER',
                    'access_token': 'VALID-TOKEN',
                })
            )
        except HTTPError, e:
            response = e.response

        expect(response.code).to_equal(401)
        expect(response.body).to_equal('Unauthorized')

    @gen_test
    def test_can_set_cookie_on_authentication(self):
        self.db.query(User).delete()
        user = UserFactory(email='test@test.com', fullname='Test', id='1')
        user.first_login = True
        with patch.object(AuthenticateHandler, 'authenticate') as auth_mock:
            result = gen.Future()
            result.set_result(user)
            auth_mock.return_value = result
            try:
                response = yield self.anonymous_fetch(
                    '/authenticate', method='POST', body=dumps({
                        'provider': 'GooglePlus',
                        'access_token': 'VALID-TOKEN',
                    })
                )
            except HTTPError, e:
                response = e.response

            expect(response.code).to_equal(200)
            expect(loads(response.body)['first_login']).to_be_true()
            expect(loads(response.body)['authenticated']).to_be_true()
            expect('HOLMES_AUTH_TOKEN' in response.headers.get('Set-Cookie')).to_equal(True)
