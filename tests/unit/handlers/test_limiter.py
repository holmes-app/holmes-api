#!/usr/bin/python
# -*- coding: utf-8 -*-

from preggy import expect
from tornado.testing import gen_test
from tornado.httpclient import HTTPError
from ujson import loads, dumps

from tests.unit.base import ApiTestCase
from tests.fixtures import LimiterFactory, UserFactory

from holmes.models import Limiter, User


class TestLimiterHandler(ApiTestCase):

    @gen_test
    def test_can_get_limiters(self):
        self.db.query(Limiter).delete()

        LimiterFactory.create(url='http://test.com/', value=100)
        LimiterFactory.create(url='http://globo.com/', value=2)

        response = yield self.authenticated_fetch('/limiters')

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

        response = yield self.authenticated_fetch('/limiters')

        expect(response.code).to_equal(200)

        limiters = loads(response.body)

        expect(limiters).to_length(0)

    @gen_test
    def test_cant_save_limiters_as_anonymous_user(self):
        self.db.query(Limiter).delete()

        try:
            yield self.anonymous_fetch(
                '/limiters', method='POST', body=dumps({
                    'url': 'http://globo.com/',
                    'maxValue': 10
                })
            )
        except HTTPError, e:
            expect(e).not_to_be_null()
            expect(e.code).to_equal(401)
            expect(e.response.reason).to_be_like('Unauthorized')
            expect(e.response.body).to_be_like('Unauthorized')
        else:
            assert False, 'Should not have got this far'

    @gen_test
    def test_cant_save_limiters_as_normal_user(self):
        self.db.query(User).delete()
        user = UserFactory(email='normalser@user.com', is_superuser=False)

        try:
            yield self.authenticated_fetch(
                '/limiters', user_email=user.email, method='POST', body=dumps({
                    'url': 'http://globo.com/',
                    'maxValue': 10
                })
            )
        except HTTPError, e:
            expect(e).not_to_be_null()
            expect(e.code).to_equal(401)
            expect(e.response.reason).to_be_like('Unauthorized')
        else:
            assert False, 'Should not have got this far'

    @gen_test
    def test_can_save_limiters_as_superuser(self):
        self.db.query(Limiter).delete()
        self.db.query(User).delete()
        user = UserFactory(email='superuser@user.com', is_superuser=True)

        response = yield self.authenticated_fetch(
            '/limiters', user_email=user.email, method='POST', body=dumps({
                'url': 'http://globo.com/',
                'maxValue': 10
            })
        )
        expect(response).not_to_be_null()
        expect(response.code).to_equal(200)

        loaded_limiter = Limiter.by_url('http://globo.com/', self.db)
        expect(loaded_limiter).not_to_be_null()

    @gen_test
    def test_cant_save_limiters_with_empty_values_as_superuser(self):
        self.db.query(Limiter).delete()
        self.db.query(User).delete()
        user = UserFactory(email='superuser@user.com', is_superuser=True)

        try:
            yield self.authenticated_fetch(
                '/limiters', user_email=user.email, method='POST', body='{}'
            )
        except HTTPError, e:
            expect(e).not_to_be_null()
            expect(e.code).to_equal(400)
            expect(e.response.body).to_equal(
                '{"reason":"Not url or value","description":"Not url or value"}'
            )

    @gen_test
    def test_cant_save_limiters_as_anonymous_user(self):
        # TODO: verify in holmes-web if this endpoint is ok
        try:
            yield self.anonymous_fetch(
                '/limiters', method='POST', body='{}'
            )
        except HTTPError, e:
            expect(e).not_to_be_null()
            expect(e.code).to_equal(401)
            expect(e.response.reason).to_be_like('Unauthorized')
            expect(e.response.body).to_be_like('Unauthorized')
        else:
            assert False, 'Should not have got this far'

    @gen_test
    def test_cant_delete_limiter_as_anonymous_user(self):
        try:
            yield self.anonymous_fetch(
                '/limiters/1', method='DELETE'
            )
        except HTTPError:
            expect(e).not_to_be_null()
            expect(e.code).to_equal(401)
            expect(e.response.reason).to_be_like('Unauthorized')
        else:
            assert False, 'Should not have got this far'

    @gen_test
    def test_cant_delete_limiter_as_normal_user(self):
        self.db.query(Limiter).delete()
        limiter = LimiterFactory.create()
        self.db.query(User).delete()
        user = UserFactory(email='normalser@user.com', is_superuser=False)

        loaded_limiter = Limiter.by_id(limiter.id, self.db)
        expect(loaded_limiter).not_to_be_null()

        try:
            yield self.authenticated_fetch(
                '/limiters/%d' % limiter.id, user_email=user.email,
                method='DELETE'
            )
        except HTTPError, e:
            expect(e).not_to_be_null()
            expect(e.code).to_equal(401)
            expect(e.response.reason).to_be_like('Unauthorized')
        else:
            assert False, 'Should not have got this far'

        loaded_limiter = Limiter.by_id(limiter.id, self.db)
        expect(loaded_limiter).not_to_be_null()

    @gen_test
    def test_can_delete_limiter_as_superuser(self):
        self.db.query(Limiter).delete()
        limiter = LimiterFactory.create()
        self.db.query(User).delete()
        user = UserFactory(email='superuser@user.com', is_superuser=True)

        loaded_limiter = Limiter.by_id(limiter.id, self.db)
        expect(loaded_limiter).not_to_be_null()

        response = yield self.authenticated_fetch(
            '/limiters/%d' % limiter.id, user_email=user.email,
            method='DELETE'
        )

        expect(response.code).to_equal(204)
        expect(response.body).to_length(0)

        loaded_limiter = Limiter.by_id(limiter.id, self.db)
        expect(loaded_limiter).to_be_null()

    @gen_test
    def test_cant_delete_limiter_with_empty_values_as_superuser(self):
        self.db.query(Limiter).delete()
        self.db.query(User).delete()
        user = UserFactory(email='superuser@user.com', is_superuser=True)

        try:
            yield self.authenticated_fetch(
                '/limiters', user_email=user.email, method='DELETE'
            )
        except HTTPError, e:
            expected = {
                'reason': 'Invalid data',
                'description': 'Invalid data'
            }
            expect(e).not_to_be_null()
            expect(e.code).to_equal(400)
            expect(e.response.reason).to_equal('Bad Request')
            expect(loads(e.response.body)).to_equal(expected)
        else:
            assert False, 'Should not have got this far'

    @gen_test
    def test_cant_delete_nonexistent_limiter_as_superuser(self):
        self.db.query(Limiter).delete()
        self.db.query(User).delete()
        user = UserFactory(email='superuser@user.com', is_superuser=True)

        try:
            yield self.authenticated_fetch(
                '/limiters/1', user_email=user.email, method='DELETE'
            )
        except HTTPError, e:
            expected = {
                'reason': 'Not Found',
                'description': 'Not Found'
            }

            expect(e).not_to_be_null()
            expect(e.code).to_equal(404)
            expect(e.response.reason).to_equal('Not Found')
            expect(loads(e.response.body)).to_equal(expected)
        else:
            assert False, 'Should not have got this far'

    @gen_test
    def test_cant_delete_limiter_as_anonymous_user(self):
        try:
            yield self.anonymous_fetch(
                '/limiters/1', method='DELETE'
            )
        except HTTPError, e:
            expect(e).not_to_be_null()
            expect(e.code).to_equal(401)
            expect(e.response.reason).to_be_like('Unauthorized')
            expect(e.response.body).to_be_like('Unauthorized')
        else:
            assert False, 'Should not have got this far'

    @gen_test
    def test_cant_delete_limiter_as_inexistent_user(self):
        try:
            yield self.authenticated_fetch(
                '/limiters/1', user_email='inexistent@email.com', method='DELETE'
            )
        except HTTPError, e:
            expect(e).not_to_be_null()
            expect(e.code).to_equal(401)
            expect(e.response.reason).to_be_like('Unauthorized')
            expect(e.response.body).to_be_like('Unauthorized')
        else:
            assert False, 'Should not have got this far'
