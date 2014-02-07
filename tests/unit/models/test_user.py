#!/usr/bin/python
# -*- coding: utf-8 -*-

from mock import Mock, patch
from datetime import datetime
from ujson import dumps

from preggy import expect
from tornado.testing import gen_test

from holmes.config import Config
from holmes.models import User
from tests.unit.base import ApiTestCase
from tests.fixtures import UserFactory


class TestUser(ApiTestCase):
    def mock_request(self, status_code, effective_url):
        def handle(*args, **kw):
            response_mock = Mock(status_code=status_code, effective_url=effective_url)
            if 'callback' in kw:
                kw['callback'](response_mock)
            else:
                args[-1](response_mock)

        client = Mock()
        self.server.application.http_client = client
        client.fetch.side_effect = handle

    def test_can_create_user(self):
        user = UserFactory.create()

        expect(str(user)).to_be_like('%s' % user.email)

        expect(user.id).not_to_be_null()
        expect(user.fullname).to_equal('Marcelo Jorge Vieira')
        expect(user.email).to_equal('marcelo.vieira@corp.globo.com')
        expect(user.is_superuser).to_equal(True)
        last_login = datetime(2013, 12, 11, 10, 9, 8)
        expect(user.last_login).to_be_like(last_login)

    def test_can_convert_user_to_dict(self):
        user = UserFactory.create()

        user_dict = user.to_dict()

        expect(user_dict['fullname']).to_equal(user.fullname)
        expect(user_dict['email']).to_equal(user.email)
        expect(user_dict['is_superuser']).to_equal(user.is_superuser)
        expect(user_dict['last_login']).to_equal(user.last_login)

    def test_can_get_user_by_email(self):
        self.db.query(User).delete()

        user = UserFactory.create()

        loaded_user = User.by_email(user.email, self.db)
        expect(loaded_user.id).to_equal(user.id)

        invalid_user = User.by_email('blah@corp.globo.com', self.db)
        expect(invalid_user).to_be_null()

    @gen_test
    def test_authenticate_user_not_valid_for_this_app(self):
        self.db.query(User).delete()

        UserFactory(email='test@test.com')

        mock_response = Mock(
            code=200,
            body='{"issued_to": "222", "email": "test@test.com"}'
        )

        def handle_request(url, handler, proxy_host, proxy_port):
            handler(mock_response)

        fetch_mock = Mock()
        fetch_mock.side_effect = handle_request

        config = Config()
        config.GOOGLE_CLIENT_ID = '000'

        access_token = '111'

        User.authenticate(
            access_token,
            fetch_mock,
            self.db,
            config,
            callback=self.stop
        )

        response = self.wait()

        expect(response.get('status')).to_equal(401)
        expect(response.get('reason')).to_equal(
            "Token's client ID does not match app's."
        )

    @gen_test
    def test_authenticate_unauthorized_user(self):
        self.db.query(User).delete()

        mock_response = Mock(
            code=200,
            body='{"issued_to": "000", "email": "test@test.com"}'
        )

        def handle_request(url, handler, proxy_host, proxy_port):
            handler(mock_response)

        fetch_mock = Mock()
        fetch_mock.side_effect = handle_request

        config = Config()
        config.GOOGLE_CLIENT_ID = '000'

        access_token = '111'

        User.authenticate(
            access_token,
            fetch_mock,
            self.db,
            config,
            callback=self.stop
        )

        response = self.wait()

        expect(response.get('status')).to_equal(403)
        expect(response.get('reason')).to_equal('Unauthorized user')

    @gen_test
    @patch('datetime.datetime')
    def test_authenticate(self, datetime_mock):
        dt = datetime(2014, 2, 14, 15, 0, 30)
        datetime_mock.now.return_value = dt

        self.db.query(User).delete()

        UserFactory(email='test@test.com')

        mock_response = Mock(
            code=200,
            body='{"issued_to": "000", "email": "test@test.com"}'
        )

        def handle_request(url, handler, proxy_host, proxy_port):
            handler(mock_response)

        fetch_mock = Mock()
        fetch_mock.side_effect = handle_request

        config = Config()
        config.GOOGLE_CLIENT_ID = '000'

        access_token = '111'

        User.authenticate(
            access_token,
            fetch_mock,
            self.db,
            config,
            callback=self.stop
        )

        response = self.wait()

        expect(response).to_be_like({
            'status': 200,
            'user': {
                'is_superuser': True,
                'fullname': u'Marcelo Jorge Vieira',
                'last_login': dt,
                'email': u'test@test.com'
            }
        })

        loaded_user = User.by_email('test@test.com', self.db)
        expect(loaded_user.last_login).to_equal(dt)

    @gen_test
    def test_authenticate_invalid_token(self):
        self.db.query(User).delete()

        UserFactory(email='test@test.com')

        mock_response = Mock(
            code=400,
            body=dumps({
                "error": "invalid_token",
                "error_description": "Invalid Value"
            })
        )

        def handle_request(url, handler, proxy_host, proxy_port):
            handler(mock_response)

        fetch_mock = Mock()
        fetch_mock.side_effect = handle_request

        config = Config()
        config.GOOGLE_CLIENT_ID = '000'

        access_token = '111'

        User.authenticate(
            access_token,
            fetch_mock,
            self.db,
            config,
            callback=self.stop
        )

        response = self.wait()

        expect(response).to_be_like({
            'status': 400,
            'reason': 'Error',
            'details': '{"error_description":"Invalid Value", \
                         "error":"invalid_token"}'
        })
