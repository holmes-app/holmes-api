#!/usr/bin/python
# -*- coding: utf-8 -*-

from preggy import expect
from tornado.testing import gen_test
from tornado.httpclient import HTTPError
from ujson import loads, dumps

from holmes.models import User
from tests.fixtures import UserFactory
from tests.unit.base import ApiTestCase


class TestUsersLocaleHandler(ApiTestCase):

    @gen_test
    def test_can_get_user_locale(self):
        user = UserFactory.create(locale='pt_BR')

        response = yield self.authenticated_fetch(
            '/users/locale/',
            user_email=user.email
        )

        expect(response.code).to_equal(200)

        locale_data = loads(response.body)

        expect(locale_data.get('locale')).to_equal('pt_BR')

    @gen_test
    def test_can_get_user_locale_as_anonymous(self):
        try:
            yield self.anonymous_fetch(
                '/users/locale/',
                method='GET'
            )
        except HTTPError, e:
            expect(e).not_to_be_null()
            expect(e.code).to_equal(401)
            expect(e.response.reason).to_be_like('Unauthorized')
            expect(e.response.body).to_be_like('Unauthorized')
        else:
            assert False, 'Should not have got this far'

    @gen_test
    def test_can_save_user_locale(self):
        user = UserFactory.create(locale='pt_BR')

        loaded_user = User.by_email(user.email, self.db)
        expect(loaded_user.id).to_equal(user.id)
        expect(loaded_user.locale).to_equal('pt_BR')

        response = yield self.authenticated_fetch(
            '/users/locale/',
            user_email=user.email,
            method='POST',
            body=dumps({'locale': 'es_ES'})
        )

        expect(response.code).to_equal(200)
        expect(loads(response.body)).to_equal('OK')

        loaded_user = User.by_email(user.email, self.db)
        expect(loaded_user.id).to_equal(user.id)
        expect(loaded_user.locale).to_equal('es_ES')

    @gen_test
    def test_can_save_user_locale_as_anonymous(self):
        try:
            yield self.anonymous_fetch(
                '/users/locale/',
                method='POST',
                body=dumps({'locale': 'es_ES'})
            )
        except HTTPError, e:
            expect(e).not_to_be_null()
            expect(e.code).to_equal(401)
            expect(e.response.reason).to_be_like('Unauthorized')
            expect(e.response.body).to_be_like('Unauthorized')
        else:
            assert False, 'Should not have got this far'
